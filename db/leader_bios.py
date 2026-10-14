"""Leader bios (<pack>/leader_bios.json): education and professional experience for each competitor's leaders.

Per competitor: {"leaders": [{name, title, experience[{company, role, from, to}], education[{institution, degree, from, to}],
bio_source, quote, note, new}], "drop": [names]}. apply() matches a record to the competitor's existing leader by first
initial + last name, fills education / experience / bio_source and the verified title, appends a leader marked `new`, and
removes the names in `drop` (people who have left, or who are a distributor's staff and not the competitor's own).
A person with nothing published keeps empty lists: the page says so, nothing is inferred.
"""
import re


def _key(name):
    t = [w for w in re.sub(r"\([^)]*\)", " ", str(name or "")).replace(".", " ").replace(",", " ").split() if len(w) > 1 or w.isalpha()]
    t = [w.lower() for w in t if w.lower() not in ("dr", "mr", "ms", "mrs", "prof", "jr", "sr")]
    return (t[0][0], t[-1]) if t else ("", "")


def apply(data, pack):
    upd = new = dropped = 0
    for cid, spec in pack.items():
        comp = (data.get("competitors") or {}).get(cid)
        if comp is None:
            continue
        lst = comp.setdefault("leadership", [])
        gone = {_key(n) for n in spec.get("drop") or []}
        before = len(lst)
        lst[:] = [l for l in lst if _key(l.get("value")) not in gone]
        dropped += before - len(lst)
        for r in spec.get("leaders") or []:
            hit = next((l for l in lst if _key(l.get("value")) == _key(r["name"])), None)
            if hit is None:
                hit = {"value": r["name"], "detail": r.get("title") or "", "url": r.get("bio_source"), "line": r.get("quote") or ""}
                lst.append(hit)
                new += 1
            else:
                upd += 1
                if r.get("title"):
                    hit["detail"] = r["title"]
            # a blank end year would read as "Present" on the page: an end the source does not state is "—"
            hit["experience"] = [dict(e, to=e.get("to") or "—") for e in r.get("experience") or []]
            hit["education"] = r.get("education") or []
            hit["bio_source"] = r.get("bio_source")
            if r.get("note"):
                hit["bio_note"] = r["note"]
    return {"updated": upd, "added": new, "dropped": dropped}


if __name__ == "__main__":
    d = {"competitors": {"X": {"leadership": [{"value": "Joseph E. (Joe) Creed", "detail": "old"}, {"value": "Gone Person", "detail": "t"}]}}}
    p = {"X": {"drop": ["Gone Person"], "leaders": [
        {"name": "Joseph E. (Joe) Creed", "title": "Chairman and CEO", "experience": [{"company": "C", "role": "CEO", "from": "2025", "to": "Present"}],
         "education": [{"institution": "U", "degree": "BSc"}], "bio_source": "https://x"},
        {"name": "Ann Lee", "title": "CFO", "experience": [], "education": [], "bio_source": "https://y", "new": True}]}}
    r = apply(d, p)
    assert r == {"updated": 1, "added": 1, "dropped": 1}, r
    L = d["competitors"]["X"]["leadership"]
    assert [l["value"] for l in L] == ["Joseph E. (Joe) Creed", "Ann Lee"] and L[0]["detail"] == "Chairman and CEO" and L[0]["education"][0]["degree"] == "BSc"
    assert apply({"competitors": {"X": {"leadership": []}}}, {"X": {"leaders": [{"name": "A B", "experience": [{"role": "r", "from": "", "to": ""}]}]}}) == {"updated": 0, "added": 1, "dropped": 0}
    d2 = {"competitors": {"X": {"leadership": []}}}
    apply(d2, {"X": {"leaders": [{"name": "A B", "experience": [{"role": "r", "from": "2001", "to": ""}, {"role": "s", "from": "2010", "to": "Present"}]}]}})
    assert [e["to"] for e in d2["competitors"]["X"]["leadership"][0]["experience"]] == ["—", "Present"]   # unknown end is not "Present"
    assert _key("Dr. Jörg Stratmann") == ("j", "stratmann") and _key("Jörg Stratmann") == ("j", "stratmann")
    print("ok")
