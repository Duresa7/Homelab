# Nginx Proxy Manager Troubleshooting Log

**Created:** 2026-07-11  
**Last updated:** 2026-07-20

I record NPM-specific operational problems here. My authoritative cross-system narrative for the initial `docker-network` deployment is the [NetBird troubleshooting log](../../Netbird/Documentation/Troubleshooting-Log.md).

## Quick Index

| # | Step | Symptom | Resolution | Status |
|---:|---|---|---|---|
| 1 | S05 | First HTTP probe returned `000` during initialization | Automatic retry returned `200`; health became `healthy` | Resolved |
| 2 | S07 | Unsaved proxy-host modal closed during Advanced navigation | Saved the basic host first, then reopened it and applied Advanced configuration | Resolved |

## 1. First HTTP Probe Raced NPM Initialization

**Date:** 2026-07-10  
**Step:** S05

**Symptom:** The first request to the NPM administrative endpoint returned HTTP result `000` while the newly created container initialized.

**Hypothesis and test:** The container was still starting rather than permanently unavailable. My deployment loop retried the same endpoint while watching the built-in health status.

**Corrective action:** I made no configuration change. The retry loop let initialization complete.

**Verification:** The second endpoint request returned HTTP `200`; the built-in health check became `healthy`; ports 80 and 81 then returned `200`.

## 2. Unsaved Proxy-Host Modal Closed During Advanced Navigation

**Date:** 2026-07-11  
**Step:** S07

**Symptom:** The unsaved NetBird form contained the intended domain, `netbird-dashboard:80` upstream, WebSocket support, and common-exploit blocking. Navigating toward the Advanced configuration closed the modal before the host was persisted.

**Observed result:** No NetBird proxy host appeared in the Proxy Hosts table. I treated this as an unsuccessful attempt and did not claim a partial save.

**Root cause:** The initial host had not been persisted before the Advanced-navigation interaction. I did not establish the exact UI event that closed the modal, but saving the basic record first eliminated the failure and confirmed that no partial host had been created.

**Corrective action:**

1. Create and save the basic host.
2. Verify the host row exists.
3. Reopen the saved host.
4. Add [netbird-advanced-config.conf](../Configuration/netbird-advanced-config.conf).
5. Run `nginx -t`, save, and validate every route.

**Verification:** The host reports Online. The applied Advanced field contains the complete 1,296-character configuration, `nginx -t` succeeds, and a Host-header request through NPM returns the NetBird dashboard with HTTP `200`. The wildcard/apex certificate is assigned, Force SSL and HTTP/2 are enabled, and the authenticated HTTPS dashboard remained available after Compose restart validation.

**Status:** Resolved.

