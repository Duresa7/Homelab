# ansible-01 Blue Migration

**Created:** 2026-09-12  
**Last updated:** 2026-09-12

I moved LXC 100 `ansible-01` from `grey-server` to `blue-server`. Its 16 GiB root volume moved from `ssd-lvm1:vm-100-disk-0` to `local-lvm:vm-100-disk-0`. I kept one vCPU, 1 GiB memory, 512 MiB swap, unprivileged mode, nesting, automatic startup, VLAN 40, the guest firewall setting, and `192.168.40.36/24` with gateway `192.168.40.1`. HA remains disabled.

## Migration

I checked five-node quorum, the guest configuration, available memory and storage on Blue, six active controller services, Semaphore HTTP 200, and no running Ansible playbook. Blue had 2,816 MiB available memory and 106,059,754 KiB available on `local-lvm`. I did not retain terminal transcripts for these preflight checks.

Through SSH Manager on Grey I ran:

```sh
pct migrate 100 blue-server --target-storage local-lvm --restart 1 --timeout 180
```

The waiting tool connection returned an internal error, so I read the existing Proxmox task rather than retrying the migration. Task `UPID:grey-server:000F7A68:15B8E0A1:6AA5A97C:vzmigrate:100:root@pam:` shut down the guest at 3:35:24 PM Eastern, copied 17,179,869,184 bytes, removed the source logical volume, started the destination, and finished at 3:38:02 PM with `TASK OK`, duration 2 minutes 38 seconds. The task status independently returned `exitstatus: OK`. I did not retain the original command transcript; these results came from the Proxmox task log and status readback.

## Verification

At 3:38 PM Eastern, `pct status 100` on Blue returned `running`, with no migration lock. CTs 104, 107, and 108 also remained running. Grey's `pvesm list ssd-lvm1 --vmid 100` returned no volumes, and its former guest configuration path was absent. Cluster quorum still held at five nodes. Blue had 2,942 MiB available memory and 97,618,808 KiB free in `local-lvm`, at 34.08% usage.

I verified Semaphore, Galaxy PXE, TFTP, SSH, cron, node_exporter, and Wazuh active. Semaphore's local API and `https://semaphore.alphasecunited.com/api/ping` returned HTTP 200. PXE `/health` returned `ok` locally and from Grey. Prometheus reported `up{host="ansible-01"}=1`; Wazuh's state file reported `connected` when read through `pct exec` as root. Direct SSH to the guest also worked.

Ansible core reported 2.21.2. The fleet inventory ping returned `pong` from all 11 running inventory hosts. `game-01` was unreachable; I independently confirmed CT 123 stopped on Green and left it stopped. The first ad-hoc invocation inherited an unsupported locale from `pct exec`; setting `LANG=C.UTF-8 LC_ALL=C.UTF-8`, consistent with the service's configured locale, allowed the run. No package or fleet configuration changed.

The full 300,032-byte TFTP boot image transferred locally and matched the source byte for byte when the client retried the initial request. A first-request failure after daemon restart remains documented in the [TFTP investigation](../../../../../Platforms/Galaxy%20PXE/Documentation/Troubleshooting/First%20TFTP%20Request%20Fails%20After%20Restart%20-%202026-09-12.md). I did not exercise a bare-metal boot or the VLAN 5 provisioning path. A PXE HTTP probe from Monitor timed out, while the documented Proxmox callback path from Grey passed. I did not change network policy.

I did not retain full terminal transcripts of the service and connectivity checks; this section records their observed results.

## Cleanup and remaining work

No snapshot or guest backup was created. Proxmox removed the source volume as part of its successful migration. During TFTP diagnosis I briefly added `--ipv4`, found it did not fix the first-request error, and restored the original configuration. The reviewed configuration copy is retained under [Backups](../../../../../Backups/ansible-01-tftpd-hpa-before-migration-2026-09-12.conf); its temporary host copy was removed after verification. No tracing process remains.

OpenIPMI remains failed inside the container. The previous boot's August 1 log contains the identical driver startup failure, and the guest has no `/dev/ipmi0`; I left that pre-existing service configuration unchanged. The migration is complete. The TFTP first-request defect remains a separate follow-up.
