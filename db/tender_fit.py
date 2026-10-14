"""Tender ranking by value AND Cummins product fit (<pack>/tender_fit.json).

Each tender gets a fit assessment made against the product catalogue: how properly a
Cummins Arabia model covers the need (strong / partial / poor), which catalogue models,
and which competitors fit and with what products. The rank is the expected revenue
weighted by that fit, so a large tender Cummins cannot really serve sinks below a smaller
one it fits well. A poor fit is labelled, not hidden.
"""
# a poor fit earns Cummins nothing: its revenue_mid is the TENDER's size (a 2 GW BESS supply
# is USD 1bn), so any weight above zero would float it to the top
FIT_WEIGHT = {"strong": 1.0, "partial": 0.5, "poor": 0.0}
FIT_GRADE = {"strong": "high", "partial": "mid", "poor": "low"}
FIT_LEAN = {"strong": "go", "partial": "maybe", "poor": "pass"}
PURSUIT_WEIGHT = 0.8      # no bid date yet, or award pending: worth less than a live bid


def score(f, pursuit):
    return (f.get("revenue_mid_usd") or 0) * FIT_WEIGHT.get(f.get("cummins_fit"), 0) * (
        PURSUIT_WEIGHT if pursuit else 1.0)


def apply(out, fits):
    """Attach the assessment to each tender (by exact title) and rank the live ones."""
    ranked = []
    for t in out.get("tenders") or []:
        f = fits.get(t.get("title"))
        if not f:
            continue
        grade = f.get("cummins_fit")
        t["cumminsFit"] = grade
        t["fitNeed"] = f.get("need")
        t["fitLabel"] = f.get("poor_label") if grade == "poor" else None
        t["fitConfidence"] = f.get("confidence")
        t["competitorFit"] = f.get("competitors") or []
        t["revenueMid"] = f.get("revenue_mid_usd")
        t["revenueBasis"] = f.get("revenue_basis")
        t["qtyEst"] = f.get("qty_estimate")   # set count restated from revenue_basis; shown as an estimate
        if grade in FIT_GRADE:
            t["lean"] = FIT_LEAN[grade]
            t["matches"] = [{"n": p, "fit": FIT_GRADE[grade], "pct": "—",
                             "lines": [["up" if grade != "poor" else "down", f.get("cummins_why") or ""]]}
                            for p in f.get("cummins_products") or []] or [
                {"n": (f.get("poor_label") or "No Cummins product fits") if grade == "poor"
                 else "Parts / service job: no set to quote", "fit": FIT_GRADE[grade], "pct": "—",
                 "lines": [["down" if grade == "poor" else "up", f.get("cummins_why") or ""]]}]
        closed = str(t.get("status", "")).lower() in ("awarded", "closed") or (
            isinstance(t.get("dl"), (int, float)) and t["dl"] <= 0 and t.get("status") != "evaluation")
        if not closed:
            t["rankScore"] = round(score(f, t.get("pursuit")))
            ranked.append(t)
    # poor fits last, largest first among themselves; ties keep the served order
    ranked.sort(key=lambda t: (t.get("cumminsFit") == "poor", -t["rankScore"], -(t.get("revenueMid") or 0)))
    for i, t in enumerate(ranked, 1):
        t["rank"] = i
    return len(ranked)


def attach_actions(out, actions):
    """The analyst's dated next steps per tender (<pack>/tender_actions.json, by title)."""
    n = 0
    for t in out.get("tenders") or []:
        if actions.get(t.get("title")):
            t["actions"] = actions[t["title"]]
            n += len(t["actions"])
    return n


if __name__ == "__main__":
    out = {"tenders": [
        {"title": "A", "dl": 10, "status": "open"}, {"title": "B", "dl": 10, "status": "open"},
        {"title": "C", "dl": 10, "status": "open"}, {"title": "D", "dl": 0, "status": "closed"}]}
    fits = {"A": {"cummins_fit": "poor", "revenue_mid_usd": 5e6, "poor_label": "Kohler parts"},
            "B": {"cummins_fit": "strong", "revenue_mid_usd": 1e6, "cummins_products": ["C2000D6E"]},
            "C": {"cummins_fit": "partial", "revenue_mid_usd": 3e6},
            "D": {"cummins_fit": "strong", "revenue_mid_usd": 9e6}}
    assert apply(out, fits) == 3
    by = {t["title"]: t for t in out["tenders"]}
    assert [by[k]["rank"] for k in "CBA"] == [1, 2, 3]           # 1.5M > 1M > poor (0) last
    assert "rank" not in by["D"] and by["A"]["fitLabel"] == "Kohler parts"
    assert by["A"]["lean"] == "pass" and by["A"]["matches"][0]["fit"] == "low"
    assert by["B"]["matches"][0]["n"] == "C2000D6E"
    print("ok")
