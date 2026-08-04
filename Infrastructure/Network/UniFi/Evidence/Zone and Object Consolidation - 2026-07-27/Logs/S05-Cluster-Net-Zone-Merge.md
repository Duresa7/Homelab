# Cluster-Net Zone Merge

**Created:** 2026-07-27  
**Last updated:** 2026-07-27

I moved `Cluster-Net` (VLAN 71) from `AlphaSec-Cluster` into `AlphaSec-Mgmt`, then removed the empty `AlphaSec-Cluster` zone.

Before the move, `Cluster-Net` used zone ID `6a4e74730e10fae12247adbb`. Its DHCP server and internet access were both disabled. After the move, it used the `AlphaSec-Mgmt` zone ID `699cfa5fc9d00a2842cceb51`; both settings remained disabled.

I confirmed zero custom firewall policies referenced `AlphaSec-Cluster` before deleting it. The post-delete readback returned 15 zones and no `AlphaSec-Cluster` entry. Custom policies stayed at 61 and firewall groups stayed at 13.

The move diff changed only `Cluster-Net.firewall_zone_id`. The delete diff removed only zone ID `6a4e74730e10fae12247adbb`; the 61 custom policy bodies, 13 groups, and network details were otherwise unchanged.

## Proxmox checks

I ran `pvecm status` and `corosync-cfgtool -s` on all four nodes before and after the change. Every node reported four members, four votes, quorum 3, and `Quorate: Yes`. Link 0 on `192.168.70.10` through `.13` and link 1 on `192.168.71.10` through `.13` reported every peer connected.

SSH Manager completed a command on each node after the change. From `monitor-01`, each Proxmox HTTPS endpoint on TCP 8006 returned HTTP 200.

## Evidence boundary

I retained the controller states before and after the UI move and zone deletion, plus the post-change service checks. I didn't retain UI screenshots or the original click-by-click interaction transcript.
