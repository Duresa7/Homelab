# TNIO Lore Bot — Structural Fixes Report

**Created:** 2026-05-11  
**Last updated:** 2026-07-17

- **Date:** 2026-05-11
- **Filename:** `tnio-bot-fixes-report-2026-05-11.md`
- **Author:** Claude (Opus 4.7)
- **Host:** `REDACTED_OPERATIONAL_HOST` (192.168.40.38, user `REDACTED_DEPLOYMENT_USER`, Ubuntu Plucky LXC)
- **Project root:** `/home/REDACTED_DEPLOYMENT_USER/lore-rag`
- **Backup stamp for everything touched:** `bak.structural-fix-20260511`

---

## 1. What was reported

> Discord bot using AI + Google Drive (TNIO folder) has been giving incorrect sources and weak answers. Not asking for cherry-pick fixes — wants structural improvements. Bot should also still handle friendly banter / off-archive questions.

## 2. System layout I confirmed

```
Discord  →  bot.js  ──HTTP POST /agent-answer──▶  lore_http_server.py (127.0.0.1:19731)
                                                    │
                                                    ▼
                                          lore_mcp_server.lore_agent_answer
                                                    │  (cache wrapper)
                                                    ▼
                                              lore_agent.agent_answer
                                                    │
                                ┌───────────────────┼─────────────────────┐
                                ▼                   ▼                     ▼
                           retrieve            sift (LLM judge)     archive_answer
                           (chunks +           ┗━ Codex via         (final LLM call)
                            records +            openclaw gateway
                            tool_calls)
```

- **LLM:** `openclaw infer model run --gateway --model openai-codex/gpt-5.4-mini` (verified working independently).
- **Embedder:** Ollama `qwen3-embedding:4b` on `127.0.0.1:11434`.
- **Vector store:** Chroma at `/home/REDACTED_DEPLOYMENT_USER/lore-rag/index/chroma`.
- **Drive sync:** `gws` CLI (`@googleworkspace/cli`) → `sync_lore.py --sync` on a 6-min systemd-user timer.
- **services:** `lore-discord-bot.service`, `lore-search-http.service`, `lore-rag-sync.timer`, `openclaw-gateway.service`, `ollama.service`.

## 3. Investigation summary

### Logs I mined

- `/home/REDACTED_DEPLOYMENT_USER/lore-rag/logs/agent-negative-feedback.jsonl` — 18 user-flagged bad answers
- `/home/REDACTED_DEPLOYMENT_USER/lore-rag/logs/agent-requests.log` — 409 recent agent requests
- `journalctl --user -u openclaw-gateway.service` — found `Context overflow: prompt too large for the model (precheck)` errors and `lane wait exceeded` diagnostics
- `journalctl --user -u lore-rag-sync.service` — confirmed sync had been failing since 18:50 UTC today

### Failure pattern breakdown (from 18 negative-feedback cases)

| Symptom | Count | Cause |
|---|---:|---|
| `sift_skipped_reason: "llm_error"` with `kept_ids: []` | 8 | LLM sift call errored (context-overflow or timeout); code returned **all 22 candidates unchanged** to the answerer |
| `sift_skipped_reason: "low_budget" / "small_pool"` | 3 | Sift skipped, candidates passed through unranked |
| Cache mismatch served wrong answer in `~3ms` | 2 | High-confidence cached answer about previous topic re-served for new question |
| Other (weak retrieval, prose vs. table) | 5 | Mixed |

### Sync auth failure

`gws` was throwing `invalid_grant: Token has been expired or revoked`. Sync had been failing silently since 18:50 UTC — only visible if you ran `systemctl --user status lore-rag-sync.service`. Nothing in the bot, no alert.

## 4. Root causes (4 distinct)

1. **Google Drive OAuth token revoked.** Sync stalled → index frozen at 2026-05-11 18:44 UTC. Failure was silent.
2. **`sift_candidates` fail-open behaviour** in `lore_agent.py`. Every error/skip path returned the unchanged candidate pool (up to 22 candidates × 1800-char excerpts ≈ 40KB → blew the model's context budget and produced more `llm_error` next round). The answerer then cited junk.
3. **Cache poisoning.** `lore_mcp_server.lore_agent_answer` only excluded `best_effort` from caching. Wrong-source answers at `confidence: "high"` or `"medium"` were cached for the full TTL, serving repeat-bad-responses in ~3 ms.
4. **No visibility into sync failures.** The wrapper script `sync_and_maybe_restart.sh` swallowed stderr from `sync_lore.py`.

## 5. Changes applied

All edits are atomic Python text replacements with backups stamped `.bak.structural-fix-20260511`. Both Python files pass `py_compile`.

### 5.1 `lore_agent.py` — sift robustness

- **Added** `_deterministic_topk(candidates, k=12)` — score-sort helper using:
  1. `match_type` (`direct_*` / `term_sweep` first)
  2. `relevance_score` desc
  3. `section` length asc
- **All 9 sift skip/error paths now return `_deterministic_topk(sift_pool)` instead of the raw pool**:
  - `small_pool`
  - `low_budget` (pre- and post-prompt)
  - `llm_error`
  - `empty_response`
  - `no_json`
  - `bad_shape`
  - `json_parse_error`
  - `empty_keep`
  - `rejected_all_passthrough`
- **Sift input capped at 16 candidates** (was 22), with dynamic excerpt size:
  - 1200 chars when `len(sift_pool) >= 12`
  - 1600 chars otherwise
  - Result: 16 × 1200 ≈ 19 KB of candidates — safe headroom under the model's prompt budget, preventing the context-overflow that was driving `llm_error`.
- **Pre-sift hard cap in `agent_answer` reduced from 22 → 16.**
- The `sifted = [row for i, row in enumerate(...)]` enumerate target switched from `candidates` to `sift_pool` so successful-sift indices line up with the new capped pool.

### 5.2 `lore_mcp_server.py` — cache safety

- **Cache-key namespace bumped** `agent-answer::v28::` → `agent-answer::v29::`. Instantly invalidates every poisoned entry.
- **Cache acceptance gate** rewritten. The old gate only excluded `best_effort`. The new gate refuses to cache when **any** of these is true:
  - `response["best_effort"]` (cold-start template)
  - `response["confidence"] == "low"` (answerer itself flagged low trust)
  - `evidence["candidate_count"] in (0, None)` (nothing retrieved)
  - `evidence["sift"]["skipped_reason"]` in `{"llm_error", "empty_response", "no_json", "bad_shape", "json_parse_error", "rejected_all_passthrough"}` (sift was unreliable)
- **Persisted on-disk cache cleared:** `state/agent_answer_cache.json` moved aside to `state/agent_answer_cache.json.bak.structural-fix-20260511` so the bumped namespace doesn't reload stale entries on restart.

### 5.3 `sync_and_maybe_restart.sh` — sync visibility

Rewrote with these changes:

- Writes `state/sync_status.json` on every run:
  ```json
  {
    "last_run_ts": 1778528561,
    "last_result": "ok" | "auth_failure" | "error",
    "detail": "<last 8 lines of sync output, truncated>",
    "consecutive_failures": <int>,
    "last_success_ts": <int|null>
  }
  ```
- Emits **`::SYNC_AUTH_FAILURE::`** on stderr when the sync output contains `invalid_grant` / `expired or revoked` / `authError`, so the failure is greppable in `journalctl --user -u lore-rag-sync.service`.
- Emits `::SYNC_FAILURE::` for non-auth errors.
- Still triggers `systemctl --user restart lore-search-http.service` when the corpus version actually changes.

### 5.4 Re-auth Google Drive (gws)

Walked through SSH-port-forward of the OAuth callback so the consent flow could complete from the user's PC against the headless LXC. Authentication succeeded for account `REDACTED_EMAIL_001` with the full default scope set (drive, sheets, gmail.modify, calendar, documents, presentations, tasks, pubsub, cloud-platform, openid, userinfo.email, userinfo.profile).

## 6. Files touched on the server

| File | Change | Backup |
|---|---|---|
| `/home/REDACTED_DEPLOYMENT_USER/lore-rag/lore_agent.py` | Sift fallback, pool cap, excerpt size | `lore_agent.py.bak.structural-fix-20260511` |
| `/home/REDACTED_DEPLOYMENT_USER/lore-rag/lore_mcp_server.py` | Cache key v29, acceptance gate | `lore_mcp_server.py.bak.structural-fix-20260511` |
| `/home/REDACTED_DEPLOYMENT_USER/lore-rag/sync_and_maybe_restart.sh` | Status file, auth-failure marker | `sync_and_maybe_restart.sh.bak.structural-fix-20260511` |
| `/home/REDACTED_DEPLOYMENT_USER/lore-rag/state/agent_answer_cache.json` | Moved aside (poisoned) | `agent_answer_cache.json.bak.structural-fix-20260511` |

New file (created by first wrapper run): `/home/REDACTED_DEPLOYMENT_USER/lore-rag/state/sync_status.json`.

## 7. Verification

### Service health after restarts

```
lore-search-http.service     active
lore-discord-bot.service     active
openclaw-gateway.service     active
lore-rag-sync.service        success (rc=0)
```

### Smoke tests via `POST http://127.0.0.1:19731/agent-answer`

1. **"can you tell me who is on the council?"** — previously cited *Codex to the Beasts of the Galaxy* 3×. Sift hit `llm_error: TimeoutExpired` again, **but the new `score_sort` fallback returned 12 ranked candidates**. Answer now correctly cites Grand Council (Darth Aiterian Revik), Jedi Council roster (Aamaw, Bren, Sella Delles, Kuso Ni, Rohu), Green Jedi Council (Adan Tal). `evidence.sift.fallback == "score_sort"`, `output_count: 12`.
2. **"Who is the current Minister of War and the current Commandant of the military?"** — previously a 3 ms cache hit returning the wrong answer about "strongest Darth". After v29 namespace bump + cache file moved aside: served a fresh response (`cached: None`). Answer was `confidence: low`, so the new gate correctly refused to cache it (no future poisoning of this question).
3. **"hey, what is up dude?"** — banter routed to `mode: persona`, `retrieval: persona`. No bogus archive citations.

### Sync verification

After re-auth and manual `systemctl --user start lore-rag-sync.service`:

```json
{
  "last_run_ts": 1778528561,
  "last_result": "ok",
  "detail": "before=9d37aea703538e3d8b67 after=9d37aea703538e3d8b67",
  "consecutive_failures": 0,
  "last_success_ts": 1778528561
}
```

New corpus version: `9d37aea703538e3d8b67`. The 6-min sync timer continues unattended.

## 8. Operational notes / follow-ups

- **No action needed now:** `lore_agent.py.bak.*` and `lore_mcp_server.py.bak.*` files (~80 of them, from prior cherry-pick cycles) are still in the directory. Safe to prune older than today after confirming nothing references them — purely a tidying exercise, not a correctness issue.
- **If you want to monitor sync health from elsewhere:** read `/home/REDACTED_DEPLOYMENT_USER/lore-rag/state/sync_status.json` — `consecutive_failures > 0` or `last_success_ts` older than ~1 hour means Drive content may be stale.
- **If `llm_error` rate stays high under load** (visible as `evidence.sift.skipped_reason: "llm_error"` in `agent-requests.log`), the next structural lever is the `openclaw-gateway` lane queue — `journalctl` shows `lane wait exceeded: waitedMs=17311 queueAhead=0` events. That's the agent serializing on a single Codex session lane. Increasing lane concurrency (or running planner/answerer/sift in distinct sessions) would let sift retry without starving the answer call. Out of scope for this round.
- **Long-term memory snapshot** (`state/memory/long_term_memory.{json,md}`) is from 2026-05-06; refresh weekly via the existing `lore-memory-build.timer` (next fire 2026-05-20).
- **Backup hygiene:** the `*.bak.structural-fix-20260511` files are the rollback target for everything in this change set. To revert a single file:
  ```
  cp /home/REDACTED_DEPLOYMENT_USER/lore-rag/<file>.bak.structural-fix-20260511 /home/REDACTED_DEPLOYMENT_USER/lore-rag/<file>
  systemctl --user restart lore-search-http.service lore-discord-bot.service
  ```

## 9. Quick reference — what the bot should now do better

| Question class | Before | After |
|---|---|---|
| Archive question, sift LLM happy | Correct, often | Correct (no regression) |
| Archive question, sift LLM errors out | **Wrong sources** (pass-through) | **Top-12 score-sorted, usually correct** |
| Repeated question that previously cached badly | **3 ms stale wrong answer** | **Fresh attempt every time** (until a *good* answer succeeds and passes the cache gate) |
| Friendly banter | Persona reply | Persona reply (no regression) |
| Drive content recently updated | Stale (silent auth fail) | Fresh on next 6-min sync, status file shows health |

---

# Round 2 — Real-world regression caught & fixed

## 10. What Round 1 missed

User reported that the bot, after Round 1 deployment, was **still** giving the wrong answer to *"can you tell me who is on the council?"* in Discord. The 19:44 UTC call cited `Inquisition Commemoratorii` + `Codex to the Beasts of the Galaxy` instead of the actual council documentation.

### Drill-down

Pulled the agent-reply-records entry for the 19:44 call:

- `pre_sift_count`: not recorded (older code path)
- `candidate_count`: 7
- `auto_sweep_terms`: `['council']` — single common word
- `sift`: succeeded normally and kept 7 of 16
- Cited sources: all wrong docs

Verified across `chunks.jsonl` that the actual authoritative docs for council content are **`Know Your Empire`**, **`Intel Faction Guide`**, **`TNIO Master Engineers: Starship Codex`**, and **`TNIO: Honor Guard Codex`** (its `GRAND COUNCIL` section). None of them appeared in the candidate pool at 19:44.

### True root cause (deeper than Round 1)

The candidate-merge loop was a plain `tool_rows + auto_sweep_rows + baseline_rows` append, capped at 16 at the end. When `_auto_sweep_terms` returned a single common word like `"council"`, `tool_term_sweep` produced 20+ literal-substring windows across half the corpus. Those rows filled the 16-slot cap **before baseline (Chroma semantic) retrieval could contribute a single row** — so the actual answer docs were never even considered.

Round 1's `_deterministic_topk` fallback couldn't fix this — it only re-orders what's already in the pool. The problem was at the merge stage, before the pool existed.

## 11. Round 2 changes

All under stamp `bak.structural-fix-r2-20260511` (agent) and `bak.structural-fix-r2b-20260511` (mcp).

### 11.1 `lore_agent.py` — per-source quota merge

Replaced the append-then-cap merge with a two-pass quota merge:

```python
quotas = [
    (sorted(tool_rows,        key=title_overlap_rank), 5),  # tool-driven
    (sorted(auto_sweep_rows,  key=title_overlap_rank), 6),  # literal hits
    (baseline_rows,                                    8),  # semantic
]
# Pass 1: each source gets up to its quota.
# Pass 2: fill leftover capacity from any source, preference order.
```

Effects:

- Baseline (semantic) retrieval is **guaranteed up to 8 slots** in every pool. The actual answer doc has a chance of appearing.
- Tool / auto-sweep rows are pre-ranked by `_title_overlap_score(question, title, hints)` so the best-titled candidate leads its quota.
- A single common-word `auto_sweep` term can no longer flood the pool.

### 11.2 `lore_agent.py` — tiered match-type ranking in `_deterministic_topk`

Round 1 had `_deterministic_topk` treating `term_sweep` matches as high-precision alongside `direct_*`. They aren't — `term_sweep` is just literal word match, the lowest-precision signal. Reordered:

| Tier | Match types | Notes |
|---:|---|---|
| 0 | `direct_*` | Hand-crafted exact matches |
| 1 | `structured_*`, `row` | Record / sheet rows |
| 2 | `keyword`, `list_records`, `section` | Section / record anchors |
| 3 | (unknown / baseline) | Chroma semantic |
| 4 | `term_sweep` | Literal word match — often noise |

Within each tier: `relevance_score` desc, then `section` length asc.

### 11.3 `lore_mcp_server.py` — tighter cache gate

Found that a high-confidence answer derived from only 5 candidates (`sift.skipped_reason == "small_pool"`) was getting cached, then served back even after services restarted. Two additions:

- `"small_pool"` added to the untrusted-sift set
- New independent floor: refuse to cache when `evidence.pre_sift_count < 8` (catches any thin-retrieval failure regardless of sift code path)
- Cache key bumped `v29 → v30`; persisted cache file moved aside again

## 12. Round 2 verification

Tests run via `POST /agent-answer`:

| Question | Result | Sources cited |
|---|---|---|
| "can you tell me who is on the council?" | **Correct**, conf `medium` | `TNIO: Honor Guard Codex - GRAND COUNCIL` (the right doc) |
| "Who is the current Minister of War and the current Commandant of the military?" | **Correct** — names Colonel Ghost + Colonel Racer | `TNIO-MD-01 The Imperial Military Faction`, `Know Your Empire` |
| "What are the minimum requirements for joining Inquisition as an NFU?" | **Correct** — Corporal in Imperial Military, then Sergeant pathway | `The Inquisition`, `Inquisitorius Specializations` |
| "hey what is up dude" | **Persona mode** (no archive citations) | — |

Beast Codex / Beast Trainers Codex no longer appears in cited sources for any council-style question.

## 13. Round 2 backup files

| File | Backup |
|---|---|
| `lore_agent.py` (R2 changes) | `lore_agent.py.bak.structural-fix-r2-20260511` |
| `lore_mcp_server.py` (R2 changes) | `lore_mcp_server.py.bak.structural-fix-r2b-20260511` |
| Persisted cache (poisoned again post-R1) | `state/agent_answer_cache.json.bak.structural-fix-r2b-20260511` |

Round 1 backups (`bak.structural-fix-20260511`) remain in place as the deeper rollback point — apply Round 1 first if reverting both rounds, otherwise the R2 patches will be redundant.

## 14. Lessons for future work

- **Cap-and-merge order matters.** A plain `A + B + C` then `[:N]` silently starves whichever source comes last when an upstream source produces more rows than the cap. Per-source quotas are the safe pattern.
- **Cache acceptance must mirror retrieval confidence.** "Confidence: high" from the answerer is necessary but not sufficient — the *retrieval* underneath also has to be trustworthy. `pre_sift_count` is a cheap floor.
- **Match-type precision tiers are worth being explicit about.** Treating `term_sweep` as direct was a subtle but harmful conflation; making the tiers explicit in code keeps future refactors honest.

---

# Round 2d — Leadership question routing

## 15. What was still missing after Round 2c

After Round 2c the bot found `TNIO Guild Rules - Grand Council (definition)` for "who's on the grand council?" but missed `Know Your Empire`, the doc that actually names the office-holders. User reported in Discord: *"the names are in know your empire"*.

### Drill-down

Direct probes against the corpus and the `/search` endpoint:

- `Know Your Empire Table 1` contains the exact roster: Darth Reken (Emperor), Darth Ar'cava Haethon (Emperor's Voice — MIA), Darth Kruea (Dark Councilor, Sphere of Philosophy), **Grand Moff Dorr'in Harik (Grand Councilor, Sphere of War)**, Darth Aiterian Revik (Dark Councilor, Sphere of Ancient Knowledge).
- Chroma semantic search for *"who is on the grand council members named"* returned 6 duplicates of `TNIO: Ministry War Forge Codex - Bounty Hunter's Guild Exclusives` at score 48, then `Mandalorian Enclave Codex`, then `TNIO Guild Rules`. **`Know Your Empire` never appeared in the top 10.**
- `_derive_source_hints("who's on the grand council")` returned `[]` — no routing rule.
- `auto_sweep_terms` produced `['council', 'grand council']` — but **member rows in Know Your Empire spell out *"Grand Councilor"* / *"Dark Councilor"*, not the body name *"Grand Council"***. The literal sweep missed those rows.

So the canonical roster doc was simultaneously:
- Not in baseline semantic top-10 (embedding similarity is dominated by "Grand" tokens elsewhere)
- Not in `_derive_source_hints` (no routing rule)
- Not caught by `term_sweep` (substring mismatch between body-name and role-name)

## 16. Round 2d changes

Under stamp `bak.structural-fix-r2d-20260511`.

### 16.1 `lore_agent.py` — leadership-question detector

Added `_LEADERSHIP_RE` regex + `_is_leadership_question(question)`. When the question matches words like *council*, *councilor*, *Grand Moff*, *Emperor*, *Emperor's Voice*, *Minister of …*, *Commandant*, *Keeper of Intelligence*, *High/Grand Inquisitor*, *head of*, *leader(ship)*, *in charge of*, *who is/are/leads/runs/rules/commands*, *Sphere of*:

- `_derive_source_hints` adds `"Know Your Empire"` as a hint
- If the question specifically mentions *grand council* or *honor guard*, also adds `"TNIO: Honor Guard Codex"`

This is deterministic routing, not LLM-dependent. Hints feed the title-overlap boost in the per-source quota merge, so the canonical doc reaches the candidate pool reliably.

### 16.2 `lore_agent.py` — org-role term variants in `_auto_sweep_terms`

`term_sweep("Grand Council")` only catches chunks where the literal phrase appears. Member rows say "Grand Councilor" instead. Added:

- `"grand council"` in question → also sweep `"Grand Councilor"`
- `"dark council"` → also sweep `"Dark Councilor"`
- `"sith council"` → also sweep `"Sith Council"`
- Any `\bcouncil(s)?\b` → also sweep `"Councilor"`

`term_sweep` now reaches the table rows that hold the actual names.

### 16.3 Cache invalidation

Persisted cache file moved aside (`agent_answer_cache.json.bak.r2d-20260511`) so the new hints take effect immediately for previously-cached questions. Cache key still at `v30`; bump not needed because hints/auto_sweep changes don't alter the key but the in-memory + persisted cache from the prior pool is what we cleared.

## 17. Round 2d verification

| Question | Conf | Sources cited |
|---|---|---|
| "who's on the grand council" | **high** | `Know Your Empire - Table 1`, `TNIO: Honor Guard Codex - Sentinel` |
| "who is the Emperor's Voice" | **high** | `Know Your Empire - Table 1`, `Know Your Empire - Table 1 / Row 3` |
| "who is the Minister of War" | **high** | `Know Your Empire - structured_record`, `Know Your Empire - Table 2 / Row 2` |
| "Inquisition NFU requirements" | **high** | `The Inquisition`, `Inquisitorius Specializations` (no regression) |
| "hey what is up dude" | **persona** | — (no regression) |

Sample correct answers:

- **Grand Council**: "*Darth Reken as Emperor, Darth Ar'cava Haethon as Emperor's Voice, Darth Kruea as Dark Councilor of the Sphere of Philosophy, Grand Moff Dorr'in Harik as Grand Councilor of the Sphere of War, and Darth Aiterian Revik as Dark Councilor of the Sphere of Ancient Knowledge*"
- **Emperor's Voice**: "*Darth Ar'cava Haethon, a Sith Pureblood female … currently MIA*"
- **Minister of War**: "*Colonel Ghost, a Chiss male*"

All three previously-broken leadership questions now return correct names from `Know Your Empire`.

## 18. Round 2d backup files

| File | Backup |
|---|---|
| `lore_agent.py` (R2d changes) | `lore_agent.py.bak.structural-fix-r2d-20260511` |
| Persisted cache (cleared again) | `state/agent_answer_cache.json.bak.r2d-20260511` |

To revert R2d alone: `cp lore_agent.py.bak.structural-fix-r2d-20260511 lore_agent.py && systemctl --user restart lore-search-http.service`. Round 1 and R2/R2b/R2c backups remain in place underneath for deeper rollbacks.

## 19. Additional lessons

- **Routing must be deterministic for canonical "who's who" docs.** Embedding similarity is unreliable when the question's salient tokens (e.g. "Grand") appear in many unrelated docs. A 5-line regex + hint-list beats hoping the embedder agrees.
- **Substring search misses role-suffix variants.** Body names ("Grand Council") and role names ("Grand Councilor") share the prefix but the suffix matters. When the user asks about the body, also search for the role.

---

# Round 3 — Source-map overhaul (data-driven cataloging)

## 20. Why this round

After Round 2d, leadership questions worked but only via a hand-coded regex + curated doc-title list. The user wanted a **general** improvement: the catalog should know what every Drive file is, what it covers, and which questions it answers — not just councils. And it must use **Google Drive as the source of truth** (no hand-curated catalog file).

Solution: build the catalog *from* Drive content via an LLM-enrichment pass, persist into `source_map.json`, and consult it during routing. Re-runs automatically whenever sync detects a corpus change.

## 21. Round 3 changes

All backups stamped `bak.structural-fix-r3-20260511` (initial) and `bak.r3fix-20260511` (post-fix for sheet/preservation).

### 21.1 New: `enrich_source_map.py`

Standalone script that:

1. Iterates every doc in `state/source_map.json`.
2. Reads its Drive export — `.txt` for Docs, `.json` for Sheets (sheets are flattened into prose by `_flatten_sheet_json`: tab name as heading + each non-empty row joined by `|`).
3. Builds a head+tail excerpt (≤ 6 KB) plus the headings list, hands it to `openai-codex/gpt-5.4-mini` via the openclaw gateway.
4. Asks for strict JSON: `description` (1-2 sentences), `topics` (5-12 tags), `key_entities` (5-20 proper nouns), `canonical_for` (subset of topics this doc owns).
5. Validates / sanitizes the response and merges back into the doc entry.
6. Rebuilds a top-level `topic_index: {topic: [doc_title, …]}` from all docs.

Per-doc `enrichment_hash` over `title + headings + file mtime/size` makes re-runs idempotent — only docs whose inputs changed get re-processed. Full pass takes ~10 min for 45 docs; subsequent runs only touch the changed ones.

### 21.2 `lore_source_map.py` — new topic_routes routing

Added two functions:

- **`topic_routes(question, limit=6)`** — for every key in `topic_index`, asks if the topic phrase matches the question (via `_topic_appears_in`: full-phrase match OR ≥2 significant-word overlap for multi-word topics). Returns docs ranked by `canonical_for-hits × 4 + topics-hits × 1 + authority`.
- **`topic_hint_titles(question, limit=4)`** — convenience wrapper returning just titles.

Also patched `build_source_map` to **preserve enrichment fields across rebuilds**. Without this, the next `sync_lore.py --sync` would wipe `description`, `canonical_for`, etc. The patched builder reads any prior `source_map.json`, carries those fields forward per doc, and rebuilds `topic_index` from the merged docs.

### 21.3 `lore_agent.py` — agent integration

Added `_topic_hint_titles(question, limit=4)` helper (wraps `lore_source_map.topic_hint_titles`). Inserted into `_derive_source_hints` as step 5b — after the existing source-map hints and before doc-title-keyword lookup. Any topic-canonical doc surfaces automatically; the Round 2d leadership regex stays as a high-precision override but is now mostly redundant for indexed topics.

### 21.4 `sync_and_maybe_restart.sh` — auto-enrichment

When the sync detects a corpus change, the wrapper now runs `enrich_source_map.py` *before* restarting `lore-search-http.service`. Result: any time Drive content changes, the catalog re-derives from the new content automatically. Drive remains the source of truth.

## 22. What ended up in `source_map.json`

After enrichment of all 45 docs (40 Google Docs + 6 Sheets — Beastmaster's Log, Imperial Mechanics Universal Registry, Inquisitorius Specializations, Master Ability List, Saber Mastery and Combat Form Tracking, TNIO Imperial Intelligence Roster — wait that's also 6 + 40 minus overlap):

- 45 docs with `description`, `topics_enriched`, `canonical_for`, `key_entities`
- 444 unique `topic_index` keys
- Examples of canonical routing:
  - *imperial leadership roster* → Know Your Empire
  - *grand council roster* → Know Your Empire
  - *military command structure* → Know Your Empire
  - *intelligence divisions* → Know Your Empire (with Intel Faction Guide as related)
  - *droid ownership* → Imperial Mechanics Universal Registry
  - *saber forms* → Master Ability List
  - *agent statuses / call signs / mia kia* → TNIO Imperial Intelligence Roster
  - *sphere of laws and justice* → The Inquisition
  - *grand council protection* → TNIO: Honor Guard Codex
  - *praetorian legion hierarchy* → Know Your Empire

Sheet content is now first-class: e.g. **Know Your Empire** carries the description *"An organizational reference guide for the Empire, listing leadership and key officers across the Grand Council, Imperial Military, Sith Academy, Intelligence, Praetorian Legion, and other auxiliary factions."*

## 23. Round 3 verification

All cited via topic_index after the run:

| Question | Sources cited | Notes |
|---|---|---|
| who's on the grand council | Know Your Empire Table 1 + Honor Guard Codex | Names Dorr'in Harik (Grand Councilor War), Kruea (Dark — Philosophy), Aiterian Revik (Dark — Ancient Knowledge) |
| who is the Emperor's Voice | Know Your Empire Table 1 / Row 3 | **Darth Ar'cava Haethon**, Sith Pureblood female, MIA |
| who is the Minister of War | Know Your Empire Table 2 / Row 2 | **Colonel Ghost**, Chiss male |
| Inquisition NFU requirements | The Inquisition + Inquisitorius Specializations | Corporal → Neophyte → Sergeant pathway |
| what saber forms can I learn | Saber Form Training Codex + Master Ability List | All 7 forms enumerated, with tier limits |
| tell me about beasts | Beast Codex + Beastmaster's Log + Trainers Codex | Per-rank point system explained |
| hey what is up dude | (persona) | No archive citations |

## 24. Round 3 backup files

| File | Backups |
|---|---|
| `lore_agent.py` | `.bak.structural-fix-r3-20260511` |
| `lore_source_map.py` | `.bak.structural-fix-r3-20260511`, `.bak.r3fix-20260511` |
| `enrich_source_map.py` (new) | `.bak.r3fix-20260511` |
| `sync_and_maybe_restart.sh` | `.bak.structural-fix-r3-20260511` |
| Persisted agent cache (cleared) | `state/agent_answer_cache.json.bak.r3-20260511`, `.bak.r3post-20260511` |

`enrich_source_map.py` is a new file (no original; backups are of the script itself across the sheet-flattener iteration).

## 25. Operational notes for Round 3

- **Re-running enrichment manually**: `/usr/bin/python3 /home/REDACTED_DEPLOYMENT_USER/lore-rag/enrich_source_map.py`. Honors `ENRICH_MAX_DOCS=N` if you want to limit. Logs at `logs/enrich-run.log`.
- **Inspecting the catalog**: every entry under `documents[*]` in `state/source_map.json` now has `description`, `topics_enriched`, `canonical_for`, `key_entities`. Top-level `topic_index` is the reverse lookup.
- **What happens when a Drive doc changes**: 6-min sync timer pulls Drive → `build_source_map` rebuilds with prior enrichment preserved by file id → if corpus version changed, `sync_and_maybe_restart.sh` runs `enrich_source_map.py` (only touches docs whose hash changed) → restarts `lore-search-http.service` so the new map takes effect. End to end fully automatic.
- **What happens when Drive auth fails**: the Round 1 visibility wrapper still fires (`::SYNC_AUTH_FAILURE::` in journal, `state/sync_status.json` updated). Enrichment is skipped because corpus didn't change.

## 26. Round 3 lessons

- **Don't curate the catalog by hand.** Have the LLM read each Drive doc and write its own metadata. As long as the corpus is the source of truth, the catalog regenerates whenever the corpus changes, and there's nothing to drift.
- **Preserve derived state across rebuilds.** Anything that takes >10 seconds per doc to recompute (LLM enrichment, embeddings, summaries) needs explicit preservation — otherwise a routine sync silently wipes it.
- **Sheets are first-class.** Don't feed raw spreadsheet JSON to a summarizer. Flatten to tab-headed pseudo-prose first; the summary quality is night-and-day better.
- **Token-overlap beats phrase-match for topic routing.** Real users won't say "grand council membership" — they'll say "who's on the grand council". Require ≥2 significant-word overlap, not the full topic phrase.
