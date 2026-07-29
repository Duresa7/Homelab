# Fleet Artifact Sweep

**Created:** 2026-07-29  
**Last updated:** 2026-07-29

**Survey date:** 2026-07-29  
**Status:** Findings only, nothing removed  
**Scope:** Read-only discovery of stale artifacts, backups, installers, package caches, journals, and unused container images across all 16 active machines

This is a work list, not a change record. I changed nothing on any host while producing it. Whoever executes the removals should write their own record and link back here.

Roughly 52 GB is safely reclaimable without a judgment call, and another 33 GB sits in installer media on `grey-server` that needs a decision rather than a command. Read the `kasm-01` warning before running anything anywhere, because the single largest number in this document is a trap.

## Read this before touching kasm-01

`docker system df` on `kasm-01` reports 114.1 GB of images with **100.4 GB reclaimable at 88 percent**. That number is wrong in the way that matters. Do not run `docker image prune -a` on this host.

Kasm sessions are ephemeral. Between sessions no container references a workspace image, so Docker reports every workspace image as unused. The host holds 23 images: 8 are the control-plane containers that are always running, and the other 15 are the workspace images behind all 34 tiles.

| Image | Size |
|---|---:|
| `kasmweb/remnux-noble-desktop:1.19.0-rolling-daily` | 32.3 GB |
| `kasmweb/kali-rolling-desktop:1.19.0-rolling-daily` | 15.9 GB |
| `kasmweb/debian-trixie-desktop:1.19.0-rolling-daily` | 15.3 GB |
| `kasmweb/fedora-43-desktop:1.19.0-rolling-daily` | 14.5 GB |
| `kasmweb/nessus:1.19.0-rolling-daily` | 10.6 GB |
| `kasmweb/forensic-osint:1.19.0-rolling-daily` | 10.3 GB |
| `kcr.kasmweb.com/kasmweb/codex-cli:1.19.0-rolling-daily` | 7.39 GB |
| `kcr.kasmweb.com/kasmweb/claude-code:1.19.0-rolling-daily` | 6.7 GB |
| `kasmweb/cyberbro:1.19.0-rolling-daily` | 6.48 GB |
| `kasmweb/hunchly:1.19.0-rolling-daily` | 5.72 GB |
| `kasmweb/spiderfoot:1.19.0-rolling-daily` | 5.23 GB |
| `kasmweb/telegram:1.19.0-rolling-daily` | 4.92 GB |
| `kasmweb/terminal:1.19.0-rolling-daily` | 4.84 GB |
| `kasmweb/chrome:1.19.0-rolling-daily` | 4.77 GB |
| `kasmweb/tor-browser:1.19.0-rolling-daily` | 4.47 GB |

Those 15 map one to one onto the registry originals in the [Kasm tile inventory](../../Platforms/Kasm%20Workspaces/README.md). Pruning them deletes every workspace image on the host, and the next launch of any tile has to pull 4 to 32 GB back over the WAN before a desktop appears.

The only genuinely dead space here is **31.83 MB of build cache**, with zero stopped containers and zero unused volumes. `docker builder prune -f` is safe. Nothing else on this host is worth the risk, and the guest still has 76 GB free of 193 GB.

The same caution applies in weaker form anywhere workspace-style images are pulled ahead of use. Everywhere else in the fleet, the reclaimable figure is real, because those hosts run their containers continuously.

## Coverage

Sixteen machines are active: four Proxmox nodes and twelve running guests. I reached 13 through the SSH Manager, `docker-blue` and `media-01` through Ansible from `ansible-01`, and `kasm-01` through the QEMU guest agent on `purple-server`.

| Reached how | Machines |
|---|---|
| SSH Manager | `grey-server`, `purple-server`, `blue-server`, `red-server`, `docker-main`, `alpha-prod-01`, `app-01`, `edge-01`, `ansible-01`, `monitor-01`, `docker-network`, `security-01`, `splunk-siem` |
| Ansible from `ansible-01` | `docker-blue`, `media-01` |
| QEMU guest agent from `purple-server` | `kasm-01` |

Three SSH Manager profiles timed out. All three point at guests that are stopped, not gone, so the profiles are correct and the hosts are simply off: `debian_dev` is VM 102 `db-13-dev`, `ai_bravo_02` is CT 105 `ai-bravo-02` which is due for deletion on 2026-08-15, and `supabase_01` is VM 117 `supabase-01`. Nothing in this document covers them, and their disks may hold artifacts of their own.

`kasm-01`, `docker-blue`, and `media-01` have no SSH Manager profile at all. That is a gap worth closing separately, since a fleet sweep that only trusts the profile list misses three running guests.

I searched `/root`, `/home`, `/opt`, `/srv`, `/usr/local`, `/var/backups`, `/var/tmp`, `/tmp`, and `/var/lib/vz`, bounded to six directory levels and one filesystem. I did not search package-owned trees like `/usr/lib` and `/usr/share`, because the [2026-07-26 purge](Galaxy%20Host%20Backup%20Artifact%20Purge%20-%202026-07-26.md) already established that hits there belong to installed packages and must stay.

## grey-server is where the space is

Root is 75 percent full at 67 GB of 94 GB, the tightest on the fleet. Everything below is on `grey-server`.

### Installer media and appliance images

| Path | Size | What it is |
|---|---:|---|
| `/var/lib/vz/wazuh/` | 7.4 GB | Wazuh 4.14.0 OVA plus its VMDK, OVF, and manifest, dated 2025-10-17. Wazuh has been running on VM 200 since then, so this is the installer appliance for a deployment that already exists. |
| `/root/nvidia-580.159.03-patched/` | 2.0 GB | Extracted NVIDIA driver tree plus its 326 MB `.run`, 2026-05-25 |
| `/root/nvidia-580.126.18-patched/` | 2.0 GB | Same, the older 580.126.18 build |
| `/root/noble-server-cloudimg-amd64.img` | 601 MB | Ubuntu 24.04 cloud image, 2026-03-07. Template 9000 already exists and is what the Kasm hosts clone. |
| `/var/lib/vz/template/iso/OPENVAS-FREE-24.10.6-VirtualBox-disk001.vmdk` | 6.08 GB | A VirtualBox appliance disk sitting in the ISO store, 2025-09-16, with its 6.4 KB `.ovf`. No guest uses it and Proxmox cannot boot a VirtualBox VMDK from the ISO store. |

That is 18.1 GB with no live dependency I could find.

### Operator files in /root

Small, but they are the residue of finished jobs: `ansible-ssh-identity-evidence-2026-07-14/` (68 KB), `ssh-key-automation-2026-07-14.tar.gz` (12 KB), `ssh-key-automation-hosts.yml`, `read-key-state-posix.yml`, four `PeaNUT-S0*` transcripts from 2026-07-22, `nvidia-driver-state-before-580-20260525-221847.txt`, two `.install-*.log` files from January, `configure_debian_lab_template.sh`, and `configure_kali_ops.sh`.

There is also a file literally named `ystemctl status zfs-mount`, created by a mistyped command. That one is unambiguous.

Check the two `configure_*.sh` scripts against the repository before deleting them. If they are the only copy of how the Debian lab template and Kali ops host were built, they belong in a `Scripts/` directory rather than in the bin.

### ISOs, which need a decision rather than a command

`/var/lib/vz/template/iso/` holds 33 GB across 12 files. This is the judgment call in this document, because an ISO is only waste until the day you want to build something.

| ISO | Size | Last touched |
|---|---:|---|
| `Win11_25H2_English_x64.iso` | 7.74 GB | 2025-10-30 |
| `X23-81958_26100...SERVER_OEMRET_x64FRE_en-us.iso` | 6.01 GB | 2026-04-01 |
| `kali-linux-2025.2-installer-amd64.iso` | 4.48 GB | 2025-08-31 |
| `ubuntu-24.04.3-live-server-amd64.iso` | 3.30 GB | 2025-12-22 |
| `Fedora-Workstation-Live-44-1.7.x86_64.iso` | 2.85 GB | 2026-07-14 |
| `Rocky-10.2-x86_64-boot.iso` | 1.05 GB | 2026-06-28 |
| `openmediavault_7.4.17-amd64.iso` | 986 MB | 2025-12-12 |
| `debian-13.0.0-amd64-netinst.iso` | 791 MB | 2025-08-24 |
| `virtio-win-0.1.285.iso` | 790 MB | 2026-01-12 |
| `debian-12.11.0-amd64-netinst.iso` | 703 MB | 2025-08-28 |

The two Windows images total 13.75 GB and are the strongest candidates, since the Active Directory domain was destroyed on 2026-07-27 and no Windows guest remains in the cluster. `virtio-win` only matters alongside a Windows guest, so it goes with them. That is 14.5 GB for one decision.

Everything is re-downloadable, so the real cost of deleting an ISO is bandwidth and a delay, not data loss.

## Installers and stale files on the guests

| Host | Path | Size | Note |
|---|---|---:|---|
| `app-01` | `/home/<YOUR_ADMIN_USERNAME>/wazuh-agent_4.10.3-1_amd64.deb` | 11.1 MB | Superseded twice over; the host runs 4.14.6-1 |
| `app-01` | `/home/<YOUR_ADMIN_USERNAME>/wazuh-agent_4.14.5-1_amd64.deb` | 13.2 MB | Superseded on 2026-07-29 |
| `app-01` | `/home/<YOUR_ADMIN_USERNAME>/wazuh-agent-linux-amd64.deb` | 111 B | A failed download, not a package |
| `edge-01` | `/home/<YOUR_ADMIN_USERNAME>/wazuh-agent_4.10.3-1_amd64.deb` | 11.1 MB | Superseded |
| `edge-01` | `/home/<YOUR_ADMIN_USERNAME>/wazuh-agent_4.14.5-1_amd64.deb` | 13.2 MB | This one matches the installed 4.14.5-1. Keep it or not, but note that `edge-01` has no Wazuh apt repository, so this file is currently the only local upgrade path. |
| `security-01` | `/home/<YOUR_ADMIN_USERNAME>/wazuh-install.sh` | 194 KB | Wazuh installer script, 2026-02-24 |
| `security-01` | `/home/<YOUR_ADMIN_USERNAME>/wazuh-install-files.tar` | 11.0 KB | Installer output bundle from 2026-02-24. Inspect before deleting rather than after. |
| `docker-main` | `/root/wazuh-agent_4.14.0-1_amd64.deb` | 13.0 MB | Superseded, and `docker-main` is not a Wazuh endpoint |
| `docker-main` | `/opt/docker/forgejo/docker-compose.yml.bak.20260511155104` | 370 B | Compose file copies beside the live file |
| `docker-main` | `/opt/docker/forgejo/docker-compose.yml.bak.20260528-184846` | 374 B | Same |
| `docker-main` | `/opt/docker/forgejo/data/gitea/conf/app.ini.bak.20260511164612` | 2.0 KB | Inside Forgejo's data directory |
| `docker-main` | `/opt/docker/homelab-dashboard-aio/data-backup-20260623-222420.tar.gz` | 2.9 KB | |
| `docker-main` | `/opt/docker/wyze-bridge/docker-compose.yml.save` | 694 B | |
| `docker-main` | `/root/.claude/remote/run/6e864a9f/remote-server.log.old` | 333 B | |
| `docker-main` | `/root/.bash_history-04350.tmp` | 0 B | Empty, from an interrupted shell exit |
| `alpha-prod-01` | `/home/<YOUR_ADMIN_USERNAME>/teamspeak-monitor/.env.save` | 41 B | An editor copy of an environment file. Inspect before deleting rather than after. |
| `splunk-siem` | `/home/<YOUR_ADMIN_USERNAME>/backups/internal-https-2026-07-22-prechange/` | 45 B | Holds `splunk-web-configs.tar.gz`, which is 45 bytes and therefore an empty archive |
| `purple-server` | `/root/.ssh/known_hosts.old` | 142 B | |
| `blue-server` | `/root/.ssh/known_hosts.old` | 142 B | |
| `red-server` | `/root/.ssh/known_hosts.old` | 142 B | |
| `grey-server` | `/root/.ssh/known_hosts.old` | small | |
| `ansible-01` | `/root/.ssh/known_hosts.old` | small | Also `/root/internal-https-2026-07-22-prechange.tar.gz` |

Two entries above say to inspect before deleting rather than after, and both mean it. Neither should be opened into anything that gets committed, pasted into a chat, or written to a log. If either turns out to hold live material, handling that is a separate task from this cleanup and does not belong in this file.

## Routine reclaimable, safe on every host

These are the boring wins and they add up to more than the interesting ones.

### Package caches, about 9.7 GB

| Host | Cache | Host | Cache |
|---|---:|---|---:|
| `grey-server` | 3.1 GB | `alpha-prod-01` | 537 MB |
| `security-01` | 1.7 GB | `red-server` | 514 MB |
| `docker-main` | 778 MB | `purple-server` | 511 MB |
| `app-01` | 671 MB | `blue-server` | 511 MB |
| `edge-01` | 347 MB | `kasm-01` | 281 MB |
| `docker-network` | 252 MB | `monitor-01` | 172 MB |
| `media-01` | 139 MB | `docker-blue` | 123 MB |
| `ansible-01` | 74 MB | `splunk-siem` | 22 MB (dnf) |

`apt-get clean` on the Debian and Ubuntu hosts, `dnf clean all` on `splunk-siem`. This is always safe; apt refetches on demand.

### Journals, about 9.2 GB

`grey-server` holds 3.7 GB and `docker-main` 3.9 GB, which together are 82 percent of the fleet total. `security-01` is 541 MB, `blue-server` 404 MB, `purple-server` 344 MB, `red-server` 125 MB, and every other host is under 100 MB.

```bash
journalctl --vacuum-size=200M
```

Better than vacuuming once is capping it, so it never grows back. Set `SystemMaxUse=200M` in `/etc/systemd/journald.conf` and restart `systemd-journald`. A 3.9 GB journal on a Docker host is usually container logging with no rotation limit, so check the daemon's log driver too, or it refills.

### Old kernels on grey-server

Twelve `proxmox-kernel` packages are installed and the host is running 7.0.14-6-pve. Four are already flagged as autoremovable: `6.14.11-6`, `6.17.13-11`, `6.17.13-2`, and `6.17.4-2`.

```bash
apt-get --purge autoremove
```

Keep the running kernel and one known-good fallback. Do not remove `proxmox-kernel-7.0.14-6-pve-signed`. The other three nodes report nothing autoremovable.

`splunk-siem` holds three Rocky kernels, which is `installonly_limit` working as designed. Leave it.

### Unused container images, about 21.7 GB

Excluding `kasm-01` for the reason above.

| Host | Images | Reclaimable |
|---|---:|---:|
| `docker-main` | 32 total, 11 active | 10.77 GB (55%) |
| `app-01` | 16 total, 7 active | 4.44 GB (58%) |
| `media-01` | 19 total, 10 active | 4.43 GB (41%) |
| `alpha-prod-01` | 9 total, 6 active | 1.46 GB (66%) |
| `docker-network` | 9 total, 5 active | 558 MB (17%) |
| `docker-blue` | 4 total, 3 active | 19 MB (5%) |
| `monitor-01` | 7 total, 7 active | none |
| `security-01` | 1 total, 1 active | none |

`docker-main` is the prize. Its dangling images include two Immich layers at 2.17 GB and 1.29 GB, six `homelab-dashboard-aio` builds at roughly 530 MB each, a `forgejo` layer at 185 MB, and a **`termix` image at 360 MB** left over from a service destroyed on 2026-07-28. It also has five unused volumes, and zero stopped containers.

```bash
docker image prune -f
docker volume prune -f
```

Use `docker image prune -f` without `-a`. That removes only dangling untagged images and cannot touch a tagged image a compose project needs. `-a` removes any image without a running container, which on these hosts would delete images that legitimately sit idle. Check the five unused volumes on `docker-main` individually before pruning; a dangling volume is sometimes a database that lost its container.

### Development tool caches

`docker-main` carries 4.0 GB in `/root`, most of it AI CLI state: 749 MB in `.claude`, 502 MB in `.antigravity-server`, 308 MB in `.cache`, 275 MB in `.codex`, and 116 MB in `.npm`. `app-01` has a smaller version of the same, 191 MB total with 83 MB in `.codex`.

These are caches, not artifacts, and they regenerate. Worth clearing on `docker-main` given its size, but they are also the least stale thing in this document.

## Do not touch

- **`kasm-01` workspace images.** Covered above. `docker builder prune -f` only.
- **`/etc/lvm/backup`** on all four nodes. Live volume-group metadata, not a stale copy.
- **`/etc/pve/authkey.pub.old`**, managed by `pve-cluster` through ticket-key rotation.
- **`/root/semaphore.pid`** on `ansible-01`. Runtime state for the running service.
- **`/root/semaphore-backups/`** on `ansible-01`. Documented recovery, cited in the [Runbook](../../Platforms/Ansible/Documentation/Runbook.md) and the [SSH Identity Automation record](../../Platforms/Ansible/Documentation/Change%20Records/SSH%20Identity%20Automation%20-%202026-07-14.md). It holds the pre-upgrade Semaphore 2.17.33 binary, database, and config. Removing it means editing both records first.
- **`/home/ansible/ansible/playbooks/`** on `ansible-01`. This looks like a dead project directory and is not: it is Semaphore's configured `tmp_path`, and the root-owned `project_1/` checkouts under it belong to the running service.
- **`/var/lib/vz/template/cache`** on `blue-server` and `red-server`, 124 MB each. LXC templates, and both nodes run containers.
- **`/opt/docker/nginx-proxy-manager/letsencrypt/archive`** on `docker-network`. Certbot's live certificate store, despite the name. Deleting it breaks every proxied hostname.
- **Package-owned paths** matching `*.bak`, `*.old`, or `*backup*` under `/usr/share` and `/usr/lib`. The 2026-07-26 purge already worked through these; deleting one corrupts an installed package.
- **`/data/coolify`** on `app-01`, and Coolify's generated compose projects. Coolify reconciles its own state.

## Suggested order

1. `docker builder prune -f` on `kasm-01`, and nothing else there.
2. Package caches everywhere. Zero risk, about 9.7 GB.
3. Journal vacuum plus a `SystemMaxUse` cap, starting with `docker-main` and `grey-server`. About 9.2 GB.
4. `docker image prune -f` and `docker volume prune -f` on the six Docker hosts, `kasm-01` excluded. About 21.7 GB.
5. `apt-get --purge autoremove` on `grey-server` for the four superseded kernels.
6. The 18.1 GB of appliance images and installers on `grey-server`, after confirming the two `configure_*.sh` scripts exist in the repository.
7. The small stale files listed per host.
8. The ISO decision, separately and deliberately.

Steps 1 through 5 are mechanical. Step 6 onward wants a human reading each path.

## Verify afterward

Re-run `df -h /` on every host and record the before and after, with `grey-server` the number that matters. Then confirm nothing broke: `pvecm status` reports 4 nodes and `Quorate: Yes`, `pve-firewall status` is `enabled/running` on all four nodes, and every Docker host returns its expected container count. On `kasm-01`, launch one tile and confirm the desktop renders without a pull, which proves the workspace images survived.

Prometheus should still report 48 of 48 targets up. That single check covers most of the fleet at once.

## One thing this survey created

I added an SSH Manager group called `artifact-sweep` holding all 16 profiles, so a single command could hit the fleet in parallel. It is local configuration on the SSH Manager, it changes nothing on any host, and it is the easiest way to run the removals and the verification. Delete it when the work is done, or keep it as the fleet-wide group the manager was missing.
