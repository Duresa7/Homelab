# Nginx Proxy Manager Troubleshooting Log

**Created:** 2026-07-11  
**Last updated:** 2026-07-18

I record NPM-specific operational problems here. My authoritative cross-system narrative for the initial `docker-network` deployment is the [NetBird troubleshooting log](../../Netbird/Documentation/Troubleshooting-Log.md).

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

## 3. Saved NPM API Credential Returned HTTP 400

**Date:** 2026-07-11  
**Step:** S07

**Symptom:** An API authentication attempt using the saved NPM administrator credential returned HTTP `400` with `Invalid email/password` after I had already created the current administrator account in the browser.

**Failed attempt:** I treated the stored value as stale immediately. I did not print the password, retain it in a command transcript, copy it into repository content, or use it for repeated login attempts.

**Root cause:** The saved credential did not match the current NPM administrator account. I did not attempt to overwrite the account I had created or infer a replacement password.

**Corrective action:** I stopped the API-login path and used the already authenticated Chrome session for the certificate and proxy-host configuration. The stale saved record is a password-manager concern I own personally and is outside this platform's tracked work.

**Verification:** Certificate creation, proxy-host assignment, Force SSL, HTTP/2, authenticated NetBird access, and post-restart validation all completed without depending on the stale API credential.

**Status:** Deployment unblocked; live administrator login works, and reconciliation of the stale saved record is out of scope.

## 4. Browser Clipboard Transfer and 1Password Re-authentication

**Date:** 2026-07-11  
**Step:** S07

**Symptom:** The browser controller's Copy action did not populate the Windows clipboard with the newly created Cloudflare token. A safety check observed an empty or implausibly short value and aborted before creating a 1Password item. The 1Password CLI session also required re-authentication before I could update protected storage.

**Failed attempt:** No token value was sent to the shell, printed in output, written to a temporary repository file, or captured in evidence. I did not retry the invalid clipboard path with weaker validation.

**Root cause:** The controlled browser copy operation and the operating-system clipboard were not sharing the expected state, while my existing 1Password CLI authorization was no longer valid for the write operation.

**Corrective action:** I re-authenticated the 1Password CLI, then transferred the token through a non-echoing secure input path and stored it in 1Password as `REDACTED_1PASSWORD_ITEM_TITLE_002`; I verified only the item name and non-secret metadata.

**Verification:** The named 1Password item is available, NPM used the credential to complete the Cloudflare DNS-01 challenge, and repository and evidence scans contain no token value.

**Status:** Resolved.
