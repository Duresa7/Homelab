# Fleet Artifact Sweep Evidence

**Created:** 2026-07-29  
**Last updated:** 2026-07-29

I retain the bounded command and readback results for the [Fleet Artifact Sweep execution record](../../Maintenance/Fleet%20Artifact%20Sweep%20Execution%20-%202026-07-29.md) here. I normalized multiline tool output into host-labelled records and excluded credentials, private keys, certificate contents, and personal metadata.

| Artifact | What it demonstrates |
|---|---|
| [S01-before-state.log](Logs/S01-before-state.log) | The 16 active root filesystems used 366,920,134,656 bytes before cleanup, package caches held 10,239,652,176 bytes, and `grey-server` was at 75 percent. |
| [S02-cleanup-results.log](Logs/S02-cleanup-results.log) | Cache and journal cleanup reached all active machines, Docker pruning stayed bounded, and inspected deployment residue was removed without touching retained recovery material. |
| [S03-kasm-acceptance.log](Logs/S03-kasm-acceptance.log) | Kasm retained 23 image IDs, launched `Terminal - Normal` without a pull, and returned to eight control-plane containers after the disposable session was deleted. |
| [S04-final-verification.log](Logs/S04-final-verification.log) | The final root-use measurements, container counts, Proxmox quorum and firewall state, and Prometheus 48-of-48 result passed. |
| [S05-local-validation.log](Logs/S05-local-validation.log) | Both retained scripts passed shell syntax, the Mission Control harness passed 1,140 checks, and no temporary Kasm credential file remained. |
| [S06-follow-up-verification.log](Logs/S06-follow-up-verification.log) | The recorded results held up against live state, and four remaining files came off: the `security-01` installer bundle with all four Wazuh services still active, and three `grey-server` files with the cluster CA, driver signing, quorum, and firewall all intact. |

The cleanup calls produced verbose package, journal, and Docker deletion output that the calling tools bounded in their responses. These files retain the exact measured values and exit results available after the calls without inventing omitted lines.

S02 and S04 record the state at capture time. Where S06 disagrees with them, S06 is the later fact: the `security-01` installer bundle that S02 lists as retained came off during the follow-up.
