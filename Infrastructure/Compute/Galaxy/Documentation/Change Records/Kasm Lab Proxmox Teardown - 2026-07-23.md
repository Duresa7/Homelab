# Kasm Lab Proxmox Teardown

**Created:** 2026-07-23  
**Last updated:** 2026-07-26

## What I did

I removed every agent-built Kasm object from the Galaxy cluster after deciding to rebuild Kasm from scratch. Nothing in the lab carried a dependent workload, so I tore it all down in one pass on 2026-07-23. The cluster stayed quorate at four of four votes throughout, and Proxmox VE 9.2.5 and the general storages are untouched.

## Objects removed

- **Ten VMs**, stopped then destroyed with their disks (`--purge --destroy-unreferenced-disks`): 6100 kasm-core (blue), 6101 kasm-agent-01 (purple), 6102 kali-ops-01 (grey), 6103 inetsim-01 (purple), 6110 debian13-kasm-base, 6120 kali2026-disposable-template, 6121 debian13-target-template, 6122 debian13-malware-template, 6123 debian13-evidence-template, and 6200 kasm-dynamic-agent-fbbb4f (grey). Nine carried `protection=1`; I cleared it before each destroy.
- **Access:** the `kasm-autoscale@pve` user and its `provider` token, the custom role `KASMAutoscale`, and all their ACLs.
- **Pool:** `KASM-AUTOSCALE`.
- **SDN:** vnets `KASM75` through `KASM79` and the `KASMLAB` vlan zone, followed by a config apply.
- **Storage:** the `kasm-snippets` dir storage and `/var/lib/vz/kasm-snippets`, which held the `kasm_guest_hook.sh` snippet.
- **Host firewall:** the `192.168.85.3 # kasm-core Proxmox API` line in `/etc/pve/firewall/cluster.fw`. I saved the prior file to `/root/cluster.fw.bak-20260723` on grey. That snapshot was deleted on 2026-07-26; see [Galaxy Host Backup Artifact Purge - 2026-07-26](../../../../../Operations/Maintenance/Galaxy%20Host%20Backup%20Artifact%20Purge%20-%202026-07-26.md).
- **Node files:** `/root/kasm-preflight-20260722/` on all four nodes, which held the staged control scripts and the pre-maintenance `/etc` config archives.

## Verification

After the teardown, `pvecm status` reported Quorate Yes, expected votes 4, total votes 4, and all four nodes online. `pvesh get /cluster/resources` returned no VM in 6000 through 6399. `pveum user list`, `pveum acl list`, and `/etc/pve/user.cfg` showed no `kasm` entries. `/etc/pve/storage.cfg` and `cluster.fw` were clean, and the SDN zone list was empty.

## Left in place

Proxmox VE 9.2.5, the running kernel, the `ssd-lvm1` and `hddpool-1` storages, VM 9000 (`ubuntu-cloud-template`, pre-existing), and every non-Kasm guest and setting. `purple-server` is guest-free again; its failed boot NVMe stays an open hardware item in the [Purple NVMe record](../Troubleshooting/Purple%20NVMe%20Reliability%20Failure%20-%202026-07-22.md).

## Scope

This is the compute half of the Kasm lab cleanup. The UniFi side is in the [Kasm lab network simplification](../../../../Network/UniFi/Documentation/Change%20Records/Kasm%20Lab%20Network%20Simplification%20-%202026-07-23.md). I'm rebuilding Kasm and its Proxmox footprint from scratch. A pre-change snapshot sits outside the repository at `D:\Documents\Kasm-Cleanup-Backup-2026-07-23\`.
