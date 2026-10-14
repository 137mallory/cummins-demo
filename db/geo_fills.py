"""Geo footprint fill: makes the footprint carry what the overlap test and the map need.

What the export's footprint rows lacked, found 2026-10-14:
  * no row named the rating bands an offering covers, and CAT_META held no keyword for a band, so the overlap
    test (frontend/src/lib/geo.js) could never put a rival and the client in the same product category and
    answered "meets Cummins Arabia in 0 of them" in every country;
  * eight dealer rows were marked "not verified" or "city n/d";
  * no row carried a place a map could draw (only the country).

apply(data, pack_dir) does three things, none of which invents a fact:
  1. applies <pack>/geo_fills.json (rows researched from the companies' own pages, each with its source);
  2. tags every offering row that states a rating range with the bands that range covers (from the range the
     row itself gives, converted at 0.8 power factor when it is given in kW) and fills CAT_META's keywords with
     the band labels, so the existing overlap test can run;
  3. gives each site row the city-level coordinates of the city it names (`points`), left off when the city is
     not named.

    python db/geo_fills.py          (self-check)
"""
import copy
import json
import os
import re

# approximate city-centre coordinates (city precision, not street)
CITY = {
    "al khobar": (26.2172, 50.1971), "khobar": (26.2172, 50.1971), "arar": (30.9753, 41.0381), "dammam": (26.4207, 50.0888),
    "dhahran": (26.2361, 50.0393), "duba": (27.35, 35.69), "hail": (27.5114, 41.7208), "hofuf": (25.3647, 49.587),
    "jeddah": (21.4858, 39.1925), "jizan": (16.8892, 42.5511), "jubail": (27.0046, 49.646), "khamis mushait": (18.3, 42.7333),
    "madinah": (24.5247, 39.5692), "makkah": (21.3891, 39.8579), "najran": (17.5656, 44.2289), "qassim": (26.326, 43.975),
    "buraidah": (26.326, 43.975), "riyadh": (24.7136, 46.6753), "sakaka": (29.9697, 40.2064), "tabuk": (28.3838, 36.555),
    "taif": (21.2703, 40.4158), "yanbu": (24.0895, 38.0618),
    "abu dhabi": (24.4539, 54.3773), "al ain": (24.2075, 55.7447), "dubai": (25.2048, 55.2708), "jebel ali": (25.0112, 55.061),
    "al quoz": (25.138, 55.231), "ras al khor": (25.185, 55.34), "sharjah": (25.3463, 55.4209), "madinat zayed": (23.66, 53.7),
    "kuwait city": (29.3759, 47.9774), "safat": (29.3759, 47.9774), "ahmadi": (29.0769, 48.0838), "shuwaikh": (29.35, 47.94),
    "kuwait free trade zone": (29.357, 47.93), "al-faiha": (29.33, 47.995),
}
GENERAL = {"dubai": ("jebel ali", "al quoz", "ras al khor"), "kuwait city": ("shuwaikh", "ahmadi"), "qassim": ("buraidah",)}
BANDS = {"sub500": (0, 499.99), "mid": (500, 1000), "hhp": (1001, 2000), "vhhp": (2001, 3000), "dc": (3001, 1e9)}
RANGE = re.compile(r"([\d.,]+)\s*(kva|kw)\s*-\s*([\d.,]+)\s*(kva|kw)", re.I)
TAG = " Rating bands covered: "


def bands_of(text):
    """The bands a stated range reaches, or []; kW is converted to kVA at 0.8 power factor."""
    m = RANGE.search(text or "")
    if not m:
        return []
    f = lambda v, u: float(v.replace(",", "")) * (1.25 if u.lower() == "kw" else 1)
    lo, hi = f(m.group(1), m.group(2)), f(m.group(3), m.group(4))
    return [b for b, (a, z) in BANDS.items() if lo <= z and hi >= a]


def points_of(place):
    t = str(place or "").lower()
    hit = [k for k in CITY if re.search(r"(?<![a-z])" + re.escape(k) + r"(?![a-z])", t)]   # whole words: "duba" is not in "Dubai"
    hit = [k for k in hit if not any(s in hit for s in GENERAL.get(k, ()))]
    out, seen = [], set()
    for k in hit:
        if CITY[k] not in seen:
            seen.add(CITY[k])
            out.append({"city": k.title().replace("Al-Faiha", "Al-Faiha"), "lat": CITY[k][0], "lng": CITY[k][1]})
    return out


def apply(data, pack_dir=None):
    geo = data.get("geoData") or {}
    report = {"rows_replaced": 0, "rows_added": 0, "notes_changed": 0, "banded": 0, "pointed": 0, "sites": 0}
    path = os.path.join(pack_dir, "geo_fills.json") if pack_dir else None
    if path and os.path.exists(path):
        for f in json.load(open(path, encoding="utf-8"))["fills"]:
            rows = geo[f["cid"]][f["country"]]
            if "replace" in f:
                i = next(i for i, r in enumerate(rows) if all(r.get(k) == v for k, v in f["replace"].items()))
                rows[i] = f["row"]
                report["rows_replaced"] += 1
            if "add" in f:
                if not any(r["name"] == f["add"]["name"] and r["val"] == f["add"]["val"] for r in rows):
                    rows.append(f["add"])
                    report["rows_added"] += 1
            if "note_replace" in f:
                n = f["note_replace"]
                r = next(r for r in rows if n["match"] in r["name"] and n["old"] in r["note"])
                r["note"] = r["note"].replace(n["old"], n["new"])
                if f.get("add_src") and f["add_src"] not in r["srcs"]:
                    r["srcs"].append(f["add_src"])
                report["notes_changed"] += 1
    # a row that only says "not verified" is not a footprint row: drop it rather than show an empty site
    for rows_by in geo.values():
        for ct, rows in rows_by.items():
            keep = [r for r in rows if not (re.match(r"(not verified|none verified)", str(r.get("val", "")), re.I) and "tracked range" not in r["name"])]
            report["placeholders_dropped"] = report.get("placeholders_dropped", 0) + len(rows) - len(keep)
            rows[:] = keep
    labels = dict(data.get("POS_CATS") or [])
    for rows_by in geo.values():
        for rows in rows_by.values():
            for r in rows:
                offering = "tracked range" in r["name"] or r["name"].startswith("Cummins diesel and gas gensets")
                bs = bands_of(r.get("val")) if offering else []
                if bs and TAG not in r["note"]:
                    r["note"] = (r["note"].rstrip() + TAG + "; ".join(labels.get(b, b) for b in bs) + "."
                                 + (" (kW converted to kVA at 0.8 power factor.)" if re.search(r"kw\s*-\s*[\d.,]+\s*kw", r["val"], re.I) else ""))
                    report["banded"] += 1
                if not offering:
                    report["sites"] += 1
                    pts = points_of(r.get("qty"))
                    if pts:
                        r["points"] = pts
                        report["pointed"] += 1
    for b, lab in labels.items():
        if b in (data.get("CAT_META") or {}):
            data["CAT_META"][b]["kw"] = [lab.lower()]
    return report


if __name__ == "__main__":
    assert bands_of("715 kVA - 5000 kVA") == ["mid", "hhp", "vhhp", "dc"]
    assert bands_of("556 kVA - 833 kVA") == ["mid"] and bands_of("1000 kVA - 4000 kVA") == ["mid", "hhp", "vhhp", "dc"]
    assert bands_of("2.5 kW - 3500 kW gensets") == ["sub500", "mid", "hhp", "vhhp", "dc"] and bands_of("n/d") == []
    assert [p["city"] for p in points_of("Dubai (Jebel Ali Free Zone)")] == ["Jebel Ali"] and [p["city"] for p in points_of("Dubai")] == ["Dubai"]
    assert [p["city"] for p in points_of("Qassim (Buraidah)")] == ["Buraidah"] and [p["city"] for p in points_of("Qassim")] == ["Qassim"] and points_of("Saudi Arabia (city not stated)") == []
    d = {"POS_CATS": [["mid", "Mid range (500 to 1,000 kVA)"]], "CAT_META": {"mid": {}},
         "geoData": {"A": {"KSA": [{"name": "X gensets · tracked range", "val": "556 kVA - 833 kVA", "note": "n.", "qty": "556 kVA - 833 kVA", "srcs": []},
                                   {"name": "Dealer · Riyadh", "val": "d", "note": "", "qty": "Riyadh", "srcs": []}]}}}
    r1 = apply(d)
    r2 = apply(copy.deepcopy(d))
    assert d["CAT_META"]["mid"]["kw"] == ["mid range (500 to 1,000 kva)"] and "Mid range" in d["geoData"]["A"]["KSA"][0]["note"] and r1["pointed"] == 1
    n = d["geoData"]["A"]["KSA"][0]["note"]
    apply(d)
    assert d["geoData"]["A"]["KSA"][0]["note"] == n, "apply must be idempotent"
    d["geoData"]["A"]["KSA"].append({"name": "Dealer branch · city n/d", "val": "Not verified", "note": "", "qty": "", "srcs": []})
    assert apply(d)["placeholders_dropped"] == 1 and len(d["geoData"]["A"]["KSA"]) == 2
    print("ok")
