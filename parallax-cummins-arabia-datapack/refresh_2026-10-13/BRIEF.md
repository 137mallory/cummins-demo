# Refresh brief, 13 Oct 2026 (read fully before you start)

Client: **Cummins Arabia** (Cummins' distributor for KSA, UAE, Kuwait; diesel and gas gensets, data-centre
power, service). Platform: 137Parallax market-intelligence demo. Today is **13 Oct 2026**. The data was last
refreshed 30 Sep (tenders) and 21 Sep / 7 Oct (news). Your job: find what happened since, with proof.

Competitors (ids): CATERPIL (Caterpillar; Gulf dealers Zahid, Al-Bahar), ROLLSROY (Rolls-Royce Power Systems / mtu),
REHLKO (Rehlko = Kohler / SDMO), MITSUBIS (Mitsubishi Heavy gensets / MHIET), WEICHAIB (Weichai / Baudouin),
PERKINSF (Perkins / FG Wilson), GENERAC (Generac), VOLVOPEN (Volvo Penta). Own company id: CUMMINS.

## Rules (non-negotiable)
1. **Never invent.** Every item needs a real URL you actually opened and a verbatim `quote` from that page (<= 220 chars,
   in the page's language). If you cannot open the page, drop the item. Estimates must be labelled "estimate".
2. **Dates matter.** `date` is the article's own publish date (ISO yyyy-mm-dd). Only items dated **2026-09-01 to 2026-10-13**
   count as news. Read the date from the page, not the search snippet. Nothing after 2026-10-13.
3. **Gulf relevance.** Prefer KSA, UAE, Kuwait (and Gulf/Middle East). Global moves are included only when they change
   the Gulf competitive picture (capacity, pricing, hyperscaler deals, new dealer deals); say how in `analysis`.
4. **Analysis** (2 sentences, grounded in the item, written for Cummins Arabia's management): what it means for Cummins
   Arabia and one action. No hype, no generic advice.
5. Do not bypass CAPTCHAs, logins, paywalls or blocked portals. Etimad public visitor pages: at most 10 requests per minute.
   CAPT (Kuwait) and DEWA results pages block outside access: do not try to get around that.
6. **Save incrementally**: write your JSON file after every ~5 items so a stall loses nothing. Final answer = a 5-line summary
   (count, date range, 3 most important findings, what you could not find). Do not paste the JSON in the answer.
7. Use your own web search / fetch tools. Output goes to the file named in your task, inside
   `/Users/zoro/parallex demo/parallax-cummins-arabia-datapack/refresh_2026-10-13/`.

## NEWS item schema (a JSON list)
```
{"title": "<= 150 chars, factual headline in your words", "description": "2 sentences, what happened, with numbers",
 "source": "domain.com", "date": "2026-10-02", "url": "https://...", "quote": "verbatim line from the page",
 "company_id": "CATERPIL|ROLLSROY|REHLKO|MITSUBIS|WEICHAIB|PERKINSF|GENERAC|VOLVOPEN|CUMMINS|MARKET",
 "lane": "competitive|market|tech",
 "kind": "Contract|Capacity|Expansion|Partnership|Financial|Product|Pipeline|Regulatory|Demand shift|Risk outlook",
 "country": "Saudi Arabia|United Arab Emirates|Kuwait|Global|Middle East",
 "level": "THREAT|WATCH|FAV",          // THREAT = hurts Cummins Arabia, FAV = helps it, WATCH = monitor
 "severity": "high|medium|low",
 "analysis": "2 sentences for Cummins Arabia"}
```
lane: `competitive` = a named competitor's move; `market` = Gulf demand, pipeline, regulation, risk (company_id MARKET, or CUMMINS for
Cummins Arabia's own news); `tech` = products, engines, fuels, controls, batteries.

## TENDER STATUS item schema (a JSON object keyed by the EXACT existing tender title)
```
"<exact title>": {"status": "open|extended|closed|awarded|cancelled|re-tendered|upcoming|unknown",
  "published": "dd Mon yyyy", "closes": "dd Mon yyyy hh:mm", "bid_opening": "...", "award_date": "...",
  "bidders": [{"name": "...", "price": "...", "currency": "..."}], "winner": null, "award_value": null, "currency": null,
  "brand": null, "milestone": "latest event with date, or null",
  "evidence": [{"url": "https://...", "quote": "verbatim"}]}
```
Status meaning: `closed` = deadline passed, no award yet; `awarded` = a winner is named. If a deadline moved, record the NEW
date. If you cannot verify, use `unknown` and leave the rest null: do not guess.
Existing statuses are in `tender_status.json` (keys = exact titles; read it first).
For a tender in `tenders_research.json` that is a **pursuit** (a project, not a buyer-issued tender) report the project's latest
milestone (contractor appointed, contract signed, bids due) in `milestone`.

## NEW TENDER item schema (list)
Same fields as an item of `tenders_research.json` (read 2 items first): title, issuer, country, portal, tender_no, url, doc_urls,
published, closes, status, category, scope, qty, value_published, revenue_estimate {usd_low, usd_high, basis}, tier (high >= USD 1M
addressable / average / low), tier_reason, fit, competitors_likely, requirements, detail, proof_quote, checked ("2026-10-13").
Only tenders **published 2026-09-30 or later** (or ones the research missed) for generators, standby/prime power, genset rental,
genset O&M or spares, data-centre or hospital power packages. Revenue = the genset share only, with the basis written out.

## NEW AWARD item schema (list)
Same fields as an item of `awards.json`: buyer, title, tender_no, country, segment, date (ISO), year, winner, value, currency, bids,
brand, url, quote. Only awards dated **2026-08-10 or later**, generator-related.

## PRODUCT IMAGES (second task, 13 Oct)
The Products page needs one real photo per genset product. Your product list is in `products_<group>.json` here (pid, owner, model,
series, hz, kVA, engine, `src` = the page the specs came from, a good place to start). Save images in
`/Users/zoro/parallex demo/parallax-cummins-arabia-datapack/refresh_2026-10-13/images/<pid>.<ext>` and write
`images_<group>.json`: {pid: {"file": "<pid>.jpg", "image_url": "...", "page_url": "...", "basis": "model|series|family", "note": "..."}}.
Rules: (1) the photo must show that maker's genset, engine or the same product family (basis says which: "model" = that exact
model, "series" = another size of the same series, "family" = the maker's data-centre / large-genset range image); never another
brand, never a car, never a render of unrelated equipment, never a logo-only or people-only image. (2) Prefer the maker's own site,
datasheet or press kit, then an official distributor page. (3) Download with curl (set a browser User-Agent), then LOOK at every
image with the Read tool: keep it only if it plainly shows the right equipment. (4) At least 500 px wide; shrink to 1000 px wide
max with `sips -Z 1000 <file>`; keep each file under 400 KB (use `sips -s format jpeg -s formatOptions 70` if needed).
(5) Do not bypass 403s, CAPTCHAs or hotlink walls; skip. (6) One photo may serve several products of the same series: copy the
file under each pid. A product with no honest photo gets no entry: say so, do not pad. Save the JSON after every ~5 products.
Final answer: counts per basis, the pids with no image, 3 lines.

## LEADER BIOS (third task, 14 Oct)
The Competitor Profile's leader page shows only **Professional Experience** and **Education**. Your input is `leaders_<group>.json`
(company, and each leader's name, title, source). For every leader write one record to `bios_<group>.json` (a JSON list):
```
{"company_id": "...", "name": "<exact name as in the input, or the new leader's name>", "title": "<current title>",
 "experience": [{"company": "...", "role": "...", "from": "2018", "to": "Present"}],   // newest first, years only, "Present" for current
 "education": [{"institution": "...", "degree": "BSc Mechanical Engineering", "from": "", "to": "1992"}],   // degree + field as published; to = graduation year if stated
 "bio_source": "https://... (the page you read)", "quote": "verbatim line from that page that supports the career or degree",
 "new": false}
```
Rules: official sources first (company leadership page, SEC proxy / 10-K / annual report, company press release on the appointment,
then a reputable business bio such as Reuters, Bloomberg, Forbes, Wikipedia as a last resort and say so in `note`). Only facts the page
states: **never infer a career from a title and never guess a degree**; an empty list means "not published". Years only. At least the
current role must be in `experience`. Do not bypass 403s or CAPTCHAs. Some leaders in the input are old or have changed: if a leader has
left, say so in `note` and keep the record.
**Thin lists:** if a company has fewer than 5 leaders, also add its senior executives that matter to a Gulf genset buyer (group CEO,
head of the power-generation / power-systems business, CFO, Middle East or EMEA head) with `"new": true` and the same fields, up to 5 per company.
Save every ~5 leaders. Final answer: counts (leaders, with education, with experience, new added) and the leaders with nothing found.

## LEADER BIOS, SECOND PASS (14 Oct)
Input `leaders_second_pass.json`: leaders for whom official pages gave no education and no career beyond the current role. Find them in
PUBLIC business-press and company sources: Reuters, Bloomberg or Forbes executive pages, Wikipedia, MarketScreener / Zonebourse,
company press releases on the appointment (Business Wire, PR Newswire, company newsroom), annual-report biographies, conference and
trade-show speaker bios, university or association pages.
**Do not use LinkedIn, and do not use any page behind a login, and no people-data aggregators that copy LinkedIn (RocketReach, ZoomInfo,
ContactOut, Apollo, SignalHire, Crunchbase people pages).** Same record schema, rules and honesty as the first pass: only what a page states,
verbatim `quote`, years only, empty list = not published, `note` names the source type (secondary press / Wikipedia / etc.).
Output `bios_second_pass.json`. Final answer: counts found, and who still has nothing.

## PATENTS (14 Oct)
The Competitor > Patent page lists each competitor's patent filings grouped by technology area. Input: `patent_areas.json` (the area names to
use, and the competitor ids). Find REAL patent documents assigned to your companies, **published 2022-2026 preferred** (older only if central),
about gensets and data-centre / backup power: engines and fuels (gas, dual-fuel, hydrogen, HVO / renewable diesel), hybrid genset + battery,
controls / paralleling / switchgear, power density / compact design, emissions and aftertreatment, cooling for high ambient, and so on.
Sources: Google Patents (patents.google.com/patent/<number>/en: these pages are server-rendered, fetch them), Espacenet, USPTO / WIPO
PatentScope public pages, Lens.org public pages. Use web search to find candidate numbers, then **open each patent page and copy the facts
from it**. Never write a patent number you did not open. Aim for 5 to 10 per company across at least 4 areas; fewer is fine if that is all
that exists, and say so.
Record schema (a JSON list, one object per patent):
```
{"comp_id": "CATERPIL|ROLLSROY|REHLKO|MITSUBIS|WEICHAIB|PERKINSF|GENERAC|VOLVOPEN",
 "area": "<one of the exact area names in patent_areas.json>",
 "no": "US 2025/0123456 A1",          // as printed (kind code included)
 "title": "...", "title_en": "<English title if the title is not English, else empty>",
 "assignee": "<applicant/assignee as printed>",
 "status": "granted|pending|filed|unknown",   // granted only if the page shows a grant (B1/B2 or a grant date); A1/A2 publications = pending
 "filed": "2024-03-12", "published": "2025-09-18", "granted": "",   // ISO dates from the page; empty if not shown
 "grant_no": "", "pub_kind": "A1|B2|...",
 "country": "US|EP|WO|CN|DE|JP|...",
 "ipc": ["F02B 63/04", "H02J 3/38"],
 "abstract": "verbatim abstract, max 450 chars (cut at a sentence)",
 "url": "https://patents.google.com/patent/US20250123456A1/en",
 "quote": "a verbatim line from the page (title or abstract start)"}
```
Rules: dates and numbers exactly as the page shows; `status` never guessed; do not bypass 403 or CAPTCHAs; skip anything you cannot open. One patent
family counted once (prefer the English-language US or EP member). Save every ~4 patents. Final answer: counts per company and per area, and the gaps.
