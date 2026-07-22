# NPM Advanced Gear Dismissed the Proxy-Host Modal

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Date:** 2026-07-11  
**Step:** S07  
**Owner:** Nginx Proxy Manager

**Symptom:** I populated the NetBird proxy-host form with the intended domain, upstream dashboard container, WebSocket support, and common-exploit blocking. Selecting the gear control intended for Advanced configuration dismissed the modal.

**Observed result:** The Proxy Hosts page still showed no saved NetBird host. I did not claim or retain a partial proxy-host change.

**Root cause:** Not established. The interaction may have targeted a dismiss control or hit an NPM UI behavior that requires saving the basic host before editing Advanced settings.

**Corrective action:** I reopened the form and saved the basic proxy host first with upstream `http://netbird-dashboard:80`, Block Common Exploits, and WebSocket Support. After the Online host row appeared, I reopened it and applied the 1,296-character [checked-in advanced configuration](../../../Nginx%20Proxy%20Manager/Configuration/netbird-advanced-config.conf).

**Verification:** The proxy host reports Online, `nginx -t` succeeds, and a Host-header request through NPM returns the NetBird dashboard with HTTP `200`. The original modal issue is resolved. Later S07 work issued and assigned the Let's Encrypt certificate, enabled Force SSL and HTTP/2, and validated the HTTPS endpoint.
