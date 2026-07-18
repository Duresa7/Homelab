#!/usr/bin/env python3
"""Corpus-artifact and retrieval-routing checks for TNIO bot accuracy.

Run on REDACTED_OPERATIONAL_HOST from /home/REDACTED_DEPLOYMENT_USER/lore-rag:

    python3 test_corpus_accuracy.py
"""
from __future__ import annotations

import json
from pathlib import Path

import lore_agent


ROOT = Path(__file__).resolve().parent
STATE = ROOT / "state"


def _load(name: str) -> dict:
    return json.loads((STATE / name).read_text(encoding="utf-8"))


def _assert_contains(text: str, *needles: str) -> None:
    low = text.lower()
    missing = [n for n in needles if n.lower() not in low]
    assert not missing, f"missing {missing!r} in {text!r}"


def test_authority_map_covers_active_manifest() -> None:
    manifest = _load("manifest.json")
    authority = _load("tnio_source_authority_map.json")
    manifest_titles = {row["name"] for row in manifest["files"].values()}
    authority_titles = {row["title"] for row in authority["files"]}
    missing = sorted(manifest_titles - authority_titles)
    assert not missing, f"authority map missing active files: {missing}"


def test_eval_questions_reference_known_sources() -> None:
    authority = _load("tnio_source_authority_map.json")
    evals = _load("tnio_eval_questions.json")
    authority_titles = {row["title"] for row in authority["files"]}
    missing = sorted({
        q["expected_source"]
        for q in evals["questions"]
        if q.get("expected_source") and q["expected_source"] not in authority_titles
    })
    assert not missing, f"eval questions reference unknown source titles: {missing}"


def test_intel_policy_uses_guide_not_roster() -> None:
    guide = {
        "title": "Intel Faction Guide",
        "section": "Rank Structure",
        "excerpt": "Sith must be at least an Apprentice before joining Imperial Intelligence.",
        "match_type": "keyword",
    }
    roster = {
        "title": "TNIO Imperial Intelligence Roster",
        "section": "Sheet1 Row 12",
        "excerpt": "Rakkos, Keeper (Sith), 15, Active",
        "match_type": "structured",
        "chunk_type": "sheet_row",
    }
    q = "what rank do I need to join Intel as a sith"
    assert lore_agent._policy_candidate_score(q, guide) > 0
    assert lore_agent._policy_candidate_score(q, roster) < 0
    filtered, log = lore_agent._filter_policy_candidates(q, [roster, guide])
    assert log["authority_present"] is True
    assert filtered[0]["title"] == "Intel Faction Guide"


def test_artifact_hints_for_high_risk_questions() -> None:
    assert "TNIO Master Engineers: Droid Codex" in lore_agent._artifact_source_hints(
        "As a military Captain, how many droids can I own, and how many functions can each one have?"
    )
    assert "TNIO Master Engineers: Starship Codex" in lore_agent._artifact_source_hints(
        "As a Captain can I own a Destroyer?"
    )
    assert "Character Progression in The New Imperial Order" in lore_agent._artifact_source_hints(
        "What do I need to do to reach Darth status?"
    )
    assert "Know Your Empire" in lore_agent._artifact_source_hints(
        "Who is the current Minister of War and the current Commandant?"
    )


def test_policy_artifact_retry_calls_are_targeted() -> None:
    droid_calls = lore_agent._policy_artifact_tool_calls(
        "As a military Captain, how many droids can I own, and how many functions can each one have?"
    )
    assert any(c["args"].get("doc_title") == "TNIO Master Engineers: Droid Codex" for c in droid_calls if c["name"] == "read_doc")
    starship_calls = lore_agent._policy_artifact_tool_calls("What rank do I need for a Destroyer?")
    assert any(c["args"].get("doc_title") == "TNIO Master Engineers: Starship Codex" for c in starship_calls if c["name"] == "read_doc")


def test_direct_answers_cover_known_failures() -> None:
    intel = lore_agent._nfu_faction_direct_answer("what rank do I need to join Intel as a sith")
    assert intel is not None
    _assert_contains(intel["answer"], "Apprentice", "Candidate")

    droid = lore_agent._droid_ownership_fast_direct_answer(
        "As a military Captain, how many droids can I own, and how many functions can each one have?"
    )
    assert droid is not None
    _assert_contains(droid["answer"], "7", "3 functions")

    starship = lore_agent._starship_policy_fast_direct_answer("As a military Captain can I own a Destroyer?")
    assert starship is not None
    _assert_contains(starship["answer"], "Corvette", "Darth/Moff/Regulator", "Destroyer")

    sithspawn = lore_agent._sithspawn_creation_fast_direct_answer("How can I create a sithspawn?")
    assert sithspawn is not None
    _assert_contains(sithspawn["answer"], "Sithspawn Alchemy", "Sith Alchemy 2", "Sphere of Ancient Knowledge")


def test_smalltalk_stays_persona() -> None:
    plan = lore_agent._heuristic_plan("beep boop")
    assert plan is not None
    assert plan["mode"] == "persona"


def run_all() -> None:
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok {name}")


if __name__ == "__main__":
    run_all()
