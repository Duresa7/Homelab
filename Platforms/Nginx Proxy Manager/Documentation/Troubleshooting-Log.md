# Nginx Proxy Manager Troubleshooting Log

**Created:** 2026-07-11  
**Last updated:** 2026-07-12

NPM-specific operational problems are recorded here. The authoritative cross-system narrative for the initial `docker-network` deployment is the [NetBird troubleshooting log](../../Netbird/Documentation/Troubleshooting-Log.md).

## Quick Index

| # | Step | Symptom | Resolution | Status |
|---:|---|---|---|---|
| 1 | S05 | First HTTP probe returned `000` during initialization | Automatic retry returned `200`; health became `healthy` | Resolved |
| 2 | S07 | Unsaved proxy-host modal closed during Advanced navigation | Saved the basic host first, then reopened it and applied Advanced configuration | Resolved |
| 3 | S07 | Saved NPM API credential returned HTTP `400` | Used the existing authenticated browser session; live administrator login works | Deployment unblocked; stale password-manager record is outside platform scope |
| 4 | S07 | Browser copy did not populate the OS clipboard, and 1Password CLI required re-authentication | Aborted the invalid clipboard path, re-authenticated, and stored the token through a non-echoing secure path | Resolved |

## 1. First HTTP Probe Raced NPM Initialization

**Date:** 2026-07-10  
**Step:** S05

**Symptom:** The first request to the NPM administrative endpoint returned HTTP result `000` while the newly created container initialized.

**Hypothesis and test:** The container was still starting rather than permanently unavailable. The deployment loop retried the same endpoint while observing the built-in health status.

**Corrective action:** No configuration change was made. The retry loop allowed initialization to complete.

**Verification:** The second endpoint request returned HTTP `200`; the built-in health check became `healthy`; ports 80 and 81 then returned `200`. See the [S05 transcript](../../Netbird/Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Logs/S05-NPM-Deployment-2026-07-10.md).

## 2. Unsaved Proxy-Host Modal Closed During Advanced Navigation

**Date:** 2026-07-11  
**Step:** S07

**Symptom:** The unsaved NetBird form contained the intended domain, `netbird-dashboard:80` upstream, WebSocket support, and common-exploit blocking. Navigating toward the Advanced configuration closed the modal before the host was persisted.

**Observed result:** No NetBird proxy host appeared in the Proxy Hosts table. This was treated as an unsuccessful attempt; the deployment did not claim a partial save.

**Root cause:** The initial host had not been persisted before the Advanced-navigation interaction. The exact UI event that closed the modal was not established, but saving the basic record first eliminated the failure and confirmed that no partial host had been created.

**Corrective action:**

1. Create and save the basic host.
2. Verify the host row exists.
3. Reopen the saved host.
4. Add [netbird-advanced-config.conf](../Configuration/netbird-advanced-config.conf).
5. Run `nginx -t`, save, and validate every route.

**Verification:** The host reports Online. The applied Advanced field contains the complete 1,296-character configuration, `nginx -t` succeeds, and a Host-header request through NPM returns the NetBird dashboard with HTTP `200`. The wildcard/apex certificate is assigned, Force SSL and HTTP/2 are enabled, and the authenticated HTTPS dashboard remained available after Compose restart validation.

**Status:** Resolved.

## 3. Saved NPM API Credential Returned HTTP 400

**Date:** 2026-07-11  
**Step:** S07

**Symptom:** An API authentication attempt using the saved NPM administrator credential returned HTTP `400` with `Invalid email/password` after the current administrator account had already been created in the browser.

**Failed attempt:** The stored value was treated as stale immediately. No password was printed, retained in a command transcript, copied into repository content, or used for repeated login attempts.

**Root cause:** The saved credential did not match the current NPM administrator account. The deployment did not attempt to overwrite the user-created account or infer a replacement password.

**Corrective action:** The API-login path was stopped, and the already authenticated Chrome session was used for the certificate and proxy-host configuration. The stale saved record is an operator password-manager concern and is outside this platform's tracked work.

**Verification:** Certificate creation, proxy-host assignment, Force SSL, HTTP/2, authenticated NetBird access, and post-restart validation completed without depending on the stale API credential.

**Status:** Deployment unblocked; live administrator login works, and reconciliation of the stale saved record is out of scope.

## 4. Browser Clipboard Transfer and 1Password Re-authentication

**Date:** 2026-07-11  
**Step:** S07

**Symptom:** The browser controller's Copy action did not populate the Windows clipboard with the newly created Cloudflare token. A safety check observed an empty or implausibly short value and aborted before creating a 1Password item. The 1Password CLI session also required re-authentication before protected storage could be updated.

**Failed attempt:** No token value was sent to the shell, printed in output, written to a temporary repository file, or captured in evidence. The invalid clipboard path was not retried with weaker validation.

**Root cause:** The controlled browser copy operation and the operating-system clipboard were not sharing the expected state, while the existing 1Password CLI authorization was no longer valid for the write operation.

**Corrective action:** The 1Password CLI was re-authenticated. The token was then transferred through a non-echoing secure input path and stored in 1Password as `REDACTED_1PASSWORD_ITEM_TITLE_002`; only the item name and non-secret metadata were verified.

**Verification:** The named 1Password item is available, NPM used the credential to complete the Cloudflare DNS-01 challenge, and repository and evidence scans contain no token value.

**Status:** Resolved.
