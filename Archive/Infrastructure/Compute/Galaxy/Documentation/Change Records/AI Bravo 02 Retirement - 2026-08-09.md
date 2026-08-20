# AI Bravo 02 Retirement

**Created:** 2026-08-09  
**Last updated:** 2026-08-20  
**Status:** Complete

## Outcome

I retired Galaxy LXC 105 `ai-bravo-02` early on 2026-08-09. I deleted the stopped guest and its 100 GiB `ssd-lvm1` root volume, removed the durable SSH Manager definition and generated documentation host page, and confirmed there was no matching live UniFi, automation, monitoring, Wazuh, or local SSH dependency. I preserved the final guest configuration and the TNIO/OpenClaw-backed source, tests, configuration, walkthrough, diagrams, and dated records in the archive.

## Starting State and Archive Gate

CT 105 was stopped on `grey-server` with `onboot: 0`. Its root volume was `ssd-lvm1:vm-105-disk-0,size=100G`; it was unprivileged and carried seven NVIDIA device mappings. I read the [retired guest record](../../../../../Operations/Inventory/Galaxy/AI%20Bravo%2002%20Archived%20Guest%20-%202026-07-25.md), the [TNIO platform archive](../../../../../Platforms/TNIO%20AI%20Bot/README.md), the [TNIO walkthrough](../../../../../Guides/TNIO-AI-Bot.md), the [OpenClaw walkthrough](../../../../../Guides/OpenClaw.md), and both archived diagram sources before deletion.

The archive contains the TNIO primary, remote, experimental, and legacy source snapshots; evaluation tests; runtime configuration; evidence; generated artifacts; product description; dated accuracy work; and the OpenClaw-backed inference records referenced by the deployed fixes. The diagrams remained readable from their Excalidraw sources. This preserved operational history is not a guest backup.

## Backup and Dependency Check

Proxmox held no CT snapshot, HA resource, replication job, configured backup, or matching backup file on `local` or `hddpool-1`. I found no retained external backup, so there is no restorable copy of the guest or its root filesystem.

UniFi held no client history for the hostname or address and no matching fixed address, DHCP reservation, local DNS record, firewall group or policy target, client group, content filter, ACL, on-off-network policy, or traffic route. The Ansible controller, monitoring host, and Wazuh manager held no active hostname or address reference. Local SSH configuration and known-host files held no entry.

## Deletion

I guarded the destructive command on all three expected conditions: the guest had to be stopped, `onboot` had to equal `0`, and the rootfs line had to exactly match `ssd-lvm1:vm-105-disk-0,size=100G`. I then ran:

```sh
pct destroy 105 --purge 1 --destroy-unreferenced-disks 1
```

Proxmox reported that it removed logical volume `vm-105-disk-0` and purged CT 105 from related configurations. The [redacted deletion evidence](../../Evidence/AI%20Bravo%2002%20Retirement%20-%202026-08-09/Logs/S01-CT-105-Deletion-2026-08-09.txt) records the guard, command, output, and post-deletion checks.

## External Cleanup

The 2026-08-09 pass reported the `ai_bravo_02` SSH Manager block removed. A second residue sweep on 2026-08-20 found that the durable environment file still contained it. I removed the exact block and verified the file now has no hostname, address, or profile-name match. SSH Manager's loaded server list also omits the retired profile. There is no alias, group membership, active session, tunnel, or pooled connection for the retired server.

The documentation site had a generated host page and stale stopped-guest references even though its repository subtree is intentionally local-only. I removed CT 105 from the private fleet snapshot, removed the generated host page, changed the operations copy to a retirement retrospective, regenerated the host index at 16 active guests and two templates, rebuilt the site, synchronized it to `docker-main`, and recreated its container. The 2026-08-20 sweep removed the remaining AI Bravo retirement prose from the active site source and rebuilt the site again.

The same sweep moved this change record and both dedicated evidence folders from the active Galaxy tree into matching `Archive/` paths. It moved the remaining Docker setup script out of the private scrub quarantine and into the archived TNIO `Scripts/` directory after confirming it contained no withheld value and passed `bash -n`. It also removed three stale Ansible runtime-audit logs whose only remaining value was an old unreachable-host list; dated Ansible records retain that historical state.

A VMID-aware Proxmox pass removed the retired LXC 105 `vz*` task logs and their aggregate index rows from Grey. VMID 105 now belongs to active QEMU VM `ubuntu-dev`, so I preserved all eight current `qm*` task logs. Grey's Proxmox daemons remained active after the surgical log cleanup.

## Verification

- `pct status 105` failed because the configuration no longer exists.
- The cluster resource list, Proxmox configuration tree, and `ssd-lvm1` volume list contain no CT 105 entry.
- Galaxy remained quorate with five votes.
- `ssd-lvm1` allocation fell from 15.72 percent before deletion to 13.05 percent afterward.
- The live documentation container returned healthy, `/healthz` returned `ok`, the host index omitted `ai-bravo-02`, and the retired host route returned HTTP `404`.
- The active inventory and backlogs no longer describe CT 105 as stopped or scheduled for deletion.
- The durable SSH Manager environment file and deployed Ansible source have no AI Bravo hostname, address, or profile-name match.
- The Proxmox task store has no retired LXC 105 task file or index row; current QEMU VM 105 history remains present.

## Recovery and Remaining Work

Deletion was intentional and no restorable backup exists. Recovery would require rebuilding a new guest from the archived source and records. No retirement work remains.
