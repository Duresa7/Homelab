# NetBird First Peer and Routed VPN Path

**Created:** 2026-07-12  
**Last updated:** 2026-07-20

**Implementation date:** 2026-07-12  
**Status:** Complete; first peers enrolled, `<YOUR_ORG_NAME>`-Access network published through a routing peer, and the VPN path into Access-A validated end to end

## Scope

I enrolled the first two peers, exercised the WireGuard data path, & routed one peer into Access-A through CT 107. The checks covered the overlay tunnel, route selection, HTTPS service path, and UniFi firewall behavior.

This closes the first item of the [network segmentation plan](../../../../Infrastructure/Network/UniFi/Documentation/Change%20Plans/Network-Segmentation-TODO.md) ("confirm reachability from both Internal and VPN") and the "First Peer and VPN Path" section of the platform [TODO](../TODO.md).

## Starting state

- The NetBird control plane was operational over HTTPS with an authenticated dashboard, but no peer had ever enrolled; all prior validation was configuration-only.
- Management/Dashboard versions: v0.74.4 / v2.90.3.
- No NetBird network route or resource existed; the dashboard's Network Routing section was empty.
- Access-A (VLAN 85) contained a single host: CT 107 `docker-network` at `192.168.85.2`.

## Walkthrough

### Step 1: Enroll the temporary Debian peer

**Action:** I generated a one-off User Device setup key in the NetBird dashboard & ran the installer on the temporary `debian` VM.

**Commands:**

```sh
curl -fsSL https://pkgs.netbird.io/install.sh | sh
netbird up --management-url https://<YOUR_NETBIRD_DOMAIN> --setup-key <SETUP_KEY>
```

**Observed result:** The peer connected as `debian` from VLAN 50 (`192.168.50.173`) with overlay address `100.121.231.114`.

**Verification:** The Peers page reported NetBird 0.74.4 on Debian GNU/Linux 13 with status `Connected`.

**Evidence:**

![The debian peer connected on the Peers page, overlay IP 100.121.231.114, running NetBird 0.74.4 on Debian GNU/Linux 13](../../Evidence/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12/Screenshots/S01-First-Peer-Debian-Connected-2026-07-12.png)

### Step 2: Confirm the first peer in Control Center

**UI path and action:** In NetBird > Control Center, I reviewed the graph after the first enrollment.

**Observed result:** The graph contained only the `debian` peer attached to the Default / All group.

**Verification:** The graph showed the same overlay address as the Peers page.

**Evidence:**

![The Control Center peer graph with the single debian peer (100.121.231.114) connected to the Default / All group](../../Evidence/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12/Screenshots/S02-Control-Center-Single-Peer-2026-07-12.png)

### Step 3: Enroll the routing peer

**Action:** I generated a one-off Server setup key & ran the same installer on CT 107 `docker-network`.

**Commands:**

```sh
curl -fsSL https://pkgs.netbird.io/install.sh | sh
netbird up --management-url https://<YOUR_NETBIRD_DOMAIN> --setup-key <SETUP_KEY>
```

**Observed result:** `docker-network` connected as a Server peer with overlay address `100.121.111.204`.

**Verification:** The Peers page listed both peers, confirming management, signal, and STUN reachability through the HTTPS front end.

**Evidence:**

![The Peers page listing docker-network (100.121.111.204) and debian (100.121.231.114), with the Add Peer menu open showing User Device, Server, and Agent](../../Evidence/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12/Screenshots/S03-Peers-Two-Peers-Add-Peer-Types-2026-07-12.png)

### Step 4: Confirm both peers in Control Center

**UI path and action:** In NetBird > Control Center, I reviewed the graph after enrolling `docker-network`.

**Observed result:** The graph contained `debian` and `docker-network`, both attached to the All group.

**Verification:** The graph showed `debian` at `100.121.231.114` & `docker-network` at `100.121.111.204`, with no third peer.

**Evidence:**

![The Control Center peer graph with debian and docker-network both attached to the All group](../../Evidence/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12/Screenshots/S04-Control-Center-Two-Peers-2026-07-12.png)

### Step 5: Capture the route before publishing Access-A

**Action:** I checked the destination route from the `debian` peer before creating a NetBird network.

**Command:**

```sh
ip route get 192.168.85.2
```

**Observed result:** Linux resolved the destination through `192.168.50.1 dev eth1`, which was the direct LAN path.

**Verification:** The result contained no `wt0` interface or NetBird routing table.

**Evidence:**

![ip route get 192.168.85.2 on the debian peer before the network existed, resolving via 192.168.50.1 dev eth1 over the LAN](../../Evidence/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12/Screenshots/S05-Debian-Route-Before-LAN-2026-07-12.png)

### Step 6: Create the Access-A network resource

**UI action:** In Network Routing > Networks, I created `<YOUR_ORG_NAME>-Access` and added resource `Access-a-subnet` with address `192.168.85.0/24`.

**Observed result:** The Add Resource dialog accepted the subnet as the network resource.

**Verification:** I reviewed the resource name and CIDR before continuing.

**Evidence:**

![The Add Resource dialog for AlphaSec-Access with name Access-a-subnet and address 192.168.85.0/24](../../Evidence/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12/Screenshots/S06-Add-Resource-Initial-2026-07-12.png)

### Step 7: Add the resource description and group

**UI path and action:** In NetBird > Network Routing > Networks > `<YOUR_ORG_NAME>-Access` > Add Resource > Optional Settings, I set the description to `Access-A zone (VLAN 85)` and assigned resource group `access-a`.

**Observed result:** The resource retained the zone description and group assignment.

**Verification:** I reviewed both optional values before saving the resource.

**Evidence:**

![The Add Resource dialog with Optional Settings expanded, description "Access-A zone (VLAN 85)" and resource group access-a](../../Evidence/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12/Screenshots/S07-Add-Resource-Details-2026-07-12.png)

### Step 8: Create the validation access policy

**UI path and action:** In NetBird > Network Routing > Networks > `<YOUR_ORG_NAME>-Access` > Access Control > Add Policy, I created `Peers → Access-A (VLAN 85)` with source group `All`, the Access-A resource as destination, all protocols and ports, and the policy enabled.

**Observed result:** NetBird accepted the policy definition.

**Verification:** I reviewed the policy name and validation-scope description before creation.

**Evidence:**

![The Create New Access Control Policy dialog naming the rule "Peers → Access-A (VLAN 85)" with a validation-scope description](../../Evidence/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12/Screenshots/S08-Access-Policy-Name-2026-07-12.png)

I kept this policy broad for the validation. Narrowing its source group and ports remains in the platform [TODO](../TODO.md).

### Step 9: Verify the resource policy

**UI path and action:** In NetBird > Network Routing > Networks > `<YOUR_ORG_NAME>-Access` > Access Control, I reviewed the resource after saving the policy.

**Observed result:** The tab showed the enabled `Peers → Access-A` policy with source group All and protocol/ports ALL.

**Verification:** The displayed source, destination scope, and permissions matched the validation design.

**Evidence:**

![The resource Access Control tab showing the Peers → Access-A policy with All source groups and ALL protocol and ports](../../Evidence/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12/Screenshots/S09-Resource-Access-Policy-2026-07-12.png)

### Step 10: Select the routing peer

**UI path and action:** In NetBird > Network Routing > Networks > `<YOUR_ORG_NAME>-Access` > Routing Peers > Add Routing Peer, I selected `docker-network` (`100.121.111.204`).

**Observed result:** NetBird accepted CT 107 as the peer that would advertise Access-A.

**Verification:** The selection dialog showed server `docker-network` at `100.121.111.204`.

**Evidence:**

![The Add Routing Peer dialog with docker-network (100.121.111.204) selected as the routing peer](../../Evidence/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12/Screenshots/S10-Add-Routing-Peer-Docker-Network-2026-07-12.png)

### Step 11: Enable routing and masquerade

**UI path and action:** In the Add Routing Peer dialog > Advanced Settings, I enabled the routing peer, enabled Masquerade, and kept metric 9999.

**Observed result:** NetBird retained the route and source-NAT settings for `docker-network`.

**Verification:** I reviewed all three settings before saving.

**Evidence:**

![The routing peer Advanced Settings with Enable Routing Peer on, Masquerade on, and metric 9999](../../Evidence/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12/Screenshots/S11-Routing-Peer-Advanced-Masquerade-2026-07-12.png)

### Step 12: Confirm the completed NetBird network

**UI path and action:** In NetBird > Network Routing > Networks, I reviewed the list after saving the routing peer.

**Observed result:** `<YOUR_ORG_NAME>-Access` showed one resource, one policy, and one routing peer.

**Verification:** The counts confirmed that every required network object existed before traffic testing.

**Evidence:**

![The Networks list showing AlphaSec-Access with 1 resource, 1 policy, and 1 routing peer](../../Evidence/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12/Screenshots/S12-Network-Complete-AlphaSec-Access-2026-07-12.png)

I used the current Networks model instead of legacy Routes because Networks grants no access until a policy permits it, matching the zone-based firewall design. Legacy Routes are reserved for exit-node scenarios and do not apply here.

### Step 13: Verify the routing peer and route change

**Action:** I checked CT 107's routing state over SSH, then tested the overlay and destination route from `debian`.

**Commands:**

```sh
# On docker-network
netbird status
cat /proc/sys/net/ipv4/ip_forward

# On debian
ping -c3 100.121.111.204
ip route get 192.168.85.2
```

**Observed result:** CT 107 reported `Networks: 192.168.85.0/24` and IP forwarding value `1`. The overlay ping returned 3/3, and the destination route changed from the Step 5 LAN path to `dev wt0 table 7120`.

**Verification:** The overlay-only address responded and the kernel selected NetBird's interface and routing table for Access-A. `Lazy connection: true` means an idle tunnel can show `Connecting` between traffic bursts.

**Evidence:**

![On the debian peer: ping 100.121.111.204 returns 3/3 over the tunnel, and ip route get 192.168.85.2 now resolves via dev wt0 table 7120](../../Evidence/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12/Screenshots/S13-Debian-Tunnel-And-Route-Flip-2026-07-12.png)

### Step 14: Test routed reachability and the bare-IP TLS response

**Action:** I tested the Access-A address and then requested the HTTPS endpoint by raw IP.

**Commands:**

```sh
ping -c3 192.168.85.2
curl -k -m5 -o /dev/null -w '%{http_code}\n' https://192.168.85.2
```

**Observed result:** The routed ping returned 3/3. The raw-IP request reached the front end and returned a TLS `unrecognized_name` alert with HTTP code `000` because no server block accepts bare-IP SNI.

**Verification:** A TLS-layer rejection instead of a timeout proved the routed connection reached Nginx Proxy Manager.

**Evidence:**

![On the debian peer: ping 192.168.85.2 returns 3/3, and a raw-IP curl to https://192.168.85.2 returns a TLS unrecognized_name error with code 000](../../Evidence/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12/Screenshots/S14-Debian-Routed-Reach-And-SNI-2026-07-12.png)

### Step 15: Verify HTTPS through the tunnel with the correct hostname

**Action:** I forced the published hostname to the Access-A address while preserving the correct TLS SNI and HTTP Host value.

**Command:**

```sh
curl -k -m5 --resolve <YOUR_NETBIRD_DOMAIN>:443:192.168.85.2 \
  -o /dev/null -w '%{http_code}\n' \
  https://<YOUR_NETBIRD_DOMAIN>
```

**Observed result:** The request returned HTTP `200` through the routed NetBird path.

**Verification:** The request returned HTTP 200 through `wt0` while preserving the published hostname for TLS SNI & the HTTP Host header.

**Evidence:**

![On the debian peer: curl with --resolve `<YOUR_NETBIRD_DOMAIN>`:443:192.168.85.2 returns HTTP 200 through the tunnel](../../Evidence/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12/Screenshots/S15-Debian-HTTPS-200-Through-Tunnel-2026-07-12.png)

## Firewall behavior

No UniFi firewall change was required. The pre-existing zone matrix already permits `Internal → <YOUR_ORG_NAME>-Access` and `VPN → <YOUR_ORG_NAME>-Access`.

Because the routing peer runs with Masquerade enabled, traffic that a remote NetBird peer sends into Access-A is source-NAT'd to the routing peer's own address (`192.168.85.2`) before it reaches another host. UniFi therefore sees the traffic originate **inside** the `<YOUR_ORG_NAME>`-Access zone. The `<YOUR_ORG_NAME>`-Access zone rules apply; the `Allow VPN to <YOUR_ORG_NAME>-Access` policy covers UniFi-native remote-user-VPN clients, a separate path. No gateway rule change was needed.

## Scope and limitations

- Access-A currently holds only CT 107, so the routed-path proof reaches the routing peer itself. Forwarding to a *second* Access-A host (true third-party forwarding) wasn't exercised because no such host exists yet; `ip_forward=1` confirms the peer is forwarding-capable when I add one.
- The `debian` peer was on VLAN 50, which is in the `Internal` zone and can reach Access-A directly over the LAN. I therefore proved the overlay path by the routing-table change (`dev wt0`) and the overlay-only ping, not merely by reachability of `192.168.85.2`.
- The `debian` peer was a temporary Hyper-V VM I used only for this validation and have since removed; it was never a permanent member of the network. The durable artifacts are the `<YOUR_ORG_NAME>`-Access network and the `docker-network` routing peer.

## Completed follow-on records

I completed the automated certificate-renewal path & bounded container logging on 2026-07-12. I intentionally descoped the remaining hardening items in [NetBird/NPM Operational Follow-ups and Hardening Descope - 2026-07-12](NetBird-NPM%20Operational%20Follow-ups%20and%20Hardening%20Descope%20-%202026-07-12.md).
