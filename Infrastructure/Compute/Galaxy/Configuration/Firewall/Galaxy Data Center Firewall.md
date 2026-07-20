# Galaxy Data Center Firewall

**Created:** 2026-07-04  
**Last updated:** 2026-07-20

**Last verified:** 2026-07-14 after Termix SSH onboarding (live TCP/22 probes from `docker-main` and authenticated Termix sessions to all four nodes confirmed).

My datacenter firewall (`/etc/pve/firewall/cluster.fw`) enables the cluster firewall and applies a single security group, `pve_mgmt`, through `[RULES]`. That datacenter-level `GROUP` attaches to **every node's** `PVEFW-HOST-IN` chain, so all four nodes are governed identically. No per-node `host.fw` exists.

## IPSets

### `pve_cluster`: Proxmox nodes (inter-node SSH + GUI proxy)

| Address | Host |
|---|---|
| 192.168.70.10 | grey-server |
| 192.168.70.11 | purple-server |
| 192.168.70.12 | blue-server |
| 192.168.70.13 | red-server |

### `pve_admins`: approved admin devices (GUI + SSH)

| Address | Host |
|---|---|
| 192.168.10.27 | `<YOUR_ADMIN_USERNAME>` Mac Air |
| 192.168.50.241 | Jedi PC |

### `pve_automation`: automation control node (GUI + SSH)

| Address | Host |
|---|---|
| 192.168.40.36 | ansible-01 |

### `pve_svc_clients`: service / API consumers (GUI/API 8006 only)

| Address | Host |
|---|---|
| 192.168.72.2 | security-01 (PVE exporter / Proxmox API) |
| 192.168.40.35 | docker-main dashboard |

### `pve_termix`: Termix SSH source (SSH only)

| Address | Host |
|---|---|
| 192.168.40.35 | Termix on docker-main |

## Security Group: `pve_mgmt`

**Comment:** Proxmox SSH/GUI management access. Applied via `GROUP pve_mgmt` in `cluster.fw [RULES]`; attaches to every node's `PVEFW-HOST-IN`.

| Type | Action | Protocol | Source | Destination | Dest. Port | Log Level | Comment |
|------|--------|----------|--------|-------------|------------|-----------|---------|
| in | ACCEPT | tcp | +pve_termix | - | 22 | inherited default | Termix SSH management |
| in | ACCEPT | tcp | +pve_cluster | - | 22,8006 | nolog | inter-node SSH + GUI proxy |
| in | ACCEPT | tcp | +pve_admins | - | 22,8006 | nolog | personal admin devices |
| in | ACCEPT | tcp | +pve_automation | - | 22,8006 | nolog | ansible control node |
| in | ACCEPT | tcp | +pve_svc_clients | - | 8006 | nolog | dashboards / API consumers |
| in | ACCEPT | tcp | 192.168.72.2/32 | - | 9100 | nolog | security-01 Prometheus node_exporter |
| in | ACCEPT | - | 10.6.0.0/24 | 192.168.70.0/24 | - | nolog | WG VPN - MGMT |
| in | ACCEPT | - | 10.6.0.0/24 | 192.168.80.0/24 | - | nolog | WG VPN - Server |
| in | DROP | tcp | - | - | 22 | nolog | DROP SSH |
| in | DROP | tcp | - | - | 8006 | nolog | Drop GUI |

I replaced the former broad `192.168.70.0/24 → 8006` "Management Access" accept with the `pve_cluster` IPSet (the four node addresses). This preserves inter-node GUI proxying while removing blanket 8006 access for any device on the management VLAN, which closes the 8006 exposure the Security-A migration had deferred for review.

Proxmox also maintains an auto-generated `management` IPSet that `RETURN`-allows console ports (VNC `5900:5999`, SPICE `3128`, migration `60000:60050`) and would allow `22`/`8006`; the explicit `pve_mgmt` DROPs for `22`/`8006` are evaluated first and take precedence for those two ports. I left it at Proxmox's default on purpose.

## History

- On 2026-07-14 I added `pve_termix` and its TCP/22-only allow for Termix on `docker-main`. UniFi already allowed the path; the Proxmox `DROP SSH` rule was the connection blocker. Live Termix SSH sessions to all four nodes passed after the change.
- I renamed the prior `zero_access` security group to `pve_mgmt` and reorganized its flat host list into four purpose-named IPSets; `pve_termix` came later.
- I removed the redundant `grey-server` `host.fw`. It applied the same group a second time (a duplicate `PVEFW-HOST-IN` jump) and held only two **disabled** Bezel rules (TCP `45876` from `192.168.40.32`, sport `8090`). All host protection now comes from the datacenter group, uniformly across nodes.
- The former TCP 9100 accept from all of `192.168.70.0/24` was removed during the Security-A migration; the `192.168.72.2/32` accept replaced it.

See [Galaxy Datacenter Firewall IPSet Restructure - 2026-07-13](../../Documentation/Change%20Records/Galaxy%20Datacenter%20Firewall%20IPSet%20Restructure%20-%202026-07-13.md) for the baseline restructure, the platform-owned [Termix SSH Host Onboarding - 2026-07-14](../../../../../Platforms/Termix/Documentation/Change%20Records/Termix%20SSH%20Host%20Onboarding%20-%202026-07-14.md) for the later SSH-source addition and verification, and the UniFi-owned [Security-A Migration - 2026-07-12](../../../../Network/UniFi/Documentation/Change%20Records/Security-A%20Migration%20-%202026-07-12.md) for the preceding cross-system work.
