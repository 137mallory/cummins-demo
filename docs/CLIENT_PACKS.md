# Client packs — one dashboard, any client

The dashboard names no client in code. Everything that makes it *someone's* dashboard — the
client's name, its rivals, product families, markets, currency, and the rules for what counts
as a threat — arrives in the served dataset. Switching the database switches the client.

## How data reaches the screen

```
<pack_dir>/parallax-*-data.json      the researched, source-cited pack (one per client)
        │  python db/build_dataset.py <pack_dir>
        ▼
<pack_dir>/dataset.json              the UI contract: ~40 globals (docs/UI_CONTRACT.md)
        │  python db/seed_serving.py --recycle <pack_dir>/dataset.json
        ▼
Postgres serving.*                   one client only (--recycle empties every schema first)
        │  GET /api/dataset          (backend/app.py, KSSL_SERVE_ORIGIN=all)
        ▼
wireDataset() → views               frontend/src/lib/dataset.js sets lib/client first
```

`frontend/src/lib/client.js` is the one place the UI asks "who is the client": `clientShort()`,
`clientName()`, `stripClient()`, money parsing (any currency) and money display (the client's
`currency` / `magnitude` / `locale`). `wireDataset` calls `setClient()` before any rule runs.

## From a standalone HTML export (current Cummins Arabia source)

The Cummins Arabia data now comes from the manager's HTML export, with the research
datapack filling in what the export leaves out:

```
<pack_dir>/137Parallax-*.html        the export: the reference app with its data embedded
        │  python db/dataset_from_html.py <export.html> <pack_dir>/dataset.html.json \
        │         --base <pack_dir>/dataset.json --pack <pack_dir> --images --drop-blank
        ▼
<pack_dir>/dataset.html.json         every export global verbatim, plus the fields the views
        │                            read (platform_fields) and the pack-only notes (merge_pack)
        │  python db/seed_serving.py --recycle <pack_dir>/dataset.html.json
        ▼
Postgres serving.*                   fields with no column of their own go to `extra` (jsonb)
                                     and are merged back into the row by the API
```

`--images` reads each cited article's own og:image once (cached in `<pack_dir>/og_images.json`,
so a rebuild fetches only new URLs) and sets it on the news rows, signal cards and details.
Site-wide share pictures are skipped: logos by name, and any picture two or more articles
declare. Needs `db/migrations/2026-09-28_extra_fields.sql` on an existing database. Open data problems
are tracked in `<pack_dir>/ISSUES.md`.

`<pack_dir>/spec_fills.json`, when present, fills PRODUCTS fields the export left blank, one
verified datasheet value each (`value`, `basis`, `url`, `quote`), keyed by PRODUCTS pid. A served
value is never overwritten. The matchups that use a filled product are re-derived by the export's
own rules (2 % decision gap, advantage wording, verdict), and `python db/spec_fills.py <dataset>`
checks those rules still reproduce every served matchup. Fill only like for like: the Cummins side
is standby fuel and dry open-set weight, so prime-basis fuel, wet weights and engine-only sizes stay out.

`<pack_dir>/tenders_research.json`, when present, adds researched tenders beside the export's own
(db/tender_research.py): each carries its revenue tier for the client (high >= USD 1M addressable,
average USD 100k-1M, low < USD 100k), the estimate and its basis, a proof quote and its sources.
Items with no bid date, or with bids opened and award pending, are marked `pursuit`. A press or
project-level figure never becomes the tender's value. `<pack_dir>/TENDERS.md` is the ranked report.

`<pack_dir>/tender_fit.json`, keyed by exact tender title, grades how properly a client catalogue
model fits each tender (strong / partial / poor), names those models and the competitors that fit
(with their catalogue products), and gives an expected-revenue midpoint. db/tender_fit.py ranks
open tenders by revenue x fit (x0.8 for pursuits); a poor fit scores zero, is labelled, and sinks.

`<pack_dir>/tender_actions.json` (by exact tender title) holds the analyst's dated next moves; the
Tender Intelligence cockpit (lib/tenderIntel.js, tested by test_tender_intel.mjs) turns the
ranked tenders into the headline, opportunity map, proof tiles, next moves and analysis tabs.

`--drop-blank` leaves out products with no fuel, size or weight on record (and the matchups built
on them), and hides matchup spec rows blank on either side. The Cummins Arabia build uses it.

## Onboarding a new client

1. Build a pack in the same shape as `parallax-cummins-arabia-datapack` (its `SCHEMA.md` is the spec).
2. `python db/build_dataset.py --demo` — converter self-check, then `python db/build_dataset.py <pack_dir>`.
3. `node frontend/check_data.mjs <pack_dir>/dataset.json` — runs the app's own wiring and
   self-checks against the dataset; must end `ALL CHECKS PASSED`.
4. `python db/seed_serving.py --recycle <pack_dir>/dataset.json`, then `docker compose restart backend`.
5. Prove the old client is gone: `docker exec kssl-db pg_dump -U postgres -d kssl --data-only | grep -ci <old name>` → `0`.

**Same industry** (another genset distributor): only the pack changes.
**Different industry**: also edit the vocabulary block at the top of `db/build_dataset.py` —
`FAMILIES` (product families + geo keywords), `HIGHER_BETTER` (which spec direction wins),
`PRODUCT_SPECS`, `ACTIVITY` (facility type → map activity), `COUNTRY`, `TECH_CATS`, and the
default `newsQuery`. That block is the only industry-specific code in the path.

## Per-client globals (all optional; absent = the rule is off, never another client's rule)

| global | what it controls | Cummins | KSSL (archive) |
|---|---|---|---|
| `client` | name, short, brand, currency, magnitude, locale, markets, `newsQuery` | USD, en-GB, genset news | INR crore, en-IN, defence news |
| `roster` | fixed rival list for the competitive views | — (competitors = roster) | 45 rivals |
| `footprintTiers` (+`footprintUnresolved`, `footprintLines`) | which markets make a rival's move a threat; `places` = home-market cities | — (derived from the client's own sites) | India / Armenia / UAE / US / Spain |
| `threatRules` `{outside, platform, home, export}` | re-grades pipeline cards by segment and geography | — (pack is analyst-graded) | defence regexes |
| `tenderTypes` `[{l, re}]` | the tender "Product Type" facet | — (facet hidden) | Land / Air-Naval |
| `reqGloss` `{re, text}` | a procurement-rule note on tender requirements | — | DAP 2020 note |
| `competitors[].ticker` | live quote on the profile | not in the pack | static map fallback |
| card `severity` | a stored analyst grade wins over the serve-time derivation | THREAT→high, WATCH→medium, OPPORTUNITY→low | derived |

## How the Cummins pack maps

| pack | dataset |
|---|---|
| `client` | `client`, `competitors[cummins]` (dir `client`), `KSSL_PARTNERS`, own `geoData`, `counterRules` |
| `competitors[]` | `competitors`, `compOrder`, `geoData`, `geoComps`, `sourceRegistry` — display name is the pack's `short` |
| `signals[]` (92) | `competitiveCards` + `details`; Product/Capacity ones also `techCards` + `innovations` |
| `matchups[]` (73) | `matchups` (spec rows scored by `HIGHER_BETTER`; the matched kVA rating is never a vote) |
| `tenders[]` (16) | `tenders` (`cat` = primary segment; fit → `matches` / `lean`) |
| `pipeline[]` (21) | `marketCards` (perceived opportunities) + `details` |
| — | `PATENTS` empty (the pack has none; the view says so) |

## What is still left (not visible to the client)

- **Internal names** keep the old prefix: env vars `KSSL_*`, database `kssl`, containers
  `kssl-db`/`kssl-backend`, contract keys `KSSL_CATS`/`KSSL_PARTNERS`, fields `koel*`/`ksslImpact`,
  CSS classes. Renaming them touches deploy config for no visible gain.
- **The extraction pipeline** (`pipeline/`, `extraction/`) is still KSSL-tuned (prompts, aliases,
  defaults in `threat_gate`). A hand-built pack does not use it; a pipeline-fed client would.
- **Pack gaps** the UI shows honestly: no patents, no innovation maturity/position, no tickers.
- **Pack typo** to fix at source: headline "Generac SD3250 (3.25 MW, Baudouin Baudouin M55)".
- `frontend/public/ops/*.html` (internal ops pages) embed KSSL in LLM prompt text.


## Refresh of 13 Oct 2026

`parallax-cummins-arabia-datapack/refresh_2026-10-13/` holds the research (BRIEF.md, one JSON per agent, the
verification verdicts, `build_news_refresh.py`). It lands in the dataset through three pack files:

- `news_refresh.json` -> `db/news_refresh.py`: replaces non-tender cards dated before `window_start` with the
  verified items (cards, details, competitorNews). Runs after `platform_fields`, which rebuilds competitorNews.
- `tender_status.json`: all 62 tenders re-checked (Etimad blocked; deadline-passed closures are labelled inferred).
- `tenders_research.json` / `tender_fit.json`: 14 new tenders and their Cummins fit.

The pre-refresh data is in `archive/`.
- `db/projects_data.py <dataset.html.json> frontend/src/lib/projectsData.js` regenerates the Projects page data
  (pursuits and high-tier tenders, each under the rivals its fit names). Run it after every dataset rebuild.

- `frontend/build_html.mjs [outDir]` builds the standalone HTML (app + dataset in one file, product-images/ and news-images/ beside it). Needs the backend on :8600.
