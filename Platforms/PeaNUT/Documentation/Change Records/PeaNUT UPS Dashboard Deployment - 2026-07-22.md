# PeaNUT UPS Dashboard Deployment

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

## Date

I completed this deployment on 2026-07-22.

## Scope

I deployed NUT 2.8.1-5 on `red-server` and `grey-server`, then deployed PeaNUT 6.0.0 on `docker-main`. The result is one authenticated browser interface for the two APC Back-UPS Pro BR1500MS2 data links. Automated shutdown wasn't part of this project.

## Starting State

Each Proxmox host exposed one APC USB HID device with vendor `051d` and product `0002`. Neither host had NUT installed or a TCP/3493 listener. `docker-main` ran Docker 29.6.1 and Compose 5.2.0, and TCP/8090 was free. The Galaxy Datacenter firewall was active; the existing UniFi path was unchanged.

## Actions

### Step 1: Inspect the hosts and ports

I checked the USB devices, operating-system and container-runtime versions, listeners, firewall state, and existing workloads. Both UPS devices matched the expected model, and the intended ports were unused. I didn't retain a separate transcript for this read-only discovery step.

### Step 2: Prepare configuration and recovery points

I pinned PeaNUT 6.0.0 to Linux AMD64 digest `sha256:81c0511efa48728cedc7954a7ff8cff5f3069615d6925af66741029dc526f2a1`. I stored the administrator login and authentication secret in the 1Password item `PeaNUT Dashboard - docker-main`. I also saved the pre-change Galaxy firewall as `/root/cluster.fw.bak.peanut-20260722` and created SSH Manager backups of `/etc/nut` on Red and Grey.

I created the 1Password item through `op item create` with the `AI Agent Account` vault selected. SSH Manager returned backup IDs `files_pre-peanut-nut-config-red-20260722_2026-07-22T12-11-39-539Z_247180ed` and `files_pre-peanut-nut-config-grey-20260722_2026-07-22T12-11-39-797Z_5c3b0ebc`. I retained no separate Step 2 transcript because it would add identifiers without exposing a useful state check. No secret or UPS serial number is present in the repository or evidence.

### Step 3: Install and configure NUT

I installed Debian `nut-server` 2.8.1-5 on both hosts. The package also installed `nut-client` and the USB driver dependencies. [Red installation transcript](../../Evidence/PeaNUT%20UPS%20Dashboard%20Deployment%20-%202026-07-22/Logs/S03-NUT-Package-Install-red-server.txt) and [Grey installation transcript](../../Evidence/PeaNUT%20UPS%20Dashboard%20Deployment%20-%202026-07-22/Logs/S03-NUT-Package-Install-grey-server.txt) retain the package operations and exit status.

I configured `ups01` on `192.168.70.13:3493` and `ups02` on `192.168.70.10:3493`. I reloaded the package-supplied udev rules so both USB device nodes became group-readable by `nut`. I disabled `nut-monitor.service`, started the two `usbhid-ups` drivers, and started `nut-server.service`.

The exact deployed files are versioned as [Red NUT configuration](../../Configuration/NUT/red-server/) and [Grey NUT configuration](../../Configuration/NUT/grey-server/). After installing them, I ran `systemctl disable --now nut-monitor.service`, `udevadm control --reload-rules`, `udevadm trigger --subsystem-match=usb --action=change`, `udevadm settle`, `systemctl restart nut-driver-enumerator.service`, and `systemctl restart nut-server.service`. The immediate driver start exposed a USB permission failure until the udev trigger changed the APC device group from `root` to `nut`; both drivers started after that correction. The [configuration correction transcript](../../Evidence/PeaNUT%20UPS%20Dashboard%20Deployment%20-%202026-07-22/Logs/S03-NUT-Configuration-Corrections.txt) retains the exact error, commands, output, and exit status.

The first Red file-deploy method failed before replacing its stock files because the helper expected `sudo` on a root-only Proxmox host. I used an explicit root upload and `install` path instead. The [troubleshooting record](../Troubleshooting/SSH%20Deploy%20Required%20sudo%20on%20red-server%20-%202026-07-22.md) records that correction.

### Step 4: Restrict the Galaxy host-firewall path

I added two TCP/3493 accepts to `pve_mgmt`: `docker-main` at `192.168.40.35` can reach only Grey at `192.168.70.10` and Red at `192.168.70.13`. `pve-firewall compile` returned exit code 0 and rendered both rules into `GROUP-pve_mgmt-IN`. The [firewall transcript](../../Evidence/PeaNUT%20UPS%20Dashboard%20Deployment%20-%202026-07-22/Logs/S04-Proxmox-Firewall.txt) retains the compiled result.

I tested both connections from `docker-main`. The existing UniFi policy path already passed them, so I made no UniFi change.

### Step 5: Deploy PeaNUT

I installed the Compose project under `/opt/docker/peanut`, bound its interface to `192.168.40.35:8090`, and mounted `/opt/docker/peanut/config` at `/config`. The `.env` file is root-owned with mode `0600`. PeaNUT reads both NUT servers without a NUT username or password, which leaves the endpoints read-only. I validated with `docker compose --env-file .env config -q`, then ran `docker compose --env-file .env pull` and `docker compose --env-file .env up -d`.

The first health check used Compose `CMD-SHELL`, but the PeaNUT image has no `/bin/sh`. I changed the probe to exec-form `CMD`, rotated the authentication secret that appeared in the first-start log, and recreated the container. The [troubleshooting record](../Troubleshooting/PeaNUT%20Health%20Check%20Required%20Exec%20Form%20-%202026-07-22.md) explains the failure and correction. The [initial deployment transcript](../../Evidence/PeaNUT%20UPS%20Dashboard%20Deployment%20-%202026-07-22/Logs/S05-Dashboard-Deploy.txt) retains the timed-out first health check.

### Step 6: Verify the result

The [Red verification transcript](../../Evidence/PeaNUT%20UPS%20Dashboard%20Deployment%20-%202026-07-22/Logs/S06-NUT-Verification-red-server.txt) shows `ups01` online with a 100% charge and a 58% load. The [Grey verification transcript](../../Evidence/PeaNUT%20UPS%20Dashboard%20Deployment%20-%202026-07-22/Logs/S06-NUT-Verification-grey-server.txt) shows `ups02` online with a 100% charge and a 17% load. Runtime and input voltage were present for both units. Both transcripts show `nut-monitor.service` disabled and inactive, and zero guest stop, shutdown, or destroy tasks since the deployment began.

The [Red guest-continuity transcript](../../Evidence/PeaNUT%20UPS%20Dashboard%20Deployment%20-%202026-07-22/Logs/S06-Guest-Continuity-red-server.txt) shows the running Red guest had been up for 19,296 seconds against 1,573 seconds of elapsed deployment time. The [Grey guest-continuity transcript](../../Evidence/PeaNUT%20UPS%20Dashboard%20Deployment%20-%202026-07-22/Logs/S06-Guest-Continuity-grey-server.txt) shows all six running Grey guests had uptimes greater than 122,000 seconds against 1,574 seconds of elapsed deployment time. No running guest started or restarted during this work.

The [dashboard verification transcript](../../Evidence/PeaNUT%20UPS%20Dashboard%20Deployment%20-%202026-07-22/Logs/S06-Dashboard-Verification.txt) shows the pinned container running and healthy, TCP/8090 listening, `/api/ping` returning `pong`, direct NUT reachability from the container, and every pre-existing `docker-main` container still running. I then opened the dashboard from this workstation, signed in with the 1Password credential, and observed PeaNUT's device table showing `ups01` and `ups02` online with live charge and load values. The [dashboard capture](../../Evidence/PeaNUT%20UPS%20Dashboard%20Deployment%20-%202026-07-22/Screenshots/S06-PeaNUT-Dashboard-After.png) retains that UI state.

## Decisions

- I kept NUT beside each physical USB device. USB passthrough and a separate NUT guest add failure points without improving this dashboard.
- I gave PeaNUT anonymous read access to NUT telemetry. There is no NUT command account to misuse.
- I disabled `nut-monitor.service`. Shutdown ordering needs a separate design and power-loss test.
- I bound PeaNUT to the `docker-main` address instead of every interface.
- I added destination-specific Proxmox rules and left UniFi unchanged after a live TCP test passed.

## Resulting Configuration

| Component | Result |
| --- | --- |
| Red NUT | `ups01`; APC `usbhid-ups`; `192.168.70.13:3493`; driver and server active |
| Grey NUT | `ups02`; APC `usbhid-ups`; `192.168.70.10:3493`; driver and server active |
| Shutdown monitor | Disabled on both Proxmox hosts |
| PeaNUT | 6.0.0 pinned by digest; healthy on `192.168.40.35:8090` |
| Dashboard authentication | Administrator login and authentication secret in 1Password |
| Galaxy firewall | `192.168.40.35` to `192.168.70.10/32` and `192.168.70.13/32`, TCP/3493 only |

## Verification

NUT returned model, load, charge, runtime, input voltage, and `OL` status from both devices. PeaNUT remained healthy after recreation, and its authenticated device table displayed both UPS units online. Existing Docker workloads stayed running, no guest stop task occurred on Red or Grey during the deployment, and the shutdown monitor remained disabled and inactive. I didn't pull utility power or test shutdown behavior.

## Rollback Points

I can stop and remove `/opt/docker/peanut` without changing either NUT server. The pre-change NUT directories are retained in SSH Manager backups named `pre-peanut-nut-config-red-20260722` and `pre-peanut-nut-config-grey-20260722` for 30 days. The pre-change Galaxy firewall is `/root/cluster.fw.bak.peanut-20260722` on Grey. Before restoring it, I must confirm no later firewall change depends on the current file.

## Remaining Work

None within this project. Automated Proxmox and guest shutdown remains outside scope and requires its own plan and controlled power-loss test.
