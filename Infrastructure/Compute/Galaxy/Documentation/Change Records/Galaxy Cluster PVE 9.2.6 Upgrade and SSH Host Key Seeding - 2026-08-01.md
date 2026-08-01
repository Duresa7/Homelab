# Galaxy Cluster PVE 9.2.6 Upgrade and SSH Host Key Seeding

**Created:** 2026-08-01  
**Last updated:** 2026-08-01

## What I Did

I upgraded all five Galaxy nodes from Proxmox VE 9.2.5 to 9.2.6, rebooted them one at a time onto kernel `7.0.14-8-pve`, and seeded the cluster SSH host key store that had been empty since the cluster was built. I also cleared the last three PeaNUT transcripts off Red and made the drive serial redactions in this repo follow one scheme instead of three.

The cluster ran 12 guests before this work and runs the same 12 now. Nothing migrated between nodes, which was the point of turning HA off first.

## Why the Kernel Was Uneven

Green booted `7.0.2-6-pve`, the kernel its PXE install laid down on 2026-07-31. It had `7.0.14-8` sitting on disk unused, because a kernel only takes effect at boot. The other four ran `7.0.14-6-pve` & didn't yet have `7.0.14-8` installed at all.

So Green was behind the fleet on the running kernel while being ahead of it on the installed one. A single `dist-upgrade` pass plus a reboot put all five on the same `7.0.14-8-pve`.

## Turning HA Off

Two containers sit under HA: `ct:107` (docker-network) & `ct:108` (docker-blue), both on Blue. Before this work `ha-manager status` showed fencing armed with the CRM watchdog active & Blue's LRM active with its watchdog armed.

I set both to `state ignored` rather than `disabled`, because `disabled` stops the guest & `ignored` leaves it running while removing it from HA management. Both containers carry `onboot: 1`, so Blue's normal boot sequence starts them whether HA is watching or not.

Roughly ten minutes later Blue's LRM dropped to `idle, watchdog standby`, matching the other four. That's the state I wanted before rebooting anything: no node holding an armed fencing watchdog.

The `pin-blue-local-storage` node-affinity rule stayed untouched throughout. It pins both containers to Blue with `strict 1` because they live on node-local `local-lvm` and there's no shared storage to fail over to. I restored both resources to `state started` after the last reboot & confirmed the rule was still intact.

## Reboot Order and Results

I worked from smallest blast radius to largest, waiting for each node to rejoin quorum & report the new kernel before starting the next.

| Order | Node | Guests affected | Down for | Kernel after |
|---|---|---|---|---|
| 1 | green-server | none | 65 s | `7.0.14-8-pve` |
| 2 | purple-server | kasm-01 | 80 s | `7.0.14-8-pve` |
| 3 | red-server | media-01 | 70 s | `7.0.14-8-pve` |
| 4 | blue-server | monitor-01, docker-network, docker-blue | 60 s | `7.0.14-8-pve` |
| 5 | grey-server | 7 guests | 170 s | `7.0.14-8-pve` |

Grey took the longest because it had five QEMU guests to shut down gracefully. The CRM master moved on its own as nodes cycled, from Red to Grey to Blue, and quorum stayed at 5 votes the whole time.

Grey's reboot is the one with real reach. It hosts `edge-01`, which terminates the Cloudflare tunnel, so external access was down for those 170 seconds along with Coolify on `app-01` and Wazuh on `security-01`.

## Two Guests That Don't Autostart

`splunk-siem` (109) & `security-01` (200) were running on Grey before the reboot but carry `onboot: 0`, so they stayed down after it. I started both with `qm start`. Every other running guest came back on its own.

This is worth knowing before any future Grey reboot: the node's guest list & its autostart list don't match, and five of Grey's eleven configured guests are deliberately stopped templates or dev boxes.

Red's `media-01` looked stopped when I first checked, about ten seconds after boot. It wasn't broken. The container config sets `startup: order=40,up=30`, so it waits 30 seconds, and its Seagate is mounted through `x-systemd.automount`, which doesn't attach until something reads the path. Both resolved without help. The container now reports 916 GB at `/data` with 175 GB used.

## What the Upgrade Actually Changed

Beyond the kernel, every node moved `pve-manager` 9.2.5 to 9.2.6, `pve-ha-manager` 5.2.4 to 5.2.5, `pve-qemu-kvm` 11.0.2-1 to 11.0.3-1, `pve-container` 6.1.11 to 6.1.12, & `qemu-server` 9.2.0 to 9.2.1. Grey, Purple, Blue & Red also picked up Ceph 19.2.4-pve1 to 19.2.5-pve2 and the Debian security updates for `libexpat1` (2.7.1-2 to 2.8.2-1~deb13u1), `libnss3`, & the Samba libraries.

I ran the upgrade as a full `dist-upgrade` rather than trying to pull the kernel alone. You can't get `proxmox-kernel-7.0` 7.0.14-8 without the packages it's built against, and running mixed `pve-manager` versions across a cluster causes more trouble than the reboot does.

The subscription popup patch survived on all five. Each run ended with `proxmox-widget-toolkit 5.2.6: popup patch already present`, which is the `DPkg::Post-Invoke` hook doing its job. After the last reboot all five nodes reported 0 packages upgradable.

## The Empty Host Key Store

Ad-hoc root SSH between cluster members failed in both directions on every pair. The cause was three separate gaps, not one.

`/etc/pve/priv/known_hosts` held a single line, an `ssh-rsa` entry for Grey, and all five `/etc/pve/nodes/<node>/ssh_known_hosts` files were empty. `pvecm updatecerts` runs clean on every node & does not repopulate them.

The `/etc/ssh/ssh_known_hosts` symlink that points at the cluster file existed only on Grey. Purple, Blue, Red & Green had no such file, so even a correct cluster store would have gone unread on four of five nodes.

Every node's `/etc/hosts` carried only its own entry. So `ssh purple-server` from Blue failed at name resolution before host key checking ever came up.

I fixed all three. I collected the ed25519, RSA & ECDSA public keys from each node and wrote 15 lines to `/etc/pve/priv/known_hosts`, each keyed to five names: the short hostname, `<node>.galaxy`, `<node>.local`, the MGMT-A address on 192.168.70.0/24, and the Cluster-Net address on 192.168.71.0/24. Because `/etc/pve` is replicated, that one write covered the cluster. Then I created the missing symlink on the four nodes lacking it and appended the four peer entries to each node's `/etc/hosts`, matching the `<node>.galaxy <node>` form already in use.

Verification was all 20 ordered pairs by hostname and the same 20 by IP, each with `StrictHostKeyChecking=yes`. All 40 returned the correct hostname. I re-ran the check after every node had rebooted and got 25 of 25 including self-connections.

## PeaNUT Transcripts Cleared From Red

Red held three files in `/root` from the 2026-07-22 NUT work, 10,005 bytes total. Two of them turned out to be byte-identical, once line endings are normalised, to transcripts already captured in [the deployment evidence folder](../../../../../Platforms/PeaNUT/Evidence/PeaNUT%20UPS%20Dashboard%20Deployment%20-%202026-07-22/Evidence-Index.md) under undated filenames. Only `S03-NUT-Configure-red-server.txt` was new, the 6-line run that exited 3 before the USB permission fix landed.

I kept the new one, added it to the evidence index, and deleted all three from Red. `/root` on Red now holds nothing but shell dotfiles & `.ssh`.

That evidence folder had never been added to the repository. Every file in it was caught by the global `**/Evidence/` ignore, including an `Evidence-Index.md` linking to files git couldn't see. I added an allowlist block for it covering the index, the 11 log transcripts & the dashboard screenshot. I read all 11 transcripts and opened the screenshot before allowing any of it: the transcripts carry package output, systemd symlinks & udev rules, and the screenshot shows the two UPS units with charge and load. No serials, no credentials.

NUT came back healthy on Red after its reboot, with `ups01` reporting 100 percent charge and status `OL`.

## Serial Redactions Now Follow One Scheme

The drive captures under [Components/Drives](../../../../Hardware/Components/Drives/) used three redaction styles at once. Most files showed `****` plus the last four characters for serials and `[redacted]` for WWN and EUI-64 values, but four files broke that pattern with `<YOUR_DRIVE_SERIAL>`, `<YOUR_DRIVE_WWN>`, or `[redacted; suffix 2896]`.

I normalised those four to the dominant scheme, preserving smartctl's own column alignment: `****252T`, `****6NSN`, `****G91N`, & `****2896` for serials, `[redacted]` for the WWN lines. All 20 serial and WWN lines across the drive captures now match.

The full Samsung serial itself was already out of the working tree. It remains in this repository's published git history, which no edit to the current files can change.

## Verification

- All five nodes report `7.0.14-8-pve` & `pve-manager/9.2.6`, with 0 packages upgradable.
- `pvecm status` shows 5 of 5 votes and `Quorate: Yes`.
- `ha-manager status` shows `ct:107` & `ct:108` back at `started` on Blue, with the `pin-blue-local-storage` rule unchanged.
- 12 guests running, the same 12 as before the work.
- 25 of 25 SSH pairs verify under `StrictHostKeyChecking=yes`.
- `monitor-01` reports Grafana, Prometheus, PeaNUT, cAdvisor, blackbox-exporter, pve-exporter & nut-exporter up.
- `docker-network` reports NetBird server & dashboard and Nginx Proxy Manager up; `docker-blue` reports hbbs & hbbr up.
- `media-01` reports Jellyfin, Sonarr, Radarr, Prowlarr, qBittorrent behind Gluetun, Jellyseerr & Flaresolverr up.
- `docker-main` reports Forgejo, Immich, Syncthing, Booklore, MariaDB & Portainer up.
- `kasm-01` reports its proxy, agent, API, manager & both RDP gateways up.
- `edge-01` reports `caddy.service` & `cloudflared.service` active, with Caddy listening on port 80.

Two results look like failures & aren't. `edge-01` returns nothing from `docker ps` because it runs Caddy and cloudflared as native systemd units, not containers. `ansible-01` reports `degraded` because `openipmi.service` fails, which it always will inside an LXC with no hardware to drive; Semaphore is active.

A reachability sweep run from Grey against the guest addresses is not a useful health signal, because Grey sits on VLAN 70 and has no route to VLANs 40, 72, 73, 78, 85 or 90. I checked each guest directly instead.

## Still Open

Grey carries `.claude`, `.claude.json`, & `.codex` in `/root`. Those are agent configuration rather than artifacts of any change, & they predate this work. Carried forward unchanged from the [2026-07-31 cleanup](../../../../../Operations/Maintenance/Galaxy%20Artifact%20Cleanup%20and%20Green%20SSH%20Parity%20-%202026-07-31.md).

Grey's own `/etc/hosts` entry still reads `grey-server grey-server.local` while the other four use the `.galaxy` suffix that the cluster TLS certificates use. I added `.galaxy` aliases for Grey on the peers & left Grey's self-entry alone rather than change how a running node resolves its own name. Worth tidying during a future maintenance window.
