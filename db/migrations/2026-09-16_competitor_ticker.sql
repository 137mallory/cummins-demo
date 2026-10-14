-- serving.competitors.ticker: the stock listing the corpus quotes, in Yahoo Finance's spelling.
--
-- The Profile page's stock widget read one hard-coded map of 20 comp_ids in backend/app.py, so a
-- listed competitor outside that map showed nothing. signals/fill_ticker.py now reads the listing
-- from the company's own press releases ("Lockheed Martin (NYSE: LMT)", "Elbit Systems Ltd.
-- (NASDAQ: ESLT and TASE: ESLT)") and writes it here; the map stays as the fallback.
-- Idempotent: IF NOT EXISTS on the column, CREATE OR REPLACE on the passthrough view.

ALTER TABLE serving.competitors ADD COLUMN IF NOT EXISTS ticker text;

-- THE APPROVAL GATE HAS TO SURVIVE THIS. 2026-09-14_competitor_approval.sql wrapped the six
-- comp_id-keyed serving_live views in serving.competitor_visible(comp_id), and said in the file
-- that any later migration redefining one of them must keep it. That wrapping was a one-shot DO
-- block, so it does NOT re-run to repair a view a later migration replaced -- and the first draft
-- of this file replaced serving_live.competitors with a bare origin filter, which would have put
-- every unapproved competitor back on the dashboard, dragging its matchups, geoComps and sources
-- with it through backend/app.py _gate_to_served. The gate is restated here, explicitly.
--
-- competitor_visible() is guarded so this file still applies to a database that predates the
-- approval migration: no function -> plain origin filter, same as before.
DO $mig$
BEGIN
  IF to_regprocedure('serving.competitor_visible(text)') IS NOT NULL THEN
    EXECUTE $v$
      CREATE OR REPLACE VIEW serving_live.competitors AS
        SELECT * FROM serving.competitors
         WHERE origin = 'pipeline' AND serving.competitor_visible(comp_id)
    $v$;
  ELSE
    EXECUTE $v$
      CREATE OR REPLACE VIEW serving_live.competitors AS
        SELECT * FROM serving.competitors WHERE origin = 'pipeline'
    $v$;
  END IF;
END
$mig$;
