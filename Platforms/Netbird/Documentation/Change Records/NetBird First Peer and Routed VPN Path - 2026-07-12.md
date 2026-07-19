# NetBird First Peer and Routed VPN Path

**Created:** 2026-07-12  
**Last updated:** 2026-07-18

**Implementation date:** 2026-07-12  
**Status:** Complete; first peers enrolled, REDACTED_PRIVATE_ORG_LABEL-Access network published through a routing peer, and the VPN path into Access-A validated end to end

## Scope

Validate the operational checks I left open after the initial NetBird control-plane deployment: enroll the first real peers, exercise the live WireGuard data path (rather than configuration-only probes), and confirm the intended VPN-client path into the Access-A zone with its owning route and firewall behavior documented.

This closes the first item of the [network segmentation plan](../../../../Infrastructure/Network/UniFi/Documentation/Change%20Plans/Network-Segmentation-TODO.md) ("confirm reachability from both Internal and VPN") and the "First Peer and VPN Path" section of the platform [TODO](../TODO.md).

## Starting state

- The NetBird control plane was operational over HTTPS with an authenticated dashboard, but no peer had ever enrolled; all prior validation was configuration-only.
- Management/Dashboard versions: v0.74.4 / v2.90.3.
- No NetBird network route or resource existed; the dashboard's Network Routing section was empty.
- Access-A (VLAN 85) contained a single host: CT 107 `docker-network` at `192.168.85.2`.

## Implementation

### 1. Peer enrollment

I enrolled two peers with the same procedure (a one-off setup key generated in the dashboard, value never recorded):

```sh
curl -fsSL https://pkgs.netbird.io/install.sh | sh
netbird up --management-url https://REDACTED_CUSTOM_DOMAIN_016 --setup-key <SETUP_KEY>
```

- **`debian`**: a temporary Hyper-V test VM on VLAN 50 (`192.168.50.173`), enrolled as a **User Device**. Overlay IP `100.121.231.114`.
- **`docker-network`** (CT 107): enrolled as a **Server** peer to act as the Access-A routing peer. Overlay IP `100.121.111.204`.

I targeted the self-hosted control plane explicitly with `--management-url`; both peers reported `Connected`, confirming management, signal, and STUN reachability through the published HTTPS front end.

<details>
<summary>S01 screenshot: debian peer enrolled and connected</summary>

![The debian peer connected on the Peers page, overlay IP 100.121.231.114, running NetBird 0.74.4 on Debian GNU/Linux 13](../../Evidence/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12/Screenshots/S01-First-Peer-Debian-Connected-2026-07-12.png)

</details>

<details>
<summary>S02 screenshot: Control Center with the single debian peer</summary>

![The Control Center peer graph with the single debian peer (100.121.231.114) connected to the Default / All group](../../Evidence/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12/Screenshots/S02-Control-Center-Single-Peer-2026-07-12.png)

</details>

<details>
<summary>S03 screenshot: both peers listed with the Add Peer types menu</summary>

![The Peers page listing docker-network (100.121.111.204) and debian (100.121.231.114), with the Add Peer menu open showing User Device, Server, and Agent](../../Evidence/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12/Screenshots/S03-Peers-Two-Peers-Add-Peer-Types-2026-07-12.png)

</details>

<details>
<summary>S04 screenshot: Control Center with both peers</summary>

![The Control Center peer graph with debian and docker-network both attached to the All group](../../Evidence/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12/Screenshots/S04-Control-Center-Two-Peers-2026-07-12.png)

</details>

### 2. REDACTED_PRIVATE_ORG_LABEL-Access network (NetBird Networks)

I built the routed path with the current **Networks** model rather than the legacy Routes model, because Networks is zero-trust by default (no access until a policy grants it), which matches my zone-based firewall posture. Legacy Routes are retained by NetBird only for exit-node scenarios, which do not apply here.

| Element | Value |
|---|---|
| Network | `REDACTED_PRIVATE_ORG_LABEL-Access` |
| Resource | `Access-a-subnet`: `192.168.85.0/24`, in resource group `access-a` |
| Access policy | `Peers → Access-A (VLAN 85)`: source group `All`, destination the Access-A resource, protocol/ports `ALL`, enabled |
| Routing peer | `docker-network` (CT 107), Masquerade on, metric 9999 |

I kept the access policy intentionally broad (`All` sources, all protocols/ports) for validation. Narrowing the source group and restricting ports is recorded as future hardening in the platform [TODO](../TODO.md).

<details>
<summary>S06 screenshot: Add Resource, name and address</summary>

![The Add Resource dialog for AlphaSec-Access with name Access-a-subnet and address 192.168.85.0/24](../../Evidence/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12/Screenshots/S06-Add-Resource-Initial-2026-07-12.png)

</details>

<details>
<summary>S07 screenshot: Add Resource, description and resource group</summary>

![The Add Resource dialog with Optional Settings expanded, description "Access-A zone (VLAN 85)" and resource group access-a](../../Evidence/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12/Screenshots/S07-Add-Resource-Details-2026-07-12.png)

</details>

<details>
<summary>S08 screenshot: access-control policy name</summary>

![The Create New Access Control Policy dialog naming the rule "Peers → Access-A (VLAN 85)" with a validation-scope description](../../Evidence/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12/Screenshots/S08-Access-Policy-Name-2026-07-12.png)

</details>

<details>
<summary>S09 screenshot: resource access-control policy summary</summary>

![The resource Access Control tab showing the Peers → Access-A policy with All source groups and ALL protocol and ports](../../Evidence/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12/Screenshots/S09-Resource-Access-Policy-2026-07-12.png)

</details>

<details>
<summary>S10 screenshot: routing peer selection</summary>

![The Add Routing Peer dialog with docker-network (100.121.111.204) selected as the routing peer](../../Evidence/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12/Screenshots/S10-Add-Routing-Peer-Docker-Network-2026-07-12.png)

</details>

<details>
<summary>S11 screenshot: routing peer advanced settings and masquerade</summary>

![The routing peer Advanced Settings with Enable Routing Peer on, Masquerade on, and metric 9999](../../Evidence/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12/Screenshots/S11-Routing-Peer-Advanced-Masquerade-2026-07-12.png)

</details>

<details>
<summary>S12 screenshot: completed AlphaSec-Access network</summary>

![The Networks list showing AlphaSec-Access with 1 resource, 1 policy, and 1 routing peer](../../Evidence/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12/Screenshots/S12-Network-Complete-AlphaSec-Access-2026-07-12.png)

</details>

### 3. Routing-peer confirmation (CT 107)

From CT 107 over SSH, `netbird status` reports `Networks: 192.168.85.0/24`, confirming it is serving as the Access-A routing peer, and `/proc/sys/net/ipv4/ip_forward` is `1`. `Lazy connection: true` is enabled, so idle peer tunnels are established on demand and report "Connecting" between traffic bursts; that is expected behavior, not a fault.

## Verification performed

I ran all checks from the `debian` peer unless noted. Before publishing the network, `ip route get 192.168.85.2` on the peer resolved over the LAN, giving me the baseline to compare the routed path against.

<details>
<summary>S05 screenshot: route to Access-A before the network was published</summary>

![ip route get 192.168.85.2 on the debian peer before the network existed, resolving via 192.168.50.1 dev eth1 over the LAN](../../Evidence/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12/Screenshots/S05-Debian-Route-Before-LAN-2026-07-12.png)

</details>

1. **Control plane**: both peers reached `Connected`; CT 107 shows Management and Signal connected to `REDACTED_CUSTOM_DOMAIN_016:443` with 2/2 relays available.
2. **Tunnel data path**: `ping 100.121.111.204` (CT 107's overlay IP) returned 3/3, latency settling to ~1 ms, indicating a direct peer-to-peer WireGuard connection. Overlay addresses are only reachable through the tunnel.
3. **Route steering**: `ip route get 192.168.85.2` changed from `via 192.168.50.1 dev eth1` (before) to `dev wt0 table 7120` (after the route), proving Access-A traffic now travels the overlay.
4. **Routed reachability**: `ping 192.168.85.2` returned 3/3 over the tunnel.
5. **Application layer**: an HTTPS request to `REDACTED_CUSTOM_DOMAIN_016` forced to `192.168.85.2` returned `200` through the tunnel. A raw-IP request returned a TLS `unrecognized_name` alert, which itself confirms the connection reached the front end (a TLS-layer rejection, not a timeout); the front end simply has no server block for a bare-IP SNI.

<details>
<summary>S13 screenshot: tunnel ping and route flip to wt0</summary>

![On the debian peer: ping 100.121.111.204 returns 3/3 over the tunnel, and ip route get 192.168.85.2 now resolves via dev wt0 table 7120](../../Evidence/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12/Screenshots/S13-Debian-Tunnel-And-Route-Flip-2026-07-12.png)

</details>

<details>
<summary>S14 screenshot: routed reachability and bare-IP SNI rejection</summary>

![On the debian peer: ping 192.168.85.2 returns 3/3, and a raw-IP curl to https://192.168.85.2 returns a TLS unrecognized_name error with code 000](../../Evidence/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12/Screenshots/S14-Debian-Routed-Reach-And-SNI-2026-07-12.png)

</details>

<details>
<summary>S15 screenshot: HTTPS 200 through the tunnel</summary>

![On the debian peer: curl with --resolve REDACTED_CUSTOM_DOMAIN_016:443:192.168.85.2 returns HTTP 200 through the tunnel](../../Evidence/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12/Screenshots/S15-Debian-HTTPS-200-Through-Tunnel-2026-07-12.png)

</details>

## Firewall behavior

No UniFi firewall change was required. The pre-existing zone matrix already permits `Internal → REDACTED_PRIVATE_ORG_LABEL-Access` and `VPN → REDACTED_PRIVATE_ORG_LABEL-Access`.

Because the routing peer runs with Masquerade enabled, traffic that a remote NetBird peer sends into Access-A is source-NAT'd to the routing peer's own address (`192.168.85.2`) before it reaches any other host. From the UniFi gateway's perspective such traffic therefore originates **inside** the REDACTED_PRIVATE_ORG_LABEL-Access zone; it is governed by the REDACTED_PRIVATE_ORG_LABEL-Access zone rules, not by the `Allow VPN to REDACTED_PRIVATE_ORG_LABEL-Access` policy (which applies to UniFi-native remote-user-VPN clients, a separate path). This is the intended behavior and the reason no gateway rule change was needed.

## Scope and limitations

- Access-A currently holds only CT 107, so the routed-path proof reaches the routing peer itself. Forwarding to a *second* Access-A host (true third-party forwarding) was not exercised because no such host exists yet; `ip_forward=1` confirms the peer is forwarding-capable when I add one.
- The `debian` peer was on VLAN 50, which is in the `Internal` zone and can reach Access-A directly over the LAN. I therefore proved the overlay path by the routing-table change (`dev wt0`) and the overlay-only ping, not merely by reachability of `192.168.85.2`.
- The `debian` peer was a temporary Hyper-V VM I used only for this validation and have since removed; it was never a permanent member of the network. The durable artifacts are the REDACTED_PRIVATE_ORG_LABEL-Access network and the `docker-network` routing peer.

## Follow-on status

I completed the automated certificate-renewal path and bounded container logging on 2026-07-12. I intentionally descoped other hardening items; see [NetBird/NPM Operational Follow-ups and Hardening Descope - 2026-07-12](NetBird-NPM%20Operational%20Follow-ups%20and%20Hardening%20Descope%20-%202026-07-12.md).
