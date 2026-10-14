# -*- coding: utf-8 -*-
"""Curated files over the pipeline: override (today) vs fallback (extraction-first), with origins.

    python backend/test_curated_fallback.py

Values are the staging rows of 2026-09-16 that the switch was measured on.
"""
import copy
import json
import os
import sys

os.environ.setdefault("KSSL_CORPUS_DSN", "postgresql://unused/unused")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "extraction", "signals"))
import app                                                            # noqa: E402

ROW = {"name": "Nexter", "starting_year": 2024, "hq": "", "sector": "Defence", "company_size": None,
       "products": ["CAESAR", {"id": "rch-155", "name": "RCH 155", "source": "forcesnews.com"}]}
FIELDS = {"starting_year": 1973, "hq": "Versailles, France", "sector": None, "company_size": "4,000 employees"}
PRODUCTS = [{"id": "rch-155", "name": "RCH-155", "category": "Artillery", "specs": {"Calibre": "155 mm"}},
            {"id": "titus", "name": "TITUS", "specs": {"Crew": "3"}}]


def edge_cases():
    fb = lambda row, f=None, p=None: app.apply_curated(copy.deepcopy(row), f, p, mode="fallback")   # noqa: E731
    ov = lambda row, f=None, p=None: app.apply_curated(copy.deepcopy(row), f, p, mode="override")   # noqa: E731

    # blank means blank: whitespace-only is empty, 0 and False are values
    r = fb({"hq": "   ", "starting_year": 0}, {"hq": "Oslo", "starting_year": 1814})
    assert r["hq"] == "Oslo" and r["origins"]["hq"] == "curated", r
    assert r["starting_year"] == 0 and r["origins"]["starting_year"] == "pipeline", r
    # a curated whitespace string never overwrites anything
    r = ov({"hq": "Kongsberg"}, {"hq": "  "})
    assert r["hq"] == "Kongsberg" and r["origins"]["hq"] == "pipeline", r
    # structured values: empty dict/list are blank, a filled object is a value in either shape
    r = fb({"sales": {}, "global_locations": []}, {"sales": {"text": "$2.2 billion"}, "global_locations": ["US"]})
    assert r["sales"] == [{"value": "$2.2 billion", "detail": None, "url": None,
                           "line": "$2.2 billion"}] and r["global_locations"] == ["US"], r
    # the curated {text, fy, srcs} shape is served as the row list the Profile page renders
    r = ov({}, {"sales": {"text": "$1,976.8 million", "fy": "FY2026", "srcs": ["https://sec.gov/x"]}})
    assert r["sales"] == [{"value": "$1,976.8 million", "detail": "FY2026", "url": "https://sec.gov/x",
                           "line": "$1,976.8 million"}] and r["origins"]["sales"] == "curated", r
    r = fb({"sales": [{"value": "$ 8billion"}]}, {"sales": {"text": "AUD 8bn"}})
    assert r["sales"] == [{"value": "$ 8billion"}] and r["origins"]["sales"] == "pipeline", r

    # products on their own switch: fields curated, products merged
    r = app.apply_curated({"starting_year": 2024, "products": [{"name": "Archer", "specs": {"Range": "50 km"}}]},
                          {"starting_year": 1973}, [{"name": "ARCHER", "category": "Artillery"},
                                                     {"name": "FH77"}], mode="override", products_mode="fallback")
    assert r["starting_year"] == 1973 and r["origins"]["starting_year"] == "curated", r
    assert [p["name"] for p in r["products"]] == ["Archer", "FH77"], r["products"]
    assert r["products"][0]["specs"] == {"Range": "50 km"} and r["products"][0]["category"] == "Artillery", r
    r = app.apply_curated({"products": [{"name": "Archer"}]}, {}, [{"name": "FH77"}], mode="override")
    assert [p["name"] for p in r["products"]] == ["FH77"], "explicit override mode still replaces"

    # specs merge per field: curated wins where it has the field, the other value is kept as
    # "also reported", enriched fills what curated lacks, and synonyms are one field
    r = app.apply_curated(
        {"products": [{"name": "BrahMos", "specs": {"Range": "400 km", "Max speed": "Mach 2.8",
                                                     "Crew": "0"}}]},
        {}, [{"name": "BRAHMOS", "specs": {"Maximum range": "290 km", "Maximum speed": "Mach 2.8",
                                            "Warhead": "200 kg"}}],
        mode="override", products_mode="fallback")
    p0 = r["products"][0]
    assert p0["specs"] == {"Maximum range": "290 km", "Maximum speed": "Mach 2.8",
                           "Warhead": "200 kg", "Crew": "0"}, p0["specs"]
    assert p0["specOrigins"] == {"Maximum range": "curated", "Maximum speed": "curated",
                                 "Warhead": "curated", "Crew": "pipeline"}, p0["specOrigins"]
    assert p0["specsAlsoReported"] == {"Maximum range": "400 km"}, p0.get("specsAlsoReported")
    assert p0["fieldOrigins"]["specs"] == "merged", p0
    # stored product with no specs gets the curated ones (the hiding bug)
    r = app.apply_curated({"products": [{"name": "Archer", "specs": {"Crew": "3"}}]}, {},
                          [{"name": "ARCHER", "specs": {"Calibre": "155 mm", "Range": "40 km"}}],
                          mode="override", products_mode="fallback")
    assert r["products"][0]["specs"] == {"Calibre": "155 mm", "Range": "40 km", "Crew": "3"}, r
    assert "specsAlsoReported" not in r["products"][0]

    # one product, many names: designator or leading name word, and only a single answer
    fbp = lambda stored, cur: app.apply_curated({"products": stored}, {}, cur, mode="override",
                                                products_mode="fallback")["products"]      # noqa: E731
    out = fbp([{"name": "Archer", "specs": {"Crew": "3"}}],
              [{"name": "ARCHER Mobile Howitzer", "specs": {"Calibre": "155 mm"}}])
    assert len(out) == 1 and out[0]["specs"] == {"Calibre": "155 mm", "Crew": "3"}, out
    out = fbp([{"name": "RCH 155", "specs": {"Range": "54 km"}}],
              [{"name": "KNDS RCH 155 wheeled howitzer", "specs": {"Calibre": "155 mm"}}])
    assert len(out) == 1 and out[0]["specs"]["Calibre"] == "155 mm", out
    out = fbp([{"name": "M777", "specs": {"Weight": "4.2 t"}}],
              [{"name": "M777 Lightweight Towed Howitzer", "specs": {"Calibre": "155 mm"}}])
    assert len(out) == 1, out
    # a bare brand shared by two curated variants matches neither
    out = fbp([{"name": "BrahMos", "specs": {"Range": "400 km"}}],
              [{"name": "BrahMos NG", "specs": {"Range": "290 km"}},
               {"name": "BrahMos ER", "specs": {"Range": "450 km"}}])
    assert len(out) == 3, out
    # sizes are not designators: two different 155 mm shells stay apart
    out = fbp([{"name": "155mm HE shell", "specs": {"Range": "24 km"}}],
              [{"name": "155mm Excalibur", "specs": {"Range": "40 km"}}])
    assert len(out) == 2, out

    # a product with no spec sheet is not served in fallback (curated always is)
    out = fbp([{"name": "Stub only"}, {"name": "Lynx KF41", "specs": {"Crew": "3"}}],
              [{"name": "TITUS", "specs": {"Crew": "3"}}])
    assert [p["name"] for p in out] == ["Lynx KF41", "TITUS"], out

    # a field not in the override list is never touched, even if the file carries it
    r = ov({"threat": "high"}, {"threat": "low", "assess": "x"})
    assert r["threat"] == "high" and "threat" not in r["origins"] and "assess" not in r, r

    # an unknown or mistyped mode is today's behaviour, never a silent switch to fallback
    for mode in ("", "Fallback ", "fallbak", None):
        r = app.apply_curated({"hq": "A"}, {"hq": "B"}, None, mode=mode)
        assert r["hq"] == ("B" if mode != "Fallback " else "A"), (mode, r)

    # products: junk entries are dropped, not served
    r = fb({"products": [None, "", "  ", {"name": ""}, {"id": "x"}, 7, "RCH 155"]}, None,
           [None, "TITUS", {"name": None}, {"name": "CAESAR"}])
    # the stored "RCH 155" has no spec sheet and is not served; the curated CAESAR always is
    assert [p["name"] for p in r["products"]] == ["CAESAR"], r["products"]
    # a name of only punctuation never matches another such name
    r = fb({"products": ["—"]}, None, [{"name": "–", "specs": {"a": "1"}}])
    # (the stored "—" has no spec sheet, so only the curated entry is served)
    assert [p["origin"] for p in r["products"]] == ["curated"], r
    # HTML-escaped stored name matches the plain curated name
    r = fb({"products": [{"name": "Rafael &amp; IAI Barak"}]}, None, [{"name": "Rafael & IAI Barak", "specs": {"r": "70 km"}}])
    assert len(r["products"]) == 1 and r["products"][0]["specs"] == {"r": "70 km"}, r
    # duplicates: one curated entry fills one stored product; a curated duplicate is appended once
    r = fb({"products": ["TITUS", "Titus"]}, None, [{"name": "TITUS", "specs": {"c": "3"}}, {"name": "TITUS", "specs": {"c": "4"}}])
    # (the second stored "Titus" is left without a spec sheet, so it is not served)
    assert [p.get("specs") for p in r["products"]] == [{"c": "3"}], r["products"]
    r = fb({"products": []}, None, [{"name": "TITUS"}, {"name": "titus"}])
    assert len(r["products"]) == 1, r["products"]
    # a stored field that is already set is never overwritten by the file
    r = fb({"products": [{"name": "RCH 155", "category": "Artillery", "specs": {}}]}, None,
           [{"name": "RCH 155", "category": "Vehicles", "specs": {"Calibre": "155 mm"}, "origin": "evil"}])
    p = r["products"][0]
    assert p["category"] == "Artillery" and p["specs"] == {"Calibre": "155 mm"} and p["origin"] == "pipeline", p
    assert p["fieldOrigins"] == {"specs": "curated"}, p
    # a stored product's own origin label is preserved
    r = fb({"products": [{"name": "X", "origin": "agent"}]})
    assert r["products"][0]["origin"] == "agent", r
    # products missing entirely stay missing; an empty list stays empty
    assert "products" not in fb({"hq": "A"}) and fb({"products": []})["products"] == []
    assert fb({"products": None})["products"] is None

    # the served JSON never aliases the curated globals: mutating the output leaves the file intact
    src = {"id": "t", "name": "T", "specs": {"a": "1"}}
    r = ov({"products": []}, None, [src])
    r["products"][0]["name"] = "changed"
    r = fb({"products": ["T"]}, None, [src])
    r["products"][0]["specs"]["a"] = "changed"
    assert src == {"id": "t", "name": "T", "specs": {"a": "1"}}, src

    # same input twice -> same output (the dataset cache rebuilds on every TTL)
    row = {"hq": "", "products": ["A"]}
    assert fb(row, {"hq": "B"}, [{"name": "A", "specs": {"x": "1"}}]) == fb(row, {"hq": "B"}, [{"name": "A", "specs": {"x": "1"}}])


def main():
    # OVERRIDE: the file wins wherever it has a value; today's screen, plus origins
    r = app.apply_curated(copy.deepcopy(ROW), FIELDS, PRODUCTS, mode="override")
    assert (r["starting_year"], r["hq"], r["sector"]) == (1973, "Versailles, France", "Defence"), r
    assert r["origins"] == {"starting_year": "curated", "hq": "curated", "sector": "pipeline",
                            "company_size": "curated"}, r["origins"]
    assert [p["name"] for p in r["products"]] == ["RCH-155", "TITUS"], r["products"]
    assert all(p["origin"] == "curated" for p in r["products"])

    # FALLBACK: the pipeline wins; the file fills only blanks
    r = app.apply_curated(copy.deepcopy(ROW), FIELDS, PRODUCTS, mode="fallback")
    assert (r["starting_year"], r["hq"], r["company_size"]) == (2024, "Versailles, France", "4,000 employees"), r
    assert r["origins"] == {"starting_year": "pipeline", "hq": "curated", "sector": "pipeline",
                            "company_size": "curated"}, r["origins"]
    # products: stored first, matched across typography, blanks filled, file-only ones appended;
    # the stored name-only "CAESAR" carries no spec sheet, so it is not served (2026-09-18)
    names = [p["name"] for p in r["products"]]
    assert names == ["RCH 155", "TITUS"], names
    rch = r["products"][0]
    assert rch["origin"] == "pipeline" and rch["source"] == "forcesnews.com", rch
    assert rch["specs"] == {"Calibre": "155 mm"} and rch["fieldOrigins"] == {"category": "curated", "specs": "curated"}, rch
    assert r["products"][1]["origin"] == "curated"

    # no curated entry: the row keeps its own values, now labelled
    r = app.apply_curated(copy.deepcopy(ROW), None, None, mode="fallback")
    assert r["starting_year"] == 2024 and r["origins"]["starting_year"] == "pipeline"
    assert "hq" not in r["origins"], r["origins"]                  # blank on both sides: no origin claimed
    assert [p["origin"] for p in r["products"]] == ["pipeline", "pipeline"]

    edge_cases()

    # the newer revenue wins over a stale curated one (fact check 2026-09-20)
    r = app.apply_curated({"sales": [{"value": "£5,177.7m", "detail": "FY2026", "url": "u", "line": "l"}]},
                          {"sales": [{"value": "£4,831.3m", "detail": "FY2025", "url": "u", "line": "l"}]}, [])
    assert r["sales"][0]["value"] == "£5,177.7m" and r["origins"]["sales"] == "pipeline"
    r = app.apply_curated({"sales": [{"value": "old", "detail": "FY2019", "url": "u", "line": "l"}]},
                          {"sales": [{"value": "new", "detail": "FY2025", "url": "u", "line": "l"}]}, [])
    assert r["sales"][0]["value"] == "new" and r["origins"]["sales"] == "curated"

    # Live Web Mentions on a product page search the product, not the company
    assert app._pulse_query("Adani Defence", "Drishti-10 Starliner") == '"Drishti-10 Starliner" Adani Defence'
    # the company query carries the CLIENT's own qualifier (dataset client.newsQuery, sent
    # by the page as `topic`) -- KSSL's is defence; a client that sends none gets none
    assert app._pulse_query("Adani Defence", topic="defence OR defense") == '"Adani Defence" defence OR defense'
    assert app._pulse_query("Caterpillar") == '"Caterpillar"'

    # enriched mode: only enrichment values (specDocs) are served, curated never
    cur = [{"name": "K9", "specs": {"Calibre": "155 mm", "Crew": "5"}}]
    row = {"products": [
        {"name": "K9", "origin": "enriched", "specs": {"Calibre": "155 mm", "Range": "40 km"},
         "specDocs": {"Calibre": 65, "Range": 37}, "specsAlsoReported": {"Range": "480 km"}},
        {"name": "K9 Thunder", "origin": "pipeline", "enrichedSpecs": ["Weight"],
         "specs": {"Weight": "47 t", "Range": ">40 km (agent)", "Crew": "3"}, "specDocs": {"Weight": 9}},
        {"name": "Old stub", "origin": "pipeline", "specs": {"Range": "10 km"}}]}
    r = app.apply_curated(row, {}, cur, products_mode="enriched")
    assert [p["name"] for p in r["products"]] == ["K9", "K9 Thunder"], r["products"]
    assert r["products"][0]["specs"] == {"Calibre": "155 mm", "Range": "40 km"}
    assert r["products"][0]["specsAlsoReported"] == {"Range": "480 km"}
    assert r["products"][0]["incomplete"] is False
    # one enriched value lists the product, marked thin; its agent values still never serve
    assert r["products"][1]["specs"] == {"Weight": "47 t"} and r["products"][1]["incomplete"] is True

    # the default is today's behaviour
    assert app.OVERRIDES_MODE == "override" or os.environ.get("KSSL_OVERRIDES_MODE")

    # the real files load and cover the companies they did on 2026-09-16
    assert len(app.COMPANY_OVERRIDES) >= 49 and len(app.PRODUCTS_OVERLAY) >= 48
    json.dumps(r)
    print("ok  curated fallback")


if __name__ == "__main__":
    main()
