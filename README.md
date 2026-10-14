# Cummins Arabia: competitive-intelligence demo

A competitive-intelligence dashboard built for **Cummins Arabia** (diesel and gas gensets in Saudi
Arabia, the UAE and Kuwait): React frontend, FastAPI backend, Postgres. It tracks eight rivals
(Caterpillar, Rolls-Royce mtu, Rehlko, Mitsubishi MHIET, Weichai/Baudouin, Perkins/FG Wilson,
Generac, Volvo Penta) across three pillars.

| Pillar | Pages |
|---|---|
| Competitive | Overview, Competitor Profile, Competitor Moment, Products, Product Evaluation, Partnership, Projects, Geo Footprint, Patent |
| Market | Top opportunity (ranked tenders and projects), Tenders, Global Requirements, Market Intelligence |
| Technology | Overview, Innovation |

The client is **data, not code**: who the client is, its rivals, products, markets and currency
all arrive in the served dataset. The data for this demo is in
[`parallax-cummins-arabia-datapack/`](parallax-cummins-arabia-datapack/); a new client is a new
pack (see [`docs/CLIENT_PACKS.md`](docs/CLIENT_PACKS.md)).

## Run it

Needs Docker, Python 3.11+ and Node 18+. Tested from a clean copy of this repo.

    docker compose up -d                                  # postgres :5460 + backend :8600
    pip install psycopg2-binary                           # the seed script's only dependency
    python db/seed_serving.py --recycle parallax-cummins-arabia-datapack/dataset.html.json
    docker compose restart backend                        # drop the 120 s dataset cache
    cd frontend && npm install && npx vite                # http://127.0.0.1:5178 (add --port 5190 if it is busy)

`--recycle` empties every data table first, so the database holds this one client and nothing
else. `dataset.html.json` is the served dataset; the steps that build it from the pack are under
"Data" below.

| what | where |
|---|---|
| Postgres (database name `kssl`, a legacy name) | 127.0.0.1:5460 (the compose file also sets `KSSL_SERVE_ORIGIN=all`, which this demo needs) |
| FastAPI backend | 127.0.0.1:8600 (`/api/dataset`, `/healthz`) |
| frontend | 127.0.0.1:5178 |

## Data

Everything the dashboard shows is a researched, source-cited record in the pack. Nothing is
invented in the build; a value the pack does not carry is shown as "not published".

| File in `parallax-cummins-arabia-datapack/` | What it holds |
|---|---|
| `dataset.html.json` | the served dataset (competitors, products, matchups, tenders, news, geo, patents) |
| `competitors/`, `client/` | one researched file per rival, and the client's own record |
| `tenders.json`, `tenders_research.json`, `tender_fit.json`, `tender_status.json`, `tender_actions.json` | tenders: scope, revenue estimate and basis, Cummins fit, checked status with evidence, dated next steps |
| `competitor_projects.json` | what each rival is working on or pursuing, Gulf and worldwide |
| `geo_fills.json` | country and city footprint rows, with sources |
| `competitor_news_lenses.json` | multi-view analysis (supply chain, manufacturing, market, ...) of each competitor news item |
| `news_refresh.json`, `patents.json`, `awards.json`, `leader_bios.json` | news, patent filings, awarded contracts, leadership |
| `ISSUES.md` | known data gaps and unverified items, by section |
| `TENDERS.md`, `verification.md`, `SCHEMA.md` | method notes and the pack schema |

Build and apply steps (each script has a self-check, run it with no arguments):

    python db/dataset_from_html.py <export.html> <out.json> --base dataset.json --pack parallax-cummins-arabia-datapack --images --drop-blank
    python db/competitor_projects.py <dataset.html.json> frontend/src/lib/competitorProjects.js
    python db/news_lenses.py parallax-cummins-arabia-datapack/competitor_news_lenses.json frontend/src/lib/newsLenses.js
    python db/geo_fills.py                    # self-check of the geo fill rules
    python db/seed_serving.py --recycle <dataset.json>

## Database

- **serving**: tables that power the UI. Every row carries `origin` (`'reference'` or `'pipeline'`).
- **serving_live**: views over `serving` filtered to `origin='pipeline'`; this is what the API serves.
  `KSSL_SERVE_ORIGIN=all` on the backend (a legacy variable name) serves the raw tables instead.
- **extracted**: documents, offset-checked spans and propositions from the extraction pipeline.

`reference_dataset.json` is the archived original reference client; it is not loaded.

## Repository layout

    backend/    FastAPI app that serves /api/dataset from Postgres
    frontend/   React + Vite app (src/pages, src/lib, src/components)
    db/         schema (00-07 .sql), seed_serving.py, migrations, and the data build scripts
    extraction/ signal extraction and the threat gate used when serving cards
    pipeline/   corpus and stage helpers
    docs/       client-pack guide, UI contract, dataset contract shapes
    parallax-cummins-arabia-datapack/   the Cummins Arabia data

## Live demo

A copy runs on a single VPS behind Caddy (static `frontend/dist` plus the backend and database in
their own compose project). It has no login, so anyone with the URL sees the client research.
