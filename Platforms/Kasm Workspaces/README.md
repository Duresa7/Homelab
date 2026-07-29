# Kasm Workspaces

**Created:** 2026-07-24  
**Last updated:** 2026-07-28

Kasm Workspaces 1.19.0 Community Edition runs on `kasm-01` (VM 122) at `192.168.78.10` on `purple-server`. It streams disposable Linux desktops and browsers while UniFi places each session in a sealed lane.

Community Edition caps the deployment at five concurrent sessions and one named user. The current VM has four vCPUs, 8 GiB of memory, and a 200 GiB disk. The `Lab Sessions` group limits `alpha` to two concurrent sessions because the VM has 5.7 GiB available to workspace containers.

## Current State

The control plane lives alone on LAB-MGMT VLAN 78. Trusted and Personal-A reach TCP 22 and 443, as does Jedi PC at `192.168.50.241`, which needed its own rule because the Secure VLAN was never in the allow list. The Management Access VPN permits the same ports, verified from a real remote client on 2026-07-28. Every other Internal network and all service zones are blocked from the UI, and the three narrow allows are ordered above the catchall blocks that enforce that.

Session containers join one of four Docker macvlan networks:

| Network | VLAN | Purpose | Internet |
| --- | ---: | --- | --- |
| `lab75` | 75 KASM-TRUSTED | Claude Code, Codex CLI, and trusted terminal work | Ordinary WAN |
| `lab74` | 74 KASM-BROWSER | Browser sessions and pentest tooling | Proton only |
| `lab77` | 77 MALWARE-OFFLINE | Linux samples and disposable targets | None |
| `lab79` | 79 EVIDENCE-QUARANTINE | Artifact review | None |

VLAN 74 may initiate toward VLAN 77. VLAN 77 cannot initiate back. Neither lane reaches VLAN 79. VLAN 75 cannot reach any other session lane. Every session lane is explicitly blocked from LAB-MGMT, Internal, Servers, Management, Access, Observability, and the gateway UI.

The `Lab Sessions` group permits browser-mediated upload and enforces a one-hour session limit. Download, clipboard in both directions, seamless clipboard, printing, sharing, microphone access, and user storage mappings are disabled. Persistent profiles are allowed at the group level but only six named tiles carry a host path. Every malware and review tile has a null profile path.

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

The `alpha` account sees 19 lane-assigned tiles through `Lab Sessions`. The 15 registry originals remain available only through `All Users`, carry the ` (UNISOLATED)` suffix, and sit in the `Unisolated - Management Network` category.

| Lane | Tiles | Persistent profiles |
| --- | --- | --- |
| Trusted 75 | Claude Code, Codex CLI, Terminal | All three, each in its own directory |
| Lab 74 | Chrome, Tor Browser, Kali, Nessus, Hunchly, Telegram, Spiderfoot, Forensic OSINT, Cyberbro, Terminal | Nessus, Hunchly, and Telegram only |
| Malware 77 | REMnux, Debian, Fedora, Terminal | None |
| Review 79 | REMnux, Debian | None |

The trusted tiles use the ordinary WAN. Lane 74 uses Proton. The malware and review tiles use nonexistent lane-local resolvers so DNS fails inside those networks.

## Running a malware session

Snapshot VM 122 first, then roll back to that snapshot when the session ends. The host is the disposable part of this design, and the snapshot is what makes that true instead of aspirational. Rolling back reverts Kasm's database too, so take a fresh snapshot after any workspace or settings change and the rollback then costs only the session just run.

Sessions are not serialised. A sample can run beside another workspace, and a container escape reaches every session on the host through the shared kernel no matter what the gateway does to their lanes. Closing that means running one session at a time, not adding a rule.

## Monitoring

`node_exporter` 1.9.0 runs here bound to `192.168.78.10:9100` and nothing else. Every other host in the fleet exports on all interfaces; this one cannot, because a session container sharing a lab subnet would reach the macvlan shim address directly and the gateway would never see the request. One policy lets `192.168.73.2` scrape that port. cAdvisor is deliberately absent, since a second listener is a second way into the lane holding the sessions.

## Access

SSH uses `<YOUR_ADMIN_USERNAME>@192.168.78.10`. The web UI is `https://192.168.78.10/`. The administrator credential and current URLs live outside this repository; nothing here holds a secret.

The `KASM Lab Proton Egress` route must stay enabled while a VLAN 74 session runs. An enabled but failed tunnel is kill-switched. Administratively disabling the VPN object causes UniFi to use the normal WAN.

## Records

| Record | Purpose |
| --- | --- |
| [Session workflows](Documentation/Session-Workflows.md) | How to run each job: phishing links, target practice, samples, inspection, review |
| [Deployment](Documentation/Deployment.md) | Original Kasm 1.19.0 build and current-state note |
| [Kasm Session Isolation](Documentation/Change%20Records/Kasm%20Session%20Isolation%20-%202026-07-28.md) | Migration, storage, network, policy, tests, exceptions, and cleanup |
| [Kasm Workspace Build-Out](Documentation/Change%20Records/Kasm%20Workspace%20Build-Out%20-%202026-07-28.md) | Disk growth, VLAN 75, 19 lane tiles, account policy, and acceptance results |
| [Kasm Session Isolation plan](Documentation/Change%20Plans/Kasm%20Session%20Isolation.md) | Executed plan and settled design |
| [Kasm Workspace Build-Out plan](Documentation/Change%20Plans/Kasm%20Workspace%20Build-Out.md) | Executed plan for the 19 tiles, VLAN 75 trusted lane, and 200 GiB disk |
| [Isolated Security Lab](../../Architecture/Isolated-Security-Lab.md) | Cross-system boundary model |
