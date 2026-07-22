# Syncthing Deployment and Operations

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Date:** 2026-07-22  
**Target:** `docker-main` & `D:\Documents\Vault-DK\The Vault`  
**Status:** Complete

## Scope

I deployed Syncthing 2.1.2 on `docker-main`, installed the same version on my Windows PC, paired the two devices, & synchronized the existing Obsidian vault. I kept the Windows path unchanged because Obsidian works from local files; `docker-main` now holds the always-on peer copy.

## Starting State

- The vault contained 15 files in six directories and used 6,430,745 bytes before I added Syncthing metadata.
- `.obsidian` contained the Minimal theme plus the Kanban & Excalidraw plugins.
- Syncthing wasn't installed through WinGet, but `%LOCALAPPDATA%\Syncthing` retained one paused `D:\Pirated` folder and one existing peer. I left both entries unchanged.
- `docker-main` had 62 GiB free on `/` and 398 GiB free on `/data`.
- TCP 8384, TCP/UDP 22000, & UDP 21027 were unused on `docker-main`.

## Decisions

- I pinned both peers to Syncthing 2.1.2 instead of following a floating container tag.
- I used host networking because Syncthing's Docker documentation recommends it for LAN discovery & direct addresses.
- I bound the server GUI to `127.0.0.1:8384`. TCP/UDP 22000 accepts synchronization traffic; the management API isn't published on the LAN.
- I configured direct peer addresses across VLANs. The peers connected between `192.168.50.241:22000` & `192.168.40.35:22000`, so I made no UniFi firewall change.
- I excluded `.obsidian/workspace.json` & `.obsidian/workspace-mobile.json` because these device-specific interface-state files change often. Plugins, themes, hotkeys, & the remaining `.obsidian` files stay synchronized.
- I enabled staggered versioning only on `docker-main`, with a 7,776,000-second maximum age. That equals 90 days.
- I created a pre-sync ZIP before pairing. Sync still isn't a backup, so a recurring independent backup remains in the [platform TODO](TODO.md).

## Step 1: Inspect the Source and Target

I counted the vault, checked for an existing Windows process or listener, inspected the Docker Compose layout, & ran the SSH Manager health check against `docker_main`. The source contained 15 files totaling 6,430,745 bytes; the server reported 13.34 percent memory use, 35 percent root use, & 78 percent `/data` use. I didn't retain the exact initial inspection transcript; the evidence record labels these values as a historical summary and includes a fresh current-state transcript.

The retained result is in the [deployment verification log](../Evidence/Syncthing%20Deployment%20-%202026-07-22/Logs/Syncthing-Deployment-Verification-2026-07-22.txt).

## Step 2: Back Up the Vault and Deploy the Server Peer

I created `D:\Documents\Vault-DK\Backups\The Vault - Pre-Syncthing - 2026-07-22.zip` before changing the vault. The 3,162,663-byte archive contains 22 entries and includes `.obsidian`.

I deployed the versioned [Compose definition](../Configuration/docker-compose.yml) to `/opt/docker/syncthing/docker-compose.yml`. The first container restart loop failed before Syncthing started because `cap_drop: ALL` blocked the image entrypoint's `chown` & `setgroups` calls. I removed that capability drop, retained `no-new-privileges`, & recreated the container. The resolved failure is recorded in [Syncthing Container Restarted After Capability Drop](Troubleshooting/Syncthing%20Container%20Restarted%20After%20Capability%20Drop%20-%202026-07-22.md).

The corrected container reached `healthy` with zero restarts. Its repository configuration & deployed Compose file share SHA-256 `deedb6cec5e1d82c4add632857043cc99a9a2e38b1b494ba0ed8dbae19b5bce8`. I didn't retain the exact deployment transcript; the evidence record includes a fresh Compose validation, container inspection, & deployed-file hash.

## Step 3: Pair the Windows Vault

I installed Syncthing 2.1.2 from WinGet package `Syncthing.Syncthing`, started it with `--no-browser --no-restart`, & created a per-user Startup shortcut with those arguments. The local GUI listens on `127.0.0.1:8384`.

I added `docker-main` as a peer without removing the pre-existing device or paused `D:\Pirated` folder. Both new peers use folder ID `obsidian-the-vault` in `sendreceive` mode. The direct connection negotiated TLS 1.3 with `TLS_AES_128_GCM_SHA256`; the initial Windows-to-server transfer sent 6,430,456 protocol bytes. I didn't retain the exact pairing transcript; the evidence record includes a fresh Windows connection check.

## Step 4: Verify Synchronization and Recovery

The synchronized user/config dataset contains 14 files totaling 6,425,692 bytes after excluding the existing workspace file & Syncthing metadata. A fresh canonical SHA-256 manifest generated independently on Windows and `docker-main` produced the same digest, `b00c4ff828260190c624a27dc664c9e689044ca82360b5727582fb51e03e3edc`. The earlier 15-file comparison had counted the 129-byte `.stfolder` sentinel on the server; the fresh count corrects that evidence-summary error.

I created one 48-byte temporary file on `docker-main`. Windows received SHA-256 `cfadef558503607980c41560476df51c2bb1a3b005000ad1f6f9e00f8f30e097`; I deleted it from Windows, `docker-main` removed the live copy, & staggered versioning archived the same hash as `.syncthing-verification-20260722~20260722-035101.txt`.

I restarted the Compose service after configuration. The container returned `healthy`, the Windows peer reconnected directly, & the GUI health endpoint returned `OK`. I didn't retain the exact initial round-trip or restart transcripts; the evidence record distinguishes those historical observations from the fresh reproducible checks.

## Resulting Configuration

| Item | Result |
|---|---|
| Server image | `syncthing/syncthing:2.1.2` |
| Server image ID | `sha256:62cee511289c3fcbaec0d0eaf1be0d24cfc329f641a6ab38d843bf9128f632f8` |
| Server state | `running`, `healthy`, restart count 0 |
| Server GUI | `127.0.0.1:8384` only |
| Direct synchronization | TCP 22000 between VLAN 50 & VLAN 40 |
| Included dataset | 14 files, 6,425,692 bytes, matching canonical manifest SHA-256 on both peers |
| Server versioning | Staggered, 90 days, `/data/syncthing/versions/the-vault` |
| Persistent ownership | UID/GID 1000, mode 0750 |
| Windows startup | Per-user `Syncthing.lnk`, `--no-browser --no-restart` |
| Pre-sync recovery copy | 3,162,663-byte ZIP with `.obsidian` present |

## Operations

Check or restart the server peer from `/opt/docker/syncthing`:

```bash
docker compose ps
docker compose logs --tail 100 syncthing
docker compose restart syncthing
```

The server GUI isn't exposed. From a computer with SSH access, forward it to local TCP 8385 so it doesn't collide with the Windows peer's TCP 8384 listener:

```bash
ssh -L 8385:127.0.0.1:8384 root@192.168.40.35
```

Then open `http://127.0.0.1:8385`. The Windows GUI remains at `http://127.0.0.1:8384`.

Upgrade only after reviewing the target release. Change the image tag in the versioned repository Compose file, copy that same file to `/opt/docker/syncthing/docker-compose.yml`, then pull & recreate the service:

```bash
cd /opt/docker/syncthing
docker compose pull
docker compose up -d
docker compose ps
docker compose exec syncthing syncthing --version
```

Confirm the reported version matches the reviewed tag and record the new repository/deployed Compose SHA-256 values.

## Rollback

To stop server synchronization without deleting data, run `docker compose down` under `/opt/docker/syncthing`. Keep `/opt/docker/syncthing/config` & `/data/syncthing` until the local vault and recovery requirements are confirmed.

On Windows, remove folder `obsidian-the-vault` from Syncthing, remove the `docker-main` peer, stop Syncthing, & delete the Startup shortcut. Do not delete `D:\Documents\Vault-DK\The Vault`; it remains the Obsidian working copy. The pre-sync ZIP is the recovery point for the original 15-file state.

## Remaining Work

- Pair the laptop after its operating system, local vault path, & network access are known.
- Add a recurring backup that can recover data after a synchronized deletion or corrupted write.
