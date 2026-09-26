# `AlphaSec-Galaxy` Network Reference

**Created:** 2026-07-12  
**Last updated:** 2026-09-25

This record captures the dashboard-managed NetBird **Network** that routes overlay peers into the homelab VLANs. I created it as `AlphaSec-Access` with a single Access-A resource on 2026-07-12 and later renamed and expanded it to `AlphaSec-Galaxy`; the original build steps are in [NetBird First Peer and Routed VPN Path](../Documentation/Change%20Records/First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12.md).

## Why Networks Instead of Legacy Routes

I built this on the Networks model because it is zero-trust by default: a resource is unreachable until an access policy grants it, which matches my zone-based, default-deny firewall posture. Legacy Network Routes grant unrestricted access once published and are retained by NetBird only for exit-node use, which does not apply here.

## Configuration

I checked this against the management store on 2026-09-04. The network was renamed and expanded after the original 2026-07-12 build, so the single-resource description that stood here until now was stale.

| Element | Value |
|---|---|
| Network | `AlphaSec-Galaxy`, "Routed access to homelab VLANs through the Access-A routing peer" |
| Routing peer | `docker-network` (CT 107, overlay `100.121.111.204`); Enable on, **Masquerade on**, metric `9999`. It is the only router on the network |
| Resources defined | 13: subnets for VLANs 10, 40, 60, 65, 70, 72, 80, 85, and 90, plus `/32` host resources for the grey, purple, blue, and red Proxmox nodes |
| Resource groups | `trusted`, `personal-a`, `secure-client`, `ad-servers`, `mgmt-a`, `security-a`, `servers-a`, `access-a`, `dmz-a`, `proxmox-nodes`, and the two scope groups `admin-scope` and `boss-scope` |
| Access policy | `Peers → Access-A (VLAN 85)`: source group `All`, destination the `Access-a-subnet` resource directly, protocol/ports `ALL`, enabled |

On 2026-09-25 I compared these resources with the current UniFi network list (read 2026-09-24) without rereading the NetBird store. The VLAN 90 subnet and the `dmz-a` group point at DMZ-A, a network I deleted; DMZ is now VLAN 30, which has no resource. The `ad-servers` group holds the VLAN 65 subnet, which is now IDENTITY-A. MONITOR-A (VLAN 73) has no resource. None of this changes reach, because only the Access-A resource is granted.

### Only one resource is actually reachable

Twelve of the thirteen resources are enabled but no policy names them or their groups, and the Networks model is default-deny, so they are unreachable. `netbird status` on the routing peer confirms it: the peer installs `Networks: 192.168.85.0/24` and nothing else.

The `Admin Users --> Security Machines` policy looks like it covers VLAN 72, but its destination is the peer group `Security-A`, not the resource group `security-a` that holds the `192.168.72.0/24` subnet. The two groups have names that differ only in case. That policy grants nothing today.

This is not currently a problem: Nginx Proxy Manager sits at `192.168.85.2` inside the one reachable subnet and proxies all 23 internal application names from there, so the single granted resource covers every published application.

### No DNS is distributed to peers

The account's overlay DNS domain is `netbird.selfhosted`, which gives peers names like `docker-network.netbird.selfhosted`. Beyond that:

- No nameserver groups exist, so `netbird status` reports `Nameservers: 0/0 Available`.
- No NetBird DNS zones or records exist.
- `Routing peer DNS resolution` is enabled in account settings, but it only resolves domain-type resources, and every resource here is a subnet or host. It changes nothing.

UniFi holds the local A records that map the 24 `alphasecunited.com` names (23 applications plus NetBird) to `192.168.85.2`, and UniFi only answers on the LAN. A remote peer therefore reaches Nginx Proxy Manager by address but cannot resolve the names, so `https://jellyfin.alphasecunited.com` fails off-LAN even though the route to the proxy works. Closing that gap means adding a NetBird nameserver group for `alphasecunited.com` pointing at the UniFi resolver, or hosting the records as a NetBird DNS zone.

## Route Behavior

- With masquerade enabled, traffic from a remote peer into Access-A is source-NAT'd to the routing peer's address (`192.168.85.2`). To the UniFi gateway it appears to originate inside the `AlphaSec-Access` zone, so it is governed by that zone's rules; no separate gateway rule was required.
- Peers that receive the route install it into NetBird routing table `7120` on `wt0`; because `192.168.85.0/24` is more specific than a peer's default gateway, Access-A traffic prefers the overlay.
- The routing peer runs with `net.ipv4.ip_forward=1`. Access-A currently contains only CT 107, so forwarding to a second Access-A host is possible but not yet exercised.

## Policy Scope

The validation-broad access policy (`All` source, all protocols/ports) is intentional, and I have no current plan to change it. My 2026-07-12 [operational descope decision](../Documentation/Change%20Records/NPM%20Operational%20Follow-ups%20and%20Hardening%20Descope%20-%202026-07-12.md) removed policy tightening from tracked work because I have not yet defined the production source groups and ports.
