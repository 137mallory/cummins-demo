"""Researched tenders (<pack>/tenders_research.json) served beside the export's own.

Each researched item carries its revenue tier for the client (high >= USD 1M addressable,
average USD 100k-1M, low < USD 100k), the estimate's basis, a verbatim proof quote and
the sources that were opened. They are shaped into the export's tender record so every
tender view reads them unchanged; the tier and estimate ride along as extra fields.
"""
import datetime as dt
import re

FIT = {"go": "high", "maybe": "mid", "pass": "low"}


def _date(s):
    try:
        return dt.date.fromisoformat(str(s)[:10])
    except (TypeError, ValueError):
        return None


def _fmt(d):
    return d.strftime("%d %b %Y") if d else None


def _usd(n):
    return f"USD {n / 1e6:.1f}M" if n >= 1e6 else f"USD {round(n / 1e3):,}k"


def category(r):
    """The export's own category words, so the market chart keeps one hue per category
    (lib/marketOverview self-check): research's broad labels map onto them, and only
    Data centre and Oil & gas are new."""
    c = r.get("category") or "Other"
    hay = f"{r.get('title') or ''} {r.get('scope') or ''}".lower()
    service = any(w in hay for w in ("maintenance", "o&m", "service", "overhaul", "repair", "spare"))
    if c == "Utility":
        return "Utility / Service" if service or not any(
            w in hay for w in ("plant", "ipp", "station", "grid", "generation", "power")) else "Utility / Power plant"
    if c in ("Transport", "Construction", "Telecom", "Other"):
        return "Service / Facilities"
    return c


def _published(r):
    """A published tender value, or None when the field is a note ("Not published ...")."""
    v = (r.get("value_published") or "").strip()
    if not v or re.match(r"(?i)not (published|disclosed|stated)|n/?d\b|unknown", v):
        return None
    # a press or industry estimate of the whole project is not a value the buyer published
    return None if re.search(r"(?i)estimat|\babout\b|approx|~|reported|industry|MEED|project value", v) else v


def to_tender(r, tid, today):
    closes, published = _date(r.get("closes")), _date(r.get("published"))
    dl = (closes - today).days if closes else 9999
    status = {"prequal": "upcoming"}.get(r.get("status"), r.get("status") or "open")
    if closes and dl <= 3 and status == "open":
        status = "closing"
    est = r.get("revenue_estimate") or {}
    est_txt = (f"{_usd(est['usd_low'])} to {_usd(est['usd_high'])} (estimate: {est.get('basis', '')})"
               if est.get("usd_low") is not None and est.get("usd_high") is not None else None)
    fit = r.get("fit") or {}
    lean = fit.get("lean") if fit.get("lean") in FIT else "maybe"
    req = [["Category", category(r)], ["Rating band", r.get("qty")], ["Buyer", r.get("issuer")],
           ["Portal", r.get("portal")], ["Tender no.", r.get("tender_no")],
           # a pursuit's published figure is the whole EPC / project, not this tender's value
           ["Project / contract value" if r.get("pursuit") else "Value", _published(r) or "not disclosed"],
           ["Value note", r.get("value_published") if r.get("value_published") and not _published(r) else None],
           ["Opportunity", "Pursuit: no bid date yet, or award pending" if r.get("pursuit") else None],
           ["Revenue tier", (r.get("tier") or "").capitalize() or None],
           ["Revenue estimate", est_txt], ["Status", status.capitalize()],
           ["Published", _fmt(published)], ["Closes", _fmt(closes)]]
    req += [list(x) for x in r.get("requirements") or [] if isinstance(x, (list, tuple)) and len(x) == 2]
    srcs = [{"label": r.get("portal") or "Notice", "url": r.get("url")}] if r.get("url") else []
    srcs += [{"label": "Tender document", "url": u} for u in r.get("doc_urls") or [] if u]
    return {
        "id": tid, "title": r.get("title"), "issuer": r.get("issuer"), "country": r.get("country"),
        "cat": category(r), "value": (None if r.get("pursuit") else _published(r)) or "n/d", "qty": r.get("qty"),
        "status": status, "deadline": closes.isoformat() if closes else "date not published", "dl": dl,
        "reqNote": r.get("tier_reason"), "req": [x for x in req if x[1]],
        "matches": [{"n": p, "fit": FIT[lean], "pct": "—", "lines": [["up", fit.get("why") or ""]]}
                    for p in (fit.get("cummins_products") or [])[:3]],
        "lean": lean, "leanTxt": r.get("detail") or fit.get("why"), "scope": r.get("scope"),
        "competitors": r.get("competitors_likely") or [], "srcs": srcs, "url": r.get("url"),
        "urlKind": "notice", "tier": r.get("tier"), "revenue_estimate": est,
        "proof": r.get("proof_quote"), "researched": True, "pursuit": bool(r.get("pursuit")),
    }


def merge(out, items, today=None):
    today = today or dt.date(2026, 10, 13)
    tenders = out.setdefault("tenders", [])
    have = {(t.get("title") or "").strip().lower() for t in tenders}
    nxt = max([t.get("id", 0) for t in tenders if isinstance(t.get("id"), int)] + [0]) + 1
    added = 0
    for r in items:
        if (r.get("title") or "").strip().lower() in have:
            continue
        tenders.append(to_tender(r, nxt, today))
        have.add((r.get("title") or "").strip().lower())
        nxt += 1
        added += 1
    # two near-duplicate export categories (one tender each) fold into their twins, so the
    # researched Data centre and Oil & gas lines get a hue of their own (ISSUES.md D44)
    ALIAS = {"Utility / Desalination": "Water / Desalination", "Water / Service": "Utility / Service"}
    for t in tenders:
        if t.get("cat") in ALIAS:
            t["cat"] = ALIAS[t["cat"]]
            t["req"] = [[k, ALIAS.get(v, v) if k == "Category" else v] for k, v in t.get("req") or []]
    cats = [ALIAS.get(c, c) for c in out.get("tpAllCats") or []]
    for t in tenders:
        if t.get("cat") and t["cat"] not in cats:
            cats.append(t["cat"])
    out["tpAllCats"] = list(dict.fromkeys(cats))
    return added


if __name__ == "__main__":
    t = to_tender({"title": "X", "closes": "2026-10-09", "published": "2026-09-20", "tier": "high",
                   "revenue_estimate": {"usd_low": 1.2e6, "usd_high": 2e6, "basis": "4 x 2 MW"},
                   "fit": {"lean": "go", "cummins_products": ["C2000D5"], "why": "w"}}, 101,
                  dt.date(2026, 9, 29))
    assert t["dl"] == 10 and ["Closes", "09 Oct 2026"] in t["req"]
    assert t["deadline"] == "2026-10-09"       # a date the UI counts days from, not a stored countdown
    assert ["Revenue estimate", "USD 1.2M to USD 2.0M (estimate: 4 x 2 MW)"] in t["req"]
    assert t["matches"][0]["fit"] == "high"
    assert category({"category": "Utility", "title": "Annual maintenance of generators"}) == "Utility / Service"
    assert category({"category": "Utility", "title": "Diesel power plant for remote grid"}) == "Utility / Power plant"
    assert category({"category": "Transport"}) == "Service / Facilities"
    assert _published({"value_published": "Not published by CAPT. KWD 3500000"}) is None
    assert _published({"value_published": "KWD 700,000"}) == "KWD 700,000"
    assert _published({"value_published": "Estimated cost USD 180m (MEED)"}) is None
    assert _published({"value_published": "About AED 34bn (USD 9.2bn) total project"}) is None
    print("ok")
