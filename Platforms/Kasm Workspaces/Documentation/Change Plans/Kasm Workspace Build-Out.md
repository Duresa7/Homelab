# Kasm Workspace Build-Out

**Created:** 2026-07-28  
**Last updated:** 2026-07-29

**Status:** Executed 2026-07-28  
**Completion record:** [Kasm Workspace Build-Out - 2026-07-28](../Change%20Records/Kasm%20Workspace%20Build-Out%20-%202026-07-28.md)

This plan turns the 15 registry images I installed on `kasm-01` into 19 lane-assigned workspace tiles, adds a fourth session lane for tools that need real Internet & saved state, grows the VM's disk, & moves my day-to-day account onto the locked-down group. The isolation plumbing for lanes 74, 77, & 79 already exists & was proven on 2026-07-28; see [Kasm Session Isolation - 2026-07-28](../Change%20Records/Kasm%20Session%20Isolation%20-%202026-07-28.md). Nothing in that record gets redone here.

Execute the phases in order. Phase 3 is a gate: if it fails, stop & report rather than continuing.

## Access

`kasm-01` has no SSH Manager profile, & the LAB-MGMT firewall blocks SSH from `purple-server`. Reach the VM through the QEMU guest agent instead, which is confirmed working:

```bash
qm guest exec 122 --timeout 60 -- /bin/bash -c "<command>"
```

Run that from `purple_server` over the SSH Manager MCP. The guest agent runs as root inside the VM, so no credential is needed anywhere in this plan. Database work goes through `docker exec kasm_db psql -U kasmapp -d kasm`.

## Decisions already made

Do not reopen these. I settled them on 2026-07-28.

Claude Code, Codex CLI, & Terminal get their own lane rather than sitting on the management VLAN. That lane is VLAN 75 & it carries real Internet through the normal WAN, not Proton.

Nessus, Hunchly, & Telegram get persistent profiles on lane 74. Nessus re-downloads a plugin feed of a gigabyte or more per launch without one, & Hunchly is keyed per install.

`alpha` is my daily account & gets every lab tile. `dkadi` stays admin-only. `alpha` stays a single account rather than splitting the persistent tiles onto a second one. That has a cost, recorded under "Consequences I accepted".

The 15 original registry entries stay enabled & attached to All Users, because I want an unisolated session available when I deliberately choose one. They get renamed so I can't confuse one with a lane tile.

## Measured starting state, 2026-07-28

VM 122 runs on `purple-server` with 4 vCPU & 8192 MB. Disk `scsi0` is `ssd-lvm2:vm-122-disk-1` at 150 GB. Inside the VM, `/dev/sda1` is 145 GB with 117 GB used & 28 GB free, which is 81 percent. Docker holds 23 images totalling 114.1 GB. REMnux alone is 32.3 GB, Kali 15.9 GB, Debian Trixie 15.3 GB, Fedora 14.5 GB.

The `ssd-lvm2` thin pool is 228.11 GB with data at 50.37 percent & metadata at 2.26 percent. Its volume group has 124 MB unallocated, so the pool itself can't be extended. About 113 GB of pool data space is free.

Memory shows 7.7 GiB total with 2.0 GiB held by Kasm's eight running containers, leaving roughly 5.7 GiB for sessions.

Inside the VM, `eth0` is 192.168.78.10 with the default route via 192.168.78.1. The macvlan parents are `enp6s19` for lab74, `enp6s20` for lab77, & `enp6s21` for lab79, each a `/24` with an IPAM range of `x.x.x.208/28` & gateway `x.x.x.1`. Host shims `shim74`, `shim77`, & `shim79` hold `x.x.x.201/32` with a route to the matching `/28`. They come from `/usr/local/sbin/kasm-lab-shims`, run once at boot by `kasm-lab-shims.service` ordered before `docker.service`.

Kasm has three groups: Administrators at priority 1, Lab Sessions at 100, All Users at 1000. Lower priority wins. `dkadi` belongs to all three. `alpha` belongs to All Users only, so today it inherits downloads, clipboard, persistence, & storage mappings all enabled. Lab Sessions has zero workspaces attached; the 15 originals are attached to All Users.

The `images` table carries exactly one unique index, on `image_id`, which defaults to `uuid_generate_v4()`. Nothing constrains `name` or `friendly_name`, so several tiles can point at one image. `run_config` is `NOT NULL` json.

UniFi has 26 networks & 15 zones. VLANs 74, 77, 78, & 79 are the lab; 75 & 76 are unused. The gateway carries 99 user-defined policies.

## Phase 0: snapshot & disk

Take the snapshot first. Everything after this point is reversible only because of it.

```bash
qm snapshot 122 pre-workspace-buildout-2026-07-28
```

Shut the VM down cleanly. Phase 2 adds a NIC & I want deterministic interface naming rather than a hotplug result.

```bash
qm shutdown 122 --timeout 300
```

Resize `scsi0` to 200 GB. The value is absolute, not an increment.

```bash
qm resize 122 scsi0 200G
```

200 GB is deliberate & is not the maximum. The pool is 228.11 GB, so a fully written 200 GB disk plus the 8 MB of `vm-122-disk-0` & `vm-122-cloudinit` leaves about 28 GB of pool slack. That slack is what a snapshot needs to hold divergence while the VM keeps writing. 220 GB would still fit the pool but would leave a snapshot nowhere to go, & thin pool exhaustion on a running VM produces I/O errors rather than a warning. Do not exceed 200 GB without redoing this arithmetic.

Start the VM, then grow the partition & filesystem.

```bash
qm start 122
```

```bash
qm guest exec 122 --timeout 120 -- /bin/bash -c "growpart /dev/sda 1 && resize2fs /dev/sda1 && df -h /"
```

Confirm the filesystem reports about 195 GB with roughly 78 GB free. If `growpart` says the partition is already at maximum, the resize never reached the guest; check that `lsblk` shows `sda` at 200 GB before running `resize2fs` again.

## Phase 1: VLAN 75 network, zone, & policies

Create the network through the UniFi MCP, mirroring the three existing lanes.

| Field | Value |
| --- | --- |
| Name | `KASM-TRUSTED` |
| Purpose | corporate |
| VLAN | 75 |
| Subnet | 192.168.75.1/24 |
| DHCP | enabled, 192.168.75.100 to 192.168.75.199 |

The DHCP range matches the other lanes for consistency. Container addresses come from Docker's IPAM at `192.168.75.208/28`, not from DHCP.

Create a firewall zone named `KASM-TRUSTED` holding only that network, then create these 17 policies. Index values matter: the gateway catchall sits below its two allows, exactly how `KASM-BROWSER` is arranged today.

| Policy name | Action | Index | Protocol | Source | Destination |
| --- | --- | ---: | --- | --- | --- |
| `KASM Allow KASM-TRUSTED DHCP to Gateway` | ALLOW | 10000 | UDP | KASM-TRUSTED / 68 | Gateway / 67 |
| `KASM Allow KASM-TRUSTED NTP to Gateway` | ALLOW | 10002 | UDP | KASM-TRUSTED / Any | Gateway / 123 |
| `KASM Block KASM-TRUSTED Other Gateway` | BLOCK | 10003 | All | KASM-TRUSTED / Any | Gateway / Any |
| `KASM Allow KASM-TRUSTED to External` | ALLOW | 10000 | All | KASM-TRUSTED / Any | External / Any |
| `KASM Block KASM-TRUSTED to KASM-BROWSER` | BLOCK | 10000 | All | KASM-TRUSTED / Any | KASM-BROWSER / Any |
| `KASM Block KASM-TRUSTED to MALWARE-OFFLINE` | BLOCK | 10000 | All | KASM-TRUSTED / Any | MALWARE-OFFLINE / Any |
| `KASM Block KASM-TRUSTED to EVIDENCE-QUARANTINE` | BLOCK | 10000 | All | KASM-TRUSTED / Any | EVIDENCE-QUARANTINE / Any |
| `KASM Block KASM-TRUSTED to LAB-MGMT` | BLOCK | 10000 | All | KASM-TRUSTED / Any | LAB-MGMT / Any |
| `KASM Block KASM-BROWSER to KASM-TRUSTED` | BLOCK | 10000 | All | KASM-BROWSER / Any | KASM-TRUSTED / Any |
| `KASM Block MALWARE-OFFLINE to KASM-TRUSTED` | BLOCK | 10000 | All | MALWARE-OFFLINE / Any | KASM-TRUSTED / Any |
| `KASM Block EVIDENCE-QUARANTINE to KASM-TRUSTED` | BLOCK | 10000 | All | EVIDENCE-QUARANTINE / Any | KASM-TRUSTED / Any |
| `LABMGMT Block to KASM-TRUSTED` | BLOCK | 10000 | All | LAB-MGMT / Any | KASM-TRUSTED / Any |
| `KASM Block KASM-TRUSTED to Internal` | BLOCK | 10000 | All | KASM-TRUSTED / Any | Internal / Any |
| `KASM Block KASM-TRUSTED to <ORG>-Servers` | BLOCK | 10000 | All | KASM-TRUSTED / Any | `<ORG>`-Servers / Any |
| `KASM Block KASM-TRUSTED to <ORG>-Mgmt` | BLOCK | 10000 | All | KASM-TRUSTED / Any | `<ORG>`-Mgmt / Any |
| `KASM Block KASM-TRUSTED to <ORG>-Access` | BLOCK | 10000 | All | KASM-TRUSTED / Any | `<ORG>`-Access / Any |
| `KASM Block KASM-TRUSTED to <ORG>-Observability` | BLOCK | 10000 | All | KASM-TRUSTED / Any | `<ORG>`-Observability / Any |

`<ORG>` is a placeholder in this repository. Use the live zone names the controller reports.

The explicit External allow is there on purpose. `MALWARE-OFFLINE` & `EVIDENCE-QUARANTINE` each carry an explicit External block while `KASM-BROWSER` carries none, so the default behaviour for a custom zone toward External isn't documented anywhere I trust. State the intent instead of inheriting it.

Read the `KASM Lab Proton Egress` traffic route & confirm its source is VLAN 74 only. VLAN 75 must not appear there, or the trusted lane loses Internet whenever the tunnel drops.

If `unifi_update_firewall_policy` refuses an index change it returns success while reporting that index was not applied. Use `unifi_get_firewall_policy_ordering` & `unifi_reorder_firewall_policies` instead, then re-read the ordering to confirm.

## Phase 2: NIC, macvlan, & shim for lane 75

Add the NIC with the per-NIC firewall off. Proxmox applies an ebtables MAC filter when `firewall=1` & that filter drops macvlan child traffic, which is why `net1` through `net3` all carry `firewall=0`.

```bash
qm set 122 --net4 virtio,bridge=vmbr0,tag=75,firewall=0
```

Start the VM & read the interface list. The name will probably be `enp6s22`, following `enp6s19` through `enp6s21`, but confirm it rather than assume.

```bash
qm guest exec 122 --timeout 60 -- /bin/bash -c "ls -1 /sys/class/net/ && ip -brief link show"
```

Append one line to `/usr/local/sbin/kasm-lab-shims`, substituting the interface name you just read:

```sh
create_shim shim75 enp6s22 192.168.75.201/32 192.168.75.208/28
```

Create the Docker network & bring the shim up.

```bash
qm guest exec 122 --timeout 120 -- /bin/bash -c "docker network create -d macvlan --subnet 192.168.75.0/24 --gateway 192.168.75.1 --ip-range 192.168.75.208/28 -o parent=enp6s22 lab75 && systemctl restart kasm-lab-shims && ip -brief addr show shim75 && ip route get 192.168.75.208"
```

`shim75` must hold `192.168.75.201/32`, & the route to `192.168.75.208/28` must resolve through `shim75`. A host can't reach its own macvlan children through the parent NIC, which is the whole reason these shims exist. Without it a session starts & then never displays.

Reboot once & confirm `shim75` comes back on its own. A shim that exists only because someone ran a command is a shim that disappears at the next power cut.

## Phase 3: gate, prove the run config override works

Everything downstream assumes Kasm passes `network` & `dns` from a workspace's Docker Run Config Override through to Docker. That was never proven. The 2026-07-28 containment tests used bare `docker run` containers, not a workspace launch.

Create one tile only, `Debian - Target 77`, using the Phase 5 method, & complete Phase 4 so `alpha` can see it.

**Operator action:** I launch `Debian - Target 77` as `alpha` & leave it running.

Inspect the live container from the host:

```bash
qm guest exec 122 --timeout 60 -- /bin/bash -c "cid=\$(docker ps --filter ancestor=kasmweb/debian-trixie-desktop:1.19.0-rolling-daily -q | head -1); docker inspect \$cid --format 'nets={{range \$k,\$v := .NetworkSettings.Networks}}{{\$k}}={{\$v.IPAddress}} {{end}} dns={{.HostConfig.Dns}} mounts={{range .Mounts}}{{.Source}} {{end}}'; docker exec \$cid cat /etc/resolv.conf"
```

Three things must all hold. The container's only network is `lab77` with an address between 192.168.77.208 & 192.168.77.223. `HostConfig.Dns` reads `[192.168.77.10]`. `/etc/resolv.conf` names 192.168.77.10 & not 127.0.0.11.

If `nets` shows `kasm_default_network` or a `172.17` or `172.18` address, Kasm ignored the `network` key. If `dns` is empty & `resolv.conf` points at 127.0.0.11, Kasm accepted the network but dropped the DNS key, & the lane resolves names through the management host. Either result fails the gate.

**On failure, stop & report.** Do not build the remaining tiles. The fallback is the `restrict_to_network` & `restrict_network_names` columns on `images`, which are Kasm's own network-pinning fields, combined with a `--dns` option on the `lab77` Docker network itself. That is a different design & needs my decision, not an improvised substitution.

## Phase 4: group & account setup

Add `alpha` to Lab Sessions. Its priority of 100 beats All Users at 1000, so Lab Sessions settings win for every session `alpha` launches.

Then set these on Lab Sessions. Four are new, one is a change, & the rest already hold the right value & only need confirming.

| Setting | Value | Why |
| --- | --- | --- |
| `allow_kasm_printing` | False | New. Kasm's print path renders to PDF & delivers it to the browser, which is a download by another name while `allow_kasm_downloads` is False. |
| `allow_user_storage_mapping` | False | New. All Users permits two mappings per user. A mapping is an inbound & outbound file path on any lane with Internet. |
| `allow_kasm_sharing` | False | New. Sharing hands out a viewer link to a running session. |
| `allow_kasm_microphone` | False | New. All Users permits it & no lab workspace needs it. |
| `max_kasms_per_user` | 2 | New. All Users sets 5, which the VM's memory can't serve. See "Consequences I accepted". |
| `allow_persistent_profile` | True | Changed from False. Required for the five persistent tiles, & the reason the disposability guarantee moves to the per-workspace profile path. |
| `allow_kasm_downloads` | False | Confirm unchanged. |
| `allow_kasm_clipboard_up`, `_down`, `_seamless` | False | Confirm unchanged. |
| `allow_kasm_uploads` | True | Confirm unchanged. Uploads ride my HTTPS session to Kasm, not the container's network, which is how a sample reaches an offline lane. |
| `session_time_limit` | 3600 | Confirm unchanged. |

Leave All Users alone. `dkadi` needs a working admin session & the 15 originals stay attached there.

## Phase 5: create the 19 tiles

Clone each source row rather than composing a new one. The source rows came from the registry through Kasm's own code, so a clone is structurally identical to what the UI produces & I don't have to guess at 50 columns. Change only the friendly name, the run config, the memory, the profile path, & the category.

Merge the run config, never replace it. Chrome, Claude Code, Codex CLI, Forensic OSINT, & Tor carry `{"hostname": "kasm"}`; Nessus carries `{"user": "root"}`; Terminal carries a hostname plus a `TERMINAL_ARGS` environment block. Overwriting any of those breaks the workspace.

Inspect `group_images` before inserting into it, since I have not confirmed its column list:

```bash
qm guest exec 122 --timeout 60 -- /bin/bash -c "docker exec kasm_db psql -U kasmapp -d kasm -c '\\d group_images'"
```

The pattern for one tile, run inside `kasm_db`:

```sql
INSERT INTO images (
  cores, description, docker_registry, docker_token, docker_user, image_src, enabled, available,
  friendly_name, hash, memory_bytes, name, x_res, y_res, run_config, volume_mappings,
  persistent_profile_path, restrict_to_network, restrict_network_names, allow_network_selection,
  restrict_to_server, exec_config, restrict_to_zone, categories, require_gpu, gpu_count,
  gpu_graphics_acceleration, gpu_video_encoding, hidden, image_type, cpu_allocation_method,
  uncompressed_size_bytes, launch_config
)
SELECT cores, description, docker_registry, docker_token, docker_user, image_src, enabled, available,
  'Debian - Target 77', hash, 2902458368, name, x_res, y_res,
  (run_config::jsonb || '{"network":"lab77","dns":["192.168.77.10"]}'::jsonb)::json,
  volume_mappings, NULL, restrict_to_network, restrict_network_names, allow_network_selection,
  restrict_to_server, exec_config, restrict_to_zone,
  '["Lane 77 - Malware Offline"]'::json, require_gpu, gpu_count,
  gpu_graphics_acceleration, gpu_video_encoding, false, image_type, cpu_allocation_method,
  uncompressed_size_bytes, launch_config
FROM images WHERE friendly_name = 'Debian Trixie';
```

`image_id`, `created_at`, & `updated_at` are left to their defaults. Attach each new row to Lab Sessions & to nothing else, so the tiles never appear for an account I have not put in that group.

Kasm's API service may hold the workspace list in memory. If new tiles do not appear on the dashboard, restart `kasm_api` & `kasm_manager` & check again before assuming the insert was wrong.

One source name has a trailing space: the Chrome row's `friendly_name` is `Chrome ` & not `Chrome`. Match it exactly or the insert selects nothing & silently creates no row.

Create the six profile directories before the tiles that use them, one per workspace so no two share a path:

```bash
qm guest exec 122 --timeout 60 -- /bin/bash -c "for d in claude-code codex-cli terminal-trusted nessus hunchly telegram; do mkdir -p /var/lib/kasm-profiles/\$d && chown 1000:1000 /var/lib/kasm-profiles/\$d; done && ls -la /var/lib/kasm-profiles/"
```

### The 19 tiles

`Source` is the exact `friendly_name` to select from. `Profile` is the `persistent_profile_path`, & an empty cell means `NULL`. Memory is in bytes: 2902458368 is 2.77 GiB, 4294967296 is 4 GiB, 1610612736 is 1.5 GiB. Cores stay at 2 everywhere.

| Tile | Source | Run config merge | Memory | Profile | Category |
| --- | --- | --- | ---: | --- | --- |
| `Claude Code - Trusted 75` | Claude Code | `{"network":"lab75","dns":["9.9.9.9","149.112.112.112"]}` | 2902458368 | `/var/lib/kasm-profiles/claude-code` | Lane 75 - Trusted Tools |
| `Codex CLI - Trusted 75` | Codex CLI | `{"network":"lab75","dns":["9.9.9.9","149.112.112.112"]}` | 2902458368 | `/var/lib/kasm-profiles/codex-cli` | Lane 75 - Trusted Tools |
| `Terminal - Trusted 75` | Terminal | `{"network":"lab75","dns":["9.9.9.9","149.112.112.112"]}` | 1610612736 | `/var/lib/kasm-profiles/terminal-trusted` | Lane 75 - Trusted Tools |
| `Chrome - Lab 74` | `Chrome ` | `{"network":"lab74","dns":["9.9.9.9","149.112.112.112"]}` | 2902458368 | | Lane 74 - Browser & Tooling |
| `Tor Browser - Lab 74` | Tor-Browser | `{"network":"lab74","dns":["9.9.9.9","149.112.112.112"]}` | 2902458368 | | Lane 74 - Browser & Tooling |
| `Kali - Lab 74` | Kali Linux | `{"network":"lab74","dns":["9.9.9.9","149.112.112.112"]}` | 2902458368 | | Lane 74 - Browser & Tooling |
| `Nessus - Lab 74` | Nessus | `{"network":"lab74","dns":["9.9.9.9","149.112.112.112"]}` | 4294967296 | `/var/lib/kasm-profiles/nessus` | Lane 74 - Browser & Tooling |
| `Hunchly - Lab 74` | Hunchly | `{"network":"lab74","dns":["9.9.9.9","149.112.112.112"]}` | 2902458368 | `/var/lib/kasm-profiles/hunchly` | Lane 74 - Browser & Tooling |
| `Telegram - Lab 74` | Telegram | `{"network":"lab74","dns":["9.9.9.9","149.112.112.112"]}` | 2902458368 | `/var/lib/kasm-profiles/telegram` | Lane 74 - Browser & Tooling |
| `Spiderfoot - Lab 74` | Spiderfoot | `{"network":"lab74","dns":["9.9.9.9","149.112.112.112"]}` | 2902458368 | | Lane 74 - Browser & Tooling |
| `Forensic OSINT - Lab 74` | Forensic OSINT | `{"network":"lab74","dns":["9.9.9.9","149.112.112.112"]}` | 2902458368 | | Lane 74 - Browser & Tooling |
| `Cyberbro - Lab 74` | Cyberbro | `{"network":"lab74","dns":["9.9.9.9","149.112.112.112"]}` | 2902458368 | | Lane 74 - Browser & Tooling |
| `Terminal - Lab 74` | Terminal | `{"network":"lab74","dns":["9.9.9.9","149.112.112.112"]}` | 1610612736 | | Lane 74 - Browser & Tooling |
| `REMnux - Malware 77` | REMnux | `{"network":"lab77","dns":["192.168.77.10"]}` | 2902458368 | | Lane 77 - Malware Offline |
| `Debian - Target 77` | Debian Trixie | `{"network":"lab77","dns":["192.168.77.10"]}` | 2902458368 | | Lane 77 - Malware Offline |
| `Fedora - Target 77` | Fedora 43 | `{"network":"lab77","dns":["192.168.77.10"]}` | 2902458368 | | Lane 77 - Malware Offline |
| `Terminal - Malware 77` | Terminal | `{"network":"lab77","dns":["192.168.77.10"]}` | 1610612736 | | Lane 77 - Malware Offline |
| `REMnux - Review 79` | REMnux | `{"network":"lab79","dns":["192.168.79.10"]}` | 2902458368 | | Lane 79 - Evidence Review |
| `Debian - Review 79` | Debian Trixie | `{"network":"lab79","dns":["192.168.79.10"]}` | 2902458368 | | Lane 79 - Evidence Review |

Nothing listens at 192.168.77.10 or 192.168.79.10. That is the point: lookups fail inside the lane rather than leaking. Dropping the `dns` member lets Docker's embedded resolver at 127.0.0.11 forward through the management host, which quietly defeats an offline lane.

Nessus is the only tile above the 2.77 GiB default, at 4 GiB. It will not co-exist with a second desktop session; see "Consequences I accepted".

## Phase 6: rename the 15 originals

Leave them enabled, attached to All Users, & with their existing run configs. Rename each to append ` (UNISOLATED)` & set the category to `Unisolated - Management Network`.

This is the one deviation from leaving them untouched, & it is reversible with an UPDATE. An unlabelled `Chrome` tile sitting beside `Chrome - Lab 74` is one misclick away from opening a phishing link on the management VLAN with my home WAN address & no containment. The rename keeps the capability I asked for & removes the way to use it by accident.

## Phase 7: verification

Run every check & record the actual output. Do not report a step as passing because a command was issued.

**Per lane, from a session on that lane.** Read the address with `ip -4 addr show eth0` & confirm it falls in the lane's `.208` to `.223` range. On lanes 77 & 79 both of these must fail:

```bash
timeout 3 bash -c 'echo > /dev/tcp/1.1.1.1/443'
```

```bash
getent hosts example.com
```

Write the probe exactly as shown. `/dev/tcp/HOST/PORT` needs that second slash; a space instead makes every probe fail regardless of the firewall, which reads as a clean pass & is nothing of the sort. That mistake was made during the 2026-07-28 work & caught late.

**From every lane, all nine of these must fail:** 192.168.78.10:443, 192.168.80.10:22, 192.168.70.10:8006, 192.168.70.11:8006, 192.168.71.10:22, 192.168.72.2:443, 192.168.73.2:9090, 192.168.1.1:443, 192.168.10.1:443.

**Lane 74 egress.** `curl -s ifconfig.me` returns a Proton exit address, not my WAN address. Read the current WAN address from UniFi first so the two can be told apart.

**Lane 75 egress.** `curl -s ifconfig.me` returns my WAN address & not a Proton exit, which is what confirms VLAN 75 stayed out of the Proton route. Lane 75 must still fail all nine protected addresses above, & must fail to reach a session on 74, 77, or 79.

**Persistence.** On a lane 75 tile, confirm `docker inspect` lists a mount from `/var/lib/kasm-profiles/`. On `REMnux - Malware 77` & `Debian - Review 79`, confirm the mount list holds nothing from that directory. This is the check that matters most, because `allow_persistent_profile` is now True for `alpha` & an empty profile path is the only thing keeping malware sessions disposable.

**Group settings.** Log in as `alpha` & confirm the session toolbar offers no download & no clipboard, that printing is absent, & that no storage mapping option appears.

**Reboot.** Reboot VM 122 & confirm all four shims return, all four Docker networks exist, & a session still launches.

**Snapshot.** Take `baseline-tiles-2026-07-28` once every check passes, & note in the change record that a rollback past it removes any tile added later.

## Phase 8: documentation

Write a change record at `Platforms/Kasm Workspaces/Documentation/Change Records/Kasm Workspace Build-Out - 2026-07-28.md` holding the measured before & after numbers, the Phase 3 gate result verbatim, the full verification output, & anything that deviated from this plan.

Update these:

- `Platforms/Kasm Workspaces/README.md`: the lane table gains VLAN 75, the workspace override section gains the lab75 JSON, & a tile inventory section replaces the closing line about adding workspaces separately.
- `Platforms/Kasm Workspaces/Documentation/Session-Workflows.md`: add lane 75 to the override table, add a trusted-tools workflow, & record that printing, storage mappings, & sharing are off.
- `Infrastructure/Network/UniFi/Configuration/firewall.md`: add the 17 new policies & correct the policy count from 99.
- `Architecture/Isolated-Security-Lab.md`: add the fourth lane to the boundary model.
- `Operations/Inventory/Galaxy/Services.md`: record the disk growth from 150 GB to 200 GB.
- `Infrastructure/Compute/Galaxy/Documentation/TODO.md`: add a watch item for the `ssd-lvm2` thin pool crossing 80 percent data use.
- Root `TODO.md`: close the Kasm workspace item & link the change record.

Leave no scripts, temporary playbooks, dumps, or SQL files behind on `purple-server` or `kasm-01`. Anything written for one step gets removed in that step & the removal recorded.

## Consequences I accepted

**Two sessions at a time.** 5.7 GiB of usable memory against a 2.77 GiB default means two desktop sessions is the honest ceiling, so `max_kasms_per_user` is 2 even though Community Edition allows five. Nessus at 4 GiB runs alone. The VM's memory allocation is the lever if I want more, & swap is 4 GiB, so an overcommit degrades rather than fails.

**Clipboard is off for everything, including the coding lane.** Clipboard & download permissions are per-account, not per-workspace, & `alpha` is one account. Getting code out of a lane 75 session means committing & pushing from inside it, which works because that lane has real Internet & a persistent profile. Turning clipboard on for convenience would turn it on for malware sessions too.

**The disposability guarantee is now a field, not a rule.** `allow_persistent_profile` is True on `alpha`, so what keeps a malware session from writing to the host is the empty `persistent_profile_path` on those workspaces. The Phase 7 mount check is not optional.

**Sessions are not isolated from each other.** A container escape reaches every session on the host through the shared kernel no matter what the gateway does to their lanes. Running one session at a time is the only thing that closes it, & no rule in this plan changes that.

**Three lane 74 tiles write to the host filesystem.** Nessus, Hunchly, & Telegram each mount a directory under `/var/lib/kasm-profiles/`. A compromise of one of those sessions can leave something behind that survives it. Each gets its own directory so a compromise of one does not reach another's data.

## Rollback

| Step | Undo |
| --- | --- |
| Everything | `qm shutdown 122 --timeout 180` then `qm rollback 122 pre-workspace-buildout-2026-07-28 --start` |
| Disk resize | Not reversible. LVM cannot shrink a thin volume, & the snapshot rollback restores the filesystem contents but not the 150 GB size. |
| Tiles | `DELETE FROM group_images` for the new rows, then `DELETE FROM images WHERE friendly_name LIKE '% - Lab 74'` & the equivalent for the other three lanes. |
| Originals rename | `UPDATE images SET friendly_name = replace(friendly_name, ' (UNISOLATED)', '')` & restore the prior categories. |
| Group settings | Restore the seven original Lab Sessions values & remove `alpha` from the group. |
| Lane 75 host side | `docker network rm lab75`, drop the `create_shim shim75` line, `qm set 122 --delete net4`. |
| Lane 75 UniFi side | Delete the 17 policies, then the zone, then the network, in that order. |

## Stop conditions

Stop & report rather than working around any of these.

The Phase 3 gate fails on either the network or the DNS check. The `ssd-lvm2` thin pool passes 85 percent data use at any point. `growpart` or `resize2fs` reports an error. A UniFi policy create returns success but the read-back shows a different index or state. A session launches but never displays after the shim & `firewall=0` checks both pass. Any verification probe in Phase 7 succeeds where this plan says it must fail.
