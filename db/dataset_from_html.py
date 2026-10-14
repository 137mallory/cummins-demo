"""Build the dashboard dataset straight from a standalone 137Parallax HTML export.

The export embeds the reference app's globals (the same contract the dashboard reads) in
its first <script>. This runs that script in node, collects every top-level global, and
writes them verbatim as dataset.json. What the HTML shows is what the platform serves.

    python db/dataset_from_html.py <export.html> <out/dataset.json> [--base <old dataset.json>] [--pack <pack dir>] [--images] [--drop-blank]
    python db/seed_serving.py --recycle <out/dataset.json>

The export's globals are kept as they are. Two things are added on top:

  platform_fields()  the fields the dashboard's views read, derived from the export's own
                     data (a competitor's `products` from PRODUCTS, `leadership` / `sales` /
                     `starting_year` ... from its `profile`, `competitorNews` from its moves,
                     the client as a `dir: client` competitor). `competitors[].threat` is the
                     dashboard's grade (high|medium|low); the export's prose read moves to
                     `assess`, and its model-count line to `threatNote`.
  attach_images()    (--images) each article's own picture (og:image, JSON-LD, or a visible body
                     image), read once from the article page and cached in
                     <pack>/article_images.json (db/article_images.py: only pictures that really
                     load and are real pictures), set on the news rows, signal cards, details,
                     regional entities and Gulf reference projects that link to it. Never a stock
                     or guessed picture; a record whose article gives none has none.
  apply_fills()      (--pack, when <pack>/spec_fills.json exists) verified datasheet values the
                     export left blank, each with its source; the matchups that use them are
                     re-derived by the export's own rules (db/spec_fills.py).
  merge_pack()       what only the research datapack holds (--pack): research gaps, fuel and
                     engine-dimension notes on products, date notes on moves, founding /
                     headcount / revenue notes, context-only sites, and the analysis behind
                     the client's own partners.

Key-level adjustments:
  - KOEL_PARTNERS (the export's older name) is served as KSSL_PARTNERS, the key the app reads,
    each row also given the `id` and `label` the app joins on (copied from `cid` and `name`).
  - client config keys the export does not carry (id, brand, markets, newsQuery) are taken
    from --base when given; `markets` is the export's own geoCountries when it has them.

Self-check: python db/dataset_from_html.py --demo
"""

import glob
import json
import math
import os
import re
import subprocess
import sys
import tempfile

RENAME = {"KOEL_PARTNERS": "KSSL_PARTNERS"}
CLIENT_CONFIG = ("id", "brand", "markets", "newsQuery")

# node: run the data script with just enough DOM stubs to not throw, then dump each
# top-level const/let/var/function-free global it declared.
NODE_DUMP = r"""
const fs = require('fs');
const [src, names, out] = process.argv.slice(2);
const stub = new Proxy(function(){}, {get: () => stub, apply: () => stub});
globalThis.document = stub; globalThis.window = globalThis; globalThis.localStorage = stub;
const code = fs.readFileSync(src, 'utf8');
const list = JSON.parse(fs.readFileSync(names, 'utf8'));
const body = code + '\n;return {' + list.map(n => JSON.stringify(n) + ':(typeof ' + n + "==='undefined'?undefined:" + n + ')').join(',') + '};';
fs.writeFileSync(out, JSON.stringify(new Function(body)()));
"""


def data_script(html):
    """The first <script> is the data; the rest is app code."""
    scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, re.S)
    if not scripts:
        raise SystemExit("no <script> in the export")
    return scripts[0]


def top_level_names(js):
    # declarations at the start of a line; the data script is a flat list of consts
    names = re.findall(r"^\s*(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=", js, re.M)
    return list(dict.fromkeys(names))


def extract(html_path):
    js = data_script(open(html_path, encoding="utf-8").read())
    names = top_level_names(js)
    with tempfile.TemporaryDirectory() as tmp:
        paths = {k: os.path.join(tmp, k) for k in ("src.js", "names.json", "out.json", "dump.js")}
        open(paths["src.js"], "w", encoding="utf-8").write(js)
        json.dump(names, open(paths["names.json"], "w"))
        open(paths["dump.js"], "w").write(NODE_DUMP)
        subprocess.run(["node", paths["dump.js"], paths["src.js"], paths["names.json"], paths["out.json"]],
                       check=True)
        return json.load(open(paths["out.json"], encoding="utf-8"))


def adapt(data, base=None):
    out = {RENAME.get(k, k): v for k, v in data.items()}
    out["KSSL_PARTNERS"] = [dict(r, id=str(r.get("cid")), label=r.get("name"))
                            for r in out.get("KSSL_PARTNERS") or []]
    client = dict(out.get("client") or {})
    for k in CLIENT_CONFIG:
        if k not in client and base and k in (base.get("client") or {}):
            client[k] = base["client"][k]
    # the export names the client by its geoComps id; the app joins on that
    bf = next((g for g in out.get("geoComps") or [] if g.get("isBf")), None)
    if bf:
        client["id"] = bf["id"]
    if out.get("geoCountries"):
        client["markets"] = out["geoCountries"]
    out["client"] = client
    return out


# ------------------------------------------------------------------ platform fields

GRADE = {"threat": "high", "watch": "medium", "fav": "low"}
LEVEL_DIR = {"THREAT": "threat", "WATCH": "watch", "OPPORTUNITY": "fav"}
CLIENT_OWNER = "CLIENT"          # PRODUCTS[].owner of the client's own catalogue


def domain(url):
    m = re.match(r"^https?://(?:www\.)?([^/]+)", url or "")
    return m.group(1) if m else ""


def js(v):
    """A number as the export's JavaScript prints it: 715, 18.13, never 715.0."""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def spec_rows(p):
    """The export's View Specs rows for one PRODUCTS entry, in its order, labels and units
    (renderSpec in the export), with empty rows left out. Rounding is JavaScript's
    toFixed (half up), not Python's half-to-even: 288.5 kW/t prints 289, as the export does."""
    def pair(a, b, unit_a, unit_b):
        if p.get(a) is not None:
            return f"{js(p[a])} {unit_a} / {js(p[b]) if p.get(b) is not None else '—'} {unit_b}"
        return f"{js(p[b])} {unit_b}" if p.get(b) is not None else None
    dash = lambda k: js(p[k]) if p.get(k) is not None else "—"
    F = [
        ("Standby rating", pair("standby_kva", "standby_kw", "kVA", "kW")),
        ("Prime rating", pair("prime_kva", "prime_kw", "kVA", "kW")),
        ("Continuous rating", f"{js(p['continuous_kw'])} kW" if p.get("continuous_kw") is not None else None),
        ("Frequency", f"{js(p['hz'])} Hz" if p.get("hz") else None),
        ("Engine", p.get("engine")), ("Cylinders", p.get("cyl")),
        ("Displacement", f"{js(p['disp'])} L" if p.get("disp") is not None else None),
        ("Aspiration", p.get("asp")),
        ("Bore x stroke", f"{p['bore']} mm" if p.get("bore") else None),
        ("Rated speed", f"{js(p['rpm'])} rpm" if p.get("rpm") else None),
        ("Fuel", p.get("fuel")),
        ("Fuel at 100 / 75 / 50 % load",
         f"{dash('f100')} / {dash('f75')} / {dash('f50')} L/h"
         if any(p.get(k) is not None for k in ("f100", "f75", "f50")) else None),
        ("Specific fuel at 100 %", f"{js(p['sfc'])} L/h per 100 kW" if p.get("sfc") is not None else None),
        ("Dimensions L x W x H",
         f"{dash('L')} x {dash('W')} x {dash('H')} mm" if any(p.get(k) is not None for k in "LWH") else None),
        ("Footprint", f"{js(p['area'])} m² · {dash('kwm2')} kW/m²" if p.get("area") is not None else None),
        ("Dry weight", f"{int(p['wt']):,} kg · " + (f"{math.floor(p['kwkg'] * 1000 + 0.5)} kW/t" if p.get("kwkg") is not None else "—")
         if p.get("wt") is not None else None),
        ("Emissions", p.get("emis")), ("Alternator", p.get("alt")), ("Controller", p.get("ctl")),
        ("Voltage", p.get("volt")), ("Ambient / derate", p.get("amb")), ("Data centre rating", p.get("dcr")),
        ("Notes", p.get("notes")),
    ]
    if p.get("category") == "BESS":
        RL = {"Alternator": "Energy / configuration", "Ambient / derate": "Battery system",
              "Data centre rating": "Target segments", "Controller": "Energy management"}
        F = [(RL.get(k, k), v) for k, v in F]
    return [(k, str(v)) for k, v in F if v not in (None, "")]


def product_row(p):
    specs = dict(spec_rows(p))
    # a verified fill says what it is and where it came from (db/spec_fills.py)
    fb = p.get("fill_basis") or {}
    if "f100" in fb:
        specs["Fuel figure basis"] = "; ".join(
            f"{k.replace('f', '')} %: {fb[k]}" for k in ("f100", "f75", "f50") if k in fb)
    if "wt" in fb:
        specs["Weight basis"] = fb["wt"]
    specs.update(p.get("fill_rows") or {})
    if p.get("fill_sources"):
        specs["Datasheet (verified fill)"] = " · ".join(p["fill_sources"])
    return {
        "id": p["pid"], "name": p["model"], "category": p.get("category"), "series": p.get("series"),
        "specs": specs,
        "image": p.get("image"), "image_src": p.get("image_src"), "image_basis": p.get("image_basis"),
        "source": domain(p.get("sheet") or p.get("src")),
        "source_url": p.get("sheet") or p.get("src"),
        "sources": [u for u in (p.get("src"), p.get("sheet")) if u],
        "tier": p.get("conf"), "hz": p.get("hz"), "band": p.get("band"), "mu": p.get("mu"),
    }


def sourced(value, detail, url, line):
    return {"value": value, "detail": detail or "", "url": url, "line": line} if value and url and line else None


def geo_facilities(rows):
    out = []
    for country, lst in (rows or {}).items():
        for g in lst:
            if "tracked range" in (g.get("name") or ""):
                continue      # a product rating range, not a site
            url = next((s.get("url") for s in g.get("srcs") or [] if s.get("url")), None)
            r = sourced(g.get("name"), g.get("val"), url, g.get("note") or f"{g.get('name')}, {country}.")
            if r:
                out.append(dict(r, country=country))
    return out


def company_fields(c, prof, products, geo_rows, cid):
    first = (prof.get("profile_sources") or [None])[0] or next(
        (s.get("url") for s in c.get("srcs") or [] if s.get("url")), None)
    founded = str(prof.get("founded") or "")
    return {
        "products": products,
        "leadership": [r for r in (sourced(l.get("name"), l.get("title"), l.get("source_url"),
                                           f"{l.get('name')}, {l.get('title')}.")
                                   for l in prof.get("leadership") or []) if r],
        "facilities": geo_facilities(geo_rows),
        "sales": [r for r in [sourced(prof.get("revenue"), "", first, prof.get("revenue"))] if r],
        "starting_year": int(founded) if founded.isdigit() else None,
        "company_size": prof.get("employees"),
        "strategic_positioning": prof.get("positioning"),
        "global_locations": list((geo_rows or {}).keys()),
    }


def news_rows(prof, cid):
    return [{"title": m.get("headline"), "description": m.get("summary"), "source": domain(m.get("url")),
             "date": m.get("date"), "category": m.get("category"), "url": m.get("url"),
             "country": m.get("country"), "level": m.get("level"), "analysis": m.get("analysis"),
             "card": m.get("card"), "pillar": m.get("pillar")}
            for m in prof.get("moves") or []]


def drop_blank(out):
    """--drop-blank: products with no fuel, size or weight on record (and no verified
    display rows) are left out, with the matchups built on them, and matchup spec rows
    blank on either side are hidden (operator, 2026-09-29).
    A product whose `mu` pointed at a dropped matchup re-points to another of its own."""
    P = out.get("PRODUCTS") or {}
    gone = {pid for pid, p in P.items() if p.get("category") != "BESS"
            and all(p.get(k) is None for k in ("f100", "L", "wt")) and not p.get("fill_rows")}
    for pid in gone:
        del P[pid]
    mus = out.get("matchups") or {}
    out["matchups"] = {k: v for k, v in mus.items() if v.get("_cp") not in gone and v.get("_kp") not in gone}
    # and a spec row one side never published is hidden rather than shown as "—"
    blank = lambda v: v is None or str(v).strip() in ("", "—", "-")
    for mu in out["matchups"].values():
        mu["specs"] = [r for r in mu.get("specs") or [] if not (blank(r.get("cv")) or blank(r.get("kv")))]
    for pid, p in P.items():
        if p.get("mu") is not None and str(p["mu"]) not in out["matchups"]:
            alt = [k for k, v in out["matchups"].items() if pid in (v.get("_cp"), v.get("_kp"))]
            p["mu"] = int(alt[0]) if alt else None
    return sorted(gone)


def winner_flag_to_direction(out):
    """The export's matchup spec rows carry `hi` as WHO WINS THE ROW (True = the client, False = the rival, None =
    undecided or not ranked): the rows it sets are exactly its own advBf / advComp lists. Everything in the app
    (lib/edge.js, specs.js, compareProducts.js) reads `hi` as DIRECTION (True = a higher figure is better), so
    where the client won on a lower figure (weight, length, footprint) the app scored it as a loss and called all
    66 pairs "rival ahead", 24 of which the export itself calls "Cummins ahead".
    The direction is recovered from the winner and the two numbers: the winner's figure is the better one, so
    `hi` = (client figure > rival figure) == (client won). Rows with no pair of numbers are left undecided."""
    n = 0
    for m in (out.get("matchups") or {}).values():
        for r in m.get("specs") or []:
            if r.get("hi") is None:
                continue
            c, k = r.get("cn"), r.get("kn")
            if c is None or k is None or c == k:
                r["hi"] = None
                continue
            r["hi"] = (k > c) == bool(r["hi"])
            n += 1
    return n


def platform_fields(out):
    """Add the fields the dashboard's views read, from the export's own data."""
    prods = list((out.get("PRODUCTS") or {}).values())
    geo = out.get("geoData") or {}
    news = {}
    for cid, c in (out.get("competitors") or {}).items():
        prof = c.get("profile") or {}
        own = [product_row(p) for p in prods if p.get("owner") == cid]
        # the export's `threat` is the prose read and `assess` the model-count line; the
        # dashboard reads `threat` as a grade, `assess` as the read, `threatNote` as the line
        c.update(company_fields(c, prof, own, geo.get(cid), cid),
                 assess=c.get("threat") or "", threatNote=c.get("assess") or "",
                 threat=GRADE.get(c.get("dir"), "medium"), country=c.get("hq"))
        news[cid] = news_rows(prof, cid)
    cl = out.get("client") or {}
    cid = cl.get("id")
    if cid and cid not in out["competitors"]:
        prof = cl.get("profile") or {}
        own = [product_row(p) for p in prods if p.get("owner") == CLIENT_OWNER]
        bf = next((g for g in out.get("geoComps") or [] if g.get("isBf")), {})
        entry = {"name": cl.get("name"), "dir": "client", "sector": prof.get("industry") or cl.get("sector"),
                 "hq": prof.get("hq_full") or bf.get("hq"), "threat": None,
                 "assess": prof.get("positioning") or "", "threatNote": "", "updates": "",
                 "center": {"id": cid, "label": cl.get("short") or cl.get("name")},
                 "partners": [], "site": cl.get("website"), "srcs": [], "profile": prof,
                 "country": bf.get("hq")}
        entry.update(company_fields(entry, prof, own, geo.get(cid), cid))
        out["competitors"][cid] = entry
        news[cid] = news_rows(prof, cid)
    out["competitorNews"] = news
    # the analyst's grade, stored with each card (the API derives one only where none is)
    for lane in ("competitiveCards", "marketCards", "techCards"):
        for card in out.get(lane) or []:
            card.setdefault("severity", GRADE.get(card.get("dir")))
    # the client's own partners, in the shape the partner panels read
    out["KSSL_PARTNERS"] = [dict(r, kind=r.get("rel"), ptype=r.get("rel"), note=r.get("role"),
                                 insight=r.get("role"))
                            for r in out.get("KSSL_PARTNERS") or []]
    return out


# ---------------------------------------------------------------------- datapack merge

def _key(s):
    return re.sub(r"[^a-z0-9]", "", str(s or "").lower())


def merge_pack(out, pack_dir):
    """Attach what only the research datapack holds. Joins on names; a record with no
    match is reported, never forced onto the wrong row."""
    unmatched = []
    packs = {}
    for f in glob.glob(os.path.join(pack_dir, "competitors", "*.json")):
        r = json.load(open(f, encoding="utf-8"))
        packs[_key(r["name"])] = r
    client_pack = json.load(open(os.path.join(pack_dir, "client", "cummins.json"), encoding="utf-8"))
    comps = out.get("competitors") or {}
    by_owner = {}
    for cid, c in comps.items():
        if c.get("dir") == "client":
            by_owner[cid] = client_pack
            continue
        prof_name = (c.get("profile") or {}).get("legal_name") or ""
        hit = next((r for k, r in packs.items()
                    if _key(r["name"]) in _key(c["name"]) or _key(c["name"]) in _key(r["name"])
                    or _key(r.get("legal_name")) == _key(prof_name)), None)
        if hit:
            by_owner[cid] = hit
        else:
            unmatched.append(f"competitor {c['name']}")
    prods = out.get("PRODUCTS") or {}
    for cid, r in by_owner.items():
        c = comps[cid]
        prof = c.setdefault("profile", {})
        if r.get("gaps"):
            c["gaps"] = r["gaps"]
        for k in ("founded_note", "employees_note", "revenue_note"):
            if r.get(k):
                prof[k] = r[k]
        # product notes, joined on the model name within this owner
        owner = CLIENT_OWNER if c.get("dir") == "client" else cid
        mine = {_key(p["model"]): p for p in prods.values() if p.get("owner") == owner}
        for rp in r.get("products") or []:
            notes = {k: rp[k] for k in ("fuel_consumption_basis", "engine_dimensions_note") if rp.get(k)}
            if not notes:
                continue
            p = mine.get(_key(rp["model"]))
            if not p:
                unmatched.append(f"product {r['name']} {rp['model']}")
                continue
            p.update(notes)
            row = next((x for x in c.get("products") or [] if x["id"] == p["pid"]), None)
            fb = p.get("fill_basis") or {}
            if row:
                # a verified fill replaces the pack's "not published" note for that figure
                if notes.get("fuel_consumption_basis") and "f100" not in fb:
                    row["specs"]["Fuel figure basis"] = notes["fuel_consumption_basis"]
                if notes.get("engine_dimensions_note") and "L" not in fb:
                    row["specs"]["Engine dimensions"] = notes["engine_dimensions_note"]
        # date notes on moves, joined on the headline
        for mv in r.get("movements") or []:
            if not mv.get("date_note"):
                continue
            hit = [m for m in prof.get("moves") or [] if _key(m.get("headline")) == _key(mv.get("headline"))]
            for m in hit:
                m["date_note"] = mv["date_note"]
            for n in (out.get("competitorNews") or {}).get(cid) or []:
                if _key(n.get("title")) == _key(mv.get("headline")):
                    n["date_note"] = mv["date_note"]
            if not hit:
                unmatched.append(f"move {mv['headline'][:60]}")
        # context-only sites: outside the three markets, so not on the geo map
        for g in r.get("geo_footprint") or []:
            if "context" in (g.get("notes") or "").lower() or "context" in (g.get("country") or "").lower():
                row = sourced(f"{g['facility_type']} · {g['city']}", g.get("entity"), g.get("source_url"),
                              g.get("notes") or "")
                if row and row["value"] not in {f["value"] for f in c.get("facilities") or []}:
                    c.setdefault("facilities", []).append(dict(row, country=g["country"], context=True))
    # the analysis behind each of the client's own partners
    why = {_key(p["partner"]): p for p in client_pack.get("partnerships") or []}
    for r in out.get("KSSL_PARTNERS") or []:
        hit = why.get(_key(r.get("name"))) or next(
            (p for k, p in why.items() if k[:12] and (k[:12] in _key(r.get("name")) or _key(r.get("name"))[:12] in k)), None)
        if not hit:
            unmatched.append(f"client partner {r.get('name')}")
            continue
        w = hit.get("why_it_matters") or {}
        if w.get("analysis"):
            r["insight"] = w["analysis"]
            r["mean"] = f"<b>{(w.get('level') or '').title()}:</b> {w['analysis']}"
        for k in ("since", "country", "scope", "source_url"):
            if hit.get(k):
                r[{"since": "date", "scope": "scope", "source_url": "src"}.get(k, k)] = hit[k]
    return out, unmatched


# --------------------------------------------------------------------------- article pictures

def attach_images(out, cache_path):
    """Set `image` on every news row, signal card, detail and dossier entry from its own article
    (db/article_images.py: og/JSON-LD/visible body image, checked to load and to be a real picture)."""
    from article_images import run, apply
    cache = run(out, cache_path)
    n, cleared = apply(out, cache)
    found = sum(1 for v in cache.values() if v.get("image"))
    print(f"article pictures: {found} of {len(cache)} article pages give a verified picture; "
          f"set on {n} records, {cleared} unverifiable ones cleared")
    return out


def demo():
    html = """<html><script>const client = {"name":"X","short":"X"};
const geoComps = [{"id":"X","name":"X","isBf":true}];
const KOEL_PARTNERS = [{"cid":1,"name":"P"}];
const geoCountries = ["A"];
function helper(){ return 1 }
</script><script>document.querySelector('#a').innerHTML = 1;</script></html>"""
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(html)
    d = adapt(extract(f.name), {"client": {"brand": "B", "id": "old"}})
    os.unlink(f.name)
    assert d["KSSL_PARTNERS"] == [{"cid": 1, "name": "P", "id": "1", "label": "P"}] and "KOEL_PARTNERS" not in d, d
    assert d["client"] == {"name": "X", "short": "X", "brand": "B", "id": "X", "markets": ["A"]}, d["client"]
    assert "helper" not in d
    print("demo ok")


def add_pack_products(out, pack_dir):
    """A competitor the export lists no products for (Volvo Penta) takes the products its research
    pack holds, as PRODUCTS entries, so platform_fields serves them like any other catalogue. Each
    gets its series page's own og:image. Nothing here overwrites a product the export carries."""
    prods = out.setdefault("PRODUCTS", {})
    owned = {p.get("owner") for p in prods.values()}
    added = []
    for f in sorted(glob.glob(os.path.join(pack_dir, "competitors", "*.json"))):
        r = json.load(open(f, encoding="utf-8"))
        cid = next((k for k, c in (out.get("competitors") or {}).items()
                    if c.get("dir") != "client" and k not in owned
                    and (_key(r["name"]) in _key(c["name"]) or _key(c["name"]) in _key(r["name"]))), None)
        if not cid:
            continue
        pics = {}
        for i, rp in enumerate(r.get("products") or [], 1):
            na = lambda v: None if not v or str(v).startswith("Not applicable") else v
            kva = rp.get("standby_kva")
            url = rp.get("source_url")
            if url not in pics:
                from article_images import candidates, check
                pics[url] = next((i for _, i in (candidates(url) or []) if check(i)), None) if url else None
            prods[f"{cid}-P{i}"] = {
                "pid": f"{cid}-P{i}", "owner": cid, "ownerName": r["name"], "model": rp["model"],
                "series": rp.get("series"), "category": rp.get("category") or "Engine",
                "hz": rp.get("frequency_hz"), "standby_kva": kva, "standby_kw": rp.get("standby_kw"),
                "prime_kva": rp.get("prime_kva"), "prime_kw": rp.get("prime_kw"),
                "engine": rp.get("engine_model"), "cyl": rp.get("cylinders"), "disp": rp.get("displacement_l"),
                "asp": rp.get("aspiration"), "rpm": rp.get("rated_rpm"), "fuel": rp.get("fuel"),
                "emis": rp.get("emissions"), "alt": na(rp.get("alternator")), "ctl": na(rp.get("controller")),
                "dcr": rp.get("data_center_rating"), "conf": rp.get("spec_confidence"), "src": url,
                "band": None if kva is None else "sub500" if kva < 500 else "mid" if kva <= 1000 else "hhp",
                "mu": None, "image": pics[url], "image_src": url if pics[url] else None,
                "image_basis": "series" if pics[url] else None,
            }
            added.append(f"{cid}-P{i}")
    return added


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo()
        sys.exit()
    opt = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
    base_path, pack_dir = opt("--base"), opt("--pack")
    args = [a for a in sys.argv[1:] if not a.startswith("--") and a not in (base_path, pack_dir)]
    if len(args) != 2:
        raise SystemExit(__doc__)
    base = json.load(open(base_path, encoding="utf-8")) if base_path else None
    data = adapt(extract(args[0]), base)
    # verified datasheet values the export left blank (see db/spec_fills.py)
    fills_path = os.path.join(pack_dir, "spec_fills.json") if pack_dir else None
    if fills_path and os.path.exists(fills_path):
        from spec_fills import apply_fills
        print("spec fills:", sorted(apply_fills(data, json.load(open(fills_path, encoding="utf-8")))))
    if "--drop-blank" in sys.argv:
        print("dropped blank products:", drop_blank(data))
    # verified product photos (db/product_images.py), copied into the frontend's public folder
    pi_path = os.path.join(pack_dir, "product_images.json") if pack_dir else None
    if pi_path and os.path.exists(pi_path):
        from product_images import apply as images_apply
        repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        print("product photos:", images_apply(data, json.load(open(pi_path, encoding="utf-8")),
                                              os.path.join(pack_dir, "product_images"),
                                              os.path.join(repo, "frontend", "public", "product-images")))
    # researched tenders (db/tender_research.py), served beside the export's own
    tr_path = os.path.join(pack_dir, "tenders_research.json") if pack_dir else None
    if tr_path and os.path.exists(tr_path):
        from tender_research import merge as merge_tenders
        print("researched tenders added:", merge_tenders(data, json.load(open(tr_path, encoding="utf-8"))))
    # verified status per tender (db/tender_status.py): before ranking, so an awarded or
    # cancelled tender never ranks as live
    st_path = os.path.join(pack_dir, "tender_status.json") if pack_dir else None
    if st_path and os.path.exists(st_path):
        from tender_status import apply as status_apply
        print("tender status checked:", status_apply(data, json.load(open(st_path, encoding="utf-8"))))
    # rank the tenders by value x Cummins product fit (db/tender_fit.py)
    fit_path = os.path.join(pack_dir, "tender_fit.json") if pack_dir else None
    if fit_path and os.path.exists(fit_path):
        from tender_fit import apply as fit_apply
        print("tenders ranked by value x fit:", fit_apply(data, json.load(open(fit_path, encoding="utf-8"))))
    act_path = os.path.join(pack_dir, "tender_actions.json") if pack_dir else None
    if act_path and os.path.exists(act_path):
        from tender_fit import attach_actions
        print("tender actions:", attach_actions(data, json.load(open(act_path, encoding="utf-8"))))
    # past contract awards found in the tender research (winners, values, brand ties)
    aw_path = os.path.join(pack_dir, "awards.json") if pack_dir else None
    if aw_path and os.path.exists(aw_path):
        data["awards"] = json.load(open(aw_path, encoding="utf-8"))
        print("awards:", len(data["awards"]))
    # qualitative advantages from each product's sourced text (db/qual_adv.py)
    if pack_dir:
        print("pack products added:", add_pack_products(data, pack_dir))
    data = platform_fields(data)
    # the newest researched news replaces older news (db/news_refresh.py); after platform_fields,
    # which rebuilds competitorNews from each competitor's moves
    nr_path = os.path.join(pack_dir, "news_refresh.json") if pack_dir else None
    if nr_path and os.path.exists(nr_path):
        import datetime as _dt
        from news_refresh import apply as news_apply
        nr = json.load(open(nr_path, encoding="utf-8"))
        gr_path = os.path.join(pack_dir, "global_requirements.json")     # worldwide market signals (Global Requirements page)
        if os.path.exists(gr_path):
            nr["items"] = nr["items"] + json.load(open(gr_path, encoding="utf-8"))
        print("news refresh:", news_apply(data, nr["items"], _dt.date.fromisoformat(nr["window_start"]),
                                          _dt.date.fromisoformat(nr["today"])))
    if pack_dir:
        data, unmatched = merge_pack(data, pack_dir)
        for u in unmatched:
            print("datapack: no match for", u)
    # qualitative advantages (db/qual_adv.py), after merge_pack: the client's own profile facts are attached by then
    print("matchup spec rows converted from winner flag to direction:", winner_flag_to_direction(data))
    from qual_adv import apply as qual_apply
    print("matchups with qualitative advantages:", qual_apply(data))
    # education and professional experience per leader (db/leader_bios.py), after merge_pack
    lb_path = os.path.join(pack_dir, "leader_bios.json") if pack_dir else None
    if lb_path and os.path.exists(lb_path):
        from leader_bios import apply as bios_apply
        print("leader bios:", bios_apply(data, json.load(open(lb_path, encoding="utf-8"))))
        # profiles the user pasted from LinkedIn (same shape), applied last so they win over the researched bios
        ll_path = os.path.join(pack_dir, "leader_linkedin.json")
        if os.path.exists(ll_path):
            print("leader bios from user-pasted profiles:", bios_apply(data, json.load(open(ll_path, encoding="utf-8"))))
    pt_path = os.path.join(pack_dir, "patents.json") if pack_dir else None
    if pt_path and os.path.exists(pt_path):
        from patents_load import apply as patents_apply
        print("patents:", patents_apply(data, json.load(open(pt_path, encoding="utf-8"))))
    if pack_dir:
        from geo_fills import apply as geo_fill
        print("geo footprint fill:", geo_fill(data, pack_dir))
    # "Entities" names who the story is about; the client is not appended to every rival's story
    own = ((data.get("client") or {}).get("name") or "").strip()
    stripped = 0
    for det in (data.get("details") or {}).values():
        for f in det.get("facts") or []:
            if str(f[0]).strip().lower() == "entities" and own and str(f[1]).endswith(f", {own}"):
                f[1] = f[1][: -len(own) - 2]
                stripped += 1
    print("entities: client name dropped from", stripped, "detail rows")
    if "--images" in sys.argv:
        attach_images(data, os.path.join(pack_dir or os.path.dirname(os.path.abspath(args[1])), "article_images.json"))
    with open(args[1], "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    print("wrote %s: %d globals" % (args[1], len(data)))
