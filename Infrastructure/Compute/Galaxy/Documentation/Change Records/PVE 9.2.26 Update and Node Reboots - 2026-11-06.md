# PVE 9.2.26 Update and Node Reboots

**Created:** 2026-11-06  
**Last updated:** 2026-11-06

**Implementation date:** 2026-11-06, 2:20 PM to 3:10 PM EST  
**Status:** Complete; all five nodes on `pve-manager` 9.2.26 and kernel `7.0.14-28-pve`, every guest back in its previous power state

I upgraded all five Galaxy nodes from `pve-manager` 9.2.21 to 9.2.26 and kernel `7.0.14-28-pve`, one node at a time in the order Green, Red, Purple, Blue, Grey. I rebooted each node before starting the next. Every guest was to end in the same power state it had before: running guests running, stopped guests stopped. I made no change to any guest's configuration, and I took no snapshots or backups.

## Starting state

At 2:20 PM the cluster was quorate with five of five votes and no HA resources. Green had no guests.

| Node | Running kernel | Up since | Running guests | Stopped guests |
|---|---|---|---|---|
| `green-server` | `7.0.14-20-pve` | 1 week | none | none |
| `red-server` | `7.0.14-22-pve` | 2026-10-28 | CT 842 `media-01` | none |
| `purple-server` | `7.0.14-22-pve` | 3 weeks | VM 121 `edge-01`, VM 401 `alpha-prod-01` | VM 116 `app-01` |
| `blue-server` | `7.0.14-20-pve`, `7.0.14-22-pve` installed | 4.5 weeks | CT 100 `ansible-01`, CT 104 `monitor-01`, CT 107 `docker-network`, CT 108 `docker-blue` | none |
| `grey-server` | `7.0.14-8-pve` | 14 weeks | VM 103 `win11-dev`, VM 105 `ubuntu-dev`, VM 109 `splunk-siem`, CT 110 `docker-main`, VM 112 `hermes-01`, VM 200 `security-01`, VM 301 `HQ-DC01`, VM 302 `HQ-DC02` | VM 102 `kali-pen`, VM 303 `HQ-MGT01`, VM 310 `HQ-WS001`, templates 101, 300 and 9000 |

Before rebooting anything I compared each guest's `onboot` setting with its power state. On Green, Red, Purple and Blue they matched: every running guest starts at boot, and `app-01` is set not to. On Grey, five running guests are not set to start at boot: `HQ-DC01`, `HQ-DC02`, `security-01`, `splunk-siem` and `ubuntu-dev`. No stopped guest anywhere is set to start at boot.

## Package update

Each node ran `apt-get --no-remove -y -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold dist-upgrade` with `DEBIAN_FRONTEND=noninteractive` and `NEEDRESTART_MODE=l`, in a transient systemd unit, and wrote its output to a log. Every transaction exited 0 with nothing removed. Green, Red and Blue upgraded 90 packages and Purple and Grey 91. Each node also installed the new `proxmox-kernel-7.0.14-28-pve-signed`. Purple's extra package was `proxmox-secure-boot-support` and Grey's was `linux-libc-dev`.

| Package | Before | After |
|---|---|---|
| `pve-manager` | 9.2.21 | 9.2.26 |
| `proxmox-kernel-7.0` | 7.0.14-20 or 7.0.14-22 | 7.0.14-28 |
| `pve-qemu-kvm` | 11.0.3-4 | 11.1.3-1 |
| `qemu-server` | 9.2.10 | 9.2.15 |
| `pve-container` | 6.1.14 | 6.1.18 |
| `corosync` | 3.1.10-pve3 | 3.2.0-pve1 |
| `libpve-common-perl` | 9.2.2 or 9.2.3 | 9.2.8 |
| `libpve-storage-perl` | 9.1.11 or 9.1.12 | 9.1.15 |
| `proxmox-backup-client` | 4.2.7-1 or 4.2.8-1 | 4.2.10-1 |
| `pve-firmware` | 3.18-6 or 3.18-7 | 3.18-9 |
| `ceph-common` | 19.2.6-pve4 | 19.2.7-pve1 |

After each transaction:
- `dpkg --audit` returned nothing.
- `apt-get -s dist-upgrade` reported zero packages.
- `/boot` held the `7.0.14-28-pve` kernel and initramfs, and the first GRUB entry was `vmlinuz-7.0.14-28-pve`.
- `pve-cluster`, `pvedaemon`, `pveproxy`, `pvestatd`, `corosync`, `pve-firewall`, `pve-ha-lrm`, `pve-ha-crm` and `wazuh-agent` were active.
- The cluster stayed quorate with five votes.

## Reboots

ssh-mcp refuses any command that names a reboot, so I connected to each node's root account directly from `ubuntu-dev`. On each node, `systemd-run --on-active=5 systemctl reboot` scheduled the reboot. For every node I waited for the following before starting on the next:
- a new boot ID;
- `systemctl is-system-running --wait` to return;
- a quorate cluster;
- every guest that should run to be running.

| Node | Upgrade | Reboot started | Booted | Kernel after |
|---|---|---|---|---|
| `green-server` | 2:20:36 to 2:22:40 PM | 2:22:55 PM | 2:23:52 PM | `7.0.14-28-pve` |
| `red-server` | 2:24:40 to 2:26:36 PM | 2:26:44 PM | 2:27:43 PM | `7.0.14-28-pve` |
| `purple-server` | 2:29:51 to 2:32:03 PM | 2:32:12 PM | 2:33:13 PM | `7.0.14-28-pve` |
| `blue-server` | 2:38:06 to 2:40:49 PM | 2:40:58 PM | 2:41:56 PM | `7.0.14-28-pve` |
| `grey-server` | 2:45:13 to 2:46:55 PM | 2:50:46 PM | 2:53:04 PM | `7.0.14-28-pve` |

Each of the four rebooted nodes came back with:
- five quorate votes and all eight Corosync peer links connected;
- the PVE services and `wazuh-agent` active;
- no failed units;
- TSO, GSO and GRO still off on `nic0` on Green and Red, as the [2026-10-15 offload change](nic0%20Offloads%20Disabled%20on%20Purple,%20Green%20and%20Red%20-%202026-10-15.md) intends.

### Guests after the first four reboots

- **Red.** `media-01` started again on its own. All ten running containers came back, and `cadvisor`, `gluetun`, `hawser` and `jellyfin` reported healthy. Jellyfin's health endpoint returned 200, and `sonarr`, `jellyfin` and `qbittorrent` (through `gluetun`) resolved an external name.
- **Purple.** `edge-01` and `alpha-prod-01` started again, and `app-01` stayed stopped.
  - `edge-01`: `cloudflared` registered four tunnel connections, and Caddy was active.
  - `alpha-prod-01`: QEMU started VM 401 at 2:33:55 PM, but the guest kernel did not log its first line until 2:35:15 PM. On 2026-10-15 the same VM took under a minute. The guest agent answered at 2:35:43 PM.
    - All nine containers came back, including the stopped `hawser-updater` helper, and `minecraft` was healthy.
    - Unlike 2026-10-15, the [Docker DNS boot race](../../../../../Platforms/Minecraft/README.md#open-items) did not hit Minecraft: `sessionserver.mojang.com` resolved inside the container.
    - Prometheus showed `teamspeak_public_up` at 0 for `ts02` and `ts03` at 2:36:49 PM. Both were back to 1 by 2:38:00 PM without my intervention, the same delay the boot-recovery script showed on 2026-10-15.
- **Blue.** All four LXCs started again, none had a failed unit, and every container that ran before ran again.
  - `docker-mcp-gateway` started at 2:43:43 PM, about two minutes after the others. Its log shows an earlier attempt that couldn't reach `unifi-network` on port 8080, then a clean start that listed the UniFi server's five tools.
  - Executor and ssh-mcp answered. A UniFi network listing returned through Executor.
  - Prometheus, Grafana and Executor answered through Nginx Proxy Manager with 302, 302 and 307.

After Blue, Prometheus had 48 of 50 targets up. The two down were `app-01`'s node and cAdvisor exporters, and `app-01` is stopped. No alert was firing.

## Grey

Grey is the last node because `ubuntu-dev` runs on it. Rebooting it takes down the workstation the other four nodes were driven from.

Five of its running guests would stay off after a plain reboot, so I added a one-time unit, `guest-restore-20261106.service`, ordered after `pve-guests.service`. Its script, `/usr/local/sbin/guest-restore-20261106.sh`, does three things:
- It starts `HQ-DC01`, `HQ-DC02`, `security-01`, `splunk-siem` and `ubuntu-dev`, in that order.
- It waits 20 seconds after each start, because four of the five sit on the Crucial BX500 behind `ssd-lvm1`.
- It logs to `/root/guest-restore-20261106.log`, then disables the unit and deletes it and the script.

Their `onboot` settings stay as they were. `win11-dev`, `docker-main` and `hermes-01` start at boot on their own. The stopped guests and templates aren't set to start and need nothing.

The guest services I recorded on Grey before its reboot:
- `security-01`, running `6.8.0-147-generic`:
  - `wazuh-manager`, `wazuh-indexer`, `wazuh-dashboard`, `filebeat` and `docker` were active, with no failed units.
  - `cadvisor`, `hawser` and `wazuh-mcp-server` were running.
  - 15 agents were Active.
- `splunk-siem`, running `6.12.0-211.62.1.el10_2`: `Splunkd`, `sc4s` and `unifi-flow-collector` were active.
- `hermes-01`: the dashboard and gateway processes were running under `dkadi`'s lingering user manager.
- `HQ-DC01` and `HQ-DC02`: `NTDS`, `DNS`, `Netlogon`, `KDC`, `ADWS` and `W32Time` were running.
- `docker-main`: every container ran except `docusaurus`, which has been stopped on purpose since 2026-09-22.

Grey's reboot also loaded the kernels that `security-01`, `splunk-siem` and `ubuntu-dev` received in that morning's [fleet update](../../../../../Operations/Maintenance/Fleet%20Update%20-%202026-11-06.md#open-state).

I started Grey's reboot from Grey itself with `systemd-run --on-active=120 systemctl reboot` at 2:48:46 PM, since `ubuntu-dev` went down with it.

### Grey after the reboot

Grey booted `7.0.14-28-pve` at 2:53:04 PM and rejoined the cluster:
- five quorate votes and eight connected Corosync links;
- the PVE services and `wazuh-agent` active.

`pve-guests` started `win11-dev` and `hermes-01` at 2:55:13 and 2:55:16 PM. The restore unit started each of its five guests with exit 0, at 2:55:20 (`HQ-DC01`), 2:55:42 (`HQ-DC02`), 2:56:04 (`security-01`), 2:56:27 (`splunk-siem`) and 2:56:49 PM (`ubuntu-dev`). At 2:57:12 PM it disabled itself and deleted its unit file and script. Every stopped guest and template stayed stopped.

#### docker-main and the GPU driver

`pve-guests` failed to start `docker-main` with `Device /dev/nvidia-caps/nvidia-cap2 does not exist`, and `nvidia-lxc-devices.service` had failed with `Module nvidia not found in directory /lib/modules/7.0.14-28-pve`.
- **Cause.** The GTX 1080 Ti's 580.159.03 driver is a DKMS module. Grey had headers, and so DKMS builds, only for `7.0.14-6`, `7.0.14-8` and `7.0.14-15`. The kernel package doesn't pull in its headers, so `7.0.14-20`, `-22` and `-28` all arrived without a driver build.
- **Missed check.** The [Ollama runbook](../../../../../Platforms/Ollama/Documentation/Runbook.md#update) requires checking the target kernel's headers and DKMS build before any Grey reboot, and I skipped that check.
- **Repair.**
  - At 2:58:20 PM I installed `proxmox-headers-7.0.14-28-pve`. Its install didn't trigger a DKMS build.
  - At 2:58:35 PM I ran `dkms install nvidia/580.159.03 -k 7.0.14-28-pve`. It built and signed the modules and finished at 2:59:17 PM.
  - I restarted `nvidia-lxc-devices.service`, which then stayed active, and `nvidia-smi` on Grey reported the GTX 1080 Ti on 580.159.03.
  - At 2:59:24 PM I ran `pct start 110`.
- **Result.**
  - Every `docker-main` container that ran before the reboot ran again, and `docusaurus` stayed stopped.
  - `nvidia-smi` worked inside `docker-main` and inside the `ollama` container. Both Immich containers had `/dev/nvidia0`.
  - A one-word prompt to `qwen3.5:2b` answered with `ollama ps` reporting `100% GPU`.
  - Immich returned 200 and Sure 302 through NPM.
  - Inside `immich_server`, a 5-second 1080p test pattern encoded with `hevc_nvenc` through `hwupload_cuda` and `scale_cuda`.
  - `immich_machine_learning`, on the `release-cuda` image, saw the GTX 1080 Ti in `nvidia-smi`. Its ONNX Runtime listed the TensorRT, CUDA and CPU execution providers.

#### Disk saturation on ssd-lvm1

Four of the five restored guests sit on the Crucial BX500, and spacing their starts 20 seconds apart didn't prevent this.
- **The write burst.** By 3:02 PM, about six minutes after starting, `security-01` had written 5.8 GB and `splunk-siem` 3.9 GB. Grey's full I/O pressure was 65%.
- **What it delayed.** `security-01`'s `ssh.service` didn't start until 3:00:23 PM, so ssh-mcp timed out on it until about 3:06 PM. `splunk-siem` and both DCs also timed out on their first attempts.
- **Recovery.** Pressure fell below 5% by 3:05:28 PM without intervention. `security-01`'s kernel logged no hung tasks this time.

#### Guest services

- **`security-01`.**
  - It booted `6.8.0-149-generic`, with no failed units.
  - `wazuh-manager`, `wazuh-indexer`, `wazuh-dashboard`, `filebeat` and `docker` were active, and Wazuh reported `v4.14.10`.
  - All three containers came back, and the dashboard returned 302.
  - 15 agents were Active. The only disconnected agent is the stopped `app-01`.
- **`splunk-siem`.**
  - It booted `6.12.0-211.74.1.el10_2`, and `dnf needs-restarting -r` exited 0.
  - `Splunkd`, `sc4s` and `unifi-flow-collector` were active.
  - Web returned 303 on 8000 and management 200 on 8089. UDP 514 was listening.
- **`hermes-01`.** The Hermes dashboard and gateway were running under `dkadi` again, and the dashboard returned 302.
- **`HQ-DC01` and `HQ-DC02`.** They booted at 2:55:28 and 2:55:51 PM. `NTDS`, `DNS`, `Netlogon`, `KDC`, `ADWS` and `W32Time` were running on both, and each resolved `ad.alphasecunited.com` to both DCs.
- **`win11-dev`.** It booted at 2:55:19 PM, and its guest agent answered.
- **`ubuntu-dev`.**
  - It booted `7.0.0-43-generic`.
  - `openipmi.service` failed, as it had on its previous boot on 2026-09-22. The guest has no `/dev/ipmi0`, `/dev/ipmi/0` or `/dev/ipmidev/0`, and it was not one of the six guests in the [2026-10-07 OpenIPMI repair](../../../../../Platforms/Ansible/Documentation/Troubleshooting/OpenIPMI%20Failed%20on%20Guests%20Without%20IPMI%20Devices%20-%202026-10-07.md).
  - I applied the same repair: disabled and masked the service and cleared the failure. `ubuntu-dev` then reported `running` with no failed units.

At 3:08 PM Prometheus had 48 of 50 targets up. The two down were `app-01`'s exporters, and no alert was firing. Grey had no failed units.

## Open items

- Grey's kernel packages still arrive without headers, so the next Proxmox kernel will boot without the NVIDIA driver again. Installing `proxmox-default-headers` on Grey would keep the headers in step with each kernel. Until then, the runbook's pre-reboot check is the only guard.
- The next Wazuh manager upgrade, or any simultaneous start of the `ssd-lvm1` guests, will saturate the BX500 again.

## Evidence

The five upgrade logs, Grey's pre-reboot guest list, the restore unit's log and the header and DKMS logs are under [evidence](../../Evidence/PVE%209.2.26%20Update%20and%20Node%20Reboots%20-%202026-11-06/Logs/). I deleted every log from the nodes after copying it, and no `20261106` unit, timer or file remains on Grey.
