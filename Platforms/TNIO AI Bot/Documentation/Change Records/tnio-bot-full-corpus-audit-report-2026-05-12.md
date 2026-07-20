# TNIO Corpus Authority Audit - 2026-05-12

**Created:** 2026-05-12  
**Last updated:** 2026-07-20

## Result

I compared all 45 active Drive files with the 45-file bot manifest, then added source-authority, policy, alias, & evaluation artifacts to the runtime.

Using the local Google Drive connector, I confirmed the TNIO folder holds 45 active Docs/Sheets. The bot manifest on `<YOUR_TNIO_HOST>` also has 45 active files, 3666 chunks, and 5061 records from the same folder ID, so the main issue was not missing Drive coverage. The issue was source selection: policy questions could still be answered from rosters, registries, generic sheet rows, or nearby but wrong sections.

## Audit Files

I generated a local audit set from the TNIO folder: a corpus inventory, a source-authority map, policy cards, an entity-alias map, and an evaluation-question set. These fed the runtime artifacts I added to the bot below.

Connector notes:

- Verified local connector listing against the TNIO folder: 45 files.
- Fetched and inspected `Intel Faction Guide`, `Know Your Empire`, & `TNIO Imperial Intelligence Roster`.
- `TNIO Master Engineers: Starship Codex` and `TNIO Master Engineers: Droid Codex` returned 403 on local text export, so their already-synced bot exports were used only for those content gaps.

## Runtime State Added

I added these runtime artifacts to `/home/<YOUR_DEPLOYMENT_USER>/lore-rag/state/`:

- `tnio_source_authority_map.json`
- `tnio_policy_cards.json`
- `tnio_entity_alias_map.json`
- `tnio_eval_questions.json`

These tell the bot which archive shelf is authoritative for each kind of question, and which sources should be avoided for policy answers.

## Bot Code Changes

I updated `/home/<YOUR_DEPLOYMENT_USER>/lore-rag/lore_agent.py`:

- Added corpus-artifact loading.
- Added source authority routing for policy, roster/current office, story, profile, ownership, progression, ability, combat, engineering, faction, and casual/persona questions.
- Policy questions now strongly prefer guides, codices, rulebooks, progression records, and policy tables.
- Roster, tracking, registry, character-profile, and raw ability-sheet rows are penalized for policy questions unless they are the right source class.
- Added artifact-based targeted retry calls when first retrieval does not contain a proper authoritative source.
- Added artifact hints from curated aliases like Ghost, Racer, Moon, Sharps, Beastarius, Rakkos, Erebus, Harik, Kujan, and Operation Bastion.
- Added stronger direct source-backed answers for Sithspawn creation so it uses Sithspawn Alchemy plus the relevant Sith Alchemy 2/3 ability rows instead of random Force ability rows.

I updated `/home/<YOUR_DEPLOYMENT_USER>/lore-rag/lore_mcp_server.py`:

- Bumped `/agent-answer` cache key from `v31` to `v32` so old wrong cached answers do not survive the routing upgrade.

I added `/home/<YOUR_DEPLOYMENT_USER>/lore-rag/test_corpus_accuracy.py`.

## Verification

Passed on `<YOUR_TNIO_HOST>`:

- `python3 -m py_compile lore_agent.py lore_mcp_server.py test_accuracy_policy.py test_corpus_accuracy.py`
- `python3 test_accuracy_policy.py`
- `python3 test_corpus_accuracy.py`

Restarted only:

- `lore-search-http.service`
- `lore-discord-bot.service`

Both services are active.

Live `/agent-answer` checks:

- `what rank do I need to join Intel as a sith` -> correct Apprentice/Candidate answer from `Intel Faction Guide`.
- `As a military Captain, how many droids can I own, and how many functions can each one have?` -> correct 7 registrations / 3 functions from `TNIO Master Engineers: Droid Codex`.
- `As a military Captain can I own a Destroyer?` -> correct Captain ceiling and Destroyer threshold from `TNIO Master Engineers: Starship Codex`.
- `Who is the current Minister of War and the current Commandant of the military?` -> correct Colonel Ghost / Colonel Racer from `Know Your Empire`.
- `What do I need to do to reach Darth status?` -> correct Road to Darth / MoG path from `Character Progression in The New Imperial Order`.
- `tell me about operation bastion in detail` -> correct Operation Bastion recap from `TNIO-Storyline-Narative`.
- `How can I create a sithspawn?` -> correct Sithspawn Alchemy answer from `Praetorian Legion Specializations Codex` plus Sith Alchemy 2/3 rows.
- `beep boop` -> persona response, no random beast-codex retrieval.

## Limits

This changed retrieval and verification, not model weights. Questions now route by topic and source class in addition to keyword overlap.

The bot still depends on the quality of Drive text extraction and the wording in the source records. If source records conflict, the intended behavior is to prefer the more authoritative/current source type and log enough evidence for later no-vote/abstain review.
