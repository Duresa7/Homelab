# Galaxy Data Center Firewall

**Created:** 2026-07-04  
**Last updated:** 2026-07-31

**Last verified:** 2026-07-31 after Green joined Galaxy. `pve-firewall compile` exited `0`, the live file held SHA256 `c3a5836e5ac37399ed0ca507a7c1191a892f953d4cab7a1d3f7588e3c6726656`, Grey reported the firewall enabled and running, and Galaxy reported five nodes with quorum.

`/etc/pve/firewall/cluster.fw` enables the Datacenter firewall and applies `pve_mgmt` through `[RULES]`. The `GROUP` enters all four `PVEFW-HOST-IN` chains, so one ordered rule set governs every node. No node has a separate `host.fw`.

## IPSets

### `pve_cluster`: Proxmox nodes (inter-node SSH + GUI proxy)

| Address | Host |
|---|---|
| 192.168.70.10 | grey-server |
| 192.168.70.11 | purple-server |
| 192.168.70.12 | blue-server |
| 192.168.70.13 | red-server |
| 192.168.70.14 | green-server |

### `pve_admins`: approved admin devices (GUI + SSH)

| Address | Host |
|---|---|
| 192.168.10.27 | `<YOUR_ADMIN_USERNAME>` Mac Air |
| 192.168.10.87 | Pixel |
| 192.168.50.241 | Jedi PC |

### `pve_automation`: automation control node (GUI + SSH)

| Address | Host |
|---|---|
| 192.168.40.36 | ansible-01 |

### `pve_svc_clients`: service / API consumers (GUI/API 8006 only)

| Address | Host |
|---|---|
| 192.168.73.2 | monitor-01 (PVE exporter / Proxmox API) |
| 192.168.40.35 | docker-main dashboard |

## Security Group: `pve_mgmt`

**Comment:** Proxmox SSH/GUI management access. Applied via `GROUP pve_mgmt` in `cluster.fw [RULES]`; attaches to every node's `PVEFW-HOST-IN`.

| Type | Action | Protocol | Source | Destination | Dest. Port | Log Level | Comment |
|------|--------|----------|--------|-------------|------------|-----------|---------|
| in | ACCEPT | tcp | +pve_cluster | - | 22,8006 | nolog | inter-node SSH + GUI proxy |
| in | ACCEPT | tcp | +pve_admins | - | 22,8006 | nolog | personal admin devices |
| in | ACCEPT | tcp | +pve_automation | - | 22,8006 | nolog | ansible control node |
| in | ACCEPT | tcp | +pve_svc_clients | - | 8006 | nolog | dashboards / API consumers |
| in | ACCEPT | tcp | 192.168.73.2/32 | - | 9100 | nolog | monitor-01 Prometheus node_exporter |
| in | ACCEPT | tcp | 192.168.73.2/32 | 192.168.70.10/32 | 3493 | nolog | monitor-01 NUT exporter to Grey NUT |
| in | ACCEPT | tcp | 192.168.73.2/32 | 192.168.70.13/32 | 3493 | nolog | monitor-01 NUT exporter to Red NUT |
| in | ACCEPT | - | 10.6.0.0/24 | 192.168.70.0/24 | - | nolog | WG VPN - MGMT |
| in | ACCEPT | - | 10.6.0.0/24 | 192.168.80.0/24 | - | nolog | WG VPN - Server |
| in | DROP | tcp | - | - | 22 | nolog | DROP SSH |
| in | DROP | tcp | - | - | 8006 | nolog | Drop GUI |

I replaced the former `192.168.70.0/24` TCP 8006 accept with `pve_cluster`, which contains only the five registered node addresses. Another device on MGMT-A does not inherit TCP 8006 access from its subnet.

Proxmox also maintains an auto-generated `management` IPSet for VNC `5900:5999`, SPICE `3128`, migration `60000:60050`, SSH 22, & GUI 8006. The explicit `pve_mgmt` drops for 22 and 8006 run first, so they take precedence. I left the generated set unchanged.

## History

- On 2026-07-30 I added `192.168.70.14 # green-server` before the first PXE install. Both the API and cluster file showed five `pve_cluster` members, `pve-firewall compile` passed, and the firewall remained enabled and running. Green completed the repaired PXE run and joined as the fifth node on 2026-07-31. The service build and repair are in [Galaxy PXE Provisioning Service - 2026-07-30](../../../../../Platforms/Galaxy%20PXE/Documentation/Change%20Records/Galaxy%20PXE%20Provisioning%20Service%20-%202026-07-30.md).

- On 2026-07-27 I removed `pve_termix` and its TCP 22 accept. `docker-main` remains in `pve_svc_clients` for the dashboard's TCP 8006 API use, but it failed all four post-change SSH probes. Jedi PC and `ansible-01` passed SSH and TCP 8006 to all four nodes. Monitoring passed its API, node-exporter, and NUT checks. The complete record is [MGMT-A Final Lockdown - 2026-07-27](../../../../Network/UniFi/Documentation/Change%20Records/MGMT-A%20Final%20Lockdown%20-%202026-07-27.md).

- On 2026-07-26 I moved PeaNUT to `monitor-01` and deleted the two `192.168.40.35` TCP/3493 accepts, taking the file from 51 lines to 49. The two `192.168.73.2` accepts now carry both readers: `prometheus-nut-exporter` and PeaNUT. I diffed the candidate before writing it, so the only change was those two lines, and both terminal `IN DROP` entries stayed last. After the reload, live iptables held exactly two 3493 accepts and Prometheus still scraped `ups01` and `ups02`. The complete record is [PeaNUT Relocation to monitor-01 - 2026-07-26](../../../../../Platforms/PeaNUT/Documentation/Change%20Records/PeaNUT%20Relocation%20to%20monitor-01%20-%202026-07-26.md).

- On 2026-07-26 I moved the monitoring source from 192.168.72.2 to 192.168.73.2. The additive candidate first placed both sources in `pve_svc_clients` and kept both node-exporter and NUT rule sets during the verification window. At cutover I removed the four old entries. The final file contains the new IPSet member plus three matching rules, retains both PeaNUT rules and both terminal drops, and has no 192.168.72.2 entry. The `pve_svc_clients` member is outside `[RULES]`; missing it would leave the Proxmox job down even if all three group rules were correct. The complete record is [Monitoring Relocation to monitor-01 - 2026-07-26](../../../../../Platforms/Prometheus/Documentation/Change%20Records/Monitoring%20Relocation%20to%20monitor-01%20-%202026-07-26.md).

- On 2026-07-26 I added the same destination-specific TCP/3493 accepts for `192.168.72.2`, so `prometheus-nut-exporter` on `security-01` can read both UPS units. This is the second firewall the path needed: the UniFi policy "Allow Security to Proxmox NUT" was already in place and 3493 stayed blocked, because this file is enforced independently on every node. Worth remembering when adding any future scrape target that lands on a node. The two new rules sit above the trailing `IN DROP` entries, which are order-sensitive.

- On 2026-07-22 I added destination-specific TCP/3493 accepts from PeaNUT on `docker-main` to the NUT listeners on Red and Grey. The compiled rules and live connections passed; no other Proxmox node or port was added.
- On 2026-07-14 I added `pve_termix` and its TCP/22-only allow for Termix on `docker-main`. UniFi already allowed the path; the Proxmox `DROP SSH` rule was the connection blocker. Live Termix SSH sessions to all four nodes passed after the change. I retired that exception on 2026-07-27.
- I renamed the prior `zero_access` security group to `pve_mgmt` and reorganized its flat host list into purpose-named IPSets.
- I removed the redundant `grey-server` `host.fw`. It applied the same group a second time (a duplicate `PVEFW-HOST-IN` jump) and held only two **disabled** Bezel rules (TCP `45876` from `192.168.40.32`, sport `8090`). All host protection now comes from the datacenter group, uniformly across nodes.
- The former TCP 9100 accept from all of `192.168.70.0/24` was removed during the Security-A migration; the `192.168.72.2/32` accept replaced it.

See [Galaxy Datacenter Firewall IPSet Restructure - 2026-07-13](../../Documentation/Change%20Records/Galaxy%20Datacenter%20Firewall%20IPSet%20Restructure%20-%202026-07-13.md) for the baseline restructure, the platform-owned [Termix SSH Host Onboarding - 2026-07-14](../../../../../Archive/Platforms/Termix/Documentation/Change%20Records/Termix%20SSH%20Host%20Onboarding%20-%202026-07-14.md) for the later SSH-source addition and verification, and the UniFi-owned [Security-A Migration - 2026-07-12](../../../../Network/UniFi/Documentation/Change%20Records/Security-A%20Migration%20-%202026-07-12.md) for the preceding cross-system work.
