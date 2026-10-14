# -*- coding: utf-8 -*-
"""A dataset field with no column of its own must still reach the browser.

db/seed_serving.py stores such fields in the row's `extra` jsonb; _emit merges them back.
A column wins over an `extra` key of the same name, and a NULL `extra` adds nothing.

Run: python backend/test_extra_fields.py
"""
import os
import sys

os.environ.setdefault("KSSL_CORPUS_DSN", "postgresql://unused/unused")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import app  # noqa: E402

row = {"name": "Caterpillar", "dir": "threat", "extra": {"strengths": ["a"], "name": "shadow"}}
out = app._emit(row, ["name", "dir", "extra"], frozenset(["extra"]))
assert out == {"name": "Caterpillar", "dir": "threat", "strengths": ["a"]}, out

out = app._emit({"name": "X", "extra": None}, ["name", "extra"], frozenset(["extra"]))
assert out == {"name": "X"}, out

for fields in (app.COMP_FIELDS, app.GEO_FIELDS, app.SRCREG_FIELDS, app.MATCHUP_FIELDS):
    assert fields[-1] == "extra", fields
for table, fields, opt in app._SERVED:
    if "extra" in fields:
        assert "extra" in opt, table  # optional: a database without the column still serves
print("extra fields ok")
