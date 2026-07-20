# TNIO Corpus Coverage Audit - 2026-05-12

**Created:** 2026-05-12  
**Last updated:** 2026-07-20

## Result

I processed all 45 files in the active Drive manifest and rebuilt the source-authority artifacts. The run covered 1,397,014 exported characters, 1,780 Sheet rows, 7,370 nonempty cells, 138 mapped topics, & 34 source-overlap risks.

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

## Rebuilt Runtime State
The following files were rebuilt on `<YOUR_TNIO_HOST>` under `/home/<YOUR_DEPLOYMENT_USER>/lore-rag/state/`:

- `tnio_deep_source_audit.json`
- `tnio_source_authority_map.json`
- `tnio_topic_authority_map.json`
- `tnio_eval_questions.json`
- `tnio_deep_source_audit.md`

The resulting source-authority map is:
- Version: `tnio-source-authority-map-v2-deep`
- Size: 171,233 bytes

## Source Metadata
The source map now carries more than broad labels. For each source, it records:

- What topics the source is primary authority for
- What topics the source can support as secondary evidence
- What topics the source should avoid answering
- Important sections or tabs
- Content size and hashes
- Topic mention counts
- Representative samples

This should reduce cases where the bot answers a rules or eligibility question from a roster, tracking sheet, random table row, or loosely related source.

## Overlap Areas
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
I ran syntax and regression checks on `<YOUR_TNIO_HOST>`:

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

## Verified Outcome

Syntax and both regression suites passed, both services returned `active`, & five live endpoint checks returned the intended source class. Policy questions now prefer guides, codices, & progression records; office questions prefer organizational references; story questions prefer narrative records; casual messages avoid archive retrieval.
