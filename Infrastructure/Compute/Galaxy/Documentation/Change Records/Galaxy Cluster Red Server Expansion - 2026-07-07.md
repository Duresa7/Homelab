# Galaxy Cluster Red Server Expansion

**Created:** 2026-07-07  
**Last updated:** 2026-07-18

**Author:** REDACTED_NAME_001  
**Date:** 2026-07-07  
**System:** Proxmox VE 9.2.2, Debian Trixie, cluster `Galaxy`

## Summary

I added `red-server` as the fourth Proxmox VE node in the `Galaxy` cluster.
The node uses the same management VLAN pattern as the existing nodes:
`vmbr0` is VLAN-aware and the host management address lives on `vmbr0.70`.

The cluster is healthy and quorate after the expansion.

## Current Node Inventory

| Node | Management IP | Role | Corosync link0 |
| --- | --- | --- | --- |
| `grey-server` | `192.168.70.10` | Founder / existing workload host | `192.168.70.10` |
| `purple-server` | `192.168.70.11` | Joined expansion node | `192.168.70.11` |
| `blue-server` | `192.168.70.12` | Joined expansion node | `192.168.70.12` |
| `red-server` | `192.168.70.13` | Joined expansion node | `192.168.70.13` |

## Join Procedure Used

My preflight checks on `red-server`:

- `pve-manager/9.2.2`
- No VMs or containers present
- Time sync active
- `pveproxy`, `pvedaemon`, `pve-cluster`, `pve-firewall`, and `ssh` active
- Management address on `vmbr0.70`: `192.168.70.13/24`
- Gateway: `192.168.70.1`

Cluster firewall change on `grey-server`:

```text
IN ACCEPT -source 192.168.70.13 -p tcp -dport 22 -log nolog # red-server (cluster SSH)
```

I added this to `[group zero_access]` immediately before the default SSH drop rule.

I established SSH trust from `red-server` to `grey-server` by adding red's root
public key to grey's root `authorized_keys`. After that, I ran the join from
`red-server`:

```bash
pvecm add 192.168.70.10 --link0 192.168.70.13 --use_ssh
```

Successful output ended with:

```text
successfully added node 'red-server' to cluster.
```

## Cluster Verification

I verified from `grey-server` after the join:

```text
Name:             Galaxy
Config Version:   7
Transport:        knet
Nodes:            4
Expected votes:   4
Total votes:      4
Quorum:           3
Quorate:          Yes
```

`pvecm nodes`:

```text
Nodeid      Votes Name
1           1     grey-server
2           1     purple-server
3           1     blue-server
4           1     red-server
```

Note: with four voting nodes, the quorum requirement is now `3`.

## SSH Hardening

I changed `red-server` to match my existing key-only root SSH posture:

```text
PermitRootLogin without-password
PubkeyAuthentication yes
PasswordAuthentication no
KbdInteractiveAuthentication no
```

I tested password-only SSH and it was rejected:

```text
Permission denied (publickey).
```

I verified key-based SSH from the admin workstation and between cluster nodes:

- `grey-server` to `red-server`
- `red-server` to `grey-server`
- `red-server` to `purple-server`
- `red-server` to `blue-server`

My local SSH manager config now includes:

```text
red_server -> root@192.168.70.13
```

## Repository And Subscription Popup Cleanup

I matched `red-server`'s APT sources to `grey-server`:

- Proxmox no-subscription repo enabled
- Proxmox enterprise repo present but disabled
- Ceph enterprise repo present but disabled
- Ceph no-subscription repo enabled
- Proxmox test repo commented out
- Debian Trixie, Trixie updates, and Trixie security enabled

`apt-get update` completed successfully on all four nodes after the repository
cleanup.

I aligned the Proxmox no-subscription login popup with the existing grey-server
patch on `purple-server`, `blue-server`, and `red-server` by changing the local
`proxmoxlib.js` subscription check to the `NoMoreNagging` sentinel already used
on `grey-server`. I restarted `pveproxy` and verified it active on all nodes.
This UI patch may need to be reapplied after future `proxmox-widget-toolkit`
package updates.

GUI reachability returned HTTP 200 for all four nodes:

- `https://192.168.70.10:8006`
- `https://192.168.70.11:8006`
- `https://192.168.70.12:8006`
- `https://192.168.70.13:8006`

## SMART Result

I ran a short SMART self-test on red's M.2 NVMe disk:

| Field | Value |
| --- | --- |
| Device | `/dev/nvme0n1` |
| Model | `SAMSUNG MZVLB256HAHQ-000L7` |
| Serial | `REDACTED_HARDWARE_SERIAL_001` |
| SMART overall health | `PASSED` |
| Short self-test | `Completed without error` |
| Percentage used | `6%` |
| Power-on hours | `25,744` |
| Media and data integrity errors | `0` |
| Error information log entries | `4,468` |

Saved result:

```text
REDACTED_PRIVATE_DIAGNOSTIC_PATH
```

## Backups And Rollback Points

Firewall backup on `grey-server`:

```text
/root/cluster.fw.bak.pre-red-20260707-105114
```

SSH hardening backup on `red-server`:

```text
/root/sshd_config.bak.pre-keyonly-20260707-105303
```

APT source snapshot on `red-server`:

```text
/root/apt-sources.bak.matched-grey-20260707-105436
```

Subscription popup patch backups:

```text
purple-server:/usr/share/javascript/proxmox-widget-toolkit/proxmoxlib.js.bak.no-sub-popup-20260707-110849
blue-server:/usr/share/javascript/proxmox-widget-toolkit/proxmoxlib.js.bak.no-sub-popup-20260707-110852
red-server:/usr/share/javascript/proxmox-widget-toolkit/proxmoxlib.js.bak.no-sub-popup-20260707-110856
```

`grey-server` already had the same no-subscription popup patch in place before this work.

## Notes

`REDACTED_INTERNAL_FQDN_003`, `REDACTED_INTERNAL_FQDN_002`, and `REDACTED_INTERNAL_FQDN_001` do not
currently resolve from my Windows admin workstation. I use the management IPs or
the SSH manager aliases until internal DNS is updated.
