# Isolated Security Lab

**Created:** 2026-07-20  
**Last updated:** 2026-07-25

## Purpose

I am building a fenced security lab for suspicious browsing, pentest practice, and malware analysis. On 2026-07-23 I simplified the network to three lab VLANs (74 KASM-BROWSER, 77 MALWARE-OFFLINE, 79 EVIDENCE-QUARANTINE), three zones, and nine firewall policies, down from seven VLANs and 53 policies, and I am rebuilding Kasm itself from scratch. The [Kasm lab network simplification](../Infrastructure/Network/UniFi/Documentation/Change%20Records/Kasm%20Lab%20Network%20Simplification%20-%202026-07-23.md) records that change.

I removed the earlier Kasm platform records and the over-built design they described on 2026-07-23. The sections below hold the cross-system boundary model I'm keeping; the detailed service design (disposable lifecycle, evidence workflow, and the autoscale guards) describes the removed build and will be redefined during the rebuild. This record explains the boundary shared by Kasm, Galaxy, UniFi, Proton VPN, and WireGuard.

On 2026-07-24 I brought the platform back up as a single host: Kasm 1.19.0 Community Edition on `kasm-01`, VM 122 on Grey, at `192.168.80.30` on VLAN 80 SERVERS-A. That address is deliberately outside every lab lane below. The management interface needs to stay reachable by SSH and HTTPS, and a sealed lane can't offer that, so the control plane sits on the server VLAN while sessions get placed into the lanes. No lab-VLAN NIC is attached yet, so at present no session is isolated. [Deployment record](../Platforms/Kasm%20Workspaces/Documentation/Deployment.md).

The tradeoff that choice buys and costs: a compromised session stays in its lane, but a full container escape that takes over `kasm-01` itself lands on SERVERS-A. For live malware I run the detonation guest with a lab-VLAN NIC only and no management interface, reaching it through the Proxmox console instead of SSH.

On 2026-07-25 I decided to move the lab off Grey and onto `purple-server`, which carries no guests. Grey holds `app-01` at 24 GiB, `splunk-siem`, `security-01`, and `alpha-prod-01`, and detonation work doesn't belong beside them. The sequence is in [Kasm Relocation to Purple](../Platforms/Kasm%20Workspaces/Documentation/Change%20Plans/Kasm%20Relocation%20to%20Purple.md). Nothing has moved yet.

Purple stays in the Galaxy cluster, and I'm recording what that costs rather than implying the move seals the boundary. Cluster members hold each other's root keys in `/etc/pve/priv/authorized_keys` along with the cluster CA private key at `/etc/pve/priv/pve-root-ca.key`, so `ssh 192.168.70.10` from Purple returns a root shell on Grey today. A sample that escapes its container and then escapes QEMU reaches Grey from either node. I chose the four-node console over closing a path that needs a QEMU vulnerability to walk, which puts the real defense at the guest boundary: current `pve-qemu-kvm`, detonation guests built with no guest agent, no USB, no audio, no SPICE, and no serial, and a snapshot before every run.

## Boundary Model

Four controls have different jobs:

1. UniFi WireGuard carries an approved remote user into the homelab.
2. Kasm authenticates the user, presents the workspace catalog, and controls session lifetime.
3. UniFi VLANs, zones, and firewall policies contain each workload.
4. Proton VPN handles selected outbound Internet traffic and fails closed. It does not make malware safe.

NetBird is not part of this lab path. I am not removing it from unrelated services.

## Network Lanes

| VLAN | Lane | Use | Internet |
| ---: | --- | --- | --- |
| 74 | Lab tools | Kasm Agent, browser containers, and attacker tooling | Proton only, fails closed |
| 77 | Detonation and targets | Targets and offline malware | None; fake services only |
| 79 | Evidence quarantine | Disposable review systems | None |

Every lane is blocked from management, cluster, monitoring, server, trusted, and unrelated lab networks unless an exact workflow rule allows the path. Offline malware sees INetSim instead of the real Internet. Evidence review cannot initiate toward a trusted system. The current firewall keeps only the DHCP, NTP, gateway-block, and External-block baseline; I removed the Kasm control-plane and attacker-to-target allows and will re-add them against real host IPs during the rebuild.

## Compute Boundary

As of 2026-07-24 every Kasm component runs on one host, `kasm-01` (VM 122) on Grey, installed with `--role all`. The earlier split across `kasm-agent-01`, `kasm-core`, and INetSim on Purple no longer exists; the 2026-07-23 teardown destroyed those guests. Purple is back in service as of 2026-07-25 on a replacement boot NVMe and carries nothing.

Malware and untrusted full desktops run as separate KVM guests beside `kasm-01`, never inside it. After the relocation those guests live on Purple. The permanent Kali VM stays separate from malware storage, and it stays on Grey: `kali-pen` (VM 106) and `W11-Test-1` (VM 103) predate this lab and are not part of it.

Purple has 15 GiB of RAM and an i5-8500T at 6 cores. The budget is 8 GiB for `kasm-01`, 1 GiB for the INetSim LXC, 4 GiB for one detonation guest, and 1.5 GiB for PVE, which is 14.5 of 15. That allows one detonation guest at a time. Going to 32 GiB would allow a victim, a target, and a monitor together.

Grey carries production and stops carrying lab work once the move completes. VLAN separation does not protect those workloads from a hypervisor escape, and neither does the node split while Purple remains a cluster member. I do not run samples that target QEMU, Proxmox, firmware, storage, or uncontrolled worm propagation on this cluster.

## Disposable Lifecycle

Kasm Community Edition may run five concurrent sessions. My normal group is limited to three sessions, and the Proxmox pre-start guard permits at most two disposable full VMs and 10 GiB of their configured memory. Disposable Kasm pools use one user and one session per VM, zero warm systems, `Reusable=false`, and a five-minute downscale delay.

The orphan sweeper considers only marked VMs in the reserved `6200` through `6299` range. It waits 30 minutes, reads active Kasm sessions, and repeats that API check before applied deletion. A Kasm API failure stops cleanup.

## Evidence Boundary

Each malware VM writes artifacts and a SHA-256 manifest to a separate evidence disk. When the VM stops, a Proxmox hook snapshots that disk under a reserved `6300`-series owner before Kasm destroys the disposable VM. A VLAN 79 review VM attaches the retained volume read-only and mounts it `ro,nodev,nosuid,noexec`.

The trusted side initiates SFTP and pulls only reviewed reports or encrypted archives. Raw samples remain encrypted and are not extracted on the permanent Kali VM or a normal workstation. LVM-thin deletion is logical disposal, not a claim that SSD blocks were physically wiped.

## Acceptance Boundary

No live sample runs until harmless test guests prove:

- Kasm is reachable locally and through WireGuard but not from the public Internet.
- Proton-routed lanes show the Proton address and lose Internet access when Proton stops.
- target, offline-malware, and evidence lanes cannot reach the real Internet.
- every lab lane fails toward management, Proxmox, cluster, trusted, server, and unrelated lab destinations.
- clipboard and file transfer match the workspace policy.
- disposable VMs, credentials, disks, and Kasm registrations disappear after session end.
- retained evidence survives source destruction and returns the original SHA-256 manifest.

## Related Records

- [Kasm lab network simplification (2026-07-23)](../Infrastructure/Network/UniFi/Documentation/Change%20Records/Kasm%20Lab%20Network%20Simplification%20-%202026-07-23.md)
- [UniFi networks and VLANs](../Infrastructure/Network/UniFi/Configuration/VLANs/network-vlan.md)
- [UniFi firewall zones](../Infrastructure/Network/UniFi/Configuration/Zones/zone.md)
- [Agent Sandbox](../Platforms/Agent%20Sandbox/Documentation/Agent%20Sandbox%20Plan.md)
