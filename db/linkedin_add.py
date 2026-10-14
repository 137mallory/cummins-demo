"""Add one leader's LinkedIn text (typed in by hand from a user's paste) to <pack>/leader_linkedin.json.

    from linkedin_add import add
    add("CATERPIL", "Jason E. Kaiser", "Caterpillar Inc.", [(role, from, to), ...], [(institution, degree, from, to), ...])

Years only (months dropped). The file has the shape db/leader_bios.py reads, and the build applies it last.
"""
import json
import os

PACK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "parallax-cummins-arabia-datapack", "leader_linkedin.json")
NOTE = "Source: LinkedIn profile text pasted by the user on {date} (Experience and Education as shown; months dropped, years kept). No profile URL was provided."


def add(cid, name, company, exp, edu, title=None, date="14 Oct 2026", url=None, path=PACK):
    d = json.load(open(path)) if os.path.exists(path) else {}
    spec = d.setdefault(cid, {"leaders": [], "drop": []})
    rec = {"name": name, "title": title,
           "experience": [{"company": c if isinstance(c, str) and c else company, "role": r, "from": a, "to": b} for (r, a, b, *c) in [(*e, None) if len(e) == 3 else e for e in exp] for c in [c[0] if c else company]],
           "education": [{"institution": i, "degree": g, "from": a, "to": b} for i, g, a, b in edu],
           "bio_source": url, "note": NOTE.format(date=date), "quote": "", "new": False}
    spec["leaders"] = [l for l in spec["leaders"] if l["name"] != name] + [rec]
    json.dump(d, open(path, "w"), indent=2, ensure_ascii=False)
    return len(rec["experience"]), len(rec["education"])


if __name__ == "__main__":
    import tempfile
    t = os.path.join(tempfile.mkdtemp(), "x.json")
    assert add("X", "A B", "Co", [("CEO", "2020", "Present"), ("CFO", "2015", "2020", "Other Co")], [("Uni", "BSc", "1990", "1994")], path=t) == (2, 1)
    r = json.load(open(t))["X"]["leaders"][0]
    assert r["experience"][1]["company"] == "Other Co" and r["experience"][0]["company"] == "Co" and r["education"][0]["to"] == "1994"
    add("X", "A B", "Co", [("COO", "2010", "2015")], [], path=t)       # same name again replaces
    assert len(json.load(open(t))["X"]["leaders"]) == 1
    print("ok")
