"""news_all.json (+ Weichai items) + the verification verdicts -> ../news_refresh.json.
Drops what could not be verified, rewrites analyses the pages do not support."""
import json
V = {v["_i"]: v for v in json.load(open("news_verdicts.json"))}
items = json.load(open("news_all.json"))
EDIT = {   # analysis text the page does not support, replaced with what it does support
 2: {"analysis": "Cat's growth is increasingly large data-centre generators and turbines, and its management says turbine orders already extend to 2029-2030, so long Cat lead times on large sets are likely. Action: give data-centre buyers considering Cat Cummins Arabia's confirmed lead times."},
 10: {"analysis": "Cummins Inc. reports record sales and robust data-centre power demand, so large-genset factory slots stay tight. Cummins Arabia should ask Cummins Power Systems for confirmed 2027 allocation on its hyperscale pipeline."},
 15: {"title": "Cummins plans 55 GW capacity by 2030 for about USD 450m of investment, per Investor Day figures", "analysis": "More Cummins large-genset capacity should ease supply from 2027-28. Plan Cummins Arabia's 2027 quotes on current lead times and re-check allocation after the Q3 results (estimated 3 Nov 2026, not confirmed)."},
 18: {"title": "Amazon's USD 8bn is a warrant-vesting threshold, not a guaranteed Generac order", "quote": "not described by Generac as a guaranteed $8 billion order",
      "analysis": "The $8bn is a warrant-vesting threshold and the $2.4bn is expected initial deliveries, not a committed order, so headlines overstate the near-term threat to other suppliers including Cummins. Brief Cummins Arabia sales not to quote $8bn to customers as committed volume."},
 36: {"analysis": "Kuwait is spending to reduce outage risk before the summer 2027 peak, which keeps standby and rental gensets part of customers' outage cover. Cummins Arabia should check rental and standby availability in Kuwait before April 2027."},
 37: {"analysis": "A 6GW campus is the largest data-centre power opportunity in the Gulf. The award is for infrastructure only (substations, bulk supply, roads, water, cabling), so the genset package is separate. Cummins Arabia should open a technical dialogue with Humain and Al-Yamama now on standby and bridging power for the first halls."},
 44: {"analysis": "Saudi data-centre capacity grew from 68MW in 2021 to over 467MW by Q1 2025, and a December AWS launch means commissioning, load testing and service work soon after. Cummins Arabia should target the AWS region's operators for service contracts and the Humain AI Zone for new standby capacity."},
}
TITLE_FIX = {"AWS says it cannot restore one of its three UAE availability zones":
             "AWS cannot restore data in its damaged UAE and Bahrain zones; Bahrain worst hit"}
DROP = {3, 12, 57, 58, 60}   # 3: behind a human-verification wall; 12: publish date unproven; 57, 58, 60: same story as 16, 14, 5
out = []
for it in items:
    i = it["_i"]
    if i in DROP:
        continue
    if it["title"].startswith(("Yahoo Finance: Generac up 16%", "Piper Sandler initiates Generac")):
        continue          # six items on one Generac-Amazon story is too many: stock-move and coverage-initiation notes dropped
    for pre, fixed in TITLE_FIX.items():     # a headline the linked article contradicts or only half-states
        if it["title"].startswith(pre):
            it["title"] = fixed
    v = V.get(i, {})
    if v.get("fixed_description"):
        it["description"] = v["fixed_description"]
    if v.get("fixed_date"):
        it["date"] = v["fixed_date"]
    it.update(EDIT.get(i, {}))
    it.pop("_file", None); it.pop("_i", None)
    out.append(it)
for k in (0, 2):                         # Weichai: times-online (company claim), baudouin.com visit
    w = json.load(open("news_mit_wei_vol.json"))[k]
    out.append(w)
w = json.load(open("news_mit_wei_vol.json"))[1]   # Sina brokerage note, quote and date checked against the page
out.append(w)
json.dump({"window_start": "2026-09-01", "today": "2026-10-13", "items": out},
          open("../news_refresh.json", "w"), indent=1, ensure_ascii=False)
print(len(out), "items written")
