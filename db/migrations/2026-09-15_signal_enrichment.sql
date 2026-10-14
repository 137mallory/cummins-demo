-- Enrichment columns for the per-pillar signal and tender write-ups (DEPLOY-ENRICHMENT-HANDOFF.md §B.1).
--
-- extraction/signals/gen_signal_text.py / gen_tender_text.py generate them on a GPU host and
-- load_enrichment_to_serving.py UPDATEs them by id. backend/app.py serves column name == JSON key,
-- so the names are the quoted camelCase keys the frontend reads. The base schema (db/02_serving.sql)
-- carries them for a FRESH build; this adds them to an existing replica.
--
-- Safe with the running pipeline: serving_fill's signal_card upsert names its own columns, so an
-- enrich pass never overwrites these; publish.py sends shared columns only, so they stay off prod
-- until prod gets this migration. Idempotent: IF NOT EXISTS on the columns, CREATE OR REPLACE on the
-- passthrough views (the new columns append at the end, so the replace is legal).

ALTER TABLE serving.signal_card
  ADD COLUMN IF NOT EXISTS "uiTitle"        text,
  ADD COLUMN IF NOT EXISTS "summary"        text,
  ADD COLUMN IF NOT EXISTS "ksslImpact"     text,
  ADD COLUMN IF NOT EXISTS "ksslImpactKind" text,
  ADD COLUMN IF NOT EXISTS "glance"         jsonb;

ALTER TABLE serving.tender
  ADD COLUMN IF NOT EXISTS "gist"    text,
  ADD COLUMN IF NOT EXISTS "summary" text;

CREATE OR REPLACE VIEW serving_live.signal_card AS
  SELECT * FROM serving.signal_card WHERE origin = 'pipeline';
CREATE OR REPLACE VIEW serving_live.tender AS
  SELECT * FROM serving.tender WHERE origin = 'pipeline';
