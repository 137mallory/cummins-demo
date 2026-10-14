-- serving.tender.posted: the tender's publication date.
--
-- pipeline/fetch_tenders.py already emits a `posted` field per tender; the base schema
-- (db/02_serving.sql) carries the column so a FRESH build has it. This migration adds it
-- to an existing REPLICA (which was built from an older base) and refreshes the
-- passthrough view so serving_live sees it too. Idempotent: IF NOT EXISTS on the column,
-- CREATE OR REPLACE on the view (append-only, so no dependent breaks).

ALTER TABLE serving.tender ADD COLUMN IF NOT EXISTS posted text;

CREATE OR REPLACE VIEW serving_live.tender AS
  SELECT * FROM serving.tender WHERE origin = 'pipeline';
