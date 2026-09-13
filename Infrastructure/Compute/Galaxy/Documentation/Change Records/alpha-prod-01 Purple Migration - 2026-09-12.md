# alpha-prod-01 Purple Migration

**Created:** 2026-09-12  
**Last updated:** 2026-09-12

**Status:** Complete.

I moved VM 401 `alpha-prod-01` from Grey to Purple, with its 60 GiB system disk and 4 MiB EFI volume on Purple's NVMe-backed `local-lvm`. The guest keeps six vCPUs, `cpu: host`, 4 GiB maximum memory with a 2 GiB balloon minimum, automatic startup, VLAN 80, and `192.168.80.118/24` with gateway `192.168.80.1`. HA is disabled. I chose an offline move because Grey uses AMD and Purple uses Intel while this guest exposes its host CPU.

## Preflight

At about 8:06 PM Eastern, Galaxy held five votes and quorum. Purple had 6,318 MiB available memory and 124,995,627 KiB available in its 147,714,048 KiB thin pool, which was 15.38% used. Its existing VMs 116 `app-01` and 121 `edge-01` were running. Purple's SATA `ssd-lvm2` was empty.

All eight containers on `alpha-prod-01` were running: `ts-valorant-02`, `ts-valorant-03`, `ts3-manager`, `playit-agent`, `teamspeak-monitor`, `portainer_edge_agent`, `cadvisor`, and `wud`. cAdvisor and WUD reported healthy. Docker, node_exporter, and Wazuh were active, and QEMU guest-agent ping succeeded. The TeamSpeak collector reported both local and public voice endpoints, DNS SRV lookup, and ServerQuery up. TS3 Manager returned HTTP 200 locally. OpenIPMI was already failed before shutdown.

The destination's total provisioned thin volumes will be 154.01 GiB, exceeding its roughly 140.87 GiB thin pool. The existing allocated use plus a fully allocated 60 GiB copy fits in the pool. I record the thin-provisioning warning because future guest disk growth still needs capacity monitoring; this migration does not enlarge the pool.

## Execution

I ran `qm shutdown 401 --timeout 180` on Grey through SSH Manager. The shutdown completed in about 14 seconds and `qm status 401` returned `stopped`.

My first migration invocation was `pvesh create /nodes/grey-server/qemu/401/migrate --target purple-server --targetstorage local-lvm --online 0`. The tool's ten-second command timeout interrupted the disk copy. Proxmox task `UPID:grey-server:00153A23:15D1C65F:6AA5E939:qmigrate:401:root@pam:` recorded `migration aborted` at 8:07:31 PM. I confirmed no active migration, the source configuration still on Grey with both source volumes attached, and no guest configuration on Purple. Proxmox removed the completed destination EFI copy; I removed the incomplete `local-lvm:vm-401-disk-1` on Purple and verified no destination volumes remained for VM 401.

I restarted the transfer independently of the SSH session:

```sh
systemd-run --unit=alpha-prod-01-purple-migration --collect /usr/sbin/qm migrate 401 purple-server --targetstorage local-lvm --online 0
```

The retry began at 8:08:12 PM Eastern as task `UPID:grey-server:00153EBC:15D1DA38:6AA5E96C:qmigrate:401:root@pam:`. The EFI import completed and the system disk copied at about 116 MB/s.

## Verification and cleanup

The retry completed at 8:17:29 PM Eastern with `TASK OK`, after 9 minutes 17 seconds. The task log confirms both original `ssd-lvm1` volumes were removed. I independently verified Grey has neither a VM 401 configuration nor any `vm-401` logical volumes. Purple holds the 60 GiB system disk and 4 MiB EFI volume on `local-lvm`.

I resumed verification and ran `qm start 401` on Purple at about 8:20 PM. It returned successfully and the guest reported running; QEMU guest-agent ping passed. The first collector cycle overlapped boot recovery and reported failed voice probes. The fresh cycle at 8:21:29 PM reported both local UDP endpoints, both public voice endpoints, both DNS SRV lookups, and both ServerQuery endpoints up. TS3 Manager returned HTTP 200 locally. All eight containers were running, with WUD and cAdvisor healthy. Docker, node_exporter, and Wazuh were active, and the Wazuh agent state was `connected`. Prometheus on `monitor-01` reported the guest's node, cAdvisor, and WUD targets up on ports 9100, 9101, and 9102. The only failed systemd unit remained the pre-existing `openipmi.service`.

After startup, Purple had 3,529 MiB available memory. Its thin pool used 28,804,239 KiB (19.50%), with 118,909,808 KiB available. Galaxy remained quorate with five votes. Future thin-pool growth remains the capacity concern described above; no migration work remains open.

These observations are summarized from live tool results; I did not retain separate full terminal transcripts. No snapshot or backup was created.
