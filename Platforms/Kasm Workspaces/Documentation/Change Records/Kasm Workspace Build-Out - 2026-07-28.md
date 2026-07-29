# Kasm Workspace Build-Out

**Created:** 2026-07-28  
**Last updated:** 2026-07-28

**Implemented:** 2026-07-28  
**Owner:** Platforms / Kasm Workspaces  
**Status:** Implemented and verified

## Result

I expanded `kasm-01` to 200 GiB, added KASM-TRUSTED/VLAN 75 for ordinary-WAN development sessions, and built 19 isolated workspaces across four macvlan lanes. Six trusted tools have dedicated persistent profile directories. The remaining lane workspaces stay disposable, and all 15 original definitions are visibly labeled `(UNISOLATED)`.

All four real-session tests passed. VLAN 74 used Proton, VLAN 75 matched the Kasm host's ordinary WAN, and VLANs 77 and 79 had neither DNS nor direct Internet access. Every lane failed all nine protected homelab probes. The four networks, shims, Kasm services, and a fresh lane 77 launch survived a guest restart.

## Scope

This change covered VM 122 storage, one UniFi network and zone, 17 UniFi policies, one new guest NIC, one Docker macvlan network, Kasm group policy, workspace definitions, selective profile storage, acceptance testing, snapshots, and the owning records. It did not change the existing Proton route target, expose Kasm through a reverse proxy, or add any WAN port forward.

## Starting State

VM 122 ran Kasm Workspaces 1.19.0 Community Edition on `purple-server`. Its 150 GiB disk held a 145 GiB ext4 filesystem. Three addressless session NICs and macvlan networks carried VLANs 74, 77, and 79. The `Lab Sessions` group allowed one-hour sessions and uploads while downloads, clipboard, and persistence were disabled.

Kasm had 15 original workspace definitions and no finished lane catalog. UniFi had no VLAN 75 network or KASM-TRUSTED zone. The live controller had 101 user-defined policies, not the 99 recorded in the plan.

## Step-Based Walkthrough

### Step 0: Snapshot and expand VM 122

I created snapshot `pre-workspace-buildout-2026-07-28`, stopped VM 122, expanded `scsi0` from 150 GiB to 200 GiB, and started it. Cloud-init had already grown partition 1 and ext4 by the time the guest agent returned. `growpart` reported no space left to add, and a separate `resize2fs` run reported that the filesystem was already at its full size.

The guest reported a 193 GiB ext4 filesystem with 117 GiB used and 76 GiB available. The thin pool stayed below the plan's stop threshold. The exact command, non-zero nested `growpart` result, follow-up command, and observed sizes are retained in [S00 Snapshot and Disk Growth](../../Evidence/Kasm%20Workspace%20Build-Out%20-%202026-07-28/Logs/S00%20Snapshot%20and%20Disk%20Growth%20-%202026-07-28.md).

### Step 1: Create KASM-TRUSTED and its firewall boundary

I created KASM-TRUSTED/VLAN 75 with subnet `192.168.75.0/24`, gateway `.1`, DHCP `.100` through `.199`, a 3,600-second lease, and UPnP disabled. I used UniFi Site Manager to create the KASM-TRUSTED zone and assigned only VLAN 75 to it.

I created 17 policies: DHCP and NTP gateway allows, a gateway catchall block, ordinary external egress, bidirectional isolation from the three existing session lanes and LAB-MGMT, and blocks from KASM-TRUSTED to Internal and the four service zones. UniFi assigned indexes 10000, 10001, and 10002 to the three gateway policies. That differs from the plan's requested 10000, 10002, and 10003 but preserves the required allow, allow, block order.

The first policy create failed because the controller rejected automatic response-policy generation. No partial policy existed. I retried with response generation disabled, then applied that setting to the full set.

UniFi automatically excluded the new VLAN from `Proxmox-Trunk`. Tagged ARP left Purple but received no reply. I used UniFi Site Manager to admit KASM-TRUSTED as a tagged network. The final trunk readback contained the original five exclusions only, and VLAN 75 received gateway ARP replies. The network, zone, policy list, order, route target, and trunk state are retained in [S01 VLAN 75, Zone, and Firewall Final State](../../Evidence/Kasm%20Workspace%20Build-Out%20-%202026-07-28/Logs/S01%20VLAN%2075,%20Zone,%20and%20Firewall%20Final%20State%20-%202026-07-28.md).

### Step 2: Attach VLAN 75 to the guest

I added VM 122 `net4` on `vmbr0`, tagged VLAN 75, with bridge firewall filtering disabled for the container MAC addresses. Ubuntu named the parent `enp6s22`. I added an addressless optional netplan stanza because the plan's service-only change did not keep the parent up.

I extended `kasm-lab-shims.service` with `shim75` at `192.168.75.201/32` and created `lab75` with subnet `192.168.75.0/24`, gateway `.1`, range `.208/28`, and parent `enp6s22`. The final interface, route, and Docker readbacks are in [S02 VLAN 75 Guest and Docker State](../../Evidence/Kasm%20Workspace%20Build-Out%20-%202026-07-28/Logs/S02%20VLAN%2075%20Guest%20and%20Docker%20State%20-%202026-07-28.md).

### Step 3: Prove the target-lane gate

I created `Debian - Target 77`, assigned it only to `Lab Sessions`, and launched it. The container joined only `lab77` at `.208` and carried `HostConfig.Dns=["192.168.77.10"]`.

Docker's generated `/etc/resolv.conf` used its embedded resolver at `127.0.0.11` and listed `192.168.77.10` as the sole external server in the generated comment. That differed from the plan's literal file-text expectation. A packet capture proved the actual behavior: the container sent only ARP toward `192.168.77.10`, returned `SERVFAIL`, and sent nothing to another resolver. I accepted the traffic proof and continued under my prior authorization. I did not retain the exact original gate transcript; [S03](../../Evidence/Kasm%20Workspace%20Build-Out%20-%202026-07-28/Logs/S03%20Gate,%20Group,%20and%20Workspace%20State%20-%202026-07-28.md) records the observed values and transcript boundary.

### Step 4: Apply the Lab Sessions policy

I added `alpha` to `Lab Sessions`, raised the concurrent-session cap to two, enabled uploads and persistent-profile support, and kept download, clipboard, microphone, printing, sharing, and user storage mappings disabled. The one-hour limit stayed in place. I did not change `All Users` or `dkadi` membership.

I read the 12 effective settings from Kasm's `group_settings` table after the change. The exact values and the target-lane gate are retained in [S03 Gate, Group, and Workspace State](../../Evidence/Kasm%20Workspace%20Build-Out%20-%202026-07-28/Logs/S03%20Gate,%20Group,%20and%20Workspace%20State%20-%202026-07-28.md).

### Step 5: Create profiles and 19 isolated workspaces

I created six host profile directories beneath `/var/lib/kasm-profiles`, each owned by UID and GID 1000 with mode 0750. They serve Claude Code, Codex CLI, Terminal on VLAN 75, Nessus, Hunchly, and Telegram. The real Terminal launch widened its directory to 0777. The final review caught that drift, and I restored all six exact paths to 0750 before replacing the final snapshot.

0750 is the state at handover rather than a property that holds. Kasm's container startup sets the mode itself, so the next launch of a tile with a profile widens its directory again. That costs nothing here: each directory is owned by UID 1000 and the session runs as UID 1000, so 0750 already grants the container everything it needs, and 0777 grants no access to a user who is not on this host. I am recording the drift rather than fighting it, because a permission I reset on every review is a permission I will eventually believe is enforced.

I cloned 19 workspace definitions:

| Lane | Workspaces | Egress |
| --- | --- | --- |
| `lab75` | Claude Code, Codex CLI, Terminal | Ordinary WAN |
| `lab74` | Chrome, Tor, Kali, Nessus, Hunchly, Telegram, Spiderfoot, Forensic OSINT, Cyberbro, Terminal | Proton |
| `lab77` | REMnux, Debian, Fedora, Terminal | None |
| `lab79` | REMnux, Debian | None |

Each clone belongs only to `Lab Sessions`, carries its lane and resolver override, and preserves the source definition's hostname, user, and environment settings. Only the six named definitions have a persistent bind.

### Step 6: Label original definitions as unisolated

I appended ` (UNISOLATED)` to all 15 original definitions and moved them to `Unisolated - Management Network`. They remain assigned only to `All Users`. An API request as `alpha` returned 34 definitions: 19 isolated lane definitions and 15 unisolated originals.

The original Chrome name carried trailing whitespace from the registry, so the bulk append left it reading `Chrome  (UNISOLATED)` with two spaces. I collapsed that to a single space in a follow-up review the same day. The row now reads `Chrome (UNISOLATED)`, which is the only name I changed outside the bulk rename.

### Step 7: Run real-session acceptance and reboot recovery

I launched Terminal on VLAN 75, Terminal on VLAN 74, REMnux on VLAN 77, and Debian on VLAN 79 as `alpha`. Each joined only its intended network at `.208`. The trusted Terminal carried its assigned host profile; the two disposable sample/review sessions had no `/var/lib/kasm-profiles` mount.

The lane 75 public address matched the Kasm host's ordinary WAN. I did not retain that address. Lane 74 returned the existing Proton exit. Lanes 77 and 79 failed DNS and direct TCP to `1.1.1.1:443`. Every lane failed all nine protected probes:

```text
192.168.78.10:443
192.168.80.10:22
192.168.70.10:8006
192.168.70.11:8006
192.168.71.10:22
192.168.72.2:443
192.168.73.2:9090
192.168.1.1:443
192.168.10.1:443
```

I also kept live TCP 6901 listeners in sessions on lanes 74, 77, and 79. The lane 75 session could not connect to any of them.

The Kasm UI uses a self-signed certificate. Browser automation could not cross the certificate warning, and I did not bypass the browser safety control. I therefore retained no visual toolbar capture. I verified the authoritative group settings in the database and used those settings in the real `alpha` sessions.

`qm reboot 122` timed out after the guest shut down instead of restarting. I verified the stopped state and ran `qm start 122`. After boot, all four parents, shims, routes, and Docker networks returned. Kasm health returned `{"ok":true}` after about 42 seconds, and a fresh `Debian - Target 77` session launched on `lab77` at `.208`.

I destroyed every test session, removed the temporary health response, and verified zero `alpha` sessions and no `/tmp/kasm-*` residue. [S04 Acceptance, Reboot, and Cleanup](../../Evidence/Kasm%20Workspace%20Build-Out%20-%202026-07-28/Logs/S04%20Acceptance,%20Reboot,%20and%20Cleanup%20-%202026-07-28.md) retains the observed matrix, restart deviation, and cleanup results. I did not retain the raw per-probe terminal output. [S05](../../Evidence/Kasm%20Workspace%20Build-Out%20-%202026-07-28/Logs/S05%20Full%20Final%20State%20Readback%20-%202026-07-28.md) retains the exact final-state commands and output.

### Step 8: Create the final recovery point and update records

I created snapshot `baseline-tiles-2026-07-28`. After correcting the profile-directory mode, I deleted only that final snapshot and recreated it under the same planned name. Both the pre-change and replacement final snapshots read back in the VM snapshot list. The final post-correction readback reported 52.24 percent data and 2.41 percent metadata. I added an 80 percent action threshold to the Galaxy backlog.

I updated the Kasm platform records, architecture, UniFi VLAN, zone, firewall, and port-profile inventories, Galaxy guest inventories, TODO indexes, evidence, and Mission Control. No credential, token, private key, or ordinary WAN address was written to the repository.

## Decisions and Deviations

- I continued past the plan's stop clauses because I had already authorized completion regardless of those clauses. I still verified each unexpected result before proceeding.
- I accepted controller-assigned gateway indexes 10000, 10001, and 10002 because they preserve the required security order.
- I added the addressless netplan stanza omitted by the plan so the VLAN 75 parent remains up.
- I accepted packet-level proof for the target-lane DNS gate because Docker's embedded resolver changes the generated file text without changing the configured upstream.
- I retained curated results rather than the original raw Phase 3 and per-probe Phase 7 transcripts. The final-state transcript is exact, but it does not recreate those destroyed sessions.
- I started VM 122 after `qm reboot` left it stopped. I verified the stopped state first.
- I did not bypass the browser certificate warning. The toolbar lacks a retained visual check; the enforced group settings and real-session behavior are retained instead.
- I restored `terminal-trusted` from Kasm's post-launch mode 0777 to 0750, then replaced only the final snapshot so its rollback state contains that correction.

## Resulting Configuration

| Layer | Final state |
| --- | --- |
| VM disk | 200 GiB `scsi0`; 193 GiB ext4 |
| Recovery points | `pre-workspace-buildout-2026-07-28`, `baseline-tiles-2026-07-28` |
| Session networks | `lab74`, `lab75`, `lab77`, `lab79`, each with `.208/28` allocation range and `.201/32` host shim |
| UniFi | KASM-TRUSTED/VLAN 75, one-network custom zone, 17 new policies, no Proton route change |
| Kasm group | `Lab Sessions`, one-hour limit, maximum two sessions, upload on, selective persistent profiles on, clipboard/download/printing/sharing/user storage off |
| Workspace catalog | 19 isolated definitions and 15 visibly unisolated originals |
| Persistent storage | Six dedicated profile directories under `/var/lib/kasm-profiles`, UID/GID 1000, mode 0750 |

## Verification Summary

| Check | Observed result |
| --- | --- |
| VLAN 75 DHCP, gateway NTP, and gateway catchall | Enabled in allow, allow, block order |
| UniFi custom policy count | 118, exactly 17 above the live baseline |
| Proton traffic route | Still targets KASM-BROWSER/VLAN 74 only |
| VLAN 75 trunk admission | Admitted; final profile retains exactly five unrelated exclusions |
| Real lane addresses | `.208` on each intended macvlan |
| VLAN 75 egress | Matched ordinary host WAN |
| VLAN 74 egress | Proton exit `185.98.168.20` |
| VLANs 77 and 79 egress | DNS and direct TCP blocked |
| Protected target matrix | 36 of 36 lane-to-target probes blocked |
| Lane 75 to active lane listeners | Three of three blocked |
| Profile mounts | Present only on intended persistent definitions tested |
| Post-restart networks and shims | Four of four restored |
| Post-restart Kasm health | `{"ok":true}` |
| Post-restart fresh session | Lane 77 `.208`, then destroyed |
| Profile directory ownership and modes | Six of six at UID/GID 1000 and 0750 at handover; Kasm rewrites the mode on each launch |
| Residue | Zero `alpha` sessions and no temporary Kasm files |

## Rollback Points

- Restore `pre-workspace-buildout-2026-07-28` to return VM 122's disk and Kasm database to the pre-build state. This discards later Kasm changes and requires a stopped guest.
- Remove the 17 named KASM-TRUSTED policies, remove VLAN 75 from `Proxmox-Trunk`, delete the KASM-TRUSTED zone and network, then remove VM 122 `net4` to unwind the network lane.
- Remove `lab75`, `shim75`, its route, the service stanza, and the `enp6s22` netplan stanza to unwind the guest network.
- Restore the 15 original names and categories and delete the 19 clones to unwind the catalog without restoring the VM snapshot.
- Remove the six host profile directories only after confirming they contain no data I want to retain.

## Remaining Work

- Watch `ssd-lvm2` data use and act before it reaches 80 percent. The owning item is in the [Galaxy TODO](../../../../Infrastructure/Compute/Galaxy/Documentation/TODO.md).
- Replace the self-signed Kasm certificate or publish the UI through the approved internal HTTPS path if I want repeatable browser-automation captures.

## Evidence

The retained phase records are indexed in [Kasm Workspace Build-Out Evidence](../../Evidence/Kasm%20Workspace%20Build-Out%20-%202026-07-28/Evidence-Index.md). The exact final VM, storage, guest, service, group, workspace, profile, snapshot, and residue output is in [S05 Full Final State Readback](../../Evidence/Kasm%20Workspace%20Build-Out%20-%202026-07-28/Logs/S05%20Full%20Final%20State%20Readback%20-%202026-07-28.md).
