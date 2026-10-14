"""Verified tender status (<pack>/tender_status.json, by exact title) and award history.

A status check records, per tender, what its portal or the press says today: open, closed
(evaluation), awarded, cancelled, re-tendered, extended or upcoming, with the latest dates,
the public bid prices and the winner. apply() writes that onto the served tender so the
Tender Pipeline's Open / Awarded / Closed views and the countdowns read the checked state;
every fact keeps its evidence url. A status nobody could verify changes nothing.
"""
import datetime as dt
import re

STATUS = {"open": "open", "extended": "open", "closed": "evaluation", "awarded": "awarded",
          "cancelled": "closed", "re-tendered": "closed", "upcoming": "upcoming"}


def _date(s):
    """ISO ("2026-10-15", "2026-10-15 09:59") or written ("15 Oct 2026", "15 October 2026")."""
    s = str(s or "").strip()
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return dt.date(*map(int, m.groups()))
    m = re.match(r"(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{4})", s)
    if m:
        for f in ("%d %b %Y", "%d %B %Y"):
            try:
                return dt.datetime.strptime(" ".join(m.groups()), f).date()
            except ValueError:
                pass
    return None


def _fmt(d):
    return d.strftime("%d %b %Y") if d else None


def _set(req, label, value):
    if value in (None, "", []):
        return
    for r in req:
        if r[0] == label:
            r[1] = value
            return
    req.append([label, value])


def apply(out, checks, today=None):
    today = today or dt.date(2026, 10, 13)
    n = 0
    for t in out.get("tenders") or []:
        c = checks.get(t.get("title"))
        if not c or c.get("status") in (None, "", "unknown"):
            continue
        st = STATUS.get(str(c["status"]).lower())
        if not st:
            continue
        n += 1
        t["status"] = st
        t["statusChecked"] = c["status"]
        req = t.setdefault("req", [])
        closes = _date(c.get("closes"))
        if closes:
            _set(req, "Closes", _fmt(closes))
            t["closingDate"] = closes.isoformat()
            # the UI counts days from `deadline` read as a DATE (a stored countdown string goes stale
            # the day after the build); an awarded tender keeps its own "Awarded ..." text
            if st != "awarded":
                t["deadline"] = closes.isoformat()
            t["dl"] = (closes - today).days if st in ("open", "upcoming") else min(0, (closes - today).days)
        if st in ("evaluation", "awarded", "closed") and isinstance(t.get("dl"), (int, float)) and t["dl"] > 0:
            t["dl"] = 0
        _set(req, "Status", str(c["status"]).capitalize())
        _set(req, "Published", _fmt(_date(c.get("published"))))
        _set(req, "Bid opening", _fmt(_date(c.get("bid_opening"))))
        _set(req, "Award date", _fmt(_date(c.get("award_date"))))
        # on a pursuit the "winner" is the EPC / main contractor the genset package sits under,
        # not an award of this tender
        if c.get("winner") and st != "awarded":
            _set(req, "Main contractor", c["winner"])
        elif c.get("winner"):
            _set(req, "Winner", c["winner"])
            val = c.get("award_value")
            if val not in (None, ""):
                _set(req, "Award value", f"{c.get('currency') or ''} {val}".strip())
            t["award"] = {k: c.get(k) for k in ("winner", "award_value", "currency", "award_date", "brand")}
        if c.get("bidders"):
            t["bidders"] = c["bidders"]
            _set(req, "Bids received", str(len(c["bidders"])))
        if c.get("milestone"):
            _set(req, "Latest milestone", c["milestone"])
        ev = [e for e in c.get("evidence") or [] if isinstance(e, dict) and e.get("url")]
        have = {s.get("url") for s in t.get("srcs") or []}
        t.setdefault("srcs", []).extend({"label": "Status check", "url": e["url"]} for e in ev if e["url"] not in have)
        t["statusEvidence"] = ev
        if st == "awarded":
            t["urlKind"] = "award"
    return n


if __name__ == "__main__":
    out = {"tenders": [{"title": "A", "dl": 5, "status": "open", "req": [["Closes", "05 Oct 2026"]]},
                       {"title": "B", "dl": 20, "status": "open"}, {"title": "C", "dl": 9, "status": "open"},
                       {"title": "D", "dl": 9999, "status": "upcoming", "pursuit": True}]}
    checks = {"A": {"status": "awarded", "winner": "Al-Rashid group", "award_value": "21,150,000", "currency": "SAR",
                    "award_date": "2026-09-20", "evidence": [{"url": "https://e/1", "quote": "q"}]},
              "B": {"status": "extended", "closes": "2026-11-15"},
              "C": {"status": "unknown"},
              "D": {"status": "upcoming", "winner": "Al Moammar Information Systems"}}
    assert apply(out, checks) == 3
    a, b, c, d = out["tenders"]
    assert ["Main contractor", "Al Moammar Information Systems"] in d["req"] and "award" not in d
    assert a["status"] == "awarded" and a["dl"] == 0 and ["Winner", "Al-Rashid group"] in a["req"]
    assert ["Award value", "SAR 21,150,000"] in a["req"] and a["urlKind"] == "award"
    assert b["status"] == "open" and b["dl"] == 33 and ["Closes", "15 Nov 2026"] in b["req"]
    assert b["deadline"] == "2026-11-15" and "deadline" not in c    # a date the UI counts from, never a stored countdown
    assert c["status"] == "open" and c["dl"] == 9      # unknown changes nothing
    assert _date("2026-10-15 09:59") == dt.date(2026, 10, 15) and _date("15 October 2026") == dt.date(2026, 10, 15)
    print("ok")
