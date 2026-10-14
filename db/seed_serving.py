"""Seed serving.* from a dataset file (the UI's globals contract, origin='reference').

Idempotent: TRUNCATEs every serving table it owns, then inserts. UI-vocabulary
globals go verbatim into serving.ui_config; data-bearing globals are flattened
into their tables. compOrder is NOT seeded (the API derives it from
serving.competitors ordering); PATENTS rows are stored flat with the two
orderings needed to rebuild byArea and byAssignee exactly.

Every field a record carries is written to the column of the same name, when the
table has one; a field with no column goes into the table's `extra` jsonb (merged back into
the row on serve). Either way it is named in the report, never dropped silently.

Usage:  python db/seed_serving.py [--recycle] [dataset.json]
        --recycle  also empties every other data table in every schema (documents,
                   extracted, metrics runs, provenance): a database switch, not a reseed.
                   After it, the database holds this dataset and nothing else.
Env:    KSSL_DSN      (default: host=127.0.0.1 port=5460 dbname=kssl user=postgres password=kssl)
        KSSL_DATASET  (default: ../reference_dataset.json next to this file; the path
                       argument wins)
Build a dataset from a client datapack with db/build_dataset.py.
"""

import json
import os
import re
import sys

# UTF-8 safe printing on Windows consoles.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import psycopg2
from psycopg2.extras import Json, execute_values

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DSN = "host=127.0.0.1 port=5460 dbname=kssl user=postgres password=kssl"
DSN = os.environ.get("KSSL_DSN", DEFAULT_DSN)
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
RECYCLE = "--recycle" in sys.argv[1:]
DATASET = ARGS[0] if ARGS else os.environ.get(
    "KSSL_DATASET", os.path.join(HERE, "..", "reference_dataset.json"))

ORIGIN = "reference"

# Globals that live in real tables; everything else goes to ui_config verbatim.
TABLE_BACKED = {
    "competitors", "compOrder",
    "competitiveCards", "marketCards", "techCards",
    "details", "matchups", "tenders", "PATENTS",
    "geoData", "geoComps", "innovations", "KSSL_PARTNERS",
    "sourceRegistry", "companySources",
}

# All serving tables this seeder owns (truncated before insert).
OWNED_TABLES = [
    "serving.ui_config", "serving.competitors", "serving.signal_card",
    "serving.signal_detail", "serving.matchup", "serving.tender",
    "serving.patent", "serving.geo_presence", "serving.geo_comp",
    "serving.innovation", "serving.partner", "serving.source_registry",
    "serving.company_source",
    # FK children of serving.competitors: TRUNCATE refuses the parent without them
    "serving.competitor_news", "serving.competitor_metrics", "serving.competitor_structure",
]

# Tables a recycle keeps: static vocabulary written by the schema, not data.
RECYCLE_KEEP = {"metrics.stage_order"}


def jz(v):
    """jsonb-wrap dicts/lists; pass scalars/None through."""
    return Json(v) if isinstance(v, (dict, list)) else v


def jall(v):
    """jsonb-wrap any non-null value (for mixed-type jsonb columns)."""
    return Json(v) if v is not None else None


def insert_rows(cur, table, columns, rows):
    if not rows:
        return
    cols = ", ".join('"%s"' % c for c in columns)
    execute_values(cur, 'INSERT INTO %s (%s) VALUES %%s' % (table, cols), rows)


DROPPED = {}
STASHED = {}


def insert_records(cur, table, records, fixed):
    """Insert dicts, one row each: every field the table has a column for, plus the
    `fixed` columns (ord, keys, origin) given per record as a dict."""
    schema, name = table.split(".")
    cur.execute("SELECT column_name, data_type FROM information_schema.columns "
                "WHERE table_schema = %s AND table_name = %s", (schema, name))
    types = dict(cur.fetchall())
    if not records:
        return
    fields = sorted({k for r in records for k in r if k in types} - set(fixed[0]))
    extra = sorted({k for r in records for k in r if k not in types})
    if extra and "extra" in types:
        # no column of its own: kept in `extra`, merged back into the row on serve
        records = [dict(r, extra={k: r[k] for k in extra if k in r} or None) for r in records]
        fields = sorted(set(fields) | {"extra"})
        STASHED[table] = extra
    elif extra:
        DROPPED[table] = extra
    cols = list(fixed[0]) + fields

    def val(col, v):
        if types[col] == "jsonb":
            return jall(v)
        return json.dumps(v) if isinstance(v, (dict, list)) else v

    rows = [tuple(val(c, f[c]) for c in fixed[i]) + tuple(val(c, r.get(c)) for c in fields)
            for i, (r, f) in enumerate(zip(records, fixed))]
    insert_rows(cur, table, cols, rows)


def recycle(cur):
    """Empty every table in every data schema, so nothing of the previous dataset
    survives anywhere -- not only in the tables this seeder writes."""
    cur.execute("""SELECT format('%I.%I', schemaname, tablename) FROM pg_tables
                   WHERE schemaname NOT IN ('pg_catalog', 'information_schema')""")
    tables = [t for (t,) in cur.fetchall() if t not in RECYCLE_KEEP]
    if tables:
        cur.execute("TRUNCATE " + ", ".join(tables) + " RESTART IDENTITY")
    return tables


def main():
    with open(DATASET, encoding="utf-8") as f:
        data = json.load(f)

    conn = psycopg2.connect(DSN)
    conn.autocommit = False
    cur = conn.cursor()

    wiped = recycle(cur) if RECYCLE else None
    cur.execute("TRUNCATE " + ", ".join(OWNED_TABLES))

    def fx(**cols):
        return dict(cols, origin=ORIGIN)

    # ---- ui_config: every global without a table, plus PATENTS aux pieces ----
    ui_rows = [(k, Json(v)) for k, v in data.items() if k not in TABLE_BACKED]
    patents = data["PATENTS"]
    ui_rows.append(("PATENTS.techAreas", Json(patents.get("techAreas", []))))
    ui_rows.append(("PATENTS._meta", Json(patents.get("_meta", {}))))
    insert_rows(cur, "serving.ui_config", ["key", "value"], ui_rows)

    # ---- competitors (dict keyed by comp id; key order = compOrder) ----
    comps = list(data["competitors"].items())
    insert_records(cur, "serving.competitors", [c for _, c in comps],
                   [fx(comp_id=cid, ord=i) for i, (cid, _) in enumerate(comps)])

    # ---- competitor news (dict comp id -> list); the table's own column names ----
    news = [(cid, n) for cid, rows in (data.get("competitorNews") or {}).items() for n in rows]
    insert_records(cur, "serving.competitor_news",
                   # only a full date fits the timestamp column; a month ("2026-03") stays in `date`
                   [dict(n, published_date=n.get("published_date") or (
                       n.get("date") if re.match(r"\d{4}-\d{2}-\d{2}", str(n.get("date") or "")) else None))
                    for _, n in news],
                   [fx(comp_id=cid) for cid, _ in news])

    # ---- signal cards: three lanes, one table ----
    cards = [(lane, i, c) for lane, gname in (("competitive", "competitiveCards"),
                                               ("market", "marketCards"),
                                               ("tech", "techCards"))
             for i, c in enumerate(data[gname])]
    insert_records(cur, "serving.signal_card", [c for _, _, c in cards],
                   [fx(lane=lane, ord=i) for lane, i, _ in cards])

    # ---- details (dict keyed by card id) ----
    dets = list(data["details"].items())
    insert_records(cur, "serving.signal_detail", [d for _, d in dets],
                   [fx(id=did, ord=i) for i, (did, _) in enumerate(dets)])

    # ---- matchups (dict keyed by numeric-string id) ----
    mus = list(data["matchups"].items())
    insert_records(cur, "serving.matchup", [m for _, m in mus],
                   [fx(matchup_id=int(mid)) for mid, _ in mus])

    # ---- tenders (list) ----
    insert_records(cur, "serving.tender", data["tenders"],
                   [fx(ord=i) for i in range(len(data["tenders"]))])

    # ---- PATENTS: flat rows; ord = position flattening byArea, assignee_ord =
    #      position flattening byAssignee (the same rows, different order) ----
    by_area_flat = [p for lst in patents.get("byArea", {}).values() for p in lst]
    by_asg_flat = [p for lst in patents.get("byAssignee", {}).values() for p in lst]
    asg_ord = {p["no"]: i for i, p in enumerate(by_asg_flat)}
    if len(asg_ord) != len(by_asg_flat):
        raise SystemExit("patent 'no' values are not unique; cannot map assignee order")
    insert_records(cur, "serving.patent", by_area_flat,
                   [fx(ord=i, assignee_ord=asg_ord.get(p["no"], i)) for i, p in enumerate(by_area_flat)])

    # ---- geoData (dict comp -> dict country -> list of entries) ----
    geo = [(cid, ci, country, ki, i, e)
           for ci, (cid, countries) in enumerate(data["geoData"].items())
           for ki, (country, entries) in enumerate(countries.items())
           for i, e in enumerate(entries)]
    insert_records(cur, "serving.geo_presence", [g[-1] for g in geo],
                   [fx(comp_id=cid, comp_ord=ci, country=country, country_ord=ki, ord=i)
                    for cid, ci, country, ki, i, _ in geo])

    # ---- geoComps (list) ----
    insert_records(cur, "serving.geo_comp", data["geoComps"],
                   [fx(ord=i) for i in range(len(data["geoComps"]))])

    # ---- innovations (dict area -> list) ----
    inn = [(area, ai, i, it) for ai, (area, items) in enumerate(data["innovations"].items())
           for i, it in enumerate(items)]
    insert_records(cur, "serving.innovation", [it for *_, it in inn],
                   [fx(area=area, area_ord=ai, ord=i) for area, ai, i, _ in inn])

    # ---- KSSL_PARTNERS: the client's own partners (list) ----
    insert_records(cur, "serving.partner", data["KSSL_PARTNERS"],
                   [fx(ord=i) for i in range(len(data["KSSL_PARTNERS"]))])

    # ---- sourceRegistry (list) ----
    insert_records(cur, "serving.source_registry", data["sourceRegistry"],
                   [fx(ord=i) for i in range(len(data["sourceRegistry"]))])

    # ---- companySources (dict company -> list of urls) ----
    rows = []
    for ci, (company, urls) in enumerate(data["companySources"].items()):
        for i, url in enumerate(urls):
            rows.append((company, ci, i, url, ORIGIN))
    insert_rows(cur, "serving.company_source",
                ["company", "comp_ord", "ord", "url", "origin"], rows)

    conn.commit()

    # Report.
    if wiped is not None:
        print("recycled: emptied %d tables across every schema" % len(wiped))
    for t in OWNED_TABLES:
        cur.execute("SELECT count(*) FROM " + t)
        print("%-32s %5d rows" % (t, cur.fetchone()[0]))
    for t, fields in STASHED.items():
        print("kept in extra: %s %s" % (t, ", ".join(fields)))
    for t, fields in DROPPED.items():
        print("no column for (not stored): %s %s" % (t, ", ".join(fields)))
    cur.close()
    conn.close()
    print("seeded from", os.path.abspath(DATASET))


if __name__ == "__main__":
    main()
