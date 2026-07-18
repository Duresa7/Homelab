# REDACTED_PRIVATE_ORG_LABEL-Access Network — Reference

**Created:** 2026-07-12  
**Last updated:** 2026-07-17

Reference for the NetBird **Network** that routes overlay peers into the Access-A zone. This is dashboard-managed state (Network Routing → Networks), not an on-disk config file; it is recorded here for reproducibility. It was created and validated on 2026-07-12 — see the change record [NetBird First Peer and Routed VPN Path - 2026-07-12](../Documentation/Change%20Records/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12.md).

## Why Networks (not legacy Routes)

The Networks model is zero-trust by default — a resource is unreachable until an access policy grants it — which matches the homelab's zone-based, default-deny firewall posture. Legacy Network Routes grant unrestricted access once published and are retained by NetBird only for exit-node use, which does not apply here.

## Configuration

| Element | Value |
|---|---|
| Network | `REDACTED_PRIVATE_ORG_LABEL-Access` |
| Resource | `Access-a-subnet` — address `192.168.85.0/24`, resource group `access-a` |
| Access policy | `Peers → Access-A (VLAN 85)` — source group `All`, destination the Access-A resource, protocol/ports `ALL`, enabled |
| Routing peer | `docker-network` (CT 107, overlay `100.121.111.204`); Enable on, **Masquerade on**, metric `9999` |

## Behavior notes

- With masquerade enabled, traffic from a remote peer into Access-A is source-NAT'd to the routing peer's address (`192.168.85.2`). To the UniFi gateway it appears to originate inside the REDACTED_PRIVATE_ORG_LABEL-Access zone, so it is governed by that zone's rules — no separate gateway rule was required.
- Peers that receive the route install it into NetBird routing table `7120` on `wt0`; because `192.168.85.0/24` is more specific than a peer's default gateway, Access-A traffic prefers the overlay.
- The routing peer runs with `net.ipv4.ip_forward=1`. Access-A currently contains only CT 107, so forwarding to a second Access-A host is possible but not yet exercised.

## Policy Scope

The validation-broad access policy (`All` source, all protocols/ports) is intentional and is not currently scheduled to change. The 2026-07-12 [operational descope decision](../Documentation/Change%20Records/NetBird-NPM%20Operational%20Follow-ups%20and%20Hardening%20Descope%20-%202026-07-12.md) removed policy tightening from tracked work because production source groups and ports require operator definition.
