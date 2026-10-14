-- Competitor product specs from the extraction first, the workbook as fallback.
--
-- signals/product_specs.py (run as the enrich step `product_specs`) reads spec rows out of
-- extracted.proposition and publishes specs = extraction rows + workbook rows for labels the
-- extraction did not state. The inputs get their own columns:
--   specs_workbook   the audited workbook's rows; competitor_specs.py / competitor_portfolio.py write here
--   specs_extracted  rows read from the corpus, each carrying its quote, source and tier
--   specs_scan       {fp, statements}: which evidence was read, so unchanged products are not re-read
--
-- Idempotent. The backfill copies today's specs (all workbook-derived: nothing else has ever
-- written this column) into specs_workbook once, so the first enrich pass merges against them.

ALTER TABLE serving.competitor_product
  ADD COLUMN IF NOT EXISTS specs_workbook  jsonb,
  ADD COLUMN IF NOT EXISTS specs_extracted jsonb,
  ADD COLUMN IF NOT EXISTS specs_scan      jsonb;

UPDATE serving.competitor_product SET specs_workbook = specs WHERE specs_workbook IS NULL;
