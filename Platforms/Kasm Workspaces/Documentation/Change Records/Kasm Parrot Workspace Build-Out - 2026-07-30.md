# Kasm Parrot Workspace Build-Out

**Created:** 2026-07-30  
**Last updated:** 2026-07-30

**Implemented:** 2026-07-30  
**Owner:** Platforms / Kasm Workspaces  
**Status:** Implemented and verified

## Result

I installed `kasmweb/parrotos-7-desktop:1.19.0-rolling-daily` without repeating the 2026-07-29 thin-pool outage. I added `Parrot OS - Full`, `Parrot OS - Normal`, and `Parrot OS - VPN`, and I renamed the existing lane 77 `Debian - Target` definition to `Debian - Malware` because its network and DNS controls already matched the requested malware tile.

The four disposable verification containers passed. Parrot Full joined `kasm_default_network`, Normal joined `lab75`, VPN joined `lab74`, and Debian Malware joined `lab77`. Normal used the ordinary WAN, VPN used the Proton exit, and Debian Malware had neither DNS nor direct Internet access. I removed the test containers and created one replacement VM snapshot, `baseline-parrot-2026-07-30`.

## Scope

This change covered Docker image cleanup, one controlled Parrot pull, Kasm image-pull policy, three Parrot workspace definitions, one Debian tile rename, lane verification, the replacement snapshot, and the owning records. It did not change UniFi, NPM, the Proton route, Kasm group policy, persistent profile paths, or VM sizing.

## Starting State

VM 122 had zero snapshots after I removed `baseline-tiles-2026-07-28`. Its 200 GiB `scsi0` retained `discard=on`. Before the controlled Parrot pull, I had stopped `kasm_agent`, pruned seven unused dangling images, trimmed the guest filesystem, and reduced `ssd-lvm2` to 51.46 percent. The guest then had 77 GB free.

The first registry install attempt did not leave a Parrot image. It added the Kasm database row, then the agent moved on to Terminal, Claude Code, and Forensic OSINT. That proved the pull was a catalog refresh, not a 108 GiB Parrot image.

## Step-Based Walkthrough

### Step 1: Stop the catalog refresh and recover working space

Kasm's [image-maintenance documentation](https://www.kasmweb.com/docs/latest/how_to/image_maintenance.html) says the agent checks every defined workspace image and pulls registry-backed tags again each hour. The retry showed that behavior in order: Parrot failed to complete, Terminal and Claude Code updated, and Forensic OSINT began next. `ssd-lvm2` climbed from 52.10 to 68.67 percent while the queue remained active.

I stopped only `kasm_agent`. The incomplete Forensic OSINT layers cleared and the pool fell to 61.61 percent. I then verified seven dangling images with no container references and pruned them. Docker reclaimed 7.112 GB. `fstrim -av` submitted 23.1 GiB from `/`, and the pool fell to 51.46 percent. The other seven Kasm services remained running.

The queue, exact cleanup targets, and before-and-after capacity readings are retained in [S00 Pull Queue and Cleanup](../../Evidence/Kasm%20Parrot%20Workspace%20Build-Out%20-%202026-07-30/Logs/S00%20Pull%20Queue%20and%20Cleanup%20-%202026-07-30.md).

### Step 2: Pull only Parrot

With the Kasm agent stopped, I pulled only `kasmweb/parrotos-7-desktop:1.19.0-rolling-daily`. The pull completed with digest `sha256:8dc7c7821c3e69f6e7d4bbef0a55d84f6e4c784851fa729773b273d72dddd736`.

Docker's image inspection reports 13,670,381,122 bytes. Its expanded storage accounting reports 40.92 GB unique, which matches the guest filesystem change better than the image-inspection number: guest use rose from 116 GB to 154 GB. `ssd-lvm2` rose from 51.46 to 67.44 percent, a 15.98-point increase or about 36.45 GiB. The guest retained 39 GB free.

The pull transcript and storage readings are retained in [S01 Controlled Parrot Pull](../../Evidence/Kasm%20Parrot%20Workspace%20Build-Out%20-%202026-07-30/Logs/S01%20Controlled%20Parrot%20Pull%20-%202026-07-30.md).

### Step 3: Stop hourly rolling-image pulls

The Kasm database held 31 workspace definitions with a Docker Registry configured. I set `docker_registry` to `NULL` on those rows, then marked the Parrot source row available with the verified local digest and size. Kasm still launches the local image by `name`; removing the registry field stops the agent from polling every moving `rolling-daily` tag.

I restarted `kasm_agent` and watched its first heartbeats. It returned healthy, performed no Docker pull, and held the pool flat. I then restarted `kasm_api` and `kasm_manager` after the tile changes. All eight services returned, seven health checks reported healthy, and the local root and health endpoints returned HTTP `200`.

This changes image maintenance from automatic to manual. Future updates must pull one named image at a time under live guest and thin-pool monitoring. The database result and agent readback are retained in [S02 Registry Control and Tiles](../../Evidence/Kasm%20Parrot%20Workspace%20Build-Out%20-%202026-07-30/Logs/S02%20Registry%20Control%20and%20Tiles%20-%202026-07-30.md).

### Step 4: Build the requested tiles

I renamed the registry source row to `Parrot OS - Full`, kept its existing `{"hostname":"kasm"}` run configuration, assigned the `Full Access - VLAN 78` category, and left it attached to `All Users`.

I cloned that row twice:

| Tile | Network | DNS | Group | Profile |
| --- | --- | --- | --- | --- |
| `Parrot OS - Normal` | `lab75` | Quad9 | `Lab Sessions` | none |
| `Parrot OS - VPN` | `lab74` | Quad9 | `Lab Sessions` | none |

Both clones preserve the Parrot hostname setting and use the existing 2.77 GiB desktop memory allocation. I did not add a persistent profile to either one.

`Debian - Target` already used `lab77`, DNS `192.168.77.10`, the `Malware - VLAN 77` category, no persistent profile, and `Lab Sessions`. I renamed that row to `Debian - Malware` instead of adding a duplicate definition with identical controls.

### Step 5: Verify the lanes and create the replacement baseline

Short-lived containers returned these results:

| Workspace definition | Observed result |
| --- | --- |
| Parrot Full | `172.18.0.10/16` on `kasm_default_network`; DNS worked |
| Parrot Normal | `192.168.75.208/24`; DNS worked; ordinary-WAN exit |
| Parrot VPN | `192.168.74.208/24`; DNS worked; Proton exit |
| Debian Malware | `192.168.77.208/24`; DNS blocked; direct TCP to `1.1.1.1:443` blocked |

I did not retain either public exit address. Each verification container used `--rm`, and the final Docker list contained only the eight Kasm services.

I created `baseline-parrot-2026-07-30` at 2026-07-30 01:05:48 EDT. Proxmox froze and thawed the guest filesystem around the snapshot. VM 122 now has exactly one snapshot. Pool data stayed at 67.45 percent, all Kasm services remained healthy, and the local health endpoint returned HTTP `200`.

The exact tile readback, lane results, cleanup, and snapshot verification are retained in [S03 Functional and Snapshot Verification](../../Evidence/Kasm%20Parrot%20Workspace%20Build-Out%20-%202026-07-30/Logs/S03%20Functional%20and%20Snapshot%20Verification%20-%202026-07-30.md).

## Final State

- VM 122 is running with `discard=on`.
- `ssd-lvm2` is 68.25 percent allocated with 2.91 percent metadata use at the 01:18 EDT final readback.
- The guest ext4 filesystem is 193 GB total, 154 GB used, and 39 GB available.
- Parrot's verified local digest is `sha256:8dc7c7821c3e69f6e7d4bbef0a55d84f6e4c784851fa729773b273d72dddd736`.
- Kasm has 33 workspace definitions: 14 Full, 19 lane-assigned, and 15 distinct Docker image names.
- Automatic registry pulls are disabled on every workspace definition.
- VM 122 has one snapshot, `baseline-parrot-2026-07-30`.
- No external VM backup exists.

## Capacity Rule

The Parrot pull proved that Kasm's 13.67 GB image-inspection size is not a safe filesystem estimate. The expanded image consumed about 38 GB in the guest and about 36.45 GiB in the thin pool.

I will not start another new workspace-image pull unless `ssd-lvm2` is at or below 55 percent and the guest has at least 70 GB free after pruning and trim. I pull one named image at a time and stop an unexpected queue before the pool reaches 70 percent. The existing 80 percent pool threshold remains the hard stop. The current 68.25 percent pool and 39 GB guest headroom fail the new-image gate.

## Rollback

The full rollback point is:

```bash
qm rollback 122 baseline-parrot-2026-07-30 --start
```

That snapshot already contains this completed change. To remove only the Parrot tiles, delete `Parrot OS - Normal` and `Parrot OS - VPN`, then rename `Parrot OS - Full` back to `Parrot OS 7` and restore its original categories. To restore automatic pulls, set Docker Hub rows back to `https://index.docker.io/v1/` and KCR rows back to `https://kcr.kasmweb.com/v1/`; doing that re-enables hourly checks for all moving tags and must not happen without more storage.

## Linked Records

- [Kasm Thin Pool Exhaustion Paused VM 122](../Troubleshooting/Kasm%20Thin%20Pool%20Exhaustion%20Paused%20VM%20122%20-%202026-07-29.md)
- [Kasm Workspaces Thin Pool Exhaustion Incident](../../../../Security/Incidents/Kasm%20Workspaces/Thin%20Pool%20Exhaustion%20-%202026-07-29.md)
- [Evidence index](../../Evidence/Kasm%20Parrot%20Workspace%20Build-Out%20-%202026-07-30/Evidence-Index.md)
