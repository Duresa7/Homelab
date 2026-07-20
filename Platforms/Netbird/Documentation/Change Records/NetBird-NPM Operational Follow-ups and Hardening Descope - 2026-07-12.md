# NetBird/NPM Operational Follow-ups and Hardening Descope

**Created:** 2026-07-12  
**Last updated:** 2026-07-20

## Scope

I closed the certificate-renewal and Docker-logging follow-ups for the NetBird and Nginx Proxy Manager stack on CT 107. I also recorded which remaining hardening items I declined or deferred.

## Starting State

The access stack was operational with HTTPS publication, authenticated administration, controlled Compose restart recovery, first-peer enrollment, and the routed VPN path into Access-A already verified. Automated certificate renewal and bounded container logging remained to be validated and applied.

## Actions and Results

### 1. Automated Let's Encrypt renewal

NPM's `npm-1` lineage covers `*.<YOUR_BASE_DOMAIN>` and `<YOUR_BASE_DOMAIN>` and expires `2026-10-08 23:49:46 UTC`. The renewal configuration uses `authenticator = dns-cloudflare`. A Let's Encrypt staging run completed successfully for `/etc/letsencrypt/live/npm-1/fullchain.pem` with exit code `0`.

NPM's running Node backend owns the observed schedule: `/app/internal/certificate.js` initializes a one-hour timer, checks immediately at startup, and processes Let's Encrypt certificates within 30 days of expiry.

### 2. Bounded Docker logging

I chose per-service Compose logging instead of a Docker daemon default because the requirement covered only the three access-stack containers. This avoided restarting the host Docker daemon and interrupting unrelated containers while keeping the limit explicit beside each owned service. The live Compose files now specify the `json-file` driver with `max-size: "10m"` and `max-file: "3"` for:

- `netbird-server`
- `netbird-dashboard`
- `nginx-proxy-manager`

Both Compose projects passed `docker compose config --quiet` before and after application. `docker compose up -d` recreated only the affected project containers, and Docker inspection returned the expected settings on all three containers. The NetBird loopback bindings, UDP 3478 publication, private/external network memberships, persistent volume, and NPM fixed address all remained intact.

### 3. Post-change upstream refresh

My immediate verification found the host routing peer's Management channel returning HTTP `502` while direct HTTP, HTTPS, NPM health, and Signal checks passed. NPM had been recreated before NetBird and Nginx retained the pre-recreation `netbird-server` address, which had been reassigned to `netbird-dashboard`. After `nginx -t` succeeded, a non-disruptive Nginx reload refreshed service-name resolution. The original failure check then returned both Management and Signal connected. This sequencing issue is recorded in the [NetBird troubleshooting log](../Troubleshooting-Log.md#7-npm-retained-a-stale-netbird-upstream-address-after-recreation).

## Descope Decision

I kept log rotation and finished only the items I could take end to end in one sitting. The resulting dispositions are:

| Item | Disposition | Reason |
|---|---|---|
| Verify automated Let's Encrypt renewal | Completed | The DNS-01 staging renewal and scheduler check passed |
| Bounded logging for NPM and NetBird | Completed | The targeted Compose changes and service checks passed |
| CT 107 reboot recovery | Descoped | Requires a disruptive maintenance window |
| Restrict NPM administrative port 81 | Descoped | I need to confirm the approved management path first, and it carries lockout risk |
| Image pinning and version-review cadence | Declined | I chose to remain on `latest` |
| Backups and restore testing | Declined | I chose not to implement them |
| Certificate-lifecycle, service, endpoint, and health monitoring | Declined | I chose not to implement monitoring |
| External reachability / ingress-NAT decision | Resolved | The service is internal-only with no WAN ingress |
| Tighten `Peers → Access-A` policy | Descoped | I have not yet defined the production source groups and ports |

The runbook keeps recovery and update procedures even though those items aren't active backlog.

## Rollback Points

- For logging, restore the prior NetBird values (`max-size: "500m"`, `max-file: "2"`) and remove the NPM `logging` block, validate each Compose project, then recreate the affected services. I removed the temporary live rollback copies only after successful verification; the before-state diff is retained in S02 evidence.
- The Nginx upstream refresh changed no persistent configuration. If a reload introduced a proxy fault, restart the existing NPM container from its unchanged Compose project and repeat `nginx -t` plus endpoint validation.
- The renewal work was read-only against live certificate state. The staging dry-run did not replace the production certificate and therefore requires no certificate rollback.

## Verification Performed

- `certbot certificates` reported lineage `npm-1`, the intended wildcard/apex identifiers, and expiry `2026-10-08 23:49:46 UTC`.
- Renewal configuration inspection showed `authenticator = dns-cloudflare`.
- Source and process inspection showed NPM's live Node backend initializes an hourly renewal timer and checks certificates within 30 days of expiry.
- `certbot renew --dry-run --no-random-sleep-on-renew` completed against Let's Encrypt staging with `Congratulations, all simulated renewals succeeded` and exit code `0`.
- Both Compose projects passed configuration validation before and after application.
- Docker inspection returned `max-size=10m` and `max-file=3` for all three containers.
- NPM returned `healthy`; `nginx -t` succeeded.
- Direct dashboard and identity-provider probes returned HTTP `200`.
- NPM-to-NetBird dashboard and identity-provider probes returned HTTP `200`.
- Internal DNS resolved `<YOUR_NETBIRD_DOMAIN>` to `192.168.85.2`, and the HTTPS endpoint returned HTTP `200`.
- After the upstream-address refresh, `netbird status` returned both `Management: Connected` and `Signal: Connected`, with the Access-A network still advertised.
- I removed the temporary live Compose rollback copies after successful validation.

## Step Evidence

| Step | Verification result |
|---|---|
| Renewal verification | Non-interactive DNS-01 path and hourly NPM scheduler confirmed; staging renewal succeeded |
| Bounded Docker logging | Compose validated and 10m × 3 applied to all three containers |
| Post-change service health | Stale upstream diagnosed and refreshed; Management/Signal connected and all HTTP checks passed |
