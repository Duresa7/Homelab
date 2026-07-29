# Fleet Artifact Sweep Execution

**Created:** 2026-07-29  
**Last updated:** 2026-07-29

**Started:** 2026-07-29  
**Status:** Complete  
**Source survey:** [Fleet Artifact Sweep](Fleet%20Artifact%20Sweep%20-%202026-07-29.md)

I completed the bounded artifact sweep across all 16 active machines. Measured root-filesystem use fell by 65,068,515,328 bytes, or 60.6 GiB. `grey-server` fell from 75 percent to 37 percent root use, and `docker-main` fell from 35 percent to 17 percent.

## Scope

I covered the four active Proxmox nodes and twelve running Linux guests. I reached 13 machines through SSH Manager, `docker-blue` and `media-01` through Ansible from `ansible-01`, and `kasm-01` through the QEMU guest agent on `purple-server`.

Five stopped guests kept their disks untouched: `db-13-dev` (VM 102), `ai-bravo-02` (105), `kali-pen` (106), `fedora-dev` (111), and `supabase-01` (117). Only the first, second, and fifth have SSH Manager profiles, so a sweep driven off the profile list never sees `kali-pen` or `fedora-dev` at all. Those two stay out of scope by choice: cleaning them would mean booting a guest to tidy it, which costs more than the 130 GiB of provisioned disk they hold is worth.

`kasm-01`, `docker-blue`, and `media-01` had no SSH Manager profile when the sweep ran, which is why I reached them through Ansible and the guest agent. The follow-up section adds all three. I deleted the temporary 16-profile SSH Manager group after verification because it included stopped guests and omitted those three.

## Starting state

The 16 active root filesystems used 366,920,134,656 bytes. `grey-server` accounted for 71,268,655,104 bytes and was the capacity concern at 75 percent. Package caches held 10,239,652,176 bytes across the fleet.

Six ordinary Docker hosts had dangling images or volumes worth inspecting. `kasm-01` reported 100.4 GB of reclaimable images, but all 23 image IDs supplied its control plane or workspace catalog. I treated that value as a false cleanup signal and limited Kasm to its 31.83 MB builder cache.

The [starting-state evidence](../Evidence/Fleet%20Artifact%20Sweep%20-%202026-07-29/Logs/S01-before-state.log) retains the per-machine root and cache measurements.

## Routine cleanup

I cleaned apt caches on 15 Debian-family machines and the dnf cache on `splunk-siem`. I vacuumed systemd journals and installed this drop-in on every active machine:

```ini
[Journal]
SystemMaxUse=200M
```

The file is `/etc/systemd/journald.conf.d/90-fleet-artifact-sweep.conf`. I restarted `systemd-journald` after writing it and confirmed the effective value on all 16 machines.

I ran `docker image prune -f` on `docker-main`, `alpha-prod-01`, `app-01`, `docker-network`, `docker-blue`, and `media-01`. I did not use `docker image prune -a`. Before pruning volumes on `docker-main`, I inspected five anonymous volumes and found only old Redis `dump.rdb` files. None matched the live Immich Redis volume, so I removed those five volumes. I preserved app-01's inactive 49.35 MB Coolify PostgreSQL volume and every tagged idle image.

On `kasm-01`, I ran only `docker builder prune -f`. It removed 31.83 MB. The host still has all 23 image IDs, and its builder cache now reports 0 bytes.

The [cleanup evidence](../Evidence/Fleet%20Artifact%20Sweep%20-%202026-07-29/Logs/S02-cleanup-results.log) records the bounded commands and observed results.

## Inspected artifact removal

On `grey-server`, I ran the current `apt-get --purge autoremove` proposal. It removed four autoremovable kernel packages and reported 3,602 MB freed. The running `7.0.14-6-pve` kernel and the installed fallback kernels remain.

I removed these deployment artifacts after checking that live configuration did not reference them:

- The 7.9 GB Wazuh appliance tree under `/var/lib/vz/wazuh`
- The 580.159.03 and 580.126.18 NVIDIA build trees under `/root`
- The 629,380,096-byte Ubuntu Noble cloud image after confirming template 9000 exists
- The 6,079,267,840-byte OpenVAS VMDK and its OVF from the ISO store
- The Debian 12.11 installer because Debian 13 remains available
- The Windows Server evaluation ISO because no Windows Server guest or planned workload remains
- Finished-job transcripts, installer logs, temporary Ansible files, stale host-key backups, and the mistyped `ystemctl status zfs-mount` file

I preserved the Windows 11 25H2 and VirtIO ISOs for the planned Agent Sandbox. I also kept the current Debian 13, Fedora 44, Kali 2025.2, Ubuntu 24.04.3, Rocky Linux 10.2, and OpenMediaVault 7.4.17 installers.

The two unversioned template scripts under `/root` contained reusable build logic. I moved sanitized versions into [the Debian template script](../../Infrastructure/Compute/Galaxy/Scripts/configure-debian-kasm-lab-template.sh) and [the Kali template script](../../Infrastructure/Compute/Galaxy/Scripts/configure-kali-kasm-ops.sh), replaced the fixed desktop username with a required argument, and deleted the host copies.

I removed smaller stale files on the other machines after checking their contents or installed versions. These included superseded Wazuh packages, stale `.bak` and `.save` files, old known-host backups, and completed-job archives. I preserved the root-only Wazuh installer bundle on `security-01`, the matching 4.14.5 Wazuh package on `edge-01`, the inactive Coolify database volume, and the current Ansible recovery material. The follow-up section below revisits that bundle and reverses the decision.

## Result

The before and after values below are measured root-filesystem bytes. They include cleanup results and normal write drift during the sweep.

| Machine | Before used | After used | Net reclaimed | Final use |
|---|---:|---:|---:|---:|
| `grey-server` | 71,268,655,104 | 34,764,120,064 | 34.00 GiB | 37% |
| `purple-server` | 6,589,652,992 | 5,874,036,736 | 0.67 GiB | 9% |
| `blue-server` | 6,783,623,168 | 6,007,496,704 | 0.72 GiB | 9% |
| `red-server` | 6,517,526,528 | 5,978,673,152 | 0.50 GiB | 9% |
| `docker-main` | 34,566,197,248 | 16,772,829,184 | 16.57 GiB | 17% |
| `alpha-prod-01` | 5,417,234,432 | 4,511,080,448 | 0.84 GiB | 9% |
| `app-01` | 12,466,454,528 | 11,509,092,352 | 0.89 GiB | 6% |
| `edge-01` | 2,380,357,632 | 1,880,780,800 | 0.47 GiB | 7% |
| `ansible-01` | 2,304,311,296 | 2,227,609,600 | 0.07 GiB | 15% |
| `monitor-01` | 5,207,220,224 | 5,044,338,688 | 0.15 GiB | 32% |
| `docker-network` | 5,030,375,424 | 4,209,577,984 | 0.76 GiB | 14% |
| `security-01` | 27,881,050,112 | 25,590,272,000 | 2.13 GiB | 26% |
| `splunk-siem` | 40,593,530,880 | 40,639,729,664 | -0.04 GiB | 55% |
| `docker-blue` | 1,736,101,888 | 1,588,178,944 | 0.14 GiB | 11% |
| `media-01` | 12,573,761,536 | 10,073,563,136 | 2.33 GiB | 11% |
| `kasm-01` | 125,604,081,664 | 125,180,239,872 | 0.40 GiB | 61% |
| **Fleet** | **366,920,134,656** | **301,851,619,328** | **60.60 GiB** | |

`splunk-siem` wrote about 44 MiB more than the cleanup removed during the measurement window. Its dnf cache is 823,300 bytes, the journal is 8 MB, and the host remains at 55 percent root use.

## Verification

All 11 Ansible-managed guests returned `system_state=running`, zero failed units, and the expected container counts. The ordinary Docker hosts reported 53 running containers out of 53 total, with zero unhealthy containers. `kasm-01` returned eight running control-plane containers, eight total containers, zero unhealthy containers, 23 image IDs, and zero builder cache.

I launched the `Terminal - Normal` Kasm workspace through the authenticated interface. The terminal prompt rendered, the session started from the retained `kasmweb/terminal:1.19.0-rolling-daily` image, and the Docker event check showed no image pull. I deleted the disposable session through Kasm, confirmed the session table was empty, and logged out.

Each Proxmox node reported four cluster nodes, `Quorate: Yes`, and `Status: enabled/running` from the Proxmox firewall. Purple and Blue retain `openipmi.service` failure timestamps from 2026-07-25 and 2026-07-23. Red retains the same 2026-07-23 OpenIPMI failure and its documented disabled NUT monitor failure state from that boot. Those states predate this sweep and did not affect quorum, firewall state, guests, or monitoring.

Prometheus reported `total=48 up=48 down=0`. The final `grey-server` check confirmed the removed deployment paths are absent, template 9000 remains registered, the live NVIDIA driver is 580.159.03, and the eight retained ISOs remain in the store.

Both retained template scripts pass `bash -n`. The Mission Control harness passes all 1,140 checks. No temporary Kasm credential file remains in the workspace, and I cleared both browser and Windows clipboard state after the short-lived credential injection.

Evidence: [Kasm acceptance](../Evidence/Fleet%20Artifact%20Sweep%20-%202026-07-29/Logs/S03-kasm-acceptance.log), [final fleet verification](../Evidence/Fleet%20Artifact%20Sweep%20-%202026-07-29/Logs/S04-final-verification.log), and [local validation](../Evidence/Fleet%20Artifact%20Sweep%20-%202026-07-29/Logs/S05-local-validation.log).

## Follow-up on 2026-07-29

I re-checked the sweep against live state the same day, found two files the first pass should have taken, and removed both. A third check of `grey-server:/root` turned up two more.

`security-01:/home/<YOUR_ADMIN_USERNAME>/wazuh-install-files.tar` was 10,983 bytes from 2026-02-24, and it was installer output rather than recovery material. Wazuh runs single-node here: `ossec.conf` carries `<disabled>yes</disabled>` in its cluster block, and the indexer is `node-1` bound to `127.0.0.1` with an empty `cluster.initial_master_nodes`. Every certificate the services load already sits in `/etc/wazuh-indexer/certs/`, `/etc/filebeat/certs/`, and `/etc/wazuh-dashboard/certs/`. The bundle only mattered for bringing up a second node, which this deployment has never had, and `wazuh-certs-tool.sh` reissues the full certificate set anyway.

I removed it with the Ansible `file` module at `state=absent` and read the host back. The path is gone, `wazuh-manager`, `wazuh-indexer`, `wazuh-dashboard`, and `filebeat` all still report `active`, and all eleven certificate files remain in the three stores. Nothing was archived first, because the bundle held secret material and secrets don't go into this repository, so the removal is terminal.

`grey-server:/root/dkms-mok-password.hash` was 103 bytes, mode 0600, written 2026-04-29 09:48. It came out of the NVIDIA driver work and was inert. `mokutil --sb-state` reports `SecureBoot disabled`, so the enrollment step it fed never runs, and module signing uses `/var/lib/dkms/mok.key`. A `grep` across `/etc`, `/usr/local`, and `/var/lib/dkms` found nothing that reads it. The source survey listed it and the first pass skipped it without saying so.

After removing it, `/var/lib/dkms/mok.key` and `mok.pub` are both still present, six nvidia modules are loaded, `nvidia-smi` reports driver 580.159.03, `modinfo nvidia` still shows `signer: DKMS module signing key`, and dkms reports the driver installed against both the 7.0.14-6-pve and 7.0.2-6-pve kernels.

That last check also caught `/root/proxmox-ca.pem` and `/root/pve-root-ca.pem`, two 2,074-byte copies from 2025-09-09. Both hash to `664c0e99cbd4a996b206b4f09e098f0de5109cc38e4a4e7ec8f6f1ea1dc6da2e`, which is the live `/etc/pve/pve-root-ca.pem` the cluster maintains itself, and nothing under `/etc` or `/usr/local` referenced either path. They hold the cluster CA certificate valid to 2035-08-20 and no private key. I removed both, and afterward the live file is unchanged at the same hash, `pveproxy`, `pvedaemon`, `pve-cluster`, and `corosync` are all active, the firewall reports `enabled/running`, the cluster reports 4 nodes and `Quorate: Yes`, and `pvesh get /version` returns 9.2.5. `/root` now holds nothing but shell and tool state.

The journald cap needed deciding rather than assuming, because `/etc/systemd/journald.conf.d/90-fleet-artifact-sweep.conf` is a standing 200 MB policy on all 16 machines and not a one-time reclaim. I measured what it actually costs in retention before keeping it:

| Machine | Journal now | Span it holds |
|---|---:|---|
| `grey-server` | 175.8M | 2026-07-08 to 2026-07-29, 21 days |
| `security-01` | 172.9M | 2026-07-13 to 2026-07-29, 16 days |
| `docker-main` | 104.6M | 2026-05-16 to 2026-07-29, 74 days |
| `monitor-01` | 24M | 3 days, well under the cap |
| `splunk-siem` | 8M | same day, its journal restarted at the 2026-07-28 reboot |

The cap stays. Two to three weeks of local history on the two busiest hosts is enough to diagnose anything I would still be chasing, the other machines never reach the ceiling so the setting does nothing to them, and security-relevant events leave the host for Wazuh and Splunk regardless. Before the sweep those journals held 9.2 GB fleet-wide for the same practical retention.

Three SSH Manager profiles closed the coverage gap this sweep exposed: `kasm_01` at `192.168.78.10`, `docker_blue` at `192.168.40.39`, and `media_01` at `192.168.40.42`, each as `<YOUR_ADMIN_USERNAME>` on port 22 with the workstation key. I confirmed that key is authorized for `<YOUR_ADMIN_USERNAME>` on all three before adding them, and all three now answer. On `kasm-01` the account isn't in the `docker` group, so Docker commands there need `sudo`, which works without a password.

## Rollback

Package caches, journals, Docker build cache, and dangling image layers are regenerable. The removed installer media can be downloaded again. The deleted Wazuh and OpenVAS appliance trees, extracted NVIDIA build trees, and finished-job files require restoration from another retained copy or backup if they are needed again.

The four autoremoved kernel packages can be reinstalled from an available package repository. I did not remove the running kernel or force-delete any installed kernel outside apt's autoremove proposal.

The journald cap is reversible by deleting `/etc/systemd/journald.conf.d/90-fleet-artifact-sweep.conf` and restarting `systemd-journald`, though I decided above to keep it. Removing that cap does not restore journals already vacuumed.

The three new SSH Manager profiles are local workstation configuration. I kept the previous server list at `ssh-manager.env.pre-3-profiles-20260729` beside the live file, outside this repository.

## Remaining work

Nothing is outstanding. The follow-up above closed the last four files, kept the journald cap on measured retention, and added the three missing SSH Manager profiles.

The five stopped guests stay out of scope by choice, not by oversight. `kali-pen` (VM 106) and `fedora-dev` (VM 111) additionally have no SSH Manager profile, so no sweep has read their disks; I'm leaving both alone rather than starting a guest to clean it.
