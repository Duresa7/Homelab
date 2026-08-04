# Internal HTTPS Service Onboarding Evidence

**Created:** 2026-07-22  
**Last updated:** 2026-08-04

This evidence set supports the [change record](../../Documentation/Change%20Records/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22.md).

| Step | Artifact | Demonstrates |
|---|---|---|
| Step 1 | `Logs/S01-Recovery-Points-2026-07-22.md` | Verified backup paths, hashes, archive results, and the failed permission attempts. |
| Step 2 | `Logs/S02-Backend-Compatibility-Verification-2026-07-22.md` | Jellyfin, qBittorrent, Semaphore, Forgejo, Syncthing, Grafana, & Prometheus resulting settings and health. |
| Step 3 | `Logs/S03-UniFi-Readback-2026-07-22.md` | DNS record count, firewall policy IDs, exact source boundary, & zero WAN port forwards. |
| Step 4 | `Logs/S04-NPM-State-Readback-2026-07-22.md` | Textual before state, final 20-row database state, shared HTTPS controls, & Immich Advanced settings. |
| Step 4 | `Screenshots/S04A-NPM-Proxy-Hosts-2026-07-22.png` | Top of the NPM proxy-host inventory; new rows are Online and use Let's Encrypt. |
| Step 4 | `Screenshots/S04B-NPM-Proxy-Hosts-2026-07-22.png` | Middle of the NPM proxy-host inventory. |
| Step 4 | `Screenshots/S04C-NPM-Proxy-Hosts-2026-07-22.png` | Bottom of the NPM proxy-host inventory, including Wazuh. |
| Step 5 | `Logs/S05-Route-and-Restart-Verification-2026-07-22.md` | Internal DNS, redirects, TLS, public NXDOMAIN, controlled restart, `nginx -t`, route status, & zero 502/504 responses. |
| Step 6 | `Logs/S06-Backup-Removal-2026-07-22.md` | Exact deletion commands and final absence checks for all six project-created archives. |

The browser screenshot API doesn't render the mouse pointer. No cursor appears in the three captures.

I didn't copy credential-bearing command context into this evidence folder.
