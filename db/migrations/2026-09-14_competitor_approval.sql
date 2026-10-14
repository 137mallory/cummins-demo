-- Competitor approval: only APPROVED competitors reach the product.
--
-- WHY A TABLE, NOT A COLUMN ON serving.competitors: enrich_serving.py deletes and re-inserts every
-- origin='pipeline' competitor each pass (step_companies, _write_companies), so a column there would
-- be wiped every rebuild. Approval is a human decision and must outlive every rebuild, so it lives
-- here, keyed by comp_id, and the pipeline keeps building profiles for everyone -- approving a
-- competitor later shows data that is already there.
--
-- SEMANTICS
--   approved = true    shown everywhere in the product
--   approved = false   pending: hidden from the product, listed for the admin dashboard
--   no row at all      pending too (a company the pipeline found after this list was made)
--   table empty        gate OFF (everything shown) -- an accidentally emptied table must not
--                      blank the client dashboard
--   comp_id NULL       visible (a patent with no attributed company is not a competitor row)
--
-- ENFORCED IN
--   * serving_live views keyed by comp_id: competitors, competitor_news, competitor_structure,
--     competitor_metrics, geo_presence, patent -- wrapped below. ANY later migration that redefines
--     one of these views must keep `WHERE serving.competitor_visible(comp_id)`.
--   * backend/app.py _gate_to_served: name-keyed collections (matchups, geoComps, sourceRegistry,
--     companySources) through threat_gate's alias resolver.
--   * signals/threat_gate.py served_roster_names: an unapproved company's cards are not threat
--     cards; the backend grades them "not a tracked rival".
--
-- ADMIN DASHBOARD (later): pending =
--   SELECT c.comp_id, c.name FROM serving.competitors c
--   LEFT JOIN serving.competitor_approval a USING (comp_id) WHERE NOT coalesce(a.approved, false);
--   approve = UPDATE serving.competitor_approval SET approved=true, decided_by=..., decided_at=now()
--   (INSERT ... ON CONFLICT (comp_id) DO UPDATE for a company with no row yet).
-- Staging is the master copy; the publish job copies this table to prod.

CREATE TABLE IF NOT EXISTS serving.competitor_approval (
    comp_id     text PRIMARY KEY,
    name        text,
    approved    boolean NOT NULL DEFAULT false,
    decided_by  text,
    decided_at  timestamptz NOT NULL DEFAULT now(),
    note        text
);

CREATE OR REPLACE FUNCTION serving.competitor_visible(p_comp_id text) RETURNS boolean
LANGUAGE sql STABLE AS $$
    SELECT p_comp_id IS NULL
        OR NOT EXISTS (SELECT 1 FROM serving.competitor_approval)
        OR EXISTS (SELECT 1 FROM serving.competitor_approval a
                    WHERE a.comp_id = p_comp_id AND a.approved)
$$;

-- The approved list of 2026-09-14 (comp.xlsx, 50 companies -> every comp_id they appear under).
INSERT INTO serving.competitor_approval (comp_id, name, approved, decided_by, note) VALUES
  ('aweil', 'AWEIL', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('AWEIL', 'AWEIL', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('nexter', 'Nexter (KNDS France)', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('knds', 'KNDS Germany', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('bae-systems', 'BAE Systems', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('leonardo', 'Leonardo', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('rheinmetall', 'Rheinmetall', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('hanwha-aerospace', 'Hanwha (Aerospace/Group)', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('hanwha-group', 'Hanwha (Aerospace/Group)', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('elbit-systems', 'Elbit Systems', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('elbit', 'Elbit Systems', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('general-dynamics', 'General Dynamics', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('norinco', 'NORINCO', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('tata-advanced-systems', 'Tata Advanced Systems', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('TASL', 'Tata Advanced Systems', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('mahindra-defence', 'Mahindra Defence', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('mahindra', 'Mahindra Defence', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('MAHINDRA', 'Mahindra Defence', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('larsen-toubro', 'Larsen & Toubro (L&T)', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('LT', 'Larsen & Toubro (L&T)', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('l-t', 'Larsen & Toubro (L&T)', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('patria', 'Patria', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('supacat', 'Supacat', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('otokar', 'Otokar', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('paramount-group', 'Paramount Group', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('roshel', 'Roshel', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('idv', 'IDV (Iveco Defence)', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('iveco', 'IDV (Iveco Defence)', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('plr-systems', 'PLR Systems (IWI+Adani)', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('kalashnikov', 'Kalashnikov Concern', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('munitions-india', 'Munitions India Ltd (MIL)', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('MIL', 'Munitions India Ltd (MIL)', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('bharat-dynamics', 'Bharat Dynamics Ltd (BDL)', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('BDL', 'Bharat Dynamics Ltd (BDL)', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('huta-stalowa-wola', 'Huta Stalowa Wola (HSW)', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('hsw', 'Huta Stalowa Wola (HSW)', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('oshkosh-defense', 'Oshkosh Defense', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('oshkosh', 'Oshkosh Defense', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('poongsan', 'Poongsan', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('nammo', 'Nammo', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('sig-sauer', 'SIG Sauer', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('sss-defence', 'SSS Defence', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('SSS', 'SSS Defence', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('rafael-advanced-defense-systems', 'Rafael Advanced Defense Systems', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('kongsberg', 'KONGSBERG', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('mbda', 'MBDA', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('israel-aerospace-industries', 'Israel Aerospace Industries (IAI)', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('l3harris', 'L3Harris', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('northrop-grumman', 'Northrop Grumman', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('lockheed-martin', 'Lockheed Martin', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('rtx', 'RTX (Raytheon)', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('raytheon', 'RTX (Raytheon)', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('saab', 'SAAB', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('thyssenkrupp-marine-systems', 'Thyssenkrupp Marine Systems', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('naval-group', 'Naval Group', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('huntington-ingalls-industries', 'Huntington Ingalls Industries', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('hii', 'Huntington Ingalls Industries', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('babcock', 'Babcock', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('diehl-defence', 'Diehl Defence', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('aerovironment', 'AeroVironment', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('anduril', 'Anduril', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('uvision-air', 'UVision Air', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('adani-defence', 'Adani Defence', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('adani', 'Adani Defence', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('ADANI', 'Adani Defence', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('brahmos-aerospace', 'BrahMos Aerospace', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('BRAHMOS', 'BrahMos Aerospace', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('premier-explosives', 'Premier Explosives', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('PEL', 'Premier Explosives', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('solar-industries', 'Solar Industries', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('SOLAR', 'Solar Industries', true, 'comp.xlsx approved list', '2026-09-14 approved list'),
  ('kalyani-strategic-systems', 'Kalyani Strategic Systems', true, 'client', 'the client is never gated')
ON CONFLICT (comp_id) DO NOTHING;

-- Everyone else the store knows today: pending.
INSERT INTO serving.competitor_approval (comp_id, name, approved, decided_by, note)
SELECT comp_id, name, false, 'comp.xlsx approved list', 'not on the 2026-09-14 approved list'
  FROM serving.competitors
ON CONFLICT (comp_id) DO NOTHING;

CREATE OR REPLACE VIEW serving_live.competitor_approval AS
    SELECT comp_id, name, approved, decided_by, decided_at, note FROM serving.competitor_approval;

-- Wrap each comp_id-keyed view around its CURRENT definition, whatever migration last wrote it,
-- so this file cannot resurrect an older column list. Skips a view already gated.
DO $$
DECLARE v text; def text;
BEGIN
  FOREACH v IN ARRAY ARRAY['competitors','competitor_news','competitor_structure',
                           'competitor_metrics','geo_presence','patent'] LOOP
    IF to_regclass(format('serving_live.%I', v)) IS NULL THEN CONTINUE; END IF;
    def := pg_get_viewdef(format('serving_live.%I', v)::regclass, true);
    IF def ILIKE '%competitor_visible%' THEN CONTINUE; END IF;
    def := regexp_replace(def, ';\s*$', '');
    EXECUTE format('CREATE OR REPLACE VIEW serving_live.%I AS SELECT * FROM (%s) v '
                   'WHERE serving.competitor_visible(v.comp_id)', v, def);
  END LOOP;
END $$;

-- Leonardo is on the approved list. 2026-09-06_leonardo_not_a_threat.sql took it off the roster
-- allowlist, which stops enrich from ever building its profile; put it back so approval has data.
DO $$
BEGIN
  IF to_regclass('serving.competitor_roster_allow') IS NOT NULL THEN
    EXECUTE $q$INSERT INTO serving.competitor_roster_allow (name, comp_id, note, at)
               SELECT 'Leonardo', 'leonardo', 'on the 2026-09-14 approved competitor list', now()
               WHERE NOT EXISTS (SELECT 1 FROM serving.competitor_roster_allow
                                  WHERE comp_id = 'leonardo' OR name = 'Leonardo')$q$;
  END IF;
END $$;
