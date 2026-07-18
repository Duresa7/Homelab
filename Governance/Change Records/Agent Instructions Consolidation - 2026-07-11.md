# Agent Instructions Consolidation - 2026-07-11

**Created:** 2026-07-11  
**Last updated:** 2026-07-15

## Scope

Restructure the mirrored agent instruction files (`CLAUDE.md` and `AGENTS.md` at the workspace root) to remove duplication with the [Documentation Standard](../Documentation-Standard.md) and the root [README](../../README.md), and to make the standard the single source of truth for documentation rules.

## Starting State

- `CLAUDE.md` and `AGENTS.md` were identical (verified by hash) but had grown to roughly 230 lines / 2,400 words across 15 sections.
- Large portions restated the Documentation Standard nearly verbatim: documentation tiers, evidence and step rules, troubleshooting record content, filename dating, `Created`/`Last updated` metadata, folder growth, and backlog management.
- The Enterprise Categories table restated the README workspace map.
- Routing guidance was spread across four overlapping sections (Enterprise Categories, New-Work Routing Table, Ownership-Based Routing, Galaxy and UniFi Records), and platform layout across three (File Placement table, Minimum New-Platform Workflow, Platform Folder Model).
- Two rules existed only in the agent files: the incident report naming convention and required sections, and the SMART output storage convention.

## Actions

1. Moved the incident report naming convention and required content into a new `Incident Reports` section of the Documentation Standard, and the `smartctl` storage convention into its Evidence section, so no rule was lost when the agent files were slimmed.
2. Rewrote `CLAUDE.md` to hold only always-relevant agent guidance: remote access via the SSH Manager and UniFi Network MCPs, the documentation-is-part-of-done behaviors, one merged ownership routing table, one merged component/platform layout table, and the conventions that apply to every edit. Detailed documentation rules are now pointers to the Documentation Standard.
3. Corrected the MCP tool references (the previous `mcp__ssh_manager__*` / `mcp__unifi_network__*` prefixes did not match the actual tool names) to prefix-agnostic `ssh_*` / `unifi_*` forms.
4. Added a header note stating that `CLAUDE.md` and `AGENTS.md` are mirrored and must be edited together.
5. Copied `CLAUDE.md` over `AGENTS.md` to restore the mirror.

## Resulting Configuration

- `CLAUDE.md` / `AGENTS.md`: ~90 lines across 5 sections, with the Documentation Standard as the deferred reference for tiers, change-record content, step evidence, and incident format.
- `Governance/Documentation-Standard.md`: gained `Incident Reports` section and the SMART storage convention; now the single authoritative source for all documentation rules.

## Verification

- `Get-FileHash` on `CLAUDE.md` and `AGENTS.md` returned identical hashes after the rewrite.
- Confirmed every rule removed from the agent files exists in the Documentation Standard or the README workspace map; the incident and SMART conventions were the only rules without an existing home and were moved rather than deleted.

## Second Pass — Documentation Standard Single-Ownership

Later the same day, the Documentation Standard itself was pruned to complete the single-owner model. Decisions were confirmed interactively before enactment.

1. Adopted one-owner-per-rule between the standard and the agent instructions: the standard owns documentation depth, content, evidence, incidents, and file metadata; the agent instructions own workspace routing, component and platform layout, and backlog handling. A pointer line in the standard's Purpose section records the split.
2. Removed the standard's `Creating a New System or Service`, `Folder Growth`, and `Backlog Management` sections, whose rules are owned by the agent instructions.
3. Promoted `Troubleshooting Records` from an Evidence subsection to its own top-level section and removed its Chrome/1Password tool-usage sentence (agent tool behavior is owned by the agent instructions).
4. Merged duplicate statements inside `Step-Based Evidence`: the secrets/redaction rule stated twice in adjacent paragraphs, and the before/after pairing rule stated in both the policy paragraph and step list item 5.
5. Verified before cutting that the step evidence table requirement is live practice (the Galaxy Docker-Network LXC Deployment change record maintains a S01–S10 evidence table), so it was retained unchanged, and that no workspace links target the removed sections' anchors.

Result: the standard went from 9 sections (~103 lines) to 7 sections (~75 lines) with every remaining rule singly owned.

## Third Pass — 1Password CLI Agent Skill

Also on 2026-07-11, a cross-agent skill was created so both Claude Code and Codex know how to use the 1Password CLI safely, replacing knowledge previously scattered across platform troubleshooting logs.

1. Created `1password-cli` skill (SKILL.md with name/description frontmatter, compatible with both agents' skill formats) covering session checks and re-authentication, secret retrieval by `op://` reference without echoing values, safe usage in local and remote commands, item creation via stdin template, SSH key handling (1Password SSH agent for authentication, public-key retrieval, no private-key export), homelab conventions (account, `REDACTED_1PASSWORD_VAULT_002` vault, item naming), and the no-secrets-in-evidence guardrails. Content is drawn from the worked examples in the NetBird/NPM troubleshooting logs and S07 evidence.
2. Placed mirrored copies at `.agents/skills/1password-cli/SKILL.md` (Codex native discovery) and `.claude/skills/1password-cli/SKILL.md` (Claude Code native discovery), with a mirror note in the file.
3. Narrowed `.gitignore` from `.claude/` to `.claude/*` with `!.claude/skills/` so the skill mirror is version-controlled while local settings and cache stay ignored.
4. Updated the 1Password line in `CLAUDE.md`/`AGENTS.md` to point at the skill as the owner of the mechanics; re-mirrored and verified identical hashes.
5. Verified both skill copies have identical hashes.

Later the same day, promptless automation access was added. The operator created the `REDACTED_1PASSWORD_SERVICE_ACCOUNT` 1Password service account scoped to a single dedicated vault, `REDACTED_1PASSWORD_VAULT` (read/write; no access to any REDACTED_1PASSWORD_VAULT_002 vault; vault creation disabled), and stored its token as the `OP_SERVICE_ACCOUNT_TOKEN` user-scope environment variable without the value entering any transcript or repository file. Verification: `op whoami` reported `User Type: SERVICE_ACCOUNT` and `op vault list` returned only `REDACTED_1PASSWORD_VAULT`. The skill was updated to a dual-mode model — service-account automation mode by default, desktop-app interactive mode (Windows Hello) as the exception for other vaults — and re-mirrored with hashes verified.

The `REDACTED_1PASSWORD_ITEM_TITLE` item was then moved from the `REDACTED_1PASSWORD_VAULT_002` vault into `REDACTED_1PASSWORD_VAULT` via `op item move` in interactive mode. The move surfaced a pre-existing duplicate the operator had copied into the vault 18 hours earlier; an in-shell comparison confirmed identical credential values (only the boolean result was emitted), and the older copy was archived (reversible) to restore unambiguous retrieval by title. End-to-end verification as the service account: identity reported `SERVICE_ACCOUNT`, the item listed in `REDACTED_1PASSWORD_VAULT`, `op read` retrieved the 53-character credential promptlessly without displaying it, and the `REDACTED_1PASSWORD_VAULT_002` vault was confirmed invisible. The NetBird README and Runbook were updated to reference the new vault location; NPM documents name no vault and remain accurate.

Separately assessed the official 1Password MCP server (beta): the binary `onepassword-mcp.exe` is present in the installed desktop app (REDACTED_IPV4_115, MSIX), so setup is feasible via Settings > Labs, but the server manages 1Password Environments only and does not expose vault items or return secret values, so it does not replace the CLI for this workspace's credential retrieval needs. No MCP setup was performed.

## Fourth Pass — Work-Hierarchy Terminology and Step Rename

Also on 2026-07-11, the workspace's work-hierarchy vocabulary was settled through an interactive domain-modeling session and recorded in a new root glossary, [CONTEXT.md](../../CONTEXT.md):

- **Project** — a bounded effort with a definable done-state, listed in the root TODO; per-system TODO files are backlogs, and the root TODO heading was renamed from "Project Backlogs" to "System Backlogs" accordingly.
- **Plan** — the one document per project answering how, stored in the owning system's `Documentation/Change Plans/`.
- **Step** — the unit of planned work, numbered like a guide: `Step N` titled phases containing `Step N.M` instructions.
- **Checkpoint** — retired. The term (and the `CP` evidence-file prefix) previously meant a verified, evidence-bearing unit of executed work; the operator chose a full retroactive rename to step/`S` rather than a legacy note, consciously overriding the do-not-mass-rename convention for this one migration.

Retroactive rename executed:

1. 69 evidence files renamed via `git mv` (history preserved): NetBird `CPnn-*` → `Snn-*` (including `S05A`, `S07A`, and `S08A/S08B`) across `Logs/` and `Screenshots/`; Galaxy Corosync `Cluster-Net-Corosync-Link1-CP-nn-*` → `...-S-nn-*` across `Logs/`, `Exports/`, and `Screenshots/`. Zero CP-named files remain.
2. 60 files' contents updated by a scripted, word-boundary-safe replacement (`CPnn`→`Snn`, `CP-nn`→`S-nn`, checkpoint→step with case preserved), covering change records, evidence indexes, troubleshooting logs, build logs, READMEs, runbooks, TODOs, the JSON transcript metadata labels, and the HTML summary. Splunk build-log occurrences were reviewed first and confirmed to be this workspace's evidence concept, not Splunk's internal forwarder-checkpoint term.
3. The Documentation Standard's evidence section was rewritten as "Step-Based Evidence" with the hierarchical numbering convention and `S`-prefix evidence naming; all verification, transcript, and redaction requirements are unchanged.
4. `CLAUDE.md`/`AGENTS.md` and the `1password-cli` skill mirrors were transformed identically; all mirror hashes re-verified. Renamed evidence links spot-checked as resolving.

CONTEXT.md and this section deliberately retain the word "checkpoint" to document what was retired; no other current-vocabulary use remains.

Two refinements followed a review of the model against the working tree: the standard's Change Records section now requires decisions to be captured with their reasoning (why the chosen approach over the alternatives considered), and the glossary now requires a project's name to be reused verbatim across its TODO entry, plan filename, evidence folder, and change record. Splunk Enterprise's pre-standard flat evidence folder was reviewed and deliberately left unchanged as historical record.

## Rollback

Both files are tracked in git; restore the prior revision of `CLAUDE.md`, `AGENTS.md`, and `Governance/Documentation-Standard.md` to roll back.
