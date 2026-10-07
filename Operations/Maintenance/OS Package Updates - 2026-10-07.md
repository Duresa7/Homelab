# OS Package Updates

**Created:** 2026-10-07  
**Last updated:** 2026-10-07

**Implementation date:** 2026-10-07, 7:48 AM to 7:56 AM EDT  
**Status:** Package installation complete; five reboots pending

I cleared the OS-update alert for `blue-server`, `grey-server`, `purple-server`, `red-server` and `splunk-siem`. Fresh repository checks confirmed six upgrades on each Proxmox node and nineteen pending packages on Splunk's Rocky Linux host. I updated the five hosts in sequence over SSH Manager, checked each completed transaction, and refreshed their monitoring collectors. I did not reboot any host or change guest placement, resources, application versions or package holds.

## Installed packages

Each Proxmox node upgraded six packages and installed one new kernel package, with no removals:

| Package | Previous | Installed |
|---|---|---|
| `libpve-common-perl` | 9.2.2 | 9.2.3 |
| `libpve-storage-perl` | 9.1.11 | 9.1.12 |
| `proxmox-backup-client` | 4.2.7-1 | 4.2.8-1 |
| `proxmox-backup-file-restore` | 4.2.7-1 | 4.2.8-1 |
| `proxmox-kernel-7.0` | 7.0.14-20 | 7.0.14-22 |
| `pve-firmware` | 3.18-6 | 3.18-7 |
| `proxmox-kernel-7.0.14-22-pve-signed` | Not installed | 7.0.14-22 |

On `splunk-siem`, DNF installed the five kernel packages for `6.12.0-211.62.1.el10_2` and upgraded fourteen packages: BIND libraries, license and utilities to `32:9.18.33-15.el10_2.12`; kernel tools, libraries and `python3-perf` to `6.12.0-211.62.1.el10_2`; sudo and its Python plugin to `1.9.17-10.p2.el10_2.7`; and the five Vim packages plus `xxd` to `2:9.1.083-9.el10_2.22`. DNF's kernel retention removed the five packages for `6.12.0-211.39.1.el10_2`, retaining kernels `211.50.1`, `211.61.1` and `211.62.1`. Splunk Enterprise remained `10.4.0-f798d4d49089`.

## Execution and verification

I ran each transaction in a transient systemd unit and retained its log. The node command was `apt-get --no-remove -y -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold dist-upgrade`, with `DEBIAN_FRONTEND=noninteractive` and `NEEDRESTART_MODE=l`. Splunk used `dnf -y upgrade` after I inspected the transaction preview. I ran no APT autoremove and took no snapshots or backups.

| Host | Transaction start | Completed | Result |
|---|---|---|---|
| red-server | 7:49:28 AM | 7:50:12 AM | Exit 0 |
| purple-server | 7:50:38 AM | 7:51:24 AM | Exit 0 |
| blue-server | 7:51:40 AM | 7:52:34 AM | Exit 0 |
| grey-server | 7:52:56 AM | 7:53:29 AM | Exit 0 |
| splunk-siem | 7:53:56 AM | 7:54:58 AM | Exit 0 |

After each node finished, I verified that `dpkg --audit` returned no findings and `apt-get -s dist-upgrade` reported zero upgrades, installations, removals or kept-back packages. All six checked PVE services and `wazuh-agent` were active, the cluster remained quorate with five votes, and every guest retained its previous running or stopped state. The four boot IDs were unchanged. All four nodes had the new kernel and initramfs in `/boot`, and the Wazuh package hold remained in place.

On Splunk, `dnf check-update` and `dnf check` both exited 0. `Splunkd`, `sc4s` and `unifi-flow-collector` were active with the same PIDs as before the update. Splunk Web returned HTTPS 303 on port 8000, management returned HTTPS 200 on 8089, and UDP 514 was listening. The boot ID was unchanged, and there were no failed units.

At 7:56:08 AM, Prometheus reported 50 of 50 targets up. After I started the APT and DNF textfile collectors, the pending-package query returned no series for these five hosts, matching the empty package-manager checks. These collectors omit pending-package series when there are no upgrades. I verified the alert's source metrics, not delivery of a resolved notification.

Grey still had its pre-existing `nut-monitor` and `zfs-import@hddpool` failures; Red still had its pre-existing `nut-monitor` and `nut-server` failures. Blue and Purple had none. I changed none of those units.

## Execution notes and evidence

Red's launch call timed out after ten seconds because `systemd-run` waited for the oneshot to finish. The unit continued and completed successfully; I did not launch it again. Subsequent launches used `--no-block`. An interim Purple read caught package triggers still running and reported incomplete configuration; the completed read was clean.

My first Splunk preflight used passwordless sudo, which the host does not allow. I repeated the privileged checks through SSH Manager's configured sudo helper. The first Web probe also used HTTP on the HTTPS listener and was reset; the corrected HTTPS probe returned 303 before and after installation. The optional `dnf versionlock list` probe exited 1; I did not install a plugin or change lock policy. The actual upgrade preview and transaction completed with the packages listed above. Splunk has no `wazuh-agent` unit; its absence in the baseline service check was not a new failure.

I retained the commands, output, exit statuses and follow-up checks in the five host transcripts under [evidence](../Evidence/OS%20Package%20Updates%20-%202026-10-07/Logs/), with separate `monitoring.txt` and `cleanup.txt` captures. I removed the temporary update scripts and logs from all five hosts after copying the evidence; every removal check passed at 7:56 AM.

## Open state

I left all five reboots pending. Blue, Purple and Red still run `7.0.14-20-pve`; Grey still runs `7.0.14-8-pve`. All four now have `7.0.14-22-pve` installed. Splunk still runs `6.12.0-211.61.1.el10_2.x86_64` and needs to boot `6.12.0-211.62.1.el10_2.x86_64`; `dnf needs-restarting -r` exited 1 and its reboot metric is 1.

The four Proxmox APT collectors report `node_reboot_required 0` despite the newer installed kernel. Their existing collector reads the reboot marker rather than comparing kernels, so I recorded the required reboots here and in the root [TODO](../../TODO.md). I did not change that collector or create a synthetic marker.

Node reboots need a guest outage or migration plan and post-boot service checks. Grey's reboot also affects `ubuntu-dev`, where this workspace runs, and Splunk, so I would coordinate those rather than reboot Splunk twice. Green was outside this five-host alert and I did not update it.
