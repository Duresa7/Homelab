# NetBird/NPM Operational Follow-ups and Hardening Descope

**Created:** 2026-07-12  
**Last updated:** 2026-07-17

## Scope

Close the operator-approved autonomous follow-ups for the NetBird and Nginx Proxy Manager access stack on CT 107 `docker-network`, record the intentionally reduced hardening scope, and reconcile the platform records with that decision.

## Starting State

The access stack was operational with HTTPS publication, authenticated administration, controlled Compose restart recovery, first-peer enrollment, and the routed VPN path into Access-A already verified. Automated certificate renewal and bounded container logging remained to be validated and applied.

## Actions and Results

### 1. Automated Let's Encrypt renewal

NPM's `npm-1` lineage covers `*.REDACTED_CUSTOM_DOMAIN_001` and `REDACTED_CUSTOM_DOMAIN_001` and expires `2026-10-08 23:49:46 UTC`. The renewal configuration uses `authenticator = dns-cloudflare` and a stored credentials-file path, proving that token re-entry is not required. No credential contents were read.

NPM's running Node backend owns the observed schedule: `/app/internal/certificate.js` initializes a one-hour timer, checks immediately at startup, and processes Let's Encrypt certificates within 30 days of expiry. A Let's Encrypt staging run completed successfully for `/etc/letsencrypt/live/npm-1/fullchain.pem` with exit code `0`.

### 2. Bounded Docker logging

Per-service Compose logging was chosen instead of a Docker daemon default because the requirement covered only the three access-stack containers. This avoided restarting the host Docker daemon and interrupting unrelated containers while keeping the limit explicit beside each owned service. The live Compose files now specify the `json-file` driver with `max-size: "10m"` and `max-file: "3"` for:

- `netbird-server`
- `netbird-dashboard`
- `nginx-proxy-manager`

Both Compose projects passed `docker compose config --quiet` before and after application. `docker compose up -d` recreated only the affected project containers, and Docker inspection returned the expected settings on all three containers. The NetBird loopback bindings, UDP 3478 publication, private/external network memberships, persistent volume, and NPM fixed address remained intact.

### 3. Post-change upstream refresh

Immediate verification found the host routing peer's Management channel returning HTTP `502` while direct HTTP, HTTPS, NPM health, and Signal checks passed. NPM had been recreated before NetBird and Nginx retained the pre-recreation `netbird-server` address, which had been reassigned to `netbird-dashboard`. After `nginx -t` succeeded, a non-disruptive Nginx reload refreshed service-name resolution. The original failure check then returned both Management and Signal connected. This sequencing issue is recorded in the [NetBird troubleshooting log](../Troubleshooting-Log.md#11-npm-retained-a-stale-netbird-upstream-address-after-recreation).

## Descope Decision

The operator retained log rotation and directed the agent to complete only work that could be finished end-to-end without human intervention. The resulting dispositions are:

| Item | Disposition | Reason |
|---|---|---|
| Verify automated Let's Encrypt renewal | Completed | Non-interactive DNS-01 staging renewal and scheduler verification were agent-runnable |
| Bounded logging for NPM and NetBird | Completed | Targeted Compose changes and health verification were agent-runnable |
| Nested `.claude/settings.local.json` ignore rule | Completed | Narrow repository hygiene correction |
| CT 107 reboot recovery | Descoped | Requires a disruptive maintenance window |
| Restrict NPM administrative port 81 | Descoped | Requires operator confirmation of the approved management path and carries lockout risk |
| Reconcile stale saved NPM credential | Descoped | Live login works; the password-manager record requires operator-held account knowledge |
| Console-password recovery | Descoped | `REDACTED_USER_001` was completed by the operator; remaining root work requires human handling |
| Image pinning and version-review cadence | Declined | The operator chose to remain on `latest` |
| Protected backups and restore testing | Declined | The operator chose not to implement them |
| Certificate-lifecycle, service, endpoint, and health monitoring | Declined | The operator chose not to implement monitoring |
| External reachability / ingress-NAT decision | Resolved | The service is internal-only with no WAN ingress |
| Tighten `Peers → Access-A` policy | Descoped | Production source groups and ports require operator definition |

Runbook recovery and update guidance remains as neutral reference material. Dated evidence and historical troubleshooting facts were not rewritten.

## Rollback Points

- For logging, restore the prior NetBird values (`max-size: "500m"`, `max-file: "2"`) and remove the NPM `logging` block, validate each Compose project, then recreate the affected services. The temporary live rollback copies used during application were removed only after successful verification; the before-state diff is retained in S02 evidence.
- The Nginx upstream refresh changed no persistent configuration. If a reload introduced a proxy fault, restart the existing NPM container from its unchanged Compose project and repeat `nginx -t` plus endpoint validation.
- The renewal work was read-only against live certificate state. The staging dry-run did not replace the production certificate and therefore requires no certificate rollback.
- After commit, the documentation and Mission Control changes can be reverted through version control without changing live service state.

## Verification Performed

- `certbot certificates` reported lineage `npm-1`, the intended wildcard/apex identifiers, and expiry `2026-10-08 23:49:46 UTC`.
- Safe renewal-config inspection showed `dns-cloudflare` and the credential path without reading its contents.
- Source and process inspection showed NPM's live Node backend initializes an hourly renewal timer and checks certificates within 30 days of expiry.
- `certbot renew --dry-run --no-random-sleep-on-renew` completed against Let's Encrypt staging with `Congratulations, all simulated renewals succeeded` and exit code `0`.
- Both Compose projects passed configuration validation before and after application.
- Docker inspection returned `max-size=10m` and `max-file=3` for all three containers.
- NPM returned `healthy`; `nginx -t` succeeded.
- Direct dashboard and identity-provider probes returned HTTP `200`.
- NPM-to-NetBird dashboard and identity-provider probes returned HTTP `200`.
- Internal DNS resolved `REDACTED_CUSTOM_DOMAIN_016` to `192.168.85.2`, and the HTTPS endpoint returned HTTP `200`.
- After the upstream-address refresh, `netbird status` returned both `Management: Connected` and `Signal: Connected`, with the Access-A network still advertised.
- Temporary live Compose rollback copies were removed after successful validation.

## Step Evidence

| Step | Evidence | Verification result |
|---|---|---|
| Renewal verification | [S01 renewal transcript](../../Evidence/Operational%20Follow-ups%20-%202026-07-12/Logs/S01-Lets-Encrypt-Renewal-Verification-2026-07-12.md) | Non-interactive DNS-01 path and hourly NPM scheduler confirmed; staging renewal succeeded |
| Bounded Docker logging | [S02 logging transcript](../../Evidence/Operational%20Follow-ups%20-%202026-07-12/Logs/S02-Bounded-Docker-Logging-2026-07-12.md) | Compose validated and 10m × 3 applied to all three containers |
| Post-change service health | [S03 health transcript](../../Evidence/Operational%20Follow-ups%20-%202026-07-12/Logs/S03-Post-Change-Health-and-Upstream-Refresh-2026-07-12.md) | Stale upstream diagnosed and refreshed; Management/Signal connected and all HTTP checks passed |
