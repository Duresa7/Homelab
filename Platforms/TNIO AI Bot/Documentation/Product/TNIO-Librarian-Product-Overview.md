# TNIO Librarian Product Overview

**Created:** 2026-05-13  
**Last updated:** 2026-07-15

## Product Name

**TNIO Librarian**

Powered by REDACTED_PRIVATE_ORG_LABEL United *Alpha-Echo-TNIO-Lore Model*.

## Short Description

The TNIO Librarian is an Imperial archive assistant for the TNIO Discord server. Members ask questions in Discord, and the Librarian answers using the TNIO Google Drive archive as its source of truth.

It is built to feel like an in-universe Imperial Librarian, not a generic helper. It can answer serious archive questions, handle rules and progression questions, cite its sources, and still respond naturally to light banter.

## Product Diagram

```text
TNIO Member in Discord
        |
        | asks a question or reacts to an answer
        v
Discord Librarian Bot
        |
        | shows typing/status reactions
        | sends the question into the archive system
        v
REDACTED_PRIVATE_ORG_LABEL United Alpha-Echo-TNIO-Lore Model
        |
        | understands the question
        | decides what kind of answer is needed
        | searches the right archive shelves
        v
TNIO Archive Knowledge Base
        |
        | Google Docs
        | Google Sheets
        | faction guides
        | codices
        | rosters
        | progression records
        | story records
        v
Answer Verification Layer
        |
        | checks source quality
        | blocks weak or unsupported answers
        | avoids raw sheet/table dumps
        v
Final Discord Answer
        |
        | in-character response
        | source list
        | accuracy reminder
        v
Feedback Loop
        |
        | no-vote reactions
        | abstain reactions
        | review queue for future improvements
```

## What The User Experiences

A member mentions the Librarian in Discord and asks a question.

The bot shows that it is working through Discord typing and status behavior. Once it has an answer, it replies in the channel with:

- a direct answer
- an Imperial Librarian tone
- source references
- a reminder to verify important information against the Google Drive archive

If the question is casual, such as a test message or light banter, the Librarian can answer in-character without pulling random archive records.

If the question is factual but unclear, the intended behavior is to ask for clarification instead of guessing.

## What The Product Is Trying To Solve

TNIO has a large archive spread across many documents and sheets. A member may ask a simple question, but the correct answer might live in a specific faction guide, codex, progression record, roster, or table.

The Librarian exists to reduce the need for members to manually search the full archive every time they need an answer.

The important goal is not just answering quickly. The important goal is answering from the right source.

## Source Of Truth

The TNIO Google Drive archive is the source of truth.

The archive includes:

- guild rules
- character progression records
- faction guides
- Sith records
- military records
- Intelligence records
- Inquisition records
- starship rules
- droid rules
- beast records
- dice and combat rules
- current office references
- character documents
- storyline and narrative records
- Google Sheets used as ledgers or registries

The Librarian does not treat every source equally. It tries to use the source that is most appropriate for the question.

For example:

- current office questions should come from organizational references
- progression questions should come from progression records
- ship questions should come from the Starship Codex
- droid questions should come from the Droid Codex
- faction-slot questions should come from Guild Rules
- roster questions should come from rosters or current office records
- story recap questions should come from story records

## How An Answer Is Made

The product follows a simple flow:

1. Read the member's question.
2. Decide whether it is an archive question, a casual message, or something the bot should not answer.
3. Identify the kind of archive answer needed.
4. Search the most relevant parts of the TNIO archive.
5. Prefer the strongest source type for that question.
6. Draft the answer in the Librarian's voice.
7. Check whether the answer is supported by the right evidence.
8. Send the final answer to Discord with sources.

This makes the Librarian more than a search box. It behaves more like an archive clerk that knows which shelf should answer which kind of question.

## Accuracy Behavior

The Librarian has an accuracy-first design.

It is supposed to avoid:

- answering a policy question from a random roster row
- using a loosely related document when a direct rule source exists
- saying the archive is thin when the answer is actually present
- copying raw spreadsheet columns into Discord
- letting an old conversation topic leak into a new question
- inventing a confident answer when the evidence is weak

When the archive evidence is not strong enough, the better behavior is to ask a useful clarifying question.

## Sheets And Tables

Some TNIO information lives in Google Sheets. Those sheets are not meant to be pasted raw into Discord.

The Librarian is designed to treat sheets as structured records. That means it should read the row, understand the fields, and turn them into a normal answer.

Example:

```text
Bad style:
Column A: Rank
Column B: Total Points
Row 5: Apprentice

Good style:
An Apprentice has a beast point cap of 10.
```

## Personality

The Librarian should sound like an Imperial archive official.

It should be:

- formal
- concise
- slightly severe when appropriate
- in-universe when possible
- practical when answering rules
- clear when the archive does not prove something

It should not sound like it is explaining backend systems to Discord users. It can cite sources, but it should not over-explain that it searched documents or sheets unless that helps the answer.

## Feedback System

Members can react to answers when something is wrong or partly wrong.

The product tracks:

- no-vote reactions for incorrect answers
- abstain reactions for partially correct or uncertain answers

Those reactions become a review queue. Later, the mistakes can be inspected to determine what went wrong:

- wrong source selected
- right source found but misread
- answer was too vague
- question was ambiguous
- personality issue rather than factual issue
- archive did not actually contain the answer

This turns Discord reactions into a practical improvement loop.

## Evaluation System

The product has a test suite built from the archive and known failure examples.

The goal is to keep improvements measurable. When the Librarian is changed, the evaluation system can check whether important questions still work.

The evaluation set covers:

- high-risk rules
- common progression questions
- source selection
- structured sheet answers
- no-vote and abstain examples
- known problem areas
- coverage across the active archive

This helps prevent the bot from getting better at one question while getting worse at another.

## Drive Change Awareness

The archive can change over time. New documents can be added, sheets can be edited, and rules can be updated.

The product includes a Drive monitoring concept so the system can tell when the known archive and the current Drive folder no longer match.

The intended product behavior is:

1. Detect archive changes.
2. Refresh the local archive understanding.
3. Update source maps and test coverage when needed.
4. Keep answers aligned with the current TNIO source of truth.

## Main Product Layers

```text
1. Discord Layer
   The member-facing bot.

2. Librarian Layer
   The in-character assistant powered by REDACTED_PRIVATE_ORG_LABEL United Alpha-Echo-TNIO-Lore Model.

3. Archive Layer
   The TNIO Google Drive documents and sheets.

4. Source Authority Layer
   The system that knows which archive source should answer which kind of question.

5. Verification Layer
   The system that checks whether the answer is supported before it reaches Discord.

6. Feedback Layer
   The no-vote and abstain review loop.

7. Evaluation Layer
   The test suite used to measure whether the Librarian is improving.
```

## What Makes It Different From A Normal Bot

A normal bot might search for matching words and answer from whatever appears first.

The TNIO Librarian is designed to be more careful:

- it distinguishes rules from rosters
- it distinguishes story records from policy records
- it understands that sheets are structured records
- it keeps a source authority map
- it tracks bad answers for later review
- it has a verification layer before sending factual answers
- it tries to preserve the Imperial Librarian identity in the final response

## Product Goal

The long-term goal is for TNIO members to treat the Librarian as the first place to ask archive questions.

The ideal outcome:

- members get faster answers
- leadership spends less time repeating rules
- sources remain visible
- wrong answers are logged and reviewable
- the bot improves from real Discord usage
- TNIO's archive becomes easier to use without losing authority or accuracy

## Current Product State

The product is active and usable.

It can answer from the current TNIO archive, cite sources, handle Discord feedback reactions, use structured archive knowledge, and run evaluations against known important questions.

It is not perfect and should not be treated as the final authority over leadership judgment. Its job is to make the archive easier to access and to provide source-backed answers that members can verify.

The Google Drive archive remains the final source of truth.
