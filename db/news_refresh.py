"""News refresh (<pack>/news_refresh.json): the newest researched news, replacing older news.

A refresh item is one verified article (url + verbatim quote + its own publish date). apply()
turns the items into the three card lanes the views read (competitiveCards, marketCards,
techCards), their detail records, and the per-company news lists (competitorNews), and drops
every non-tender card dated before the window start: the feed is the new window, not a
history. Tender cards (meta "Tender · ...") are untouched; they follow the tender data.
An item with no url, quote, usable date or known lane is refused and counted, never guessed.
"""
import datetime as dt
import re

LANES = {"competitive": ("competitiveCards", "cm", "Competitive Signal"),
         "market": ("marketCards", "m", "Market Signal"),
         "tech": ("techCards", "ti", "Technology Signal")}
DIR = {"THREAT": "threat", "WATCH": "watch", "FAV": "fav"}
SEV = {"high": 0, "medium": 1, "low": 2}
LENS = {"Contract": "COMMERCIAL", "Capacity": "SUPPLY CHAIN", "Expansion": "COMMERCIAL",
        "Partnership": "COMMERCIAL", "Financial": "FINANCIAL", "Product": "TECHNOLOGY",
        "Pipeline": "COMMERCIAL", "Regulatory": "REGULATORY", "Demand shift": "COMMERCIAL",
        "Risk outlook": "GEOPOLITICAL"}
OWN = "Cummins Arabia"          # competitorNews key of the client's own news
MIN_MOVES = 3                   # fewer moves than this in the window: older ones are kept, marked `older`


def _date(s):
    """ISO ("2026-09-22") or written ("22 Sep 2026", "Sep 2026") -> date; written month-only = day 1."""
    s = str(s or "").strip()
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return dt.date(*map(int, m.groups()))
    m = re.fullmatch(r"(\d{4})(?:-(\d{2}))?", s)         # "2026-04" / "2023": first day of that month / year
    if m:
        return dt.date(int(m.group(1)), int(m.group(2) or 1), 1)
    for f, pat in (("%d %b %Y", r"(\d{1,2} [A-Za-z]{3} \d{4})"), ("%b %Y", r"([A-Za-z]{3} \d{4})")):
        m = re.search(pat, s)
        if m:
            try:
                return dt.datetime.strptime(m.group(1), f).date()
            except ValueError:
                pass
    return None


def _fmt(d):
    return d.strftime("%d %b %Y")


def _key(s):
    return re.sub(r"[^a-z0-9]+", " ", str(s or "").lower()).strip()


def _url_key(u):
    return re.sub(r"^https?://(www\.)?|[?#].*$|/+$", "", str(u or "").lower())


def valid(it, start, today):
    d = _date(it.get("date"))
    return bool(it.get("title") and str(it.get("url", "")).startswith("http") and it.get("quote")
                and it.get("lane") in LANES and it.get("level") in DIR and d and start <= d <= today)


def _company(out, it):
    cid = it.get("company_id")
    if cid == "CUMMINS":
        return OWN
    comp = (out.get("competitors") or {}).get(cid) or {}
    return comp.get("name") or it.get("entity") or "Market"


def _meta(it, company, d):
    kind = it.get("kind") or "News"
    if it["lane"] == "market":
        parts = [kind, it.get("country") or "", it.get("segment") or "", _fmt(d)]
        return " · ".join(p for p in parts if p)
    return f"{kind} · {company} · {_fmt(d)}"


def apply(out, items, start, today):
    kept, bad, seen = [], 0, set()
    for it in items:
        if not valid(it, start, today):
            bad += 1
            continue
        k = (_url_key(it["url"]), _key(it["title"]))
        if k[0] in {s[0] for s in seen} or k[1] in {s[1] for s in seen}:
            continue                           # the same article twice
        seen.add(k)
        kept.append(it)

    # an article already in the feed (a kept card carries its url) is not added a second time
    have = {_url_key(c.get("url")) for f, _, _ in LANES.values() for c in out.get(f) or []
            if str(c.get("meta", "")).startswith("Tender ·") or ((_date(c.get("ago") or c.get("meta")) or today) >= start)}
    # the same story from another page: similar headline (word overlap) within 5 days of a kept card
    words = lambda t: set(re.findall(r"[a-z0-9]+", str(t).lower())) - {"the", "a", "an", "of", "to", "and", "in", "for", "on", "at", "by", "as"}
    cards = [(words(c.get("title")), _date(c.get("ago") or c.get("meta")))
             for f, _, _ in LANES.values() for c in out.get(f) or [] if not str(c.get("meta", "")).startswith("Tender ·")]

    def same_story(it):
        w, d = words(it["title"]), _date(it["date"])
        return any(cw and d and cd and abs((d - cd).days) <= 5 and len(w & cw) / len(w | cw) >= 0.5 for cw, cd in cards)
    before = len(kept)
    kept = [it for it in kept if _url_key(it["url"]) not in have and not same_story(it)]
    dup = before - len(kept)

    # The Technology page neutralises every card to "advancement" and leaves threats to the Competitive
    # feed ("anything that directly impacts the client is a competitive threat there"): a tracked
    # competitor's product move graded THREAT is served as a competitive card
    for it in kept:
        if it["lane"] == "tech" and it["level"] == "THREAT" and it.get("company_id") in (out.get("competitors") or {}):
            it["lane"] = "competitive"

    dropped = 0
    news = out.setdefault("competitorNews", {})
    for lane, (field, prefix, label) in LANES.items():
        old = out.get(field) or []
        keep = []
        for c in old:
            d = _date(c.get("ago") or c.get("meta"))
            if str(c.get("meta", "")).startswith("Tender ·") or (d and d >= start):
                keep.append(c)
            else:
                dropped += 1
        new = []
        for it in sorted((i for i in kept if i["lane"] == lane),
                         key=lambda i: (SEV.get(i.get("severity"), 1), -_date(i["date"]).toordinal())):
            d = _date(it["date"])
            company = _company(out, it)
            cid = f"rf{prefix}{len(new) + 1}"
            lens = LENS.get(it.get("kind"), "COMMERCIAL")
            # The Market overview lists non-tender signals as "Perceived opportunities": cards marked
            # `watch` whose tags name one of the client's categories (KSSL_CATS). A market signal is
            # served that way; the researched level stays in `severity` and the analysis text.
            dirn = "watch" if lane == "market" else DIR[it["level"]]
            tags = " ".join(out.get("KSSL_CATS") or []) if lane == "market" else DIR[it["level"]]
            card = {"id": cid, "dir": dirn, "title": it["title"],
                    "meta": _meta(it, company, d), "company": company, "lens": lens,
                    "sowhat": it.get("analysis") or "", "sec": [], "url": it["url"], "ago": _fmt(d),
                    "tags": tags or dirn, "severity": it.get("severity") or "medium"}
            new.append(card)
            src = re.sub(r"^https?://(www\.)?|/.*$", "", it["url"])
            (out.setdefault("details", {}))[cid] = {
                "dir": card["dir"], "title": card["title"],
                "facts": [["Date", it["date"]], ["Category", it.get("kind") or "News"],
                          ["Country", it.get("country") or "—"]]
                         # the company the story is about; no row for a market story (no named company), and
                         # the client is not appended to every competitor's story
                         + ([["Entities", company]] if company not in ("Market", "") else [])
                         + [["Source", it.get("source") or src]],
                "what": it.get("description") or "", "why": it.get("analysis") or "",
                "lens": [[lens, it.get("analysis") or ""]], "actions": [], "url": it["url"],
                "srcs": [{"label": it.get("source") or src, "url": it["url"]}],
                "provenance": "sourced", "quote": it["quote"],
                "suggest": [f"What does this mean for {OWN}?", f"What should {OWN} do here?",
                            "Show the full-spectrum read"]}
            cnews = OWN if it.get("company_id") == "CUMMINS" else it.get("company_id")
            if cnews in news or cnews == OWN:
                news.setdefault(cnews, []).append(
                    {"title": it["title"], "description": it.get("description") or "",
                     "source": it.get("source") or src, "date": it["date"], "category": it.get("kind"),
                     "url": it["url"], "country": it.get("country"), "level": it["level"],
                     "analysis": it.get("analysis") or "", "card": cid, "pillar": lane})
        out[field] = new + keep
        for i, c in enumerate(out[field], 1):
            c["rank"] = f"{i:02d}"
    live = {c.get("id") for f, _, _ in LANES.values() for c in out.get(f) or []}
    for cid, rows in list(news.items()):       # per-company lists: the window, newest first
        # an undated row follows its card: kept only while that card is
        win = [r for r in rows if (_date(r.get("date")) >= start if _date(r.get("date")) else r.get("card") in live)]
        # a company with fewer than MIN_MOVES moves in the window keeps its newest older moves, marked
        # `older`, so its page is never empty; the dates stay on every row
        old = sorted((r for r in rows if r not in win and _date(r.get("date"))), key=lambda r: _date(r["date"]), reverse=True)
        if cid != OWN:
            win += [dict(r, older=True) for r in old[:max(0, MIN_MOVES - len(win))]]
        rows[:] = sorted(win, key=lambda r: _date(r.get("date")) or dt.date.min, reverse=True)
    return {"added": len(kept), "refused": bad, "already_in_feed": dup, "dropped_cards": dropped,
            "cards": {f: len(out.get(f) or []) for f, _, _ in LANES.values()}}


if __name__ == "__main__":
    today, start = dt.date(2026, 10, 13), dt.date(2026, 9, 1)
    out = {"KSSL_CATS": ["Below 500 kVA", "Mid range (500 to 1,000 kVA)"], "competitors": {"REHLKO": {"name": "Rehlko (Kohler / SDMO)"}},
           "competitorNews": {"REHLKO": [{"title": "old", "date": "2026-07-01"}], OWN: []},
           "competitiveCards": [{"id": "cm1", "meta": "Capacity · Rehlko · 22 Sep 2026", "ago": "22 Sep 2026", "title": "kept"},
                                {"id": "cm2", "meta": "Capacity · Rehlko · 01 Jun 2026", "ago": "01 Jun 2026", "title": "old"}],
           "marketCards": [{"id": "m1", "meta": "Tender · MoH · closes 15 Oct 2026", "ago": "15 Oct 2026"},
                           {"id": "m2", "meta": "Pipeline · Kuwait · Jul 2026", "ago": "01 Jul 2026"}],
           "techCards": []}
    good = {"title": "Rehlko opens plant", "url": "https://rehlko.com/a?x=1", "quote": "q", "date": "2026-10-02",
            "lane": "competitive", "level": "THREAT", "severity": "high", "kind": "Capacity",
            "company_id": "REHLKO", "analysis": "so what", "country": "Global"}
    items = [good, dict(good, url="https://www.rehlko.com/a/", title="Same article"),   # duplicate url
             dict(good, title="No quote", url="https://x/1", quote=""),
             dict(good, title="Too old", url="https://x/2", date="2026-08-30"),
             dict(good, title="Future", url="https://x/3", date="2026-10-14"),
             {"title": "Gulf data centre wave", "url": "https://x/4", "quote": "q", "date": "2026-10-05", "lane": "market",
              "level": "FAV", "kind": "Pipeline", "country": "Saudi Arabia", "segment": "Data centre", "company_id": "MARKET"}]
    out["competitiveCards"][0]["title"] = "Rehlko opens plant in Changzhou"
    items.append(dict(good, title="Rehlko opens its plant in Changzhou", url="https://other.com/x", date="2026-09-23"))   # same story, other page
    out["competitiveCards"][0]["url"] = "https://rehlko.com/already"
    items.append(dict(good, title="Same as a kept card", url="https://www.rehlko.com/already/"))
    items.append(dict(good, title="Rehlko launches a 5 MW set", url="https://x/tech1", date="2026-10-06", lane="tech", level="THREAT"))
    items.append(dict(good, title="Rehlko shows a gas range", url="https://x/tech2", date="2026-10-07", lane="tech", level="WATCH"))
    r = apply(out, items, start, today)
    assert any(c["title"] == "Rehlko launches a 5 MW set" for c in out["competitiveCards"]) and out["techCards"][0]["title"] == "Rehlko shows a gas range"
    assert r["added"] == 4 and r["refused"] == 3 and r["already_in_feed"] == 2, r
    assert {c["id"] for c in out["competitiveCards"]} == {"rfcm1", "rfcm2", "cm1"} and r["dropped_cards"] == 2   # old cm2 and m2 go
    assert [c["id"] for c in out["marketCards"]] == ["rfm1", "m1"]                                      # tender card stays
    assert out["marketCards"][0]["meta"] == "Pipeline · Saudi Arabia · Data centre · 05 Oct 2026"
    assert out["marketCards"][0]["dir"] == "watch" and "Mid range" in out["marketCards"][0]["tags"]   # served as a perceived opportunity
    assert out["competitiveCards"][0]["rank"] == "01" and out["details"]["rfcm1"]["quote"] == "q"
    titles = [n["title"] for n in out["competitorNews"]["REHLKO"]]
    assert "Rehlko opens plant" in titles and "old" not in titles                                     # the old one left the window
    # a company with one move in the window keeps older moves up to MIN_MOVES, marked, newest first
    n2 = {"REHLKO": [{"title": "new", "date": "2026-09-20"}, {"title": "o1", "date": "2026-07-01"}, {"title": "o2", "date": "2026-05-01"}, {"title": "o3", "date": "2026-03-01"}]}
    apply({"competitors": {"REHLKO": {}}, "competitorNews": n2, "competitiveCards": [], "marketCards": [], "techCards": []}, [], start, today)
    assert [r["title"] for r in n2["REHLKO"]] == ["new", "o1", "o2"] and n2["REHLKO"][1].get("older") and not n2["REHLKO"][0].get("older")
    assert _date("2026-04") == dt.date(2026, 4, 1) and _date("2023") == dt.date(2023, 1, 1) and _date("") is None
    print("ok")
