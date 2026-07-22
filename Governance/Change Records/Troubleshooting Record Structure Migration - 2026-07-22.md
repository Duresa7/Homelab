# Troubleshooting Record Structure Migration

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Date:** 2026-07-22  
**Status:** Complete

## Scope

I replaced every combined `Documentation/Troubleshooting-Log.md` with a `Documentation/Troubleshooting/` folder. Each folder now has an undated `README.md` index and one dated Markdown file per issue.

## Starting State

Eleven infrastructure and platform owners kept 44 issues in combined troubleshooting logs. Links from runbooks, TODOs, build logs, change records, incidents, guides, and owner READMEs targeted those files or their heading anchors.

## Actions

1. I split the 44 issue sections into separate records without removing their investigation notes, findings, commands, or status history.
2. I created an index for each of the 11 troubleshooting folders.
3. I changed issue-specific references to target the new issue files directly.
4. I changed general troubleshooting references to target the applicable folder index.
5. I updated the workspace instructions and [Documentation Standard](../Documentation-Standard.md) so future issues use the same structure.

## Decisions

- I use `<Issue Name> - YYYY-MM-DD.md` for issue records. The date is the investigation date when the source identifies one; otherwise, it is the first retained date in the issue.
- I keep `README.md` undated because it is a living index.
- I keep one issue per file so a repair can be linked, updated, reviewed, or retired without changing unrelated troubleshooting history.
- I preserve incidents as separate records under `Security/Incidents/` and cross-link the applicable troubleshooting issue.

## Resulting Configuration

The workspace has 11 troubleshooting folders, 11 indexes, and 44 dated issue records. No active Markdown link uses the retired `Troubleshooting-Log.md` path.

## Verification

- I compared all 44 migrated issue bodies with the combined logs and confirmed that every retained line remains after the expected heading, path, and link-label changes.
- I confirmed that each troubleshooting folder contains one `README.md` index.
- I confirmed that every new Markdown file has one H1 plus `Created` and `Last updated` metadata.
- I checked relative Markdown links in every changed or new file and confirmed that their local targets exist.
- I compared `AGENTS.md` and `CLAUDE.md` after the instruction update and confirmed that they remain identical.

No separate terminal transcript was retained. The file moves, new records, link changes, and standard changes are visible in the Git diff for this migration.

## Rollback

Git can restore each deleted combined log and remove the corresponding troubleshooting folder. A rollback must also restore the old inbound links and the prior troubleshooting rule in the workspace instructions and Documentation Standard.

## Remaining Work

None. New troubleshooting issues should be created as dated records and added to the owning folder's `README.md` index.
