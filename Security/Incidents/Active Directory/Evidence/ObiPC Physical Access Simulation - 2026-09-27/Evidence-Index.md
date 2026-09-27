# ObiPC Physical Access Simulation Evidence

**Created:** 2026-09-27  
**Last updated:** 2026-09-27

I collected this evidence for [ASU-AD-20260927-001](../../ObiPC%20Physical%20Access%20Simulation%20-%202026-09-27.md), an authorized physical-access sign-in exercise. I kept the review window fixed at 2026-09-24 8:11:43 AM through 2026-09-27 8:11:43 AM EDT.

## Collection Register

| Artifact | Collection and result | Use |
|---|---|---|
| [Event review](Exports/Event-Review.json) | `OBIPC`, SSH Manager server `obipc`; 2026-09-27 8:21:07 AM EDT; exit code 0, empty stderr | All 22 selected failed-event records with unique record IDs, 1,416 successful events aggregated by account and logon type, empty human-success and other-security-event lists |
| [State readback](Exports/State-Readback.json) | Same target and transport; 2026-09-27 8:21:29 AM EDT; exit code 0, empty stderr | Log boundaries, audit settings, console-user readback, last boot and zero matching Terminal Services session events |
| [Collection failures](Exports/Collection-Failures.json) | Two rejected combined queries on 2026-09-27 before the successful collection; exact attempt times not retained; exit code 1 | Exact rejected command, empty stdout and `The command line is too long.` stderr; splitting the query resolved the transport limit |
| [SHA-256 manifest](SHA256SUMS.txt) | Generated after writing the three JSON artifacts | Detects subsequent changes to these exported files |

The JSON artifacts carry the exact command issued. The successful artifacts hold selected fields after identity substitution, not complete stdout or a terminal transcript. The failure artifact preserves the observed command rejection. I have not reconstructed a missing raw transcript or original EVTX file.

## Method and Verification

I queried Security events 4624, 4625, 4778, 4801, 1102 and 4719 using explicit start and end bounds, with no maximum-event cap. I parsed named XML fields rather than positional message text. The event query returned matching records and completed successfully. The separate Terminal Services query handles a no-matching-events result explicitly and fails on other event-query errors.

I grouped all 4624 events by account and logon type, then selected types 2, 7, 10, 11, 12 and 13 for the human-session check. I excluded `DWM-*`, `UMFD-*`, `SYSTEM`, `LOCAL SERVICE` and `NETWORK SERVICE` from that human-only selection while retaining their successful-event counts. I preserved all failed events in the selected window rather than filtering failures to the expected identities.

I reconciled the 4624 category counts to 1,416 and verified 22 distinct failed-event record IDs. The repeated query agreed with the initial investigation. The state readback independently established retention boundaries and current effective auditing. Source event and capture timestamps remain UTC in the JSON; the report and this register use Eastern time.

I replaced personal identities with their existing publication aliases before writing files. The SSH virtual service identity is represented by its role, `sshd service account`. Event record IDs are local log sequence numbers, not directory object identifiers. I preserved those IDs for correlation.

## Provenance and Limits

I first checked ObiPC at 2026-09-27 8:11:42 AM EDT. That connection generated two type-3 `local-obipc` events and one SSH-service type-5 event inside the fixed window. Subsequent collection connections occurred after its end. I made no intentional endpoint configuration changes, but live collection necessarily leaves authentication and execution records.

The initial network-logon inspection identified `sshd` as the logon process for `local-obipc`; a lookup on `HQ-DC01` resolved the other network identity to enabled account `svc-action1-deploy`. No separate file capture was retained for those initial checks. The retained event export independently preserves that service account's 68 type-3 events.

My confirmation that I conducted an authorized test is first-person context recorded in the report, not an endpoint artifact. The logs cannot establish who entered a name, whether a supplied password was correct, or the exact physical action behind each event.

I did not acquire raw EVTX files, disk or memory images, or a step-by-step exercise transcript. I did not create a snapshot or backup. SHA-256 checks establish the integrity of the sanitized exports from this point forward; they do not authenticate the endpoint's original logs or supply forensic chain of custody before collection.

