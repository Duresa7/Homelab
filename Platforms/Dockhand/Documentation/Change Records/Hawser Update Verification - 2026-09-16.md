# Hawser Update Verification

**Created:** 2026-09-16  
**Last updated:** 2026-09-16

**Status:** Complete.  
**Update runs:** 2026-09-16, 4:15 AM Eastern.

I ran all six `hawser-updater` containers from Dockhand's authenticated container Start API, one host at a time. Each helper pulled `ghcr.io/finsys/hawser:latest`, applied its Hawser Compose service, printed its completion message, and exited with code 0. All six running agents match the pulled image and report 0.2.48, the [latest upstream release](https://github.com/Finsys/hawser/releases/tag/v0.2.48) when checked.

| Host | Updater exit | Agent version | Agent state | Recreated |
|---|---:|---|---|---|
| docker-network | 0 | 0.2.48 | Healthy, connected | No |
| monitor-01 | 0 | 0.2.48 | Healthy, connected | No |
| media-01 | 0 | 0.2.48 | Healthy, connected | No |
| alpha-prod-01 | 0 | 0.2.48 | Healthy, connected | No |
| security-01 | 0 | 0.2.48 | Healthy, connected | Yes |
| docker-blue | 0 | 0.2.48 | Healthy, connected | No |

No newer image was available. Compose recreated Hawser on security-01 with the same image ID; the other five agents retained their IDs and start timestamps. My first verification required unchanged agent IDs and therefore flagged security-01. I inspected the difference, confirmed only Hawser had been recreated, and verified its health and Dockhand connection. Recreating an agent is within this update operation; the application checks remain strict.

All application container IDs, image IDs, start timestamps, and running states on these six hosts remained unchanged. Each Dockhand environment connection test passed after its updater completed. The helpers are now stopped in `exited` state with code 0, ready to start again for a later update.

[Dockhand update results](../../Evidence/Hawser%20Update%20Verification%20-%202026-09-16/Exports/Dockhand-Update-Results.json) retain the updater times, exit codes, reported versions, and connection results. [Host verification](../../Evidence/Hawser%20Update%20Verification%20-%202026-09-16/Exports/Host-Verification.json) records application preservation, agent health, recreation, completion-log checks, and agreement with the pulled image. I retained these structured results rather than full terminal or container logs; no complete transcript is retained for these steps.

I made no Compose or updater-script changes and created no snapshot, backup, or host-side temporary file. This completes the live updater workflow test that remained unexercised in the [registry and agent cutover](Registry%20and%20Agent%20Cutover%20-%202026-09-15.md).
