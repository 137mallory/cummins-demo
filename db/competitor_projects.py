"""Projects page data: frontend/src/lib/competitorProjects.js.

What each tracked competitor is working on or pursuing, in the Gulf and worldwide: customer deals, framework
supply, capacity builds and the Gulf reference projects its dealers have delivered. The curation is
<pack>/competitor_projects.json (db/competitor_projects_seed.py): which records form one project, and its kind,
stage, scale and dated timeline. The words (what happened, the analyst's read for the client), the dates and the
links are read from the records in the dataset, so nothing here is written that a record does not say.

    python db/competitor_projects.py <dataset.html.json> <frontend/src/lib/competitorProjects.js> [competitor_projects.json]
"""
import json
import os
import re
import sys

STAGES = ["Planned", "Committed", "In progress", "Delivered"]
STANCE = {"THREAT": "threat", "WATCH": "watch", "OPPORTUNITY": "fav", "FAV": "fav", "Threat": "threat", "Watch": "watch", "Opportunity": "fav"}
SEVERITY = {"threat": 3, "watch": 2, "fav": 1}


def starts(text, prefixes):
    return any(str(text or "").startswith(p) for p in prefixes)


def mean_parts(mean):
    """('Threat', 'text') from a partner row's `mean` ('<b>Threat:</b> text <span>source</span>')."""
    m = str(mean or "")
    verdict = re.match(r"\s*(?:<b>)?\s*(Threat|Watch|Opportunity)\s*:", m)
    text = re.sub(r"<span[^>]*>[\s\S]*?</span>", "", m)
    text = re.sub(r"^\s*(?:<b>)?\s*(?:Threat|Watch|Opportunity)\s*:\s*(?:</b>)?\s*", "", text)
    return (verdict.group(1) if verdict else None), re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", text)).strip()


def norm_date(s):
    s = str(s)
    return s + "-01-01"[len(s) - 4:] if re.fullmatch(r"\d{4}(-\d{2})?", s) else s


def uniq(items):
    out = []
    for x in items:
        if x and x not in out:
            out.append(x)
    return out


def build_one(p, data, as_of):
    co = data["competitors"][p["cid"]]
    prof = co.get("profile") or {}
    refs = p["refs"]
    moves = [m for m in prof.get("moves") or [] if starts(m.get("headline"), refs.get("move", []))]
    news = [n for n in (data.get("competitorNews") or {}).get(p["cid"], []) if starts(n.get("title"), refs.get("news", []))]
    gulf = [r for r in prof.get("refs") or [] if starts(r.get("project"), refs.get("ref", []))]
    part = [x for x in co.get("partners") or [] if x.get("id") in refs.get("partner", [])]
    # every record the curation names must exist: a missing one means the dataset changed under the curation
    for kind, found, key, wanted in (("move", moves, "headline", refs.get("move", [])), ("news", news, "title", refs.get("news", [])),
                                     ("ref", gulf, "project", refs.get("ref", [])), ("partner", part, "id", refs.get("partner", []))):
        for w in wanted:
            assert any(str(x.get(key) or "").startswith(w) for x in found), f"{p['id']}: {kind} '{w}' not found under {p['cid']}"
    overview = uniq([m.get("summary") for m in moves] + [n.get("description") for n in news] + [r.get("summary") for r in gulf])[:3]
    analyses = uniq([m.get("analysis") for m in moves] + [n.get("analysis") for n in news])
    stances = [STANCE.get(m.get("level")) for m in moves] + [STANCE.get(n.get("level")) for n in news]
    if not analyses:
        for x in part:
            verdict, text = mean_parts(x.get("mean"))
            if text:
                analyses.append(text)
                stances.append(STANCE.get(verdict))
    stances = [s for s in stances if s] or ([p["stance"]] if p.get("stance") else [])
    stance = max(stances, key=lambda s: SEVERITY[s]) if stances else None
    sources = []
    for url, label in ([(m.get("url"), "News") for m in moves] + [(n.get("url"), n.get("source")) for n in news]
                       + [(r.get("source_url"), "Source") for r in gulf]
                       + [(s.get("url"), s.get("label")) for x in part for s in x.get("srcs") or []]):
        if url and url.startswith("http") and url not in [s["url"] for s in sources]:
            host = re.sub(r"^https?://(www\.)?", "", url).split("/")[0]
            sources.append({"label": host, "url": url})
    events = sorted(({"date": e[0], "label": e[1], "expected": len(e) > 2} for e in p["timeline"]),
                    key=lambda e: norm_date(e["date"]) if e["date"][:1].isdigit() else "0000")
    done = [e for e in events if e["date"][:1].isdigit() and not e["expected"] and norm_date(e["date"]) <= as_of]
    return {
        "id": p["id"], "cid": p["cid"], "company": co.get("name"), "name": p["name"], "kind": p["kind"], "region": p["region"],
        "customer": p["customer"], "location": p["location"], "stage": STAGES[p["stage"] - 1], "stageRank": p["stage"],
        "stageNote": p["stageNote"], "mw": p.get("mw"), "specs": [{"k": k, "v": v} for k, v in p["specs"]],
        "timeline": events, "latest": done[-1] if done else None,
        "overview": overview, "assessment": {"stance": stance, "read": analyses[:2]}, "sources": sources,
    }


def build(data, curation):
    as_of = curation.get("_asOf", "2026-10-13")
    return [build_one(p, data, as_of) for p in curation["projects"]], as_of


JS = """/**
 * COMPETITOR PROJECTS: generated by db/competitor_projects.py from the served dataset and
 * <pack>/competitor_projects.json. Do not edit by hand.
 *
 * What each tracked competitor is working on or pursuing, in the Gulf and worldwide. Text, dates and links are
 * read from the dataset's own records. Data is as of %(as_of)s.
 */

export const AS_OF = %(as_of)s;

export const PROJECT_STAGES = %(stages)s;

export const PROJECTS_DATA = %(projects)s;
"""

if __name__ == "__main__":
    if len(sys.argv) < 3:
        d = {"competitors": {"X": {"name": "Xco", "profile": {"moves": [{"headline": "Big deal", "summary": "S", "level": "THREAT", "analysis": "A", "url": "https://a.com/x"}],
                                                              "refs": [{"project": "Old job", "summary": "R", "source_url": "https://b.com/y"}]},
                                   "partners": [{"id": "P1", "mean": "<b>Watch:</b> reads this. <span style='o'>· <a href='u'>s</a></span>", "srcs": [{"url": "https://c.com/z"}]}]}},
             "competitorNews": {"X": []}}
        c = {"_asOf": "2026-10-13", "projects": [
            {"id": "a", "cid": "X", "name": "A", "kind": "k", "region": "Gulf", "customer": "c", "location": "l", "stage": 2, "stageNote": "n",
             "refs": {"move": ["Big"], "ref": ["Old"]}, "timeline": [["2026-12", "later", "expected"], ["2026-01-05", "first"]], "specs": [["k", "v"]], "mw": None},
            {"id": "b", "cid": "X", "name": "B", "kind": "k", "region": "Gulf", "customer": "c", "location": "l", "stage": 4, "stageNote": "n",
             "refs": {"partner": ["P1"], "ref": ["Old"]}, "timeline": [["Undated", "x"]], "specs": []}]}
        ps, _ = build(d, c)
        assert ps[0]["assessment"] == {"stance": "threat", "read": ["A"]} and ps[0]["latest"]["label"] == "first" and ps[0]["overview"] == ["S", "R"]
        assert ps[1]["assessment"] == {"stance": "watch", "read": ["reads this."]} and ps[1]["latest"] is None and len(ps[1]["sources"]) == 2
        assert mean_parts("plain") == (None, "plain")
        print("ok")
        sys.exit()
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    path = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), "competitor_projects.json")
    ps, as_of = build(data, json.load(open(path, encoding="utf-8")))
    open(sys.argv[2], "w", encoding="utf-8").write(JS % {"as_of": json.dumps(as_of), "stages": json.dumps(STAGES), "projects": json.dumps(ps, indent=2, ensure_ascii=False)})
    from collections import Counter
    print(f"{len(ps)} projects -> {sys.argv[2]}", dict(Counter(p['company'] for p in ps)))
