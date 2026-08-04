# MGMT-A Final Lockdown

**Created:** 2026-07-27  
**Last updated:** 2026-07-27

## Date

I completed this change on 2026-07-27.

## Scope

I limited access to the four Proxmox management addresses on MGMT-A/VLAN 70. The four approved management devices are Jedi PC, Pixel, MacBook Air, and `ansible-01`. I retained broad access from the WireGuard VPN. I did not add or reserve a NetBird management path.

The dashboard and monitoring systems still need machine-to-machine access, but they are not approved interactive management devices. I kept those paths limited to the service ports they use.

## Starting State

UniFi allowed every Internal-zone client into the whole management zone. A second policy allowed `docker-main` to both SSH and the Proxmox API. The Galaxy Datacenter firewall also gave Termix on `docker-main` a separate SSH exception.

The Galaxy firewall already had narrower entries for the approved devices, the Proxmox nodes, `docker-main` API access, monitoring, and WireGuard. Those entries let me remove the broad paths without replacing them.

## Actions

### S01: Capture the starting state

I saved a full UniFi firewall snapshot before each controller mutation. I also downloaded the live Galaxy `cluster.fw` before editing it.

### S02: Narrow the UniFi policies

I disabled `Allow Internal to AlphaSec-Mgmt`. This removed the broad Internal-zone path and left UniFi's zone default block in charge for unmatched clients.

I changed `Docker-main Allowed -> Server` from all protocols on ports 22 and 8006 to TCP 8006 only. This keeps the read-only homelab dashboard working without treating `docker-main` or Termix as an approved SSH device.

I left these policies enabled and unchanged:

- `Device Access to Proxmox`, which contains the four approved devices and targets ports 22 and 8006
- `Allow VPN to AlphaSec-Mgmt`, which keeps broad WireGuard VPN access
- Both `Allow Monitor to Proxmox` policies for TCP 8006, 9100, and 3493

### S03: Remove the Termix SSH exception

I removed the `pve_termix` IPSet and its TCP 22 accept from `/etc/pve/firewall/cluster.fw`. I kept `docker-main` in `pve_svc_clients`, where it can reach TCP 8006 only. I also retained the four-device management entries, inter-node access, monitoring, and the broad `10.6.0.0/24` WireGuard rule.

The first file-install command copied the candidate but returned an error when it tried to change permissions. Proxmox stores this file on `pmxcfs`, which accepts the content write but does not accept a normal `chmod`. I checked the live checksum before doing anything else. It matched the reviewed candidate, and `pve-firewall compile` passed.

## Decisions

- I treated the four named devices as the approved interactive SSH and web-management set.
- I kept broad WireGuard access because it is an approved remote-management path.
- I ignored NetBird for this change and created no future exception for it.
- I kept `docker-main` TCP 8006 because the healthy homelab dashboard reads the Proxmox API.
- I kept monitoring access because Prometheus, the PVE exporter, and both NUT readers passed their checks.

## Resulting Configuration

The broad Internal-to-MGMT policy is disabled. The approved-device rule remains enabled for ports 22 and 8006. WireGuard remains broadly allowed into the management zone.

At the Proxmox layer, Jedi PC, Pixel, MacBook Air, and `ansible-01` can use SSH and the web interface. `docker-main` and `monitor-01` can use TCP 8006 as service clients. `monitor-01` also retains TCP 9100 to all four nodes and TCP 3493 to Grey and Red. Unmatched SSH and web traffic reaches the final Proxmox drop rules.

## Verification

| Check | Observed result |
|---|---|
| UniFi broad Internal policy | Disabled |
| UniFi approved-device policy | Enabled for four devices and ports 22/8006 |
| UniFi WireGuard policy | Enabled, all traffic from Vpn to the management zone |
| UniFi `docker-main` policy | Enabled, TCP 8006 only |
| Galaxy firewall compile | Passed |
| Galaxy firewall service | Enabled and running on all four nodes |
| Jedi PC to all nodes | 8 of 8 SSH and web-interface probes opened |
| `ansible-01` to all nodes | 8 of 8 SSH and web-interface probes opened |
| `docker-main` to all nodes | 4 of 4 SSH probes blocked; 4 of 4 TCP 8006 probes opened |
| Homelab dashboard | Container healthy after the change |
| `monitor-01` | TCP 8006 and 9100 opened on all four nodes; TCP 3493 opened on Grey and Red |
| WireGuard | UniFi Vpn-to-MGMT allow and Galaxy `10.6.0.0/24` MGMT allow both remain; no connected VPN client was available for a traffic probe |
| NetBird | No management policy or Galaxy exception added |

The retained evidence is indexed in [MGMT-A Final Lockdown evidence](../../Evidence/MGMT-A%20Final%20Lockdown%20-%202026-07-27/Evidence-Index.md).

## Rollback

To restore the controller state, I can re-enable `Allow Internal to AlphaSec-Mgmt` and change `Docker-main Allowed -> Server` back to its prior all-protocol port-group target. The pre-change UniFi snapshot is retained on my workstation outside this repository as `firewall_20260727T122034Z_before.json`.

To restore the Galaxy firewall, I can copy the retained before export from the evidence folder to `/etc/pve/firewall/cluster.fw`, run `pve-firewall compile`, and verify `pve-firewall status` on all four nodes.

## Remaining Work

None for this lockdown. A live WireGuard traffic check is useful when a VPN client is next connected, but I verified both enforced rule layers and chose to keep that path broad.
