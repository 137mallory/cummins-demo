"""Build the dashboard dataset (the UI's globals contract) from a client datapack.

The dashboard has no client baked into it: who the client is, its rivals, product
families, countries and currency all arrive in the dataset. A new client is a new pack:

    python db/build_dataset.py <pack_dir>            # -> <pack_dir>/dataset.json
    python db/seed_serving.py --recycle <pack_dir>/dataset.json

A pack is one client's researched, source-cited bundle (see <pack_dir>/SCHEMA.md):
    parallax-*-data.json   client, competitors, signals, matchups, tenders, pipeline, countries

Nothing is invented here. Every value is the pack's, reshaped; a value the pack does not
carry is left empty and the UI prints its "not published" state. The only derived
numbers are arithmetic on the pack's own figures (a kVA delta, a model's kVA range).

Self-check: python db/build_dataset.py --demo
"""

import glob
import json
import os
import re
import sys
from datetime import date
from urllib.parse import urlparse

LEVEL_DIR = {"THREAT": "threat", "WATCH": "watch", "OPPORTUNITY": "fav"}
LEAN = {"STRONG": "go", "PARTIAL": "maybe", "WEAK": "no"}
# The pack's analyst grade, as the API's severity scale (a stored grade wins over the
# serve-time derivation).
SEVERITY = {"THREAT": "high", "WATCH": "medium", "OPPORTUNITY": "low"}

# One spelling per market, applied everywhere a country is printed or joined on.
COUNTRY = {"KSA": "Saudi Arabia", "UAE": "UAE", "Kuwait": "Kuwait"}

# Product families. Key -> label; the positioning list, the geo keyword model and the
# client's own category list all read this one table.
FAMILIES = [
    ("dg", "Diesel gensets", ["diesel", "genset", "generator", "standby", "prime"]),
    ("gas", "Gas gensets", ["gas genset", "natural gas", "gas engine", "hsk78g", "biogas"]),
    ("bess", "Battery storage", ["bess", "battery", "energy storage", "hybrid"]),
    ("eng", "Engines", ["engine"]),
]
FAMILY_OF = {"Diesel genset": "dg", "Gas genset": "gas", "BESS": "bess", "Engine": "eng"}
FAMILY_LABEL = {k: label for k, label, _ in FAMILIES}

# Relationship vocabulary, as the pack's SCHEMA.md defines it.
REL_LABEL = {
    "exclusive_distributor": "Exclusive distributor", "dealer": "Dealer", "jv": "Joint venture",
    "oem_supplier": "OEM supplier", "packager": "Packager", "framework_supplier": "Framework supplier",
    "mou": "MoU", "localization_partner": "Localisation partner", "service_partner": "Service partner",
    "key_account": "Key account", "rental_fleet_supply": "Rental fleet supply",
    "technology_licence": "Technology licence",
}

# Facility type -> geo activity code (lp local production, pt partner, ex sales/logistics,
# sv service). The labels are served as actLabel.
ACTIVITY = {
    "Manufacturing": "lp", "Dealer branch": "pt", "Service centre": "sv", "Rebuild centre": "sv",
    "Training centre": "sv", "Regional HQ": "ex", "Warehouse": "ex", "Rental depot": "ex",
}

# Spec row key -> higher-is-better (True), lower-is-better (False). Anything absent is not
# a scored dimension: the rating a pair was matched on, and descriptive fields.
HIGHER_BETTER = {
    "fuel_consumption_lph_100": False, "fuel_consumption_lph_75": False,
    "fuel_consumption_lph_50": False, "lph_per_100kw": False, "dry_weight_kg": False,
    "footprint_m2": False, "kw_per_m2": True, "kw_per_tonne": True,
}
# Rows the pack labels alike ("Standby rating" in kVA and in kW) need distinct labels:
# the spec panels key on the label.
UNIT_LABELED = {"standby_kva", "standby_kw", "prime_kva", "prime_kw"}

PRODUCT_SPECS = [  # (pack key, label, unit)
    ("frequency_hz", "Frequency", "Hz"), ("standby_kva", "Standby rating", "kVA"),
    ("standby_kw", "Standby rating (kW)", "kW"), ("prime_kva", "Prime rating", "kVA"),
    ("prime_kw", "Prime rating (kW)", "kW"), ("continuous_kw", "Continuous rating", "kW"),
    ("engine_model", "Engine", ""), ("cylinders", "Cylinders", ""),
    ("displacement_l", "Displacement", "L"), ("aspiration", "Aspiration", ""),
    ("rated_rpm", "Rated speed", "rpm"), ("fuel", "Fuel", ""),
    ("fuel_consumption_lph_100", "Fuel at 100% load", "L/h"),
    ("fuel_consumption_lph_75", "Fuel at 75% load", "L/h"),
    ("fuel_consumption_lph_50", "Fuel at 50% load", "L/h"),
    ("length_mm", "Length", "mm"), ("width_mm", "Width", "mm"), ("height_mm", "Height", "mm"),
    ("dry_weight_kg", "Dry weight", "kg"), ("emissions", "Emissions", ""),
    ("alternator", "Alternator", ""), ("controller", "Controller", ""), ("voltage", "Voltage", ""),
    ("ambient_derate_note", "Ambient / derate", ""), ("data_center_rating", "Data centre rating", ""),
]


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s or "").lower()).strip("-")


def domain(url):
    h = urlparse(url or "").netloc.lower()
    return h[4:] if h.startswith("www.") else h


def country(c):
    return COUNTRY.get(c, c)


def nice_date(iso):
    """'2026-09-22' -> '22 Sep 2026'; '2026-05' -> 'May 2026'; '2017' stays."""
    s = str(iso or "")
    for fmt, out in (("%Y-%m-%d", "%d %b %Y"), ("%Y-%m", "%b %Y")):
        try:
            from datetime import datetime
            return datetime.strptime(s, fmt).strftime(out)
        except ValueError:
            pass
    return s


def num(v):
    """'1,500' -> 1500.0; non-numeric -> None."""
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None


def fmt_num(v):
    return f"{v:,.0f}" if float(v).is_integer() else f"{v:,.2f}".rstrip("0").rstrip(".")


def src(url):
    return {"label": domain(url), "url": url} if url else None


def srcs(urls, cap=12):
    seen, out = set(), []
    for u in urls or []:
        if u and u not in seen:
            seen.add(u)
            out.append(src(u))
    return out[:cap]


def html_esc(s):
    return str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------- per-record builders

def product(p, owner):
    specs = {}
    for key, label, unit in PRODUCT_SPECS:
        v = p.get(key)
        if v in (None, "", []):
            continue
        n = num(v)
        specs[label] = f"{fmt_num(n)} {unit}".strip() if n is not None and unit else str(v)
    return {
        "id": p.get("id") or slug(f"{owner}-{p['model']}"),
        "name": p["model"],
        "category": FAMILY_LABEL.get(FAMILY_OF.get(p.get("category")), p.get("category")),
        "series": p.get("series"),
        "specs": specs,
        "source": domain(p.get("datasheet_url") or p.get("source_url")),
        "source_url": p.get("datasheet_url") or p.get("source_url"),
        "sources": [u for u in (p.get("source_url"), p.get("datasheet_url")) if u],
        "tier": p.get("spec_confidence"),
    }


def partner(p, owner_name):
    rel = str(p.get("relationship_label") or "").lower()
    why = p.get("why_it_matters") or {}
    level = why.get("level") or ""
    return {
        "id": slug(p["partner"]),
        "cid": slug(p["partner"]),
        "label": p["partner"],
        "kind": p.get("partner_type"),
        "rel": rel,
        "sig": {"THREAT": 3, "WATCH": 2, "OPPORTUNITY": 1}.get(level, 1),
        "ptype": REL_LABEL.get(rel, p.get("partner_type")),
        "note": p.get("scope"),
        "date": p.get("since") or "n/d",
        "country": ", ".join(country(c.strip()) for c in str(p.get("country") or "").split(",") if c.strip()),
        "deal": "n/d",
        "insight": why.get("analysis") or p.get("scope") or "",
        "mean": f"<b>{level.title()}:</b> {html_esc(why.get('analysis'))}" if level else "",
        "src": p.get("source_url"),
        "srcs": [s for s in [src(p.get("source_url"))] if s],
        "alsoHeldBy": p.get("also_held_by") or [],
    }


def sourced_row(value, detail, url, line):
    # the profile's harvested-row shape; a row without all four is not rendered
    return {"value": value, "detail": detail, "url": url, "line": line} if value and url and line else None


def site_of(c):
    """The company's own site, when the pack cites one: a source whose domain carries
    a token of the company's id ('caterpillar' -> caterpillar.com)."""
    toks = [t for t in c["id"].split("-") if len(t) > 3]
    for u in (c.get("profile_sources") or []) + (c.get("sources") or []):
        d = domain(u)
        if any(t in d for t in toks):
            return f"https://{urlparse(u).netloc}/"
    return None


def display_name(c):
    return c.get("short") or c["name"]


def competitor(c, is_client=False):
    moves = sorted(c.get("movements") or [], key=lambda m: m.get("date") or "", reverse=True)
    updates = "".join(
        f"<div><b>{nice_date(m['date'])}</b> — {html_esc(m['headline'])}</div>" for m in moves[:5])
    threat = c.get("threat") or ""
    first_src = (c.get("profile_sources") or c.get("sources") or [None])[0]
    rev_url = (c.get("revenue_sources") or [first_src])[0]
    geo = c.get("geo_footprint") or []
    return {
        "name": display_name(c),
        "dir": "client" if is_client else LEVEL_DIR.get(threat, "watch"),
        "sector": c.get("sector"),
        "hq": c.get("hq"),
        # three grades from the pack's two: THREAT, or WATCH on a core / watch-tier rival
        "threat": None if is_client else (
            "high" if threat == "THREAT" else "medium" if c.get("tier") == "core" else "low"),
        "assess": c.get("read") or c.get("positioning_text") or "",
        "threatNote": c.get("assess") or "",
        "updates": updates,
        "center": {"id": c["id"], "label": display_name(c)},
        "partners": [partner(p, c["name"]) for p in c.get("partnerships") or []],
        "site": site_of(c),
        "srcs": srcs((c.get("profile_sources") or []) + (c.get("positioning_sources") or [])
                     + (c.get("sources") or []), cap=10),
        "products": [product(p, c["id"]) for p in c.get("products") or []],
        "leadership": [r for r in (
            sourced_row(l.get("name"), l.get("title"), l.get("source_url"),
                        f"{l.get('name')}, {l.get('title')}.")
            for l in c.get("leadership") or []) if r],
        "facilities": [r for r in (
            sourced_row(f"{g['facility_type']}, {g['city']}", g.get("entity"), g.get("source_url"),
                        g.get("notes") or f"{g['facility_type']} in {g['city']}, {country(g['country'])}.")
            for g in geo) if r],
        "sales": [r for r in [sourced_row(c.get("revenue"), "", rev_url, c.get("revenue"))] if r],
        "starting_year": int(c["founded"]) if str(c.get("founded") or "").isdigit() else None,
        "company_size": c.get("employees"),
        "strategic_positioning": c.get("positioning_text"),
        "global_locations": sorted({country(g["country"]) for g in geo}),
        "country": c.get("hq_country"),
    }


def signal_card(s, rank, lane_prefix=""):
    cid = f"{lane_prefix}{s['id']}"
    return {
        "id": cid,
        "dir": LEVEL_DIR.get(s["level"], "watch"),
        "severity": SEVERITY.get(s["level"]),
        "rank": f"{rank:02d}",
        "title": s["headline"],
        "meta": " · ".join(x for x in (s.get("category"), s["company"], country(s.get("country"))) if x),
        "company": s["company"],
        "lens": "COMPETITIVE",
        "sowhat": html_esc(s.get("analysis")),
        "summary": s.get("summary"),
        "sec": [{"lens": str(s.get("category") or "SIGNAL").upper(), "read": s.get("summary")}],
        "url": s.get("url"),
        "ago": nice_date(s.get("date")),
        "tags": " ".join(x for x in (LEVEL_DIR.get(s["level"], "watch"), s.get("category")) if x),
    }


def signal_detail(s, rank, pillar, client_short):
    return {
        "rank": f"{pillar} Signal · {rank:02d}",
        "dir": LEVEL_DIR.get(s["level"], "watch"),
        "title": s["headline"],
        "facts": [[k, v] for k, v in (
            ("Company", s["company"]), ("Category", s.get("category")),
            ("Country", country(s.get("country"))), ("Date", nice_date(s.get("date"))),
            ("Source", s.get("domain") or domain(s.get("url")))) if v],
        "summary": s.get("summary"),
        "what": html_esc(s.get("summary")),
        "why": html_esc(s.get("analysis")),
        "lens": [[str(s.get("level") or "").title() or "Read", html_esc(s.get("analysis"))]],
        "actions": [],
        "url": s.get("url"),
        "suggest": [f"What does this mean for {client_short}?",
                    f"How does {s['company']} compare with {client_short}?"],
    }


def matchup(m, i, comps, client, fam_label):
    fam = FAMILY_OF.get(m["category"], "dg")
    specs, adv_c, adv_k = [], [], []
    for r in m.get("rows") or []:
        cn, kn = num(r.get("cv")), num(r.get("kv"))
        label = f"{r['l']} ({r['u']})" if r["k"] in UNIT_LABELED else r["l"]
        hi = HIGHER_BETTER.get(r["k"])
        specs.append({"l": label, "cv": r.get("cv"), "cn": cn, "kv": r.get("kv"), "kn": kn,
                      "u": r.get("u") or "", "hi": hi, "p": "s", "cp": "s", "kp": "s"})
        if r.get("hi") in ("c", "k") and cn is not None and kn is not None:
            better = "Lower" if hi is False else "Higher"
            line = f"{better} {r['l'].lower()}: <b>{r.get('cv') if r['hi'] == 'c' else r.get('kv')}</b> vs " \
                   f"{r.get('kv') if r['hi'] == 'c' else r.get('cv')} {r.get('u') or ''}".rstrip()
            (adv_c if r["hi"] == "c" else adv_k).append(line)
    comp = comps.get(m["comp"], {})
    short = client["short"]
    kva = (f"{fmt_num(m['kva_c'])} kVA vs {fmt_num(m['kva_k'])} kVA ({m['delta_pct']:+.1f}%)"
           if m.get("kva_c") and m.get("kva_k") else "the nearest published rating")
    ca, ka, tie = m.get("cadv") or 0, m.get("kadv") or 0, m.get("tie") or 0
    lead = (f"{m['company']} leads" if ca > ka else f"{short} leads" if ka > ca else "Level")
    return str(i), {
        "cat": fam_label[fam],
        "catKey": fam,
        "anchor": m["kp_model"],
        "global": False,
        "dir": "threat" if ca > ka else "fav" if ka > ca else "watch",
        "country": comp.get("hq_country") or "",
        "comp": f"{m['company']} · {m['cp_model']}",
        "compBy": m["company"],
        "bf": f"{client['brand']} · {m['kp_model']}",
        "bfBy": client["name"],
        "reason": f"<b>{html_esc(m['cp_model'])}</b> ({html_esc(m['company'])}) is matched against "
                  f"{html_esc(short)}'s <b>{html_esc(m['kp_model'])}</b>: same class ({m['category'].lower()}, "
                  f"{m.get('freq')} Hz), matched on standby rating, {kva}.",
        "specs": specs,
        "advComp": adv_c,
        "advBf": adv_k,
        "det": [[k, v] for k, v in (
            ("Competitor", m["company"]), ("HQ / origin", comp.get("hq")),
            ("Model", m["cp_model"]), ("Frequency", f"{m.get('freq')} Hz"),
            ("Spec confidence", m.get("c_conf")), ("Source", m.get("c_sheet"))) if v],
        "verdictH": f"Positioning verdict · {fam_label[fam]}",
        "verdict": f"<b>{lead} on the datasheets.</b> {html_esc(m['company'])} leads on {ca} measured "
                   f"dimension{'s' if ca != 1 else ''}, {html_esc(short)} on {ka}, {tie} level.",
        "srcs": srcs([m.get("c_sheet"), m.get("k_sheet")]),
    }


def tender(t, i):
    fit = t.get("cummins_fit") or t.get("client_fit") or {}
    grade = fit.get("fit") or ""
    status = str(t.get("status") or "")
    prods = fit.get("matching_products") or []
    matches = [{"n": p, "fit": grade.lower(), "pct": None,
                "lines": [["up" if grade != "WEAK" else "down", fit.get("analysis")]] if j == 0 and fit.get("analysis") else []}
               for j, p in enumerate(prods)]
    rivals = fit.get("likely_competitors") or []
    return {
        "id": t["id"],
        "title": t["title"],
        "gist": t["title"],
        "summary": t.get("scope_summary"),
        "issuer": t.get("issuer"),
        "country": country(t.get("country")),
        # the primary segment is the category ("Utility / Desalination" -> "Utility"); the
        # full segment stays in the requirement rows
        "cat": (t.get("segment") or "").split("/")[0].strip() or None,
        "value": t.get("value"),
        "qty": None,
        "posted": t.get("published"),
        # the close date travels as a "d Mon yyyy" string: tenderCalc resolves the
        # countdown from it against today, so the pack's frozen `days` is not served
        "deadline": nice_date(t.get("closes")) if t.get("closes") else None,
        "status": status.lower(),
        # an expected tender has no window yet; its stage is what the list prints
        "stage": "Expected" if status == "Expected" else None,
        "reqNote": t.get("genset_relevance"),
        "req": [[k, v] for k, v in (
            ("Scope", t.get("scope_summary")), ("Portal", t.get("portal")), ("Segment", t.get("segment")),
            ("Status", status), ("Published", nice_date(t.get("published"))),
            ("Closing date", nice_date(t.get("closes")))) if v],
        "matches": matches,
        "lean": LEAN.get(grade),
        "leanTxt": html_esc(fit.get("analysis")) + (
            f"<br><b>Likely competitors:</b> {html_esc(', '.join(rivals))}" if rivals else ""),
        "url": t.get("source_url"),
        "srcs": [s for s in [src(t.get("source_url"))] if s],
    }


def pipeline_card(p, i):
    fams = [label for key, label, kw in FAMILIES
            if any(k in str(p.get("expected_power_need") or "").lower() for k in kw)]
    return {
        "id": f"pl{i + 1}",
        "dir": "watch",
        "rank": f"{i + 1:02d}",
        "title": p["project"],
        "meta": " · ".join(x for x in (p.get("segment"), country(p.get("country")), p.get("stage")) if x),
        "company": "",
        "lens": "MARKET / DEMAND",
        "sowhat": html_esc(p.get("analysis")),
        "summary": p.get("signal"),
        "sec": [{"lens": "EXPECTED POWER NEED", "read": p.get("expected_power_need")}],
        "url": p.get("source_url"),
        "ago": nice_date(p.get("date")),
        "tags": " ".join(["watch", p.get("segment") or ""] + fams).strip(),
    }, {
        "rank": f"Market Signal · {i + 1:02d}",
        "dir": "watch",
        "title": p["project"],
        "facts": [[k, v] for k, v in (
            ("Project", p["project"]), ("Country", country(p.get("country"))),
            ("Segment", p.get("segment")), ("Stage", p.get("stage")),
            ("Date", nice_date(p.get("date"))), ("Source", domain(p.get("source_url")))) if v],
        "summary": p.get("signal"),
        "what": html_esc(p.get("signal")),
        "why": html_esc(p.get("analysis")),
        "lens": [["Expected power need", html_esc(p.get("expected_power_need"))]],
        "actions": [],
        "url": p.get("source_url"),
        "suggest": ["What power equipment will this need?", "Who is likely to bid?"],
    }


def geo_row(g):
    code = ACTIVITY.get(g.get("facility_type"), "ex")
    return {
        "name": f"{g['facility_type']} · {g['city']}",
        "c": code,
        "qty": g.get("city"),
        "val": g.get("entity"),
        "since": "",
        "stage": g.get("facility_type"),
        "note": g.get("notes") or "",
        "src": g.get("source_url") or "",   # the URL the row was read from ("syn" = estimate)
        "srcnote": g.get("entity") or "",
    }


def tech_domain(s):
    if s.get("category") == "Capacity":
        return "capacity"
    t = f"{s['headline']} {s.get('summary') or ''}".lower()
    if re.search(r"\bbess\b|battery|energy storage", t):
        return "bess"
    if re.search(r"\bgas\b|natural gas|biogas|hydrogen|hsk78g", t):
        return "gas"
    return "diesel"


TECH_CATS = [("diesel", "Diesel gensets"), ("gas", "Gas gensets"),
             ("bess", "Battery storage"), ("capacity", "Manufacturing capacity")]


# ---------------------------------------------------------------------------- build

def build(pack):
    cl = pack["client"]
    # A rival's display name is its short name ("Rolls-Royce mtu", not "Rolls-Royce Power
    # Systems (mtu)"): it is printed on every card. Every join downstream (profile news,
    # positioning, grading) keys on that name, so signals and matchups are pointed at it
    # once, here, whatever spelling they carry.
    canon = {c["id"]: display_name(c) for c in pack["competitors"]}
    pack = dict(pack,
                signals=[dict(s, company=canon.get(s.get("comp"), s["company"])) for s in pack.get("signals") or []],
                matchups=[dict(m, company=canon.get(m.get("comp"), m["company"])) for m in pack.get("matchups") or []])
    brand = (cl.get("brands") or [cl["name"]])[0]
    client = {
        "id": cl["id"],
        "name": cl["name"],
        "short": cl.get("short") or cl["name"],
        "brand": brand,
        "sector": cl.get("sector"),
        "website": cl.get("website") or site_of(cl),
        "currency": cl.get("currency") or "USD",
        "magnitude": cl.get("magnitude") or "",
        "locale": cl.get("locale") or "en-GB",
        # the qualifier the live news lookup appends to a rival's name
        "newsQuery": cl.get("news_query") or "generator OR genset OR \"power generation\"",
        "markets": [country(c) for c in pack.get("countries") or []],
    }
    fam_label = {k: label for k, label, _ in FAMILIES}
    rivals = pack["competitors"]
    comps = {c["id"]: c for c in rivals}

    competitors = {c["id"]: competitor(c) for c in rivals}
    competitors[cl["id"]] = competitor(cl, is_client=True)

    signals = sorted(pack.get("signals") or [], key=lambda s: s.get("date") or "", reverse=True)
    comp_cards = [signal_card(s, i + 1) for i, s in enumerate(signals)]
    tech_sig = [s for s in signals if s.get("category") in ("Product", "Capacity")]
    tech_cards = [signal_card(s, i + 1, "t-") for i, s in enumerate(tech_sig)]
    details = {}
    for i, s in enumerate(signals):
        details[s["id"]] = signal_detail(s, i + 1, "Competitive", client["short"])
    for i, s in enumerate(tech_sig):
        details["t-" + s["id"]] = signal_detail(s, i + 1, "Technology", client["short"])

    market_cards = []
    for i, p in enumerate(sorted(pack.get("pipeline") or [], key=lambda p: p.get("date") or "", reverse=True)):
        card, det = pipeline_card(p, i)
        market_cards.append(card)
        details[card["id"]] = det

    matchups = dict(matchup(m, i + 1, comps, client, fam_label)
                    for i, m in enumerate(pack.get("matchups") or []))
    tenders = [tender(t, i) for i, t in enumerate(pack.get("tenders") or [])]

    geo = {}
    for c in rivals + [cl]:
        rows = {}
        for g in c.get("geo_footprint") or []:
            rows.setdefault(country(g["country"]), []).append(geo_row(g))
        if rows:
            geo[c["id"]] = rows
    geo_comps = [{"id": c["id"], "name": display_name(c), "dir": LEVEL_DIR.get(c.get("threat"), "watch"),
                  "hq": c.get("hq_country") or c.get("hq"), "isBf": False} for c in rivals]
    geo_comps.insert(0, {"id": cl["id"], "name": cl["name"], "dir": "fav",
                         "hq": cl.get("hq"), "isBf": True})

    # the client's counter-product per family: its own model range, from its own catalogue
    counter = []
    for key, label, _ in FAMILIES:
        own = [p for p in cl.get("products") or [] if FAMILY_OF.get(p.get("category")) == key]
        if not own:
            continue
        rated = sorted((p for p in own if p.get("standby_kva")), key=lambda p: p["standby_kva"])
        span = (f"{rated[0]['model']} ({fmt_num(rated[0]['standby_kva'])} kVA) to "
                f"{rated[-1]['model']} ({fmt_num(rated[-1]['standby_kva'])} kVA)") if rated else \
            ", ".join(p["model"] for p in own[:3])
        counter.append({"band": key, "label": label, "product": span,
                        "note": f"{len(own)} {label.lower()} models on the {client['short']} catalogue."})

    innovations = {}
    for s in tech_sig:
        innovations.setdefault(tech_domain(s), []).append({
            "t": s["headline"], "mat": None, "gap": None, "driver": s["company"],
            "horizon": nice_date(s.get("date")), "body": s.get("summary"),
            "impact": html_esc(s.get("analysis")), "whatsNew": s.get("summary"), "compNote": "",
            "sources": s.get("domain") or domain(s.get("url")), "url": s.get("url"),
        })
    tech_area_meta = {k: {"area": label, "desc": f"{len(innovations.get(k, []))} tracked developments.",
                          "maturity": "", "position": "", "trend": "", "reason": "", "why": ""}
                      for k, label in TECH_CATS}

    source_registry, company_sources = [], {}
    for c in rivals + [cl]:
        urls = [u for u in dict.fromkeys(c.get("sources") or []) if u]
        company_sources[display_name(c)] = urls
        source_registry += [{"company": display_name(c), "label": domain(u), "url": u, "kind": "source"} for u in urls]

    n_threat = sum(1 for c in comp_cards if c["dir"] == "threat")
    n_watch = sum(1 for c in comp_cards if c["dir"] == "watch")
    short = client["short"]
    filters = [{"f": "all", "l": "All"}, {"f": "threat", "l": "Threat", "c": "var(--threat)"},
               {"f": "watch", "l": "Watch", "c": "var(--watch)"}, {"f": "fav", "l": "Opportunity", "c": "var(--fav)"}]
    dir_word = {"threat": "Threat", "watch": "Watch", "fav": "Opportunity"}
    fam_labels = [label for _, label, _ in FAMILIES]

    return {
        "client": client,
        "competitors": competitors,
        "compOrder": [c["id"] for c in sorted(rivals, key=lambda c: c.get("tier") != "core")],
        "competitiveCards": comp_cards,
        "marketCards": market_cards,
        "techCards": tech_cards,
        "details": details,
        "matchups": matchups,
        "tenders": tenders,
        "competitorNews": {},
        "POS_CATS": [[k, label] for k, label, _ in FAMILIES],
        "CAT_KEY": {label: k for k, label, _ in FAMILIES},
        "CAT_META": {k: {"label": label, "kw": kw, "desc": label} for k, label, kw in FAMILIES},
        "CAT_ALIASES": {},
        "KSSL_CATS": fam_labels,
        "KSSL_PARTNERS": [partner(p, cl["name"]) for p in cl.get("partnerships") or []],
        "REL_LABEL": REL_LABEL,
        "COMPSYN": {},
        "TRACEIDS": {},
        "FIELDSYN": {"patterns": [], "bottom": ""},
        "sourceRegistry": source_registry,
        "companySources": company_sources,
        "geoData": geo,
        "geoComps": geo_comps,
        "geoCountries": client["markets"],
        "actLabel": {"lp": "Manufacturing / assembly", "pt": "Dealer branch",
                     "ex": "Office / warehouse / rental", "sv": "Service / rebuild / training",
                     "bf": f"{short} present"},
        "counterRules": counter,
        "tpAllCats": sorted({t["cat"] for t in tenders if t["cat"]}),
        "tpAllCountries": sorted({t["country"] for t in tenders if t["country"]}),
        "PATENTS": {"techAreas": [], "byArea": {}, "byAssignee": {},
                    "_meta": {"total": 0, "providers": [], "note": "No patent records in this dataset.",
                              "status": "empty"}},
        "innovations": innovations,
        "techCats": [{"id": k, "name": label} for k, label in TECH_CATS],
        "techAreaMeta": tech_area_meta,
        "chatSuggest": {
            "overview": [f"Which rivals threaten {short} in data centres?",
                         f"Which open tenders fit {short} best?",
                         "Who has the densest service network in Saudi Arabia?"],
            "positioning": ["Which rival leads on fuel consumption?"],
            "tender": [f"Which tenders are a strong fit for {short}?"],
        },
        "overviewMetrics": {"competitive": [], "market": [], "technology": []},
        "overviewConfig": {
            "competitive": {
                "title": "Competitive Intelligence",
                "cnt": f"{len(comp_cards)} competitor moves · sorted threats first",
                "metrics": [
                    {"act": "threat", "l": "Competitive threats", "dot": "var(--threat)", "v": str(n_threat),
                     "sub": f"rival moves with direct loss risk for {short}"},
                    {"act": "watch", "l": "Watch signals", "v": str(n_watch), "sub": "moves to monitor"},
                    {"act": "all", "l": "Companies tracked", "v": str(len(rivals)), "sub": "core and watch rivals"},
                ],
                "groups": [{"n": n_threat, "h": "Priority — Competitive Threats",
                            "s": f"— rival moves with direct loss risk for {short}"},
                           {"n": 99, "h": "Competitive Movement", "s": "— moves to monitor"}],
                "dirWord": dir_word, "filters": filters,
            },
            "market": {
                "title": "Market Intelligence",
                "cnt": f"{len(tenders)} tenders · {len(market_cards)} demand signals",
                "metrics": [], "groups": [], "dirWord": dir_word, "filters": filters,
            },
            "technology": {
                "title": "Technology Intelligence",
                "cnt": f"{len(tech_cards)} product and capacity moves",
                "metrics": [], "groups": [], "dirWord": dir_word, "filters": filters,
            },
        },
    }


def load_pack(pack_dir):
    files = glob.glob(os.path.join(pack_dir, "parallax-*-data.json"))
    if len(files) != 1:
        raise SystemExit(f"expected one parallax-*-data.json in {pack_dir}, found {len(files)}")
    with open(files[0], encoding="utf-8") as f:
        return json.load(f)


def demo():
    here = os.path.dirname(os.path.abspath(__file__))
    packs = glob.glob(os.path.join(here, "..", "parallax-*-datapack"))
    assert packs, "no datapack next to the repo root to check against"
    pack = load_pack(packs[0])
    d = build(pack)
    cid = pack["client"]["id"]
    assert d["client"]["id"] == cid and d["competitors"][cid]["dir"] == "client"
    assert cid not in d["compOrder"], "the client is not its own rival"
    assert len(d["compOrder"]) == len(pack["competitors"])
    assert len(d["competitiveCards"]) == len(pack["signals"])
    assert len(d["matchups"]) == len(pack["matchups"]) and all(k.isdigit() for k in d["matchups"])
    ids = [c["id"] for lane in ("competitiveCards", "marketCards", "techCards") for c in d[lane]]
    assert len(ids) == len(set(ids)), "card ids must be unique across lanes"
    assert all(i in d["details"] for i in ids), "every card opens a detail"
    assert all(m["cat"] in d["CAT_KEY"] for m in d["matchups"].values())
    assert any(g["isBf"] and g["id"] == cid for g in d["geoComps"])
    assert cid in d["geoData"], "the client's own footprint is served"
    # a spec row is scored only when the pack's own direction says which way is better
    m = next(iter(d["matchups"].values()))
    assert all(r["hi"] in (True, False, None) for r in m["specs"])
    assert not any("KSSL" in json.dumps(v) for k, v in d.items() if k not in ("KSSL_CATS", "KSSL_PARTNERS"))
    print("build_dataset demo ok:", {k: len(v) for k, v in d.items() if isinstance(v, (list, dict))})


if __name__ == "__main__":
    if sys.argv[1:] == ["--demo"]:
        demo()
        sys.exit(0)
    if not sys.argv[1:]:
        raise SystemExit(__doc__)
    pack_dir = sys.argv[1]
    out = sys.argv[3] if sys.argv[2:3] == ["-o"] else os.path.join(pack_dir, "dataset.json")
    data = build(load_pack(pack_dir))
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("wrote", out, {k: len(v) for k, v in data.items() if isinstance(v, (list, dict))})
