# TNIO Bot Secondary Deep Corpus Audit Report - 2026-05-12

**Created:** 2026-05-12  
**Last updated:** 2026-07-18

## Summary
I completed a secondary deep-pass corpus audit for the TNIO Discord bot. This pass processed every active file in the bot's current Google Drive manifest end-to-end, then rebuilt the runtime source authority artifacts so the bot has a stronger map of which records should answer which kinds of questions.

This was not limited to a small manual sample. The audit read all active exported Docs and Sheets available to the bot, including full text exports for Docs and all tabs, rows, and cells for Sheets.

## Scope
- Active manifest files processed: 45
- Total exported text processed: 1,397,014 characters
- Sheet rows processed: 1,780
- Nonempty sheet rows processed: 1,704
- Nonempty sheet cells processed: 7,370
- Topics mapped: 138
- Source-overlap risks identified: 34
- Evaluation questions generated: 97

The two files still blocked by the local Google Drive connector were included through the bot's synced exports:
- TNIO Master Engineers: Starship Codex
- TNIO Master Engineers: Droid Codex

## Updated Runtime Artifacts
The following files were rebuilt on `REDACTED_OPERATIONAL_HOST` under `/home/REDACTED_DEPLOYMENT_USER/lore-rag/state/`:

- `tnio_deep_source_audit.json`
- `tnio_source_authority_map.json`
- `tnio_topic_authority_map.json`
- `tnio_eval_questions.json`
- `tnio_deep_source_audit.md`

The source authority map is now a deep-pass version:
- Version: `tnio-source-authority-map-v2-deep`
- Size: 171,233 bytes

## What Changed
The source map now carries more than broad labels. For each source, it records:

- What topics the source is primary authority for
- What topics the source can support as secondary evidence
- What topics the source should avoid answering
- Important sections or tabs
- Content size and hashes
- Topic mention counts
- Representative samples

This should reduce cases where the bot answers a rules or eligibility question from a roster, tracking sheet, random table row, or loosely related source.

## High-Risk Overlap Areas Found
The deep pass found overlapping source coverage in several areas that can confuse retrieval:

- abilities
- asset registry
- beast policy
- beast roster
- character progression
- combat rules
- crafting policy
- crystal policy
- current offices
- droid policy

These areas now have stronger authority hints so the bot can prefer the correct class of source.

## Validation
I ran syntax and regression checks on `REDACTED_OPERATIONAL_HOST`:

```text
python3 -m py_compile lore_agent.py lore_mcp_server.py test_accuracy_policy.py test_corpus_accuracy.py
python3 test_accuracy_policy.py
python3 test_corpus_accuracy.py
```

All checks passed.

Restarted:

```text
lore-search-http.service
lore-discord-bot.service
```

Both services came back active.

Live endpoint checks passed for:

- Intel Sith joining rank
- current Minister of War and military Commandant
- military Captain destroyer ownership
- Sithspawn creation
- casual non-archive banter

## Practical Impact
The bot should now have a broader, more accurate understanding of the whole TNIO corpus, not just the small set of previously reported failures. The biggest improvement is source selection: policy questions should lean on guide/codex/progression authority, office questions should lean on current organizational references, story questions should lean on narrative records, and casual banter should avoid pulling random archive fragments.
