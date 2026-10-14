-- serving.signal_card.severity: an analyst's grade, stored with the signal.
--
-- A hand-researched client dataset (db/build_dataset.py) rates every signal itself. The
-- API derives severity at serve time for pipeline cards that carry none (threat_gate);
-- a stored grade wins over that derivation (backend/app.py _grade_cards). The base
-- schema (db/02_serving.sql) carries the column for a FRESH build; this adds it to an
-- existing database and refreshes the passthrough view. Idempotent.

ALTER TABLE serving.signal_card ADD COLUMN IF NOT EXISTS severity text;

CREATE OR REPLACE VIEW serving_live.signal_card AS
  SELECT * FROM serving.signal_card WHERE origin = 'pipeline';
