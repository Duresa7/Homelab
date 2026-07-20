# `<YOUR_ORG_NAME>`-Access Network Reference

**Created:** 2026-07-12  
**Last updated:** 2026-07-20

This is my reference for the NetBird **Network** that routes overlay peers into the Access-A zone. It is dashboard-managed state (Network Routing → Networks), not an on-disk config file; I record it here so I can rebuild it. I created and validated it on 2026-07-12; see the change record [NetBird First Peer and Routed VPN Path - 2026-07-12](../Documentation/Change%20Records/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12.md).

## Why Networks Instead of Legacy Routes

I built this on the Networks model because it is zero-trust by default: a resource is unreachable until an access policy grants it, which matches my zone-based, default-deny firewall posture. Legacy Network Routes grant unrestricted access once published and are retained by NetBird only for exit-node use, which does not apply here.

## Configuration

| Element | Value |
|---|---|
| Network | `<YOUR_ORG_NAME>-Access` |
| Resource | `Access-a-subnet`, address `192.168.85.0/24`, resource group `access-a` |
| Access policy | `Peers → Access-A (VLAN 85)`: source group `All`, destination the Access-A resource, protocol/ports `ALL`, enabled |
| Routing peer | `docker-network` (CT 107, overlay `100.121.111.204`); Enable on, **Masquerade on**, metric `9999` |

## Behavior notes

- With masquerade enabled, traffic from a remote peer into Access-A is source-NAT'd to the routing peer's address (`192.168.85.2`). To the UniFi gateway it appears to originate inside the `<YOUR_ORG_NAME>`-Access zone, so it is governed by that zone's rules; no separate gateway rule was required.
- Peers that receive the route install it into NetBird routing table `7120` on `wt0`; because `192.168.85.0/24` is more specific than a peer's default gateway, Access-A traffic prefers the overlay.
- The routing peer runs with `net.ipv4.ip_forward=1`. Access-A currently contains only CT 107, so forwarding to a second Access-A host is possible but not yet exercised.

## Policy Scope

The validation-broad access policy (`All` source, all protocols/ports) is intentional, and I have no current plan to change it. My 2026-07-12 [operational descope decision](../Documentation/Change%20Records/NetBird-NPM%20Operational%20Follow-ups%20and%20Hardening%20Descope%20-%202026-07-12.md) removed policy tightening from tracked work because I have not yet defined the production source groups and ports.
