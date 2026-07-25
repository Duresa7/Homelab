# TNIO Librarian

**Created:** 2026-05-13  
**Last updated:** 2026-07-20

**Model identity:** `<YOUR_ORG_NAME>` United `Alpha-Echo-TNIO-Lore Model`  
**Interface:** TNIO Discord server  
**Source of truth:** TNIO Google Drive archive

## What I Built

I built the TNIO Librarian to answer Discord questions from the TNIO archive. It searches Google Docs and Sheets, chooses a source based on the question type, drafts an in-universe answer, cites the source, & blocks answers that fail its verification checks.

The bot handles three request classes:

- Archive questions use retrieval and source verification.
- Ambiguous factual questions trigger a clarification request.
- Casual messages stay in character without pulling unrelated archive records.

## Request Path

```text
Discord question
      |
      v
Intent and topic routing
      |
      v
Google Drive archive retrieval
      |
      v
Source-authority ranking
      |
      v
Answer draft and verification
      |
      v
Discord answer with source titles
      |
      v
No-vote or abstain review queue
```

## Archive Coverage

The active corpus contains 45 Docs and Sheets covering:

- guild rules;
- character and faction progression;
- military, Intelligence, Inquisition, Sith, droid, starship, beast, dice, & combat rules;
- current offices and rosters;
- character records;
- storyline records;
- ledgers and registries stored in Sheets.

The Librarian doesn't rank every record equally. Current-office questions prefer organizational references. Progression questions prefer progression records. Ship and droid questions prefer their codices. Faction-slot questions prefer Guild Rules. Story questions prefer narrative records. Rosters remain valid for membership questions but don't override a direct policy source.

## Answer Constraints

The verifier rejects an answer when it detects one of these conditions:

- a policy answer relies only on a roster or tracking row;
- a direct rule source was retrieved but a weaker source won;
- the response says the archive lacks an answer that appears in the retrieved text;
- raw Sheet labels such as `Column A` or `Row` leak into the response;
- stale conversation context changes the topic;
- the cited source doesn't support the factual claim.

Sheets enter retrieval with headers, row fields, sheet title, row number, & a primary row label. The answer uses those fields as one record instead of pasting the raw table into Discord.

## Discord Behavior

The Librarian answers in a concise Imperial archive voice. Factual answers include source titles. Casual messages don't need citations.

The bot records two feedback reactions:

- no-vote for an incorrect answer;
- abstain for a partly correct or uncertain answer.

`build_feedback_eval_queue.py` converts those reactions into review cases. I use the resulting queue to distinguish source-selection errors, source-reading errors, vague answers, ambiguous questions, voice problems, & genuine archive gaps.

## Evaluation

The generated suite contains 214 cases across all 45 active corpus files. It checks required facts, required or forbidden sources, forbidden answer fragments, raw Sheet-field leaks, and final verifier state. On 2026-05-13, all 26 P0 cases passed against the live `/agent-answer` endpoint.

Drive monitoring compares the active manifest with the current archive. When a file changes, the sync rebuilds the local corpus and source map; the evaluation artifacts can then be regenerated against the new version.

## Current Limits

- The archive wording and Drive text extraction still bound answer quality.
- Conflicting source records require authority ranking and may still need leadership review.
- A passing evaluation covers the recorded cases, not every future phrasing.
- The Google Drive archive remains authoritative when the bot and source disagree.
