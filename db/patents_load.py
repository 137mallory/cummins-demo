"""Patent records for the Competitive > Patent page.

    python db/patents_load.py merge <out patents.json> <research file.json> [more files ...]
    python db/patents_load.py --demo

`merge` reads the research files (a JSON list of records each, see refresh_2026-10-13/BRIEF.md),
refuses any record that is not a complete, sourced filing, drops repeats of one patent number and
writes <pack>/patents.json. `apply(data, records)` (used by dataset_from_html.py when
<pack>/patents.json exists) fills PATENTS.byArea / byAssignee / _meta, which the page's own adapter
turns into the rival and field lenses. No threat or relevance grade is written: nobody assessed one.

A record is kept only if: comp_id is a tracked competitor, area is one of the dataset's areas, `no`
and `title` and `assignee` are present, `status` is granted or pending, dates are YYYY-MM-DD or
empty, and `url` is an http(s) page.
"""
import json
import re
import sys
from urllib.parse import urlparse

DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PROVIDER = {"lens.org": "Lens.org", "patents.google.com": "Google Patents", "patentimages.storage.googleapis.com": "Google Patents",
            "ppubs.uspto.gov": "USPTO", "pdfaiw.uspto.gov": "USPTO", "patft.uspto.gov": "USPTO", "data.epo.org": "EPO",
            "worldwide.espacenet.com": "EPO Espacenet", "register.epo.org": "EPO", "patentscope.wipo.int": "WIPO Patentscope"}


def problems(r, comps, areas):
    """Why a record is refused (empty list = keep)."""
    p = []
    if r.get("comp_id") not in comps:
        p.append(f"comp_id {r.get('comp_id')!r} is not tracked")
    if r.get("area") not in areas:
        p.append(f"area {r.get('area')!r} is not one of the areas")
    for k in ("no", "title", "assignee"):
        if not str(r.get(k) or "").strip():
            p.append(f"{k} missing")
    if r.get("status") not in ("granted", "pending"):
        p.append(f"status {r.get('status')!r}")
    for k in ("filed", "published", "granted"):
        if r.get(k) and not DATE.match(r[k]):
            p.append(f"{k} {r[k]!r} is not a date")
    if urlparse(r.get("url") or "").scheme not in ("http", "https"):
        p.append("url is not a page")
    if r.get("status") == "granted" and not r.get("granted"):
        p.append("granted without a grant date")
    return p


def merge(files, comps, areas):
    kept, seen, refused = [], set(), []
    for f in files:
        for r in json.load(open(f, encoding="utf-8")):
            if not str(r.get("title") or "").strip() and r.get("title_en"):
                r["title"] = r["title_en"]      # DE/FR filings: the page only prints an English machine translation
            why = problems(r, comps, areas)
            key = re.sub(r"\W", "", str(r.get("no") or "")).upper()
            if key in seen:
                why.append("repeats a patent number already kept")
            if why:
                refused.append((r.get("no"), why))
                continue
            seen.add(key)
            kept.append(r)
    return kept, refused


def apply(data, records):
    """PATENTS.byArea / byAssignee (the same rows, grouped two ways) and _meta."""
    areas = (data.get("PATENTS") or {}).get("techAreas") or []
    by_area = {a: [r for r in records if r["area"] == a] for a in areas}
    by_area = {a: l for a, l in by_area.items() if l}
    by_asg = {}
    for r in records:
        by_asg.setdefault(r["assignee"], []).append(r)
    host = lambda r: urlparse(r["url"]).netloc.removeprefix("www.")
    providers = sorted({PROVIDER[host(r)] for r in records if host(r) in PROVIDER})
    data["PATENTS"].update(byArea=by_area, byAssignee=by_asg,
                           _meta={"providers": providers, "total": len(records), "filings12m": 0})
    return len(records)


def demo():
    comps, areas = {"A"}, ["X"]
    good = {"comp_id": "A", "area": "X", "no": "US 1 B2", "title": "t", "assignee": "a", "status": "granted",
            "granted": "2024-01-02", "filed": "2022-01-01", "url": "https://www.lens.org/lens/patent/US_1_B2"}
    assert problems(good, comps, areas) == []
    assert len(problems({**good, "status": "filed", "area": "Y", "url": "x"}, comps, areas)) == 3
    d = {"PATENTS": {"techAreas": ["X"], "byArea": {}, "byAssignee": {}}}
    assert apply(d, [good]) == 1 and d["PATENTS"]["byArea"] == {"X": [good]} and d["PATENTS"]["_meta"]["providers"] == ["Lens.org"]
    print("demo ok")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo()
    elif sys.argv[1:2] == ["merge"]:
        pack = json.load(open("parallax-cummins-arabia-datapack/dataset.html.json", encoding="utf-8"))
        kept, refused = merge(sys.argv[3:], set(pack["competitors"]), pack["PATENTS"]["techAreas"])
        json.dump(kept, open(sys.argv[2], "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print(f"kept {len(kept)}, refused {len(refused)}")
        for n, why in refused:
            print("  refused", n, why)
