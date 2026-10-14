-- serving.*.extra: every dataset field that has no column of its own.
--
-- A client dataset built from a standalone HTML export (db/dataset_from_html.py) carries
-- fields the tables were never given columns for (a competitor's profile, strengths and
-- weaknesses, a matchup's kVA delta, a tender's scope). db/seed_serving.py writes them
-- here instead of dropping them; backend/app.py _emit merges them back into the served
-- row, so the browser gets the record exactly as the dataset had it. The base schema
-- (db/02_serving.sql) carries the column for a FRESH build; this adds it to an existing
-- database and refreshes the passthrough views (SELECT * is expanded at CREATE time).
-- Idempotent.

ALTER TABLE serving.competitors ADD COLUMN IF NOT EXISTS extra jsonb;
ALTER TABLE serving.competitor_news ADD COLUMN IF NOT EXISTS extra jsonb;
ALTER TABLE serving.signal_card ADD COLUMN IF NOT EXISTS extra jsonb;
ALTER TABLE serving.signal_detail ADD COLUMN IF NOT EXISTS extra jsonb;
ALTER TABLE serving.matchup ADD COLUMN IF NOT EXISTS extra jsonb;
ALTER TABLE serving.tender ADD COLUMN IF NOT EXISTS extra jsonb;
ALTER TABLE serving.patent ADD COLUMN IF NOT EXISTS extra jsonb;
ALTER TABLE serving.geo_presence ADD COLUMN IF NOT EXISTS extra jsonb;
ALTER TABLE serving.geo_comp ADD COLUMN IF NOT EXISTS extra jsonb;
ALTER TABLE serving.innovation ADD COLUMN IF NOT EXISTS extra jsonb;
ALTER TABLE serving.partner ADD COLUMN IF NOT EXISTS extra jsonb;
ALTER TABLE serving.source_registry ADD COLUMN IF NOT EXISTS extra jsonb;

CREATE OR REPLACE VIEW serving_live.competitor_news AS
  SELECT id, comp_id, title, description, source, published_date, category,
         is_trending, url, updated_at, image, extra
    FROM serving.competitor_news WHERE origin = 'pipeline';
CREATE OR REPLACE VIEW serving_live.competitors AS SELECT * FROM serving.competitors WHERE origin = 'pipeline';
CREATE OR REPLACE VIEW serving_live.signal_card AS SELECT * FROM serving.signal_card WHERE origin = 'pipeline';
CREATE OR REPLACE VIEW serving_live.signal_detail AS SELECT * FROM serving.signal_detail WHERE origin = 'pipeline';
CREATE OR REPLACE VIEW serving_live.matchup AS SELECT * FROM serving.matchup WHERE origin = 'pipeline';
CREATE OR REPLACE VIEW serving_live.tender AS SELECT * FROM serving.tender WHERE origin = 'pipeline';
CREATE OR REPLACE VIEW serving_live.patent AS SELECT * FROM serving.patent WHERE origin = 'pipeline';
CREATE OR REPLACE VIEW serving_live.geo_presence AS SELECT * FROM serving.geo_presence WHERE origin = 'pipeline';
CREATE OR REPLACE VIEW serving_live.geo_comp AS SELECT * FROM serving.geo_comp WHERE origin = 'pipeline';
CREATE OR REPLACE VIEW serving_live.innovation AS SELECT * FROM serving.innovation WHERE origin = 'pipeline';
CREATE OR REPLACE VIEW serving_live.partner AS SELECT * FROM serving.partner WHERE origin = 'pipeline';
CREATE OR REPLACE VIEW serving_live.source_registry AS SELECT * FROM serving.source_registry WHERE origin = 'pipeline';
