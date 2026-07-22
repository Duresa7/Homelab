# NPM Retained a Stale NetBird Upstream Address After Recreation

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Date:** 2026-07-12  
**Step:** Operational follow-up / bounded logging

**Symptom and exact error:** Immediately after I recreated NPM and then recreated the NetBird containers to apply bounded logging, direct dashboard and identity-provider probes returned HTTP `200`, NPM was healthy, HTTPS returned `200`, and Signal was connected, but `netbird status` reported:

```text
Management: Disconnected, reason: rpc error: code = Unavailable desc = unexpected HTTP status code received from server: 502 (Bad Gateway)
```

**Investigation:** The failure reproduced for more than 90 seconds. NPM's proxy error log showed management and signal requests still being sent to `grpc://172.31.85.2:80`. Docker inspection showed that after recreation `172.31.85.2` belonged to `netbird-dashboard`, while `netbird-server` had moved to `172.31.85.3`. NPM had started before the NetBird recreation and Nginx retained the address it resolved at its earlier configuration load.

**Root cause:** Sequential recreation changed the dynamic NetBird container addresses after Nginx had resolved the service names. The Compose definitions and advanced proxy routes were correct; the loaded Nginx upstream address was stale.

**Corrective action:** I ran `nginx -t` successfully inside `nginx-proxy-manager`, then did a non-disruptive Nginx reload to refresh service-name resolution. I changed no Compose, network, port, or NetBird configuration.

**Verification:** The original `netbird status` check then returned both `Management: Connected` and `Signal: Connected`. Direct dashboard and identity-provider probes, NPM-to-NetBird probes, and the HTTPS client path all returned HTTP `200`; NPM remained `healthy`, and Docker inspection still showed `max-size=10m` and `max-file=3` on all three containers.
