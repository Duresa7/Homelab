# SPICE Console Firewall Access - 2026-08-07

**Created:** 2026-08-07  
**Last updated:** 2026-08-07

**Implementation date:** 2026-08-07  
**Status:** Complete  
**Primary owner:** Infrastructure/Compute/Galaxy (Proxmox datacenter firewall)  
**Affected systems:** `/etc/pve/firewall/cluster.fw` on all five nodes, UniFi port group `Proxmox-Admin-Ports`; no guest change

## Scope

I opened TCP 3128 to my admin devices so the SPICE console works from the Proxmox GUI. Two firewalls blocked it and both needed the port. The change is additive: one port added to one existing UniFi port group and one existing `pve_mgmt` rule. No policy was created, deleted, or reordered, and no other port changed.

## Symptom

Clicking **Console** then **SPICE** on VM 102 `debian-dev` downloaded the `.vv` file, and Virt-Viewer on Jedi PC (192.168.50.241) failed with `Unable to connect to the graphic server`. The VM was configured correctly: `vga: qxl,memory=256`, `agent: 1`, and the running QEMU process carried `-spice tls-port=61000,addr=127.0.0.1,tls-ciphers=HIGH,seamless-migration=on`. `spiceproxy` was active on grey-server and listening on `*:3128`. `pvesh create /nodes/grey-server/qemu/102/spiceproxy` returned a well-formed ticket whose `host-subject` matched the node certificate.

## Root Cause

The client never reached TCP 3128. Virt-Viewer talks only to `spiceproxy` on 3128, and `spiceproxy` reaches port 61000 over loopback on the node, so 61000 never needs to leave the host. From Jedi PC, 22 and 8006 connected and 3128 did not. Both firewalls in the path permitted 22 and 8006 only:

- **UniFi.** Policy `Device Access --> Proxmox` admits the four administrative client MACs to the `AlphaSec-Mgmt` zone through port group `Proxmox-Admin-Ports`, whose members were `22` and `8006`.
- **Proxmox.** The `pve_mgmt` rule for `+pve_admins` allowed `-dport 22,8006`. Proxmox does generate its own 3128 accept, but it matches the auto-maintained `management` IPSet, which holds `192.168.70.0/24` and nothing else. That is why purple-server (192.168.70.11) reached grey-server on 3128 while Jedi PC on VLAN 50 did not.

## Decisions

- I added the port to the shared `Proxmox-Admin-Ports` group rather than writing a SPICE-specific UniFi policy. The group already carries every admin device through one policy, so one edit covers all of them and the policy ordering stays untouched.
- I added `3128` to the existing `+pve_admins` accept rather than a new rule. The source stays the `pve_admins` IPSet, so any device added to that set in future gets SPICE with the rest of its management access.
- I did not extend 3128 to `pve_automation` or `pve_svc_clients`. Neither runs a SPICE client, and `pve_svc_clients` is deliberately 8006 only.
- I left the auto-generated `management` IPSet alone, as with every prior change to this file.
- I did not widen the source to the VLAN 50 subnet. The IPSet already names the exact devices.

## Actions and Observed Results

1. I confirmed the guest side was not at fault: `qm config 102` showed `vga: qxl,memory=256`, `systemctl is-active spiceproxy` returned `active`, and `ss -lntp` showed `LISTEN *:3128`.
2. I read the compiled rules on grey-server. `iptables -S PVEFW-HOST-IN` held `-m set --match-set PVEFW-0-management-v4 src -m tcp --dport 3128 -j RETURN`, and `ipset list PVEFW-0-management-v4` returned a single member, `192.168.70.0/24`.
3. I reproduced the split from Jedi PC. TCP 22 and 8006 to 192.168.70.10 connected; TCP 3128 did not. From purple-server, on the same VLAN as grey-server, 3128 connected. That put the block on the source address, not on the service.
4. I read UniFi port group `69cd8ab722432d562f1c424d` (`Proxmox-Admin-Ports`) and found members `22` and `8006`.
5. I updated the port group to `22`, `8006`, `3128` through the plugin's preview-then-confirm flow. Re-reading the group returned the three members.
6. I copied `cluster.fw` to `/tmp`, generated the candidate with a single anchored substitution, and diffed it before writing. The diff was one line, line 35, and both terminal `IN DROP` entries stayed last.
7. I wrote the candidate over `/etc/pve/firewall/cluster.fw`, ran `pve-firewall compile` (exit 0) and `pve-firewall restart`, then deleted both temporary copies from the node.

## Resulting `pve_mgmt` Rule

```
IN ACCEPT -source +pve_admins -p tcp -dport 22,8006,3128 -log nolog # personal admin devices (3128 = SPICE proxy)
```

IPSet membership and the full rule set are in the [firewall configuration reference](../../Configuration/Datacenter-Firewall.md). The port group is in the UniFi [objects reference](../../../../Network/UniFi/Configuration/objects.md).

## Verification

| Check | Result |
|---|---|
| UniFi group re-read after write | `Proxmox-Admin-Ports` returned `22`, `8006`, `3128` |
| `pve-firewall compile` | exit 0 |
| Live rule, grey-server | `GROUP-pve_mgmt-IN ... --match-set PVEFW-0-pve_admins-v4 src -m multiport --dports 22,8006,3128 -g PVEFW-SET-ACCEPT-MARK` |
| Live rule, blue-server | identical rule present, confirming the cluster-wide group reached a second node |
| `cluster.fw` SHA256 | `10a2ff822eeb7ba30881362111a56695e1c666bb144474324defa99b88758858`, 45 lines, unchanged from 45 before |
| `pve-firewall status` | `enabled/running` |
| `pvecm status` | 5 nodes, Quorate |
| TCP 3128 from Jedi PC | open to all five nodes: 192.168.70.10, .11, .12, .13, .14 |
| Temporary copies | both removed from grey-server after verification |

The file kept its line count because the change edits one line rather than adding one.

## Notes for Later

The `.vv` ticket names its proxy from the hostname in the browser address bar, because `pvemanagerlib.js` passes `PVE.Utils.windowHostname()` as the `proxy` parameter. Reaching the GUI at `https://192.168.70.10:8006` puts the address in the file and needs no name resolution. A ticket generated from the CLI instead carries `http://grey-server.galaxy:3128`, and `grey-server.galaxy` does not resolve from Jedi PC, so a CLI-generated file fails on the name before it reaches the port. Adding the record to UniFi local DNS is the fix if that path ever matters. It does not today.

SPICE has no in-browser client here. The GUI button downloads the `.vv` file and Virt-Viewer opens it in its own window. noVNC still works against `qxl` and stays the default console.

## Rollback

Remove `3128` from the `+pve_admins` line in `cluster.fw`, then `pve-firewall compile && pve-firewall restart`. Remove `3128` from the `Proxmox-Admin-Ports` members. Both revert to the prior state with no other side effect, since nothing else references the port.
