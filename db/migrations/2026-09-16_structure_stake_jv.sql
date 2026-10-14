-- serving.competitor_structure: two new ownership labels, each drawn as a pair of edges.
--
--   stake  / shareholder  -- a minority or unspecified non-controlling share (Rheinmetall's
--                            40% of EuroSpike, Leonardo's 25.1% of HENSOLDT)
--   jv     / jv_owner     -- a joint venture and one of its co-owners
--
-- Before this the prompt offered only subsidiary | division, so a stake had no label, the model
-- answered "joint venture" or null, and step_structure refused the fact. Idempotent: drop the
-- old CHECK if present, add the widened one.

ALTER TABLE serving.competitor_structure
  DROP CONSTRAINT IF EXISTS competitor_structure_relationship_type_check;
ALTER TABLE serving.competitor_structure
  ADD CONSTRAINT competitor_structure_relationship_type_check
  CHECK (relationship_type IN ('parent', 'subsidiary', 'sister', 'division',
                               'stake', 'shareholder', 'jv', 'jv_owner'));
