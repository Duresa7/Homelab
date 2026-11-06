# Fleet Update

**Created:** 2026-11-06  
**Last updated:** 2026-11-06

**Implementation date:** 2026-11-06, 1:13 PM to 1:41 PM EST  
**Status:** Complete; packages current on every running Linux guest, new kernels booted on 2026-11-06

I patched the operating system packages on every running Linux VM and LXC: the eleven reachable guests in the `fleet-updates` inventory and `ubuntu-dev`. The run left out `app-01`, which has been stopped since 2026-10-09. Every guest now shows zero pending and zero kept-back packages. I didn't update Compose images, the Proxmox nodes or the Windows guests, and I didn't reboot anything.

## Execution

Each step ran as a transient systemd unit on the host doing the work, and I read each log back afterwards. Times are Eastern.

| Time | Step | Result |
|---|---|---|
| 1:13:33 PM | `os-update.yml` from `ansible-01` for `os_update_targets:!docker-blue:!docker-network:!app-01`, `reboot=report`, `apt_autoremove=false`, `apt_autoclean=false` | Ended about 1:38 PM, exit 0; 9 hosts, `failed=0`, `unreachable=0` |
| 1:13:55 PM | `apt-get upgrade` with `--force-confdef --force-confold` on `ubuntu-dev` | Exit 0; 35 packages; the 7.0.0-43 kernel metapackages were kept back |
| 1:17:09 PM | `apt-get --no-remove dist-upgrade` on `ubuntu-dev` for the kept-back kernel | Exit 0; 3 upgraded, 8 new, `wazuh-agent` left on its hold |
| 1:31:24 PM | `os-update.yml` for `docker-network` | Exit 0 |
| 1:39:03 PM | `os-update.yml` for `docker-blue` | Exit 0 |

I ran `docker-network` and `docker-blue` on their own, after the main batch had cleared their nodes. Nginx Proxy Manager is on `docker-network`, and Executor is on `docker-blue`. A Docker Engine upgrade restarts both, which cuts the path every remote tool uses. When the `docker-network` restart took NPM down, the Executor connection dropped for about a minute. I checked that run over direct SSH from `ubuntu-dev` to `ansible-01` until Executor answered again.

## What changed

The deployed `os-update.yml` and `ansible.cfg` on `ansible-01` matched this repository by MD5 before the run. The play uses `upgrade --with-new-pkgs` on apt hosts, so new kernel packages came in without a dist-upgrade.

| Host | Packages from this run | Notes |
|---|---|---|
| `docker-main` | 33 upgraded | Docker Engine 29.9.3, containerd 2.4.2 |
| `media-01` | 24 upgraded | Docker Engine 29.9.3, containerd 2.4.2 |
| `alpha-prod-01` | 26 upgraded, 1 installed | Docker Engine 29.9.3, containerd 2.4.2 |
| `hermes-01` | none | Already current from its 2026-11-04 build |
| `edge-01` | 21 upgraded, 1 installed | |
| `security-01` | 29 upgraded, 7 installed | Wazuh manager, indexer and dashboard 4.14.8-1 to 4.14.10-1; kernel 6.8.0-149; Docker Engine 29.9.3 |
| `splunk-siem` | 105 upgraded, 6 installed, 5 removed | Kernel 6.12.0-211.74.1.el10_2; DNF's kernel retention removed the 211.50.1 packages; Splunk Enterprise stayed 10.4.0 |
| `ansible-01` | 20 upgraded | |
| `monitor-01` | 24 upgraded | Docker Engine 29.9.3, containerd 2.4.2 |
| `docker-network` | 25 upgraded | Docker Engine 29.9.3; NPM stayed on its 2.15.1 pin |
| `docker-blue` | 24 upgraded | Docker Engine 29.9.3; MCP Gateway stayed on v0.43.3 |
| `ubuntu-dev` | 38 upgraded, 8 installed | Docker Engine 29.9.3, kernel 7.0.0-43 |

**The Wazuh central stack moved to 4.14.10.** The Wazuh repository stays enabled on `security-01`, so the safe upgrade took `wazuh-manager`, `wazuh-indexer` and `wazuh-dashboard` in the same transaction. All three ended on 4.14.10-1, and `wazuh-control info` reports `v4.14.10`. The 15 agents stay held at 4.14.8-1, which the manager still accepts, so this wasn't a version mismatch.

## Disk saturation on ssd-lvm1

`security-01`'s apt transaction ran from 1:15:51 PM to 1:33:27 PM, much longer than any other guest's. At 1:24 PM dpkg had been configuring `wazuh-dashboard` for three minutes with no child process. It was in state `D` on `jbd2_log_wait_commit`. Twelve tasks were blocked, the guest's full I/O pressure was 93%, write-out was zero, the kernel logged hung tasks, and systemd killed `systemd-journald` after its watchdog timed out. On `grey-server`, I/O pressure was 80% full. `/dev/sda`, the Crucial CT2000BX500SSD1 behind `ssd-lvm1`, was busy 100% of a 5-second sample while it wrote about 4 MB/s. SMART reported PASSED with no reallocated or pending sectors.

Per-process write counters inside the guest showed what was writing. `wazuh-modulesd` had written about 16 GB since the manager restarted on 4.14.10, and it was still writing about 80 MB/s. The vulnerability detector rebuilds its content database under `/var/ossec/queue/vd`, which reached 5.9 GB, the first time a new manager version starts. VM 200's QEMU process was writing 85.1 MB/s while the other `ssd-lvm1` guests (`splunk-siem`, `hermes-01`, `HQ-DC01`, `HQ-DC02`) wrote under 0.5 MB/s. The BX500 has no DRAM cache, and its write speed collapses once its fast cache fills.

I didn't stop the manager, because the rebuild would only run again on the next start. Dirty pages drained, dpkg finished, and by about 1:35 PM the guest's I/O pressure was back to 1.5%. The next manager upgrade will do the same thing to that disk. I'd schedule it when nothing else on `ssd-lvm1` is mid-write.

## Verification

- **Packages.** On all eleven apt guests, `apt-get -s upgrade` and `apt-get -s dist-upgrade` both reported zero packages, and `dpkg --audit` returned nothing. `dnf check` and `dnf check-update` exited 0 on `splunk-siem`.
- **Services.** No guest had a failed unit. Every Docker host reports Engine 29.9.3, no container is unhealthy, and the only containers not running are `docusaurus`, stopped on purpose since 2026-09-22, and the one-shot `hawser-updater` helpers.
- **Wazuh.** On `security-01`, `wazuh-manager`, `wazuh-indexer`, `wazuh-dashboard`, `filebeat` and `docker` are active. The dashboard answered HTTPS 302, and `agent_control -l` listed 15 agents Active. The one disconnected agent is `app-01`, which is stopped.
- **Splunk.** `Splunkd`, `sc4s` and `unifi-flow-collector` are active. Splunk Web returned HTTPS 303 on 8000, and management returned 200 on 8089.
- **Remote access.** Executor, ssh-mcp, the UniFi MCP and the MCP gateway were healthy on `docker-blue` two minutes after its run.
- **Monitoring.** Prometheus had 48 of 50 targets up. The two down are `app-01`'s exporters on `192.168.80.10`.

The play logs and the two `ubuntu-dev` apt logs are under [evidence](../Evidence/Fleet%20Update%20-%202026-11-06/Logs/). The `ubuntu-dev` logs have the password manager's package name replaced with a placeholder. I removed the run directories from `ansible-01` and `ubuntu-dev` after copying them. I created no snapshots.

## Open state

Three guests needed a reboot to load their new kernels. All three booted them later that day during [Grey's reboot](../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/PVE%209.2.26%20Update%20and%20Node%20Reboots%20-%202026-11-06.md#guest-services):

| Guest | Running | Installed |
|---|---|---|
| `security-01` | 6.8.0-147-generic | 6.8.0-149-generic |
| `splunk-siem` | 6.12.0-211.62.1.el10_2 | 6.12.0-211.74.1.el10_2 |
| `ubuntu-dev` | 7.0.0-31-generic | 7.0.0-43-generic |

The LXCs run their node's kernel and need nothing. The Debian VMs `alpha-prod-01`, `edge-01` and `hermes-01` received no new kernel.

Out of scope for this pass: the stopped guests (`app-01`, `kali-pen`, `HQ-MGT01`, `HQ-WS001`), the Windows guests `win11-dev`, `HQ-DC01` and `HQ-DC02`, the five Proxmox nodes, and the Compose images handled by `docker-compose-update.yml`.
