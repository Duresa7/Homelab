#!/usr/bin/env python3
"""Regression checks for accuracy-first policy retrieval.

These are intentionally lightweight so they can run on REDACTED_OPERATIONAL_HOST without a
pytest dependency:

    python3 test_accuracy_policy.py
"""
from __future__ import annotations

import lore_agent
import lore_source_map


def _assert_contains(text: str, *needles: str) -> None:
    low = text.lower()
    missing = [n for n in needles if n.lower() not in low]
    assert not missing, f"missing {missing!r} in {text!r}"


def test_intel_sith_join_direct_answer() -> None:
    out = lore_agent._nfu_faction_direct_answer("what rank do I need to join Intel as a sith")
    assert out is not None
    assert out["sources"][0]["title"] == "Intel Faction Guide"
    assert "Roster" not in out["sources"][0]["title"]
    _assert_contains(out["answer"], "Apprentice", "Candidate")
    assert "any rank" not in out["answer"].lower()


def test_intel_generic_join_direct_answer() -> None:
    out = lore_agent._nfu_faction_direct_answer("what rank do you need to join Intel?")
    assert out is not None
    _assert_contains(out["answer"], "Imperial Military", "any rank", "Sith", "Apprentice", "Candidate")


def test_intel_nfu_and_cipher_distinction() -> None:
    nfu = lore_agent._nfu_faction_direct_answer("what rank does an NFU need to join Intel?")
    assert nfu is not None
    _assert_contains(nfu["answer"], "Imperial Military", "any rank", "7S", "Cipher")

    cipher = lore_agent._nfu_faction_direct_answer("as a Sith what do I need to become Cipher?")
    assert cipher is not None
    _assert_contains(cipher["answer"], "Apprentice", "additional marks", "Cipher")


def test_policy_candidate_filter_suppresses_roster_rows() -> None:
    rows = [
        {
            "title": "TNIO Imperial Intelligence Roster",
            "section": "Sheet1 Row 12",
            "excerpt": "Agent Rank: Death Trooper. Sith: yes.",
            "match_type": "structured record",
            "relevance_score": 99,
            "chunk_type": "sheet_row",
        },
        {
            "title": "Intel Faction Guide",
            "section": "Rank Structure",
            "excerpt": "Sith must be at least an Apprentice before joining Imperial Intelligence.",
            "match_type": "keyword",
            "relevance_score": 5,
        },
    ]
    filtered, log = lore_agent._filter_policy_candidates("what rank do I need to join Intel as a sith", rows)
    assert log["applied"] is True
    assert filtered[0]["title"] == "Intel Faction Guide"
    assert all("Roster" not in r["title"] for r in filtered)


def test_auto_sweep_uses_expanded_intel_terms() -> None:
    terms = [t.lower() for t in lore_agent._auto_sweep_terms("what rank do I need to join Intel as a sith")]
    assert "intel" not in terms
    assert "imperial intelligence" in terms
    assert "joining imperial intelligence" in terms


def test_source_map_topic_aliases_route_intel_joining() -> None:
    routes = lore_source_map.topic_routes("what rank do I need to join Intel as a sith", limit=4)
    titles = [r["title"] for r in routes]
    assert "Intel Faction Guide" in titles, titles


def run_all() -> None:
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok {name}")


if __name__ == "__main__":
    run_all()
