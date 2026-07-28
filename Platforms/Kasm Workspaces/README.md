# Kasm Workspaces

**Created:** 2026-07-24  
**Last updated:** 2026-07-28

Kasm Workspaces 1.19.0 Community Edition runs on `kasm-01` (VM 122) at `192.168.78.10` on `purple-server`. It streams disposable Linux desktops and browsers while UniFi places each session in a sealed lane.

Community Edition caps the deployment at five concurrent sessions and one named user. The current 4-vCPU, 8 GiB VM is sized for a small lab, not a shared desktop service.

## Current State

The control plane lives alone on LAB-MGMT VLAN 78. Trusted and Personal-A reach TCP 22 and 443, as does Jedi PC at `192.168.50.241`, which needed its own rule because the Secure VLAN was never in the allow list. The Management Access VPN policy permits the same ports, but its live client-path test remains open. Every other Internal network and all service zones are blocked from the UI, and the two allows are ordered above the catchall block that enforces that.

Session containers join one of three Docker macvlan networks:

| Network | VLAN | Purpose | Internet |
| --- | ---: | --- | --- |
| `lab74` | 74 KASM-BROWSER | Browser sessions and pentest tooling | Proton only |
| `lab77` | 77 MALWARE-OFFLINE | Linux samples and disposable targets | None |
| `lab79` | 79 EVIDENCE-QUARANTINE | Artifact review | None |

VLAN 74 may initiate toward VLAN 77. VLAN 77 cannot initiate back. Neither lane reaches VLAN 79. Every session lane is explicitly blocked from LAB-MGMT, Internal, Servers, Management, Access, Observability, and the gateway UI.

The `Lab Sessions` group permits browser-mediated upload and enforces a one-hour session limit. Download, clipboard in both directions, seamless clipboard, persistent profiles, and host shares remain disabled.

## Workspace Network Overrides

Each lab workspace needs an explicit network and resolver in its Docker Run Config Override:

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
| [Deployment](Documentation/Deployment.md) | Original Kasm 1.19.0 build and current-state note |
| [Kasm Session Isolation](Documentation/Change%20Records/Kasm%20Session%20Isolation%20-%202026-07-28.md) | Migration, storage, network, policy, tests, exceptions, and cleanup |
| [Kasm Session Isolation plan](Documentation/Change%20Plans/Kasm%20Session%20Isolation.md) | Executed plan and settled design |
| [Isolated Security Lab](../../Architecture/Isolated-Security-Lab.md) | Cross-system boundary model |

I add workspace registries, images, and individual workspace definitions separately. The isolation plumbing is ready for them.
