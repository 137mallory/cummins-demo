# -*- coding: utf-8 -*-
"""Only approved competitors reach the name-keyed collections of /api/dataset.

    python backend/test_competitor_gate.py

The comp_id-keyed tables are gated in their serving_live views (competitor_visible). Matchups,
geoComps, sourceRegistry and companySources carry a company NAME instead, so _gate_to_served
matches them through threat_gate's alias resolver. Cases are the real rows staging held on
2026-09-14 that a plain name match got wrong.
"""
import os
import sys

os.environ.setdefault("KSSL_CORPUS_DSN", "postgresql://unused/unused")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "extraction", "signals"))
import app                                                            # noqa: E402


def dataset():
    return {
        "competitors": {"larsen-toubro": {"name": "Larsen &amp; Toubro"}, "knds": {"name": "KNDS"},
                        "bae-systems": {"name": "BAE Systems"}},
        "matchups": {"1": {"compBy": "KNDS"}, "2": {"compBy": "Ashok Leyland"},
                     "3": {"compBy": "Leonardo"}, "4": {"compBy": "IWI"}},
        "geoComps": [{"name": "Larsen &amp;amp; Toubro"}, {"name": "IWI"},
                     {"name": "Bharat Forge", "isBf": True}],
        "sourceRegistry": [{"company": "BAE Systems"}, {"company": "IWI"}],
        "companySources": {"KNDS": ["u"], "IWI": ["u"], "Kalyani Strategic Systems": ["u"]},
    }


def main():
    out = app._gate_to_served(dataset(), ["Leonardo", "KNDS"])
    # an approved company with no profile yet keeps its matchups; unapproved ones go
    assert set(out["matchups"]) == {"1", "3"}, out["matchups"]
    # double-escaped name still resolves; the client's own row is never gated
    assert [g["name"] for g in out["geoComps"]] == ["Larsen &amp;amp; Toubro", "Bharat Forge"], out["geoComps"]
    assert out["sourceRegistry"] == [{"company": "BAE Systems"}]
    assert set(out["companySources"]) == {"KNDS", "Kalyani Strategic Systems"}, out["companySources"]
    # nothing approved and nothing served: leave the product as it is, never blank it
    empty = app._gate_to_served({"competitors": {}, "matchups": {"1": {"compBy": "IWI"}}}, [])
    assert empty["matchups"] == {"1": {"compBy": "IWI"}}
    print("competitor gate ok")


if __name__ == "__main__":
    main()
