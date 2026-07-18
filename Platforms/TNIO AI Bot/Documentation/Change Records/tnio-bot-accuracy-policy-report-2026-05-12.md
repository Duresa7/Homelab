# TNIO Bot Accuracy-First Retrieval Fix Report - 2026-05-12

**Created:** 2026-05-12  
**Last updated:** 2026-07-16

## Summary

Implemented the accuracy-first retrieval plan on `REDACTED_OPERATIONAL_HOST` for the TNIO Discord Librarian bot.

The main issue was not missing Google Drive data. The correct answers were present in the synced TNIO archive, but the bot sometimes selected the wrong source class when answering new phrasings. In the Intel/Sith example, the `Intel Faction Guide` clearly says Sith must be at least Apprentice before joining Imperial Intelligence, but broad `Intel` retrieval could pull in `TNIO Imperial Intelligence Roster` rows and fallback ranking could surface those instead of the authoritative guide.

## Root Cause Fixed

- Added policy/requirement intent detection so rank, eligibility, ownership, permission, and progression questions are treated differently from roster/profile/lore recap questions.
- Added source authority handling so guides, codices, faction rules, and progression records outrank rosters, registries, and tracking sheets for policy questions.
- Added source-backed Intel eligibility handling from `Intel Faction Guide`.
- Added normalized Intel routing:
  - `Intel` -> `Imperial Intelligence`
  - `join` / `joining`
  - `eligible` / `eligibility`
  - `requirement` / `requirements`
  - `Sith` / `Apprentice`
  - `NFU` / `Cipher`
- Reduced noisy auto-sweep behavior for broad one-word terms like `Intel`, `Intelligence`, and `Sith`.
- Added targeted policy retry hooks for when the first retrieval pass lacks authoritative evidence.
- Added answer verification to block:
  - roster-only policy answers
  - raw sheet/table dumps
  - "not found / no specific rank" answers when direct policy evidence is present

## Files Changed On AI Bravo 02

- `/home/REDACTED_DEPLOYMENT_USER/lore-rag/lore_agent.py`
- `/home/REDACTED_DEPLOYMENT_USER/lore-rag/lore_source_map.py`
- `/home/REDACTED_DEPLOYMENT_USER/lore-rag/lore_mcp_server.py`
- `/home/REDACTED_DEPLOYMENT_USER/lore-rag/test_accuracy_policy.py`

Backups were created before overwrite:

- `/home/REDACTED_DEPLOYMENT_USER/lore-rag/lore_agent.py.bak.accuracy-policy-20260512T150221Z`
- `/home/REDACTED_DEPLOYMENT_USER/lore-rag/lore_source_map.py.bak.accuracy-policy-20260512T150221Z`
- `/home/REDACTED_DEPLOYMENT_USER/lore-rag/lore_mcp_server.py.bak.accuracy-policy-20260512T150221Z`

## Intel Policy Card Added

First source-backed policy card: Imperial Intelligence eligibility.

Correct behavior now:

- Sith joining Intel: must be at least **Apprentice**.
- NFU joining Intel: must be part of the **Imperial Military**; initial Intel entry is available at any Military rank.
- New Intel members start as **Candidate**.
- NFU **7S** requirement is for later Cipher consideration, not initial entry.
- Sith do not need additional marks before Cipher consideration once eligible through the Apprentice path.

## Cache / Runtime Changes

- Agent answer cache key was bumped from `v30` to `v31` so old bad cached answers are bypassed.
- Restarted:
  - `lore-search-http.service`
  - `lore-discord-bot.service`
- Both services came back active.

## Verification

Syntax checks passed:

```bash
python3 -m py_compile lore_agent.py lore_source_map.py lore_mcp_server.py test_accuracy_policy.py
```

Regression script passed:

```bash
python3 test_accuracy_policy.py
```

Passing tests:

- `test_auto_sweep_uses_expanded_intel_terms`
- `test_intel_generic_join_direct_answer`
- `test_intel_nfu_and_cipher_distinction`
- `test_intel_sith_join_direct_answer`
- `test_policy_candidate_filter_suppresses_roster_rows`
- `test_source_map_topic_aliases_route_intel_joining`

Live endpoint checks passed:

- `what rank do I need to join Intel as a sith`
  - Correctly answers **Apprentice**
  - Source: `Intel Faction Guide`
  - Retrieval: `direct_faction_eligibility`
  - Confidence: high

- `as a Sith can I join Intelligence?`
  - Correctly answers **Apprentice**
  - Source: `Intel Faction Guide`

- `what rank does an NFU need to join Intel?`
  - Correctly separates initial entry from the **7S** Cipher requirement
  - Source: `Intel Faction Guide`

- `what do I need to become Cipher as a Sith?`
  - Correctly says Sith need Apprentice eligibility and no additional marks before Cipher consideration
  - Source: `Intel Faction Guide`

- `bot`
  - Correctly stays persona/small-talk
  - No random archive retrieval

- `Who is the current Minister of War and the current Commandant of the military?`
  - Correctly answers from `Know Your Empire`
  - No stale-session answer from the previous Darth comparison

## Remaining Concern

The Minister/Commandant answer was accurate, but still took about 55 seconds. The next root improvement should be latency reduction for non-direct roster/current-office questions, likely by adding a direct current-office answer path or improving `Know Your Empire` routing speed.

