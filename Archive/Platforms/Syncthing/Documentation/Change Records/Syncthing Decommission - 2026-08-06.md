# Syncthing Decommission

**Created:** 2026-08-06  
**Last updated:** 2026-08-06

**Date:** 2026-08-06  
**Scope:** Remove Syncthing from `docker-main`, destroy the server copy of the Obsidian vault and its version history, and clear the network path. I kept no backup.

## Why

I stopped using the server peer. Syncthing existed so my Obsidian vault had an always-on second copy and 90 days of staggered versions, but I decided I did not want the service any more. The Windows working copy at `D:\Documents\Vault-DK\The Vault` is untouched and is now the only copy.

I chose deletion over preserving the server data first. That was a deliberate call, not an oversight: I was offered a copy of the vault and version history before removal and declined it.

## Starting state

Syncthing 2.1.2 ran on `docker-main` (`192.168.40.35`) in host network mode, healthy since 2026-08-01 15:17:40 UTC. The Compose project and its 708 KB configuration sat at `/opt/docker/syncthing/`. The synchronized data lived at `/data/syncthing`: 17 files and 9,419,543 bytes under `vaults/the-vault`, plus 2 retained version files under `versions/the-vault`. The image was 41.5 MB. The project used bind mounts, so there was no named Docker volume.

The platform reached the network through `syncthing.alphasecunited.com`: a UniFi static A record, NPM proxy host 16 forwarding to `192.168.40.35:8384`, and one Prometheus blackbox probe.

## Step 1: Destroy the service and its data

`docker compose down --rmi all` stopped and removed the `syncthing` container and its image in one pass. I then removed `/opt/docker/syncthing` and `/data/syncthing`.

`docker-main` retains no container, image, volume, directory, or systemd unit matching Syncthing, and nothing listens on TCP or UDP 22000, TCP 8384, or UDP 21027. Twelve Compose projects remain under `/opt/docker/`, and `/data/` holds `booklore` and `immich`.

## Step 2: Remove the Prometheus probe

I dropped the `https://syncthing.alphasecunited.com/` target from `/home/dkadi/monitoring/prometheus.yml` on `monitor-01`, leaving 19 probed service names. `promtool check config` passed.

The reload did not take on the first two attempts, and the reason is worth recording. `POST /-/reload` returned HTTP 403 with `Lifecycle API is not enabled`, so I sent `SIGHUP` instead. That also changed nothing: the container still read the old target list. `prometheus.yml` is a single-file bind mount, and `sed -i` writes a replacement file rather than editing in place, so the container kept the original inode. Recreating the Prometheus service picked up the new file. **A `sed -i` against a single-file bind mount needs a container recreate, not a reload.**

## Step 3: Clear the network path

I deleted NPM proxy host 16 through the `/api/tokens` API path, leaving 20 proxy hosts with none disabled. I then deleted the `syncthing.alphasecunited.com` A record from the UniFi controller, leaving 21 static DNS records.

## Step 4: Archive the records

The platform moved from `Platforms/Syncthing/` to `Archive/Platforms/Syncthing/` with its Compose definition, deployment record, device-addition runbook, alternatives research, troubleshooting index, and deployment evidence. I deleted its backlog: both open items — pairing the laptop and adding an independent vault backup — died with the service.

## Verification

| Check | Result |
|---|---|
| `docker-main` containers and images | No container, image, or volume matching Syncthing |
| `docker-main` filesystem | `/opt/docker/syncthing` and `/data/syncthing` both absent |
| `docker-main` listeners | Nothing on TCP 8384, TCP/UDP 22000, or UDP 21027 |
| `docker-main` systemd | No unit matching Syncthing |
| Prometheus | 48 of 48 targets up, zero down, no Syncthing probe |
| NPM | 20 proxy hosts, none disabled, no Syncthing domain |
| UniFi DNS | 21 records; `syncthing.alphasecunited.com` absent |

## Rollback

None. The container, image, configuration, vault replica, and version history were destroyed with no backup, and this environment keeps none. Rebuilding means a fresh Syncthing deployment and a first-time pair against the Windows vault.

## Follow-up, same day

I closed the two items this record left open.

**The shared UniFi policy is narrowed.** `Allow NPM to docker-main web UIs` listed TCP `2283,3000,3001,6060,8080,8384,9443`. I checked every port against the live listeners on `docker-main` first: 8384 was Syncthing and 8080 was Termix, retired on 2026-07-28, and neither had a listener. The other five answered. The policy now reads `2283,3000,3001,6060,9443`. From NPM at `192.168.85.2` all five remaining ports still connect and both removed ports refuse, and the five affected service probes stayed at `probe_success=1`.

**The stored Syncthing credential is retired.** I archived it rather than destroying it, so it stays recoverable.

## Remaining work

None from this decommission.
