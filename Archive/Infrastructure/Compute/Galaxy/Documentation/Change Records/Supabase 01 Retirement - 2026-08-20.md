# Supabase 01 Retirement

**Created:** 2026-08-20  
**Last updated:** 2026-08-20  
**Status:** Complete

## Outcome

I confirmed Galaxy VM 117 `supabase-01` had already been deleted from `grey-server`, then removed its remaining current-state references. The active Ansible projects, durable SSH Manager configuration, Galaxy inventory, architecture diagram, and internal documentation site no longer define the guest. Prometheus, Nginx Proxy Manager, and Wazuh held no matching active dependency.

## Deleted Guest

The last living inventory described VM 117 as a Debian 13 guest with four vCPUs, 12.60 GiB memory, OVMF firmware, a 100 GiB `ssd-lvm1` system disk, a 4 MiB EFI disk, and VLAN 80 address `192.168.80.20/24`. I preserved that historical configuration in the dated Galaxy inventory snapshots and this retirement record instead of leaving it in the living VM inventory.

I did not perform the original deletion during this change. The user confirmed it was intentional, and I retained no destruction transcript, so this record does not claim which command removed the guest.

## Proxmox Verification

I checked the cluster and storage state from `grey-server`:

- `/etc/pve/qemu-server/117.conf` is absent.
- The cluster resource API returns no VMID 117.
- `pvesm list ssd-lvm1 --vmid 117` returns no volume.
- The local logical-volume inventory returns no VM 117 volume.
- Each of the five nodes retained `/var/lib/rrdcached/db/pve-vm-9.0/117`, a 1,346,072-byte historical metric file. I guarded their removal on the absent VM configuration and cluster resource, deleted all five, and confirmed they did not reappear during the final pass.

The cross-retirement task-log pass also removed every VM 117 task file and matching row from Grey's Proxmox task indexes. The same bounded cleanup covered deleted VM 122, retired LXC 105, and the removed Kasm autoscaler identity, 69 task-log files across Grey and Purple in total. Current QEMU VM 105 retained all eight of its task logs, and both nodes kept their Proxmox daemons active.

The VMID 105 storage currently present on Grey belongs to active VM 105 `ubuntu-dev`. It is unrelated to retired LXC 105 `ai-bravo-02`, so I left it unchanged.

## Access and Automation Cleanup

I removed `supabase-01` from the tracked SSH inventory and from the host-access inventory comment and validator's outside-model list. I deployed those source changes to `ansible-01`, removed the guest from two private identity allowlists, and deleted three stale runtime-audit logs whose old unreachable-host results named this guest and AI Bravo. Both deployed project validators passed afterward: the SSH-key project reported 14 supported hosts, four identities, no unknown hosts, and 17 Semaphore templates; the host-access project reported ten `ai-agent` hosts, one key-only host, six `dkadi` hosts, and ten templates.

I removed the exact `supabase_01` block from SSH Manager's durable environment file and verified that file has no hostname, address, or profile-name match. SSH Manager's loaded server list also omits the deleted profile. It has no active session, tunnel, or pooled connection for the deleted guest.

## Monitoring, Proxy, and Documentation Cleanup

Prometheus returned no source match, instance label, or active target for the retired hostname or address. Nginx Proxy Manager's generated configuration and logs returned no matching hostname. The Wazuh manager held no matching active agent.

I removed VM 117 from the living Galaxy inventory and service context, removed its card and unused icon from the Excalidraw source and exported SVG, and copied the SVG into the documentation source. I removed the private host page, host-index row, and stopped-guest references, rebuilt the Docusaurus site, synchronized it to `docker-main`, and verified the deployed site remained healthy while the retired host route returned HTTP `404`.

I moved the two dedicated AI Bravo change records and evidence folders into matching archive paths during the same retired-guest documentation pass. Historical dated records that mention either guest remain unchanged because they record the state observed at the time.

## Evidence

I retained no terminal transcript for this follow-up. The source changes and archived records are in Git; the observed live-state results are recorded above without private configuration or credential material.

## Remaining Work

No VM, storage, Proxmox task-log, automation, monitoring, proxy, Wazuh, diagram, or documentation-site work remains for `supabase-01`. I removed the guest from the UniFi network-design placement example, but live UniFi controller state was outside this pass and was not queried or changed.
