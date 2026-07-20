# Galaxy Datacenter Firewall IPSet Restructure - 2026-07-13

**Created:** 2026-07-13  
**Last updated:** 2026-07-20

**Implementation date:** 2026-07-13  
**Status:** Complete  
**Primary owner:** Infrastructure/Compute/Galaxy (Proxmox datacenter firewall)  
**Affected systems:** `/etc/pve/firewall/cluster.fw`, `/etc/pve/nodes/grey-server/host.fw` (removed); no guest or UniFi change

## Scope

I replaced flat security group `zero_access` with `pve_mgmt` and four role-based IPSets. I also narrowed the MGMT-A TCP 8006 accept from `192.168.70.0/24` to the four cluster addresses & removed the duplicate `grey-server/host.fw`. The only intended access change was closing TCP 8006 to other MGMT-A clients.

## Starting State

- `cluster.fw [RULES]` referenced `GROUP zero_access`; `grey-server/host.fw [RULES]` also referenced it, producing a duplicate application, plus two disabled Bezel rules.
- `zero_access` was a flat list of per-host ACCEPTs ending in `DROP 22` / `DROP 8006`, including a broad `IN ACCEPT -source 192.168.70.0/24 -p tcp -dport 8006 # Management Access`.
- The datacenter `GROUP` attaches to every node's `PVEFW-HOST-IN`, so all four nodes were already governed by the group; `grey-server` received it twice.

## Decisions

- I modeled management sources as IPSets: `pve_cluster` (nodes), `pve_admins` (personal devices), `pve_automation` (ansible-01), `pve_svc_clients` (security-01, docker-main).
- I renamed security group `zero_access` to `pve_mgmt`.
- I replaced the broad `192.168.70.0/24 → 8006` accept with `+pve_cluster` (the four node IPs), preserving inter-node GUI proxying while closing blanket management-VLAN access to `8006`.
- I added no unused admin-laptop allow; `pve_admins` contains only the two current devices.
- I removed `grey-server/host.fw` as redundant (its only active rule duplicated the datacenter group; the Bezel rules were disabled) and chose not to retain a backup of it.

## Actions and Observed Results

1. I backed up `cluster.fw`, then rewrote it with the four `[IPSET ...]` blocks and the `[group pve_mgmt]` definition, and pointed `[RULES]` at `GROUP pve_mgmt`. `pve-firewall compile` returned exit 0.
2. The first compile surfaced `no such security group 'zero_access'`: `grey-server/host.fw` still referenced the old name, which would have left grey's host-input group empty. I repointed `host.fw` to `GROUP pve_mgmt`; the recompile was clean.
3. I applied with `pve-firewall restart` and confirmed the four IPSets materialized (`PVEFW-0-pve_cluster/admins/automation/svc_clients` v4+v6) and `PVEFW-HOST-IN -j GROUP-pve_mgmt-IN`.
4. I determined the `host.fw` reference was redundant: purple-server (no `host.fw`) already receives `GROUP-pve_mgmt-IN` from the datacenter rule, while grey received it twice. I removed `grey-server/host.fw`, recompiled clean, and reapplied. Grey's `PVEFW-HOST-IN` `pve_mgmt` jump count went from 2 to 1, and no `host.fw` remains on any node.

## Resulting `pve_mgmt` Rules

```
IN ACCEPT -source +pve_cluster      -p tcp -dport 22,8006   # inter-node SSH + GUI proxy
IN ACCEPT -source +pve_admins       -p tcp -dport 22,8006   # personal admin devices
IN ACCEPT -source +pve_automation   -p tcp -dport 22,8006   # ansible control node
IN ACCEPT -source +pve_svc_clients  -p tcp -dport 8006      # dashboards / API consumers
IN ACCEPT -source 192.168.72.2      -p tcp -dport 9100      # security-01 node_exporter
IN ACCEPT -source 10.6.0.0/24 -dest 192.168.70.0/24         # WG VPN - MGMT
IN ACCEPT -source 10.6.0.0/24 -dest 192.168.80.0/24         # WG VPN - Server
IN DROP -p tcp -dport 22
IN DROP -p tcp -dport 8006
```

IPSet membership is recorded in the [firewall configuration reference](../../Configuration/Firewall/Galaxy%20Data%20Center%20Firewall.md).

## Verification

| Check | Result |
|---|---|
| `pve-firewall compile` | exit 0, no errors/warnings after the host.fw repoint and after removal |
| IPSets live | `PVEFW-0-{pve_cluster,pve_admins,pve_automation,pve_svc_clients}` present (v4 + v6) |
| Simulate: docker-main `40.35 → :8006` | ACCEPT |
| Simulate: prometheus `72.2 → :9100` | ACCEPT |
| Simulate: random mgmt `70.150 → :8006` and `:22` | DROP; the subnet-wide TCP 8006 accept was gone |
| Live: purple `70.11 → grey :8006` | HTTP `200` (0.03s); inter-node GUI proxy intact |
| Live: purple `70.11 → grey :22` | SSH banner returned |
| Live: my admin session `<YOUR_ADMIN_SOURCE_IP> → :22` | continuous throughout (pve_admins) |
| Cluster | `pvecm status`: 4 nodes, Quorate, 4 votes (corosync unaffected) |
| host.fw removal | grey `PVEFW-HOST-IN` pve_mgmt jump 2 → 1; no `host.fw` on any node |

`pve-firewall simulate` didn't evaluate the `multiport --dports 22,8006` rules. I tested those accepts with live inter-node HTTP, SSH banner, & continuous admin-session traffic instead.

## Rollback

Git history of the [firewall reference](../../Configuration/Firewall/Galaxy%20Data%20Center%20Firewall.md) retains the prior flat rule set. A rollback would recreate `zero_access`, including the `192.168.70.0/24` TCP 8006 accept, and point `cluster.fw [RULES]` back to it. Recreating `grey-server/host.fw` would require `enable: 1`, `GROUP zero_access`, & the two disabled Bezel rules (`|IN ACCEPT -source 192.168.40.32 -p tcp -dport 45876 -sport 8090`, `|IN DROP -p tcp -dport 45876`). I removed the temporary host copies after verification.

## Unchanged Proxmox Management Set

I left the auto-generated `management` IPSet unchanged. It governs console, VNC, SPICE, & migration `RETURN` rules; the explicit `pve_mgmt` drops run first for TCP 22 and 8006. No availability or security incident occurred.
