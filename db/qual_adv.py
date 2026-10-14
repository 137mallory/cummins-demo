"""Qualitative advantages: facts from each product's sourced text fields that a spec row
cannot carry (operator, 2026-09-29, "add qualitative"). Kept apart from the measured
advantages (advComp / advBf) and never counted in the verdict or the edge index.

Three conservative reads, each returning None when the text is not clear-cut:
  emissions   EPA Tier 4 > certified EPA Tier 2 > unregulated. "Tier 2 variant available"
              or a mixed card is unclear -> None.
  dc rating   a numeric data-centre rating (DCC / DCR / DCP / Mission Critical / Critical
              Power) published for one side only.
  ambient     the STANDARD rated ambient (°C) before derate; an optional radiator is not it.
"""
import re

_UNCLEAR = re.compile(r"variant|available|optional|optimi[sz]ed|;.*tier", re.I)


def emissions(t):
    t = (t or "").strip()
    if not t or t in ("—", "Not stated"):
        return None
    if re.search(r"non-certified", t, re.I):
        return (0, "not certified")
    if re.match(r"unregulated", t, re.I):
        return (0, "unregulated")      # the base model; a Tier 2 "E" variant is another model
    if re.search(r"tier\s*4", t, re.I) and re.search(r"certified", t, re.I):
        return (4, "EPA Tier 4 certified")
    if re.search(r"tier\s*2", t, re.I) and not _UNCLEAR.search(t):
        return (2, "EPA Tier 2")
    return None


_DC = re.compile(r"(DCC|DCR|DCP|DCCP|data cent(?:er|re) continuous(?: power)?|mission critical|critical power)"
                 r"[^.;]*?(\d[\d,.]*)\s*(kVA|ekW|kW)", re.I)


def dc_rating(t):
    m = _DC.search(t or "")
    if not m or re.search(r"not (published|stated|listed)|no dcc", t or "", re.I):
        return None
    return f"{m.group(1)} {m.group(2)} {m.group(3)}"


def ambient(t):
    t = t or ""
    m = (re.search(r"(\d{2})\s*(?:°|degree)?\s*C\s+standard", t, re.I)
         or re.search(r"standard (?:ambient )?(?:up to )?(\d{2})\s*(?:°|degree)?\s*C", t, re.I)
         or re.search(r"(?:radiator (?:rated for |ambient )|ambient design |maximum operating ambient |"
                      r"^ambient )(\d{2})\s*(?:°|degree)?\s*C", t, re.I)
         or re.search(r"^(\d{2}) degree C cooling package", t, re.I))
    return int(m.group(1)) if m else None


def qualitative(comp_p, bf_p):
    """-> (competitor items, Cummins items)."""
    qc, qb = [], []
    ec, eb = emissions(comp_p.get("emis")), emissions(bf_p.get("emis"))
    if ec and eb and ec[0] != eb[0]:
        win, lose, side = (ec, eb, qc) if ec[0] > eb[0] else (eb, ec, qb)
        side.append(f"Emissions: {win[1]} vs {lose[1]} (published certification)")
    dc, db = dc_rating(comp_p.get("dcr")), dc_rating(bf_p.get("dcr"))
    if dc and not db:
        qc.append(f"Data-centre rating published: {dc} (none published for the other set)")
    if db and not dc:
        qb.append(f"Data-centre rating published: {db} (none published for the other set)")
    ac, ab = ambient(comp_p.get("amb")), ambient(bf_p.get("amb"))
    if ac and ab and abs(ac - ab) >= 5:
        hi, lo, side = (ac, ab, qc) if ac > ab else (ab, ac, qb)
        side.append(f"Rated ambient: {hi} °C vs {lo} °C standard, before derate")
    return qc, qb


def client_support(out):
    """What the client itself offers around any of its sets, from its own sourced profile: service reach,
    rebuild centre, distribution. Stated as support, never as a datasheet advantage over a rival."""
    c = (out.get("competitors") or {}).get((out.get("client") or {}).get("name") or "") or {}
    items = []
    m = re.search(r"(\d+) service branches, (\d+) warehouses", str(c.get("assess") or ""))
    if m:
        items.append(f"{m.group(1)} service branches and {m.group(2)} warehouses across Saudi Arabia, the UAE and Kuwait")
    for r in c.get("facilities") or []:
        if "rebuild" in str(r.get("value", "")).lower():
            line = str(r.get("line") or "").split(". ")[0].strip(" .")
            items.append((str(r["value"]).split(" · ")[0] + ": " + line) if line else str(r["value"]))
            break
    if re.search(r"exclusive Cummins distribution", str(c.get("assess") or ""), re.I):
        items.append("Exclusive Cummins distribution and service company for Saudi Arabia, the UAE and Kuwait (formed 2017 by Cummins Inc. and Olayan)")
    return [f"Support, not a datasheet advantage: {t}" for t in items]


def apply(out):
    P = out.get("PRODUCTS") or {}
    support = client_support(out)
    n = 0
    for mu in (out.get("matchups") or {}).values():
        qc, qb = qualitative(P.get(mu.get("_cp"), {}), P.get(mu.get("_kp"), {}))
        if not qb and not mu.get("advBf"):         # nothing for the client on this matchup: say what it does offer
            qb = list(support)
        mu["advCompQ"], mu["advBfQ"] = qc, qb
        n += bool(qc or qb)
    return n


if __name__ == "__main__":
    # the check: each reader on the export's own phrasings
    assert emissions("EPA Tier 2 (EPA certified stationary emergency)") == (2, "EPA Tier 2")
    assert emissions("EPA Tier 2 genset models available") is None
    assert emissions("Unregulated (UR on 2025 rating card)") == (0, "unregulated")
    assert emissions("EPA Tier 4 certified with SCR aftertreatment") == (4, "EPA Tier 4 certified")
    assert emissions("NEA ORDE and Tier 2 optimized; HVO approved") is None
    assert emissions("Non-certified equivalent to EU Stage II, China II") == (0, "not certified")
    assert emissions("Low BSFC (non-certified emissions)") == (0, "not certified")
    assert dc_rating("DCC 2750 kVA / 2200 kW (2025 rating card)") == "DCC 2750 kVA"
    assert dc_rating("In FG Wilson data centre range list; DCC value not published") is None
    assert ambient("Data sheet lists 40 C standard and 50 C optional ambient design.") == 40
    assert ambient("50 degree C cooling package") == 50
    assert ambient("Radiator ambient 50°C (122°F) per sheet") == 50
    assert ambient("Consult distributor for derating information (datasheet)") is None
    print("ok")
