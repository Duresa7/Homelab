# TNIO Bot Full Accuracy Upgrade Report - 2026-05-13

**Created:** 2026-05-13  
**Last updated:** 2026-07-20

## Summary
I implemented the full accuracy-first upgrade for the TNIO Discord bot. This pass focused on making the bot choose the right class of source, prove factual TNIO answers from the corpus, avoid raw sheet/table dumps, preserve structured sheet data, and turn no-vote/abstain feedback into a reusable evaluation queue.

This was not a one-off hardcoded fix for one question. The upgrade adds reusable routing, verification, monitoring, and test coverage around the whole active corpus.

## Corpus And Evaluation Coverage
- Active bot manifest files: 45
- Drive files discovered by the runtime monitor: 45
- Missing active Drive files: 0
- Golden evaluation cases generated: 214
- Active manifest files covered by golden cases: 45 of 45
- Feedback queue items generated from no-vote/abstain logs: 19
- No-vote items: 16
- Abstain items: 3

## Key Runtime Changes
- Added a stronger final answer verifier in `lore_agent.py`.
- Added source authority alignment checks using the deep corpus source map.
- Added source conflict detection so the bot can flag when a weaker source is competing with a better authority source.
- Added stricter policy-question handling so guide/codex/progression sources beat rosters and tracking sheets.
- Added guards against "thin archives" / "not found" answers when retrieved evidence actually contains a direct rule.
- Added guards against raw sheet/table fragments such as `Column A`, `Row`, `Sheet`, or copied separator tables in final Discord answers.
- Added specific verification for the Intel/Sith joining issue so the answer must include the Apprentice requirement when the evidence supports it.
- Tightened session-context use so fresh questions do not inherit stale previous topics.
- Improved casual/persona routing so messages like `beep`, `beep boop`, or `bot` do not pull random archive records.

## Structured Sheets
Sheet rows are now preserved with structured metadata instead of only plain text:

- `headers_json`
- `row_fields_json`
- `chunk_type`
- `sheet_title`
- `row_number`
- `row_primary`

The HTTP/source compaction path now carries those fields forward into agent evidence. This lets the bot interpret rows as records instead of copying sheet internals into Discord.

## New Scripts And Artifacts
Added:

- `build_golden_eval_suite.py`
- `test_golden_eval_suite.py`
- `run_golden_eval_suite.py`
- `build_feedback_eval_queue.py`
- `drive_change_monitor.py`

Generated on `<YOUR_TNIO_HOST>`:

- `/home/<YOUR_DEPLOYMENT_USER>/lore-rag/state/tnio_golden_eval_suite.json`
- `/home/<YOUR_DEPLOYMENT_USER>/lore-rag/state/feedback_eval_queue.jsonl`
- `/home/<YOUR_DEPLOYMENT_USER>/lore-rag/state/feedback_eval_summary.json`
- `/home/<YOUR_DEPLOYMENT_USER>/lore-rag/state/drive_change_report.json`

## Discord Logging Improvements
The Discord bot now logs more evidence with each agent answer:

- verifier blocked status
- verifier reasons
- targeted retry use
- roster attempted for policy question
- source conflict issues
- clarification asked
- whether session context was used

No-vote and abstain reactions continue to be captured and can now be converted into the structured feedback evaluation queue.

## Live Smoke Tests
Live `/agent-answer` checks passed after restart for:

- `what rank do I need to join Intel as a sith`
  - Correctly answered Apprentice from `Intel Faction Guide`.
- `Who is the current Minister of War and the current Commandant of the military?`
  - Correctly used `Know Your Empire`.
- `As a military Captain, how many droids can I own, and how many functions can each one have?`
  - Correctly used `TNIO Master Engineers: Droid Codex`.
- `What saber forms has Grand Moff Harik mastered?`
  - Correctly used `Saber Mastery and Combat Form Tracking`.
- `beep boop`
  - Correctly routed as persona, not archive retrieval.
- `Who is the current Minister of War?` with unrelated old Darth-comparison session context
  - Correctly ignored stale session context and answered from `Know Your Empire`.

## Live Golden Evaluation
Added a runnable live golden evaluator:

```text
python3 run_golden_eval_suite.py --priority P0 --offset <n> --limit <n>
```

The live evaluator checks:

- required answer facts
- required source titles when explicitly known
- forbidden source titles
- forbidden answer fragments
- raw sheet/table metadata leaks
- final verifier blocked status

All **26 P0 golden cases** passed live after the final fixes. The P0 pass exposed additional reusable source-routing gaps, which were fixed before completion:

- combat dice/HP rank stats now route directly to `TNIO Dice Roll System`
- guild faction-slot limits now route directly to `TNIO Guild Rules`
- Emperor, Emperor's Voice, Sphere of War, Sith Academy, and Praetorian Legion office questions now route directly to `Know Your Empire`
- Sith progression and MoG questions now route directly to `Character Progression in The New Imperial Order`
- Beastmaster point-cap questions now route directly to `Beastmaster's Log`

The agent-answer cache namespace was bumped to `v34` so stale persisted answers from before these fixes cannot mask the new behavior.

The HTTP server now quietly handles client disconnects during long-running live evaluations, preventing evaluator timeouts from producing noisy `BrokenPipeError` stack traces.

## Verification
Passed on `<YOUR_TNIO_HOST>`:

```text
python3 -m py_compile lore_agent.py lore_mcp_server.py sync_lore.py build_feedback_eval_queue.py build_golden_eval_suite.py drive_change_monitor.py test_accuracy_policy.py test_corpus_accuracy.py test_golden_eval_suite.py
python3 -m py_compile lore_http_server.py run_golden_eval_suite.py
node --check discord-bot/bot.js
python3 test_accuracy_policy.py
python3 test_corpus_accuracy.py
python3 test_golden_eval_suite.py
python3 build_feedback_eval_queue.py
python3 build_golden_eval_suite.py
python3 run_golden_eval_suite.py --priority P0 --offset 0 --limit 8 --max-seconds 20
python3 run_golden_eval_suite.py --priority P0 --offset 8 --limit 8 --max-seconds 20
python3 run_golden_eval_suite.py --priority P0 --offset 16 --limit 8 --max-seconds 20
python3 run_golden_eval_suite.py --priority P0 --offset 24 --limit 8 --max-seconds 20
python3 drive_change_monitor.py
```

Services restarted and came back active:

```text
lore-search-http.service
lore-discord-bot.service
```

## Practical Impact
The bot now has a measurable accuracy system around the corpus instead of relying on individual fixes after each bad answer. It still cannot guarantee every future phrasing will be perfect, but it now has stronger source selection, better table interpretation, final-answer blocking, feedback-driven evaluation, and Drive-change monitoring to keep improvements systematic.
