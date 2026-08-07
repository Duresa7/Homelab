# Kasm Workspaces

**Created:** 2026-07-24  
**Last updated:** 2026-08-06

Kasm Workspaces 1.19.0 Community Edition runs on `kasm-01` (VM 122) at `192.168.78.10` on `purple-server`. It streams disposable Linux desktops and browsers while UniFi places each session in a sealed lane.

Community Edition caps the deployment at five concurrent sessions and one named user. The VM has six vCPUs, 12 GiB of memory, and a 200 GiB disk after I raised it from four vCPUs and 8 GiB on 2026-07-28. VM 122 is the only guest on `purple-server`, which has six cores and 15 GiB, so the guest takes every core and leaves roughly 2 GiB for Proxmox. That is enough on a node running one VM against LVM-thin rather than ZFS, since there is no ARC competing for memory.

`alpha` is limited to three concurrent sessions through `Lab Sessions`; my own account is set to five, the Community Edition ceiling. Kasm's own containers hold about 2 GiB, leaving 9.7 GiB for workspaces against a 2.70 GiB per-session limit, so three busy desktops fit and a fourth does not. That limit is a Docker `--memory` ceiling rather than a reservation, so five idle terminals are fine and five working desktops will reach the 4 GiB swap file. The node has 15 GiB total and VM 122 is its only guest, so raising the guest past 12 GiB would starve Proxmox; more sessions means more physical memory, not a bigger number in the group. Storage is the constrained dimension: the `ssd-lvm2` volume group has 124 MB unallocated, so the thin pool cannot grow without another physical disk. The first Parrot attempt filled the 228.11 GiB pool and paused VM 122. I recovered, enabled discard, removed both old snapshots, pruned unused Docker layers, and installed Parrot one image at a time. The final pool readback is 68.25 percent, the guest has 39 GB free, and `baseline-parrot-2026-07-30` is the only snapshot.

## Current State

The control plane lives alone on LAB-MGMT VLAN 78. Trusted and Personal-A reach TCP 22 and 443, as does Jedi PC at `192.168.50.241`, which needed its own rule because the Secure VLAN was never in the allow list. The Management Access VPN permits the same ports, verified from a real remote client on 2026-07-28. NPM at `192.168.85.2` has one TCP 443 path. Every other Internal network and all service zones are blocked from the UI, and the four narrow allows are ordered above the catchall blocks that enforce that.

Session containers join one of four Docker macvlan networks:

| Network | VLAN | Purpose | Internet |
| --- | ---: | --- | --- |
| `lab75` | 75 KASM-TRUSTED | Claude Code, Codex CLI, and trusted terminal work | Ordinary WAN |
| `lab74` | 74 KASM-BROWSER | Browser sessions and pentest tooling | Proton only |
| `lab77` | 77 MALWARE-OFFLINE | Linux samples and disposable targets | None |
| `lab79` | 79 EVIDENCE-QUARANTINE | Artifact review | None |

VLAN 74 may initiate toward VLAN 77. VLAN 77 cannot initiate back. Neither lane reaches VLAN 79. VLAN 75 cannot reach any other session lane. Every session lane is explicitly blocked from LAB-MGMT, Internal, Servers, Management, Access, Observability, and the gateway UI.

The `Lab Sessions` group permits browser-mediated upload. Download, clipboard in both directions, seamless clipboard, printing, sharing, microphone access, and user storage mappings are disabled. Persistent profiles are allowed at the group level but only six named tiles carry a host path. Every malware and review tile has a null profile path.

Policy is per account rather than per group as of 2026-08-01. `alpha` gets everything above plus 3600 seconds through `Lab Session Time Limit` at priority 50. My own account is exempt through `Administrators` at priority 1: no time limit, no idle disconnect, a seven-day keepalive window, five concurrent slots, and download, clipboard, printing, sharing, microphone, and storage mappings all enabled on every tile. The lanes, DNS blackholes, and firewall rules are unchanged and still apply to both accounts, so network containment holds while data-egress containment is now discipline rather than policy on my sessions. [Kasm Session Limit Exemption](Documentation/Change%20Records/Kasm%20Session%20Limit%20Exemption%20-%202026-08-01.md) has the resolution rule and why a `session_time_limit` of `0` blocks the keepalive instead of removing the cap.

## Workspace Network Overrides

Each lab workspace needs an explicit network and resolver in its Docker Run Config Override:

```json
{"network":"lab75","dns":["9.9.9.9","149.112.112.112"]}
```

```json
{"network":"lab74","dns":["9.9.9.9","149.112.112.112"]}
```

```json
{"network":"lab77","dns":["192.168.77.10"]}
```

```json
{"network":"lab79","dns":["192.168.79.10"]}
```

Nothing listens at the VLAN 77 or VLAN 79 resolver address. Those lanes therefore fail DNS locally. Omitting the `dns` member lets Docker's embedded resolver forward through the management host, so a network-only override does not meet the offline requirement.

A workspace with no override uses `kasm_default_network` and ordinary management-plane egress. I treat that as a failed lab workspace definition.

## Workspace Tile Inventory

The `alpha` account sees 19 lane-assigned tiles through `Lab Sessions`. Fourteen Full definitions remain available through `All Users`. The catalog points at 15 distinct Docker images.

Tile names say what the tile is for, not which VLAN carries it. The suffix is the whole label: `Chrome - VPN`, `REMnux - Malware`, `Debian - Target`. Each tile's category line underneath carries the VLAN, so the number stays visible without crowding the name. I renamed them this way on 2026-07-28 because the first scheme put the lane number in the name, which truncated in the dashboard grid and told me nothing about what the tile does.

| Suffix | Category | Network | Tiles | Persistent profiles |
| --- | --- | --- | --- | --- |
| `- Normal` | `Normal - VLAN 75` | `lab75` | Claude Code, Codex CLI, Parrot OS, Terminal | Claude Code, Codex CLI, and Terminal only |
| `- VPN` | `VPN - VLAN 74` | `lab74` | Chrome, Cyberbro, Forensic OSINT, Hunchly, Kali, Parrot OS, Spiderfoot, Terminal, Tor Browser | Hunchly only |
| `- Malware` | `Malware - VLAN 77` | `lab77` | Debian, REMnux, Terminal | None |
| `- Target` | `Malware - VLAN 77` | `lab77` | Fedora | None |
| `- Review` | `Review - VLAN 79` | `lab79` | REMnux, Debian | None |
| `- Full` | `Full Access - VLAN 78` | none | Chrome, Claude Code, Codex CLI, Cyberbro, Debian Trixie, Fedora 43, Forensic OSINT, Hunchly, Kali Linux, Nessus, Parrot OS, REMnux, Spiderfoot, Terminal | None |

`- Malware` and `- Target` share VLAN 77 and differ only in role. Malware tiles are where I detonate and inspect; target tiles are disposable victims I attack from a VPN tile. Splitting the word keeps that distinction in the name.

The `- Normal` tiles use the ordinary WAN. `- VPN` uses Proton. The malware, target, and review tiles point at nonexistent lane-local resolvers so DNS fails inside those networks.

The `- Full` tiles have no override at all, so they run on `kasm_default_network` with ordinary management-plane egress and no containment. Keeping them is deliberate, for the rare job that needs a plain session. The word carries less warning than the `- Unsafe` label I used first, so the `Full Access - VLAN 78` category is what tells me a tile has no lane, and I renamed it on 2026-07-28 because these are a capability rather than a mistake.

## Running a malware session

I don't stack another VM snapshot before a malware session. VM 122 carries one verified snapshot, `baseline-parrot-2026-07-30`. I end the session and roll back that same baseline after detonation. A snapshot retains every old block that the running VM replaces, so repeated snapshots on the same 228.11 GiB pool would consume the space that Docker needs.

No external VM backup exists. The current baseline includes Parrot Full, Normal, and VPN; Debian Malware; null Docker Registry fields; and the verified service state. A future workspace or settings change must delete this snapshot before the controlled change, pass the full checks, and replace it with one new baseline. I never keep both generations.

Sessions are not serialised. A sample can run beside another workspace, and a container escape reaches every session on the host through the shared kernel no matter what the gateway does to their lanes. Closing that means running one session at a time, not adding a rule.

## Monitoring

`node_exporter` 1.9.0 runs here bound to `192.168.78.10:9100` and nothing else. Every other host in the fleet exports on all interfaces; this one cannot, because a session container sharing a lab subnet would reach the macvlan shim address directly and the gateway would never see the request. One policy lets `192.168.73.2` scrape that port. cAdvisor is deliberately absent, since a second listener is a second way into the lane holding the sessions.

VM 122's 200 GiB `scsi0` has `discard=on` as of 2026-07-29. Removing both old snapshots, pruning seven unused Docker images, and trimming the guest reduced `ssd-lvm2` to 51.46 percent before the controlled Parrot pull. Parrot then raised the pool to 67.44 percent and guest use from 116 GB to 154 GB. The capacity check must read both Proxmox `data_percent` and guest `df`.

Automatic workspace-image pulls are disabled. Every Kasm image row has a null Docker Registry, so the agent uses the local images without checking all moving `rolling-daily` tags each hour. Updates are manual and one image at a time. I require `ssd-lvm2` at or below 55 percent and at least 70 GB free in the guest before another new-image pull; the present state fails that gate. The open monitoring task is to warn before the 80 percent hard stop.

## Access

SSH uses `dkadi@192.168.78.10`. The normal web path is `https://kasm.alphasecunited.com/` through NPM; direct fallback is `https://192.168.78.10/`. The administrator credential lives outside this repository; nothing here holds a secret.

The `KASM Lab Proton Egress` route must stay enabled while a VLAN 74 session runs. An enabled but failed tunnel is kill-switched. Administratively disabling the VPN object causes UniFi to use the normal WAN.

## Records

| Record | Purpose |
| --- | --- |
| [Session workflows](Documentation/Session-Workflows.md) | How to run each job: phishing links, target practice, samples, inspection, review |
| [Deployment](Documentation/Deployment.md) | Original Kasm 1.19.0 build and current-state note |
| [Kasm Session Isolation](Documentation/Change%20Records/Kasm%20Session%20Isolation%20-%202026-07-28.md) | Migration, storage, network, policy, tests, exceptions, and cleanup |
| [Kasm Workspace Build-Out](Documentation/Change%20Records/Kasm%20Workspace%20Build-Out%20-%202026-07-28.md) | Disk growth, VLAN 75, 19 lane tiles, account policy, and acceptance results |
| [Kasm Parrot Workspace Build-Out](Documentation/Change%20Records/Kasm%20Parrot%20Workspace%20Build-Out%20-%202026-07-30.md) | Controlled Parrot pull, automatic-update control, three Parrot tiles, Debian Malware, lane tests, and replacement snapshot |
| [Kasm Session Limit Exemption](Documentation/Change%20Records/Kasm%20Session%20Limit%20Exemption%20-%202026-08-01.md) | Group priority resolution, the zero-versus-absent keepalive trap, per-account time limits, and the concurrency arithmetic |
| [Kasm Workspaces Internal HTTPS](../Nginx%20Proxy%20Manager/Documentation/Change%20Records/Kasm%20Workspaces%20Internal%20HTTPS%20-%202026-07-28.md) | NPM host, DNS, firewall return path, monitoring, & route verification |
| [Kasm Session Isolation plan](Documentation/Change%20Plans/Kasm%20Session%20Isolation.md) | Executed plan and settled design |
| [Kasm Workspace Build-Out plan](Documentation/Change%20Plans/Kasm%20Workspace%20Build-Out.md) | Executed plan for the 19 tiles, VLAN 75 trusted lane, and 200 GiB disk |
| [Thin-pool exhaustion troubleshooting](Documentation/Troubleshooting/Kasm%20Thin%20Pool%20Exhaustion%20Paused%20VM%20122%20-%202026-07-29.md) | `502` diagnosis, baseline rollback, discard enablement, trim, & verification |
| [Thin-pool exhaustion incident](../../Security/Incidents/Kasm%20Workspaces/Thin%20Pool%20Exhaustion%20-%202026-07-29.md) | Availability impact, timeline, root cause, & evidence |
| [Isolated Security Lab](../../Architecture/Isolated-Security-Lab.md) | Cross-system boundary model |
