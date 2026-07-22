# Unsaved Proxy-Host Modal Closed During Advanced Navigation

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Date:** 2026-07-11  
**Step:** S07

**Symptom:** The unsaved NetBird form contained the intended domain, `netbird-dashboard:80` upstream, WebSocket support, and common-exploit blocking. Navigating toward the Advanced configuration closed the modal before the host was persisted.

**Observed result:** No NetBird proxy host appeared in the Proxy Hosts table. I treated this as an unsuccessful attempt and did not claim a partial save.

**Root cause:** The initial host had not been persisted before the Advanced-navigation interaction. I did not establish the exact UI event that closed the modal, but saving the basic record first eliminated the failure and confirmed that no partial host had been created.

**Corrective action:**

1. Create and save the basic host.
2. Verify the host row exists.
3. Reopen the saved host.
4. Add [netbird-advanced-config.conf](../../Configuration/netbird-advanced-config.conf).
5. Run `nginx -t`, save, and validate every route.

**Verification:** The host reports Online. The applied Advanced field contains the complete 1,296-character configuration, `nginx -t` succeeds, and a Host-header request through NPM returns the NetBird dashboard with HTTP `200`. The wildcard/apex certificate is assigned, Force SSL and HTTP/2 are enabled, and the authenticated HTTPS dashboard remained available after Compose restart validation.

**Status:** Resolved.
