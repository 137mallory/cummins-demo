"""Verified datasheet values the export left blank, applied to PRODUCTS and the matchups.

The export's matchups carry spec rows, a per-row `hi` (True: Cummins leads the row), the
advantage lists and a verdict, all computed from PRODUCTS by rules this module reproduces
(rebuild() re-derives the 55 complete matchups byte for byte; see __main__):

  * a directional row is decided when the gap is at least 2 % of the smaller value;
    fuel, size and weight win lower, power density and power to weight win higher;
  * an advantage reads "Label: <Cummins value> <unit> vs <rival value> <unit>";
  * the verdict counts decided rows each way.

A fill file (<pack>/spec_fills.json) maps a PRODUCTS pid to fields with their source:
    {"WEICHAIB-P4": {"f100": {"value": 512, "url": "...", "quote": "..."}, ...}}
Only a field the export left empty is filled; a served value is never overwritten.
"""
import json
import math
import re

# matchup row label -> PRODUCTS key; the directional ones carry lower-is-better
ROWS = {
    "Power Rating (kVA)": "standby_kva", "Power Rating (kW)": "standby_kw",
    "Prime Rating (kVA)": "prime_kva", "Prime Rating (kW)": "prime_kw",
    "Continuous Rating (kW)": "continuous_kw", "Cylinders": "cyl",
    "Displacement (L)": "disp", "Rated Speed (rpm)": "rpm",
    "Fuel Consumption @100% Load": "f100", "Fuel Consumption @75% Load": "f75",
    "Fuel Consumption @50% Load": "f50", "Specific Fuel @100% (L/hr per 100 kW)": "sfc",
    "Length (mm)": "L", "Width (mm)": "W", "Height (mm)": "H", "Ground Area (sq.m)": "area",
    "Power Density (kW/sq.m)": "kwm2", "Weight (kg)": "wt", "Power to Weight (kW/kg)": "kwkg",
}
LOWER_WINS = {"Fuel Consumption @100% Load", "Fuel Consumption @75% Load",
              "Fuel Consumption @50% Load", "Specific Fuel @100% (L/hr per 100 kW)",
              "Length (mm)", "Width (mm)", "Height (mm)", "Ground Area (sq.m)", "Weight (kg)"}
HIGHER_WINS = {"Power Density (kW/sq.m)", "Power to Weight (kW/kg)"}
FILLABLE = {"standby_kw", "prime_kva", "prime_kw", "continuous_kw", "cyl", "disp", "rpm",
            "f100", "f75", "f50", "L", "W", "H", "wt"}


def half_up(x, n):
    return math.floor(x * 10 ** n + 0.5) / 10 ** n


def fmt(x):
    """As the export prints a row value: thousands commas, at most 2 decimals."""
    if x is None:
        return "—"
    r = half_up(float(x), 2)
    s = f"{r:,.2f}".rstrip("0").rstrip(".")
    return s


def derive(p):
    """The export's derived columns, from its own inputs (only where they are empty)."""
    kw = p.get("standby_kw")
    if p.get("area") is None and p.get("L") and p.get("W"):
        p["area"] = half_up(p["L"] * p["W"] / 1e6, 2)
    if p.get("kwm2") is None and kw and p.get("area"):
        p["kwm2"] = half_up(kw / p["area"], 1)
    if p.get("kwkg") is None and kw and p.get("wt"):
        p["kwkg"] = half_up(kw / p["wt"], 4)
    if p.get("sfc") is None and kw and p.get("f100"):
        p["sfc"] = half_up(p["f100"] / kw * 100, 2)


def _names(verdict):
    v = re.sub(r"^<b>[^<]*</b>\s*", "", verdict or "")
    for rx, order in (
        (r"^(.+) leads on \d+ of \d+ directional specs? against (.+)\.$", "win"),
        (r"^No directional spec is published on both datasheets for (.+) and (.+); ratings", "cb"),
        (r"^The \d+ directional specs? both datasheets publish for (.+) and (.+) are level", "cb"),
        (r"^\d+ directional specs? each way between (.+) and (.+)\.$", "cb"),
    ):
        mm = re.match(rx, v)
        if mm:
            return mm.group(1), mm.group(2), order
    return None


def rebuild(mu, comp_p, bf_p):
    """Re-derive one matchup's rows, hi flags, advantages and verdict from PRODUCTS."""
    names = _names(mu.get("verdict"))
    adv_c, adv_b = [], []
    for s in mu["specs"]:
        key = ROWS.get(s["l"])
        if key:
            for side, p in (("c", comp_p), ("k", bf_p)):
                val = p.get(key)
                if val is not None and s[side + "n"] is None:
                    s[side + "n"] = val
                    s[side + "v"] = fmt(val)
        if s["l"] not in LOWER_WINS | HIGHER_WINS:
            continue
        c, k = s["cn"], s["kn"]
        s["hi"] = None
        if c is None or k is None or min(abs(c), abs(k)) == 0:
            continue
        if abs(c - k) / min(abs(c), abs(k)) < 0.02:
            continue
        bf_wins = (k < c) if s["l"] in LOWER_WINS else (k > c)
        s["hi"] = bf_wins
        (adv_b if bf_wins else adv_c).append(f"{s['l']}: {s['kv']} {s['u']} vs {s['cv']} {s['u']}")
    mu["advComp"], mu["advBf"] = adv_c, adv_b
    if names:
        a, b, order = names
        # "leads on" names the winner first; the other two templates name the rival first
        comp_n, bf_n = (b, a) if order == "win" and a.startswith("Cummins") else (a, b)
        nc, nb = len(adv_c), len(adv_b)
        dec = nc + nb
        both = [x for x in mu["specs"] if x["l"] in LOWER_WINS | HIGHER_WINS
                and x["cn"] is not None and x["kn"] is not None]
        if dec == 0 and both:
            # published on both sides but every one within the 2 % decision gap
            mu["verdict"] = (f"<b>Not decided.</b> The {len(both)} directional spec{'s' if len(both) != 1 else ''} "
                             f"both datasheets publish for {comp_n} and {bf_n} are level (within 2 %).")
        elif dec == 0:
            mu["verdict"] = (f"<b>Not decided.</b> No directional spec is published on both datasheets "
                             f"for {comp_n} and {bf_n}; ratings and engine identity only.")
        elif nc == nb:
            mu["verdict"] = (f"<b>Even.</b> {nc} directional spec{'s' if nc != 1 else ''} each way "
                             f"between {comp_n} and {bf_n}.")
        elif nc > nb:
            mu["verdict"] = (f"<b>Rival ahead.</b> {comp_n} leads on {nc} of {dec} directional "
                             f"spec{'s' if dec != 1 else ''} against {bf_n}.")
        else:
            mu["verdict"] = (f"<b>Cummins ahead.</b> {bf_n} leads on {nb} of {dec} directional "
                             f"spec{'s' if dec != 1 else ''} against {comp_n}.")
    return mu


UNIT = {"Fuel Consumption @100% Load": "L/hr", "Fuel Consumption @75% Load": "L/hr",
        "Fuel Consumption @50% Load": "L/hr", "Specific Fuel @100% (L/hr per 100 kW)": "L/hr/100kW",
        "Length (mm)": "mm", "Width (mm)": "mm", "Height (mm)": "mm", "Ground Area (sq.m)": "sq.m",
        "Power Density (kW/sq.m)": "kW/sq.m", "Weight (kg)": "kg", "Power to Weight (kW/kg)": "kW/kg"}


def add_rows(mu, comp_p, bf_p):
    """A directional row the export never wrote (neither sheet had it then) is added once a
    fill gives BOTH products the value, in the export's row order."""
    have = {s["l"] for s in mu["specs"]}
    order = list(ROWS)
    for label in order:
        key = ROWS[label]
        if label in have or label not in UNIT or comp_p.get(key) is None or bf_p.get(key) is None:
            continue
        row = {"l": label, "cv": fmt(comp_p[key]), "cn": comp_p[key], "kv": fmt(bf_p[key]),
               "kn": bf_p[key], "u": UNIT[label], "hi": None, "p": "x"}
        at = next((i for i, s in enumerate(mu["specs"])
                   if s["l"] in order and order.index(s["l"]) > order.index(label)), len(mu["specs"]))
        mu["specs"].insert(at, row)


def apply_fills(out, fills):
    """Fill empty PRODUCTS fields from `fills`, then rebuild the matchups that use them.
    Returns the pids actually changed."""
    P = out.get("PRODUCTS") or {}
    changed = set()
    for pid, fields in fills.items():
        p = P.get(pid)
        if not p:
            continue
        for key, rec in fields.items():
            if key in FILLABLE and p.get(key) is None and rec.get("value") is not None:
                p[key] = rec["value"]
                p.setdefault("fill_basis", {})[key] = rec.get("basis") or ""
                changed.add(pid)
        # display-only rows with no PRODUCTS field (gas consumption, engine-only sizes):
        # {"_rows": {"value": null, "rows": {"Label": "text"}, "url": ...}}
        rows = (fields.get("_rows") or {}).get("rows")
        if rows:
            p.setdefault("fill_rows", {}).update(rows)
            changed.add(pid)
        if pid in changed:
            derive(p)
            srcs = p.setdefault("fill_sources", [])
            for rec in fields.values():
                if rec.get("url") and rec["url"] not in srcs:
                    srcs.append(rec["url"])
    for mu in (out.get("matchups") or {}).values():
        if mu.get("_cp") in changed or mu.get("_kp") in changed:
            add_rows(mu, P.get(mu["_cp"], {}), P.get(mu["_kp"], {}))
            rebuild(mu, P.get(mu["_cp"], {}), P.get(mu["_kp"], {}))
            have = {(x.get("u") if isinstance(x, dict) else x) for x in mu.get("srcs") or []}
            for pid in (mu["_cp"], mu["_kp"]):
                for u in P.get(pid, {}).get("fill_sources", []):
                    if u not in have:
                        mu.setdefault("srcs", []).append({"l": "Datasheet (verified fill)", "u": u})
                        have.add(u)
    return changed


if __name__ == "__main__":
    # the check: rebuild() reproduces every served matchup exactly (rows, hi, advantages,
    # verdict) from PRODUCTS, so a filled matchup reads as the export would have written it
    import copy
    import sys
    d = json.load(open(sys.argv[1]))
    bad = 0
    for k, mu in d["matchups"].items():
        before = copy.deepcopy(mu)
        rebuild(mu, d["PRODUCTS"][mu["_cp"]], d["PRODUCTS"][mu["_kp"]])
        for f in ("advComp", "advBf", "verdict"):
            if before[f] != mu[f]:
                bad += 1
                print("DIFF", k, f, "\n  was", before[f], "\n  now", mu[f])
        for a, b in zip(before["specs"], mu["specs"]):
            if (a["hi"], a["cv"], a["kv"]) != (b["hi"], b["cv"], b["kv"]) and a["l"] in LOWER_WINS | HIGHER_WINS:
                bad += 1
                print("ROW", k, a["l"], (a["hi"], a["cv"], a["kv"]), "->", (b["hi"], b["cv"], b["kv"]))
    print("ok" if not bad else f"{bad} differences")
