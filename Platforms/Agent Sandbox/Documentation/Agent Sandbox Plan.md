# Agent Sandbox Plan

**Created:** 2026-07-20  
**Last updated:** 2026-07-20

I want my AI agents to spin up their own test machines & tear them down when they're done. Sometimes a job needs a Docker container, sometimes a full Linux VM, sometimes Windows. This record is the design I've locked, the order I'll build it in, & the decisions I still owe. Nothing is built as of 2026-07-20.

The whole point is that an agent asks for a box, gets one that's fenced off from everything I care about, uses it, & the box disappears. No agent ever holds a Proxmox credential, & no sandbox ever reaches my LAN, my hypervisor management plane, or my production guests.

## Diagram

![Agent Sandbox architecture: AI agents call one broker that holds the only Proxmox & Docker keys; the broker provisions Docker containers & full VMs into an isolated VLAN, trusted boxes reach the internet through ProtonVPN, untrusted boxes get none, & a red barrier blocks any path to my internal network](Diagrams/agent-sandbox.png)

Agents on the left reach one broker; the broker holds the only keys & drops every box into the isolated VLAN on the right, walled off from my internal network.

## Two lanes

The sandboxes run in two trust lanes, & the baseline is built to the stricter one. The fast lane is for trusted-ish work: install a package, reproduce a Linux bug, run a build, try a config. The locked lane is for code I haven't vetted: arbitrary internet downloads, pentest tooling, anything that could be hostile. Every box, either lane, sits in its own isolated network with no path back to the Internal zone.

I split by lane because autonomous agents running things I never read is a hostile-code risk profile even on a normal day. Building the floor to the locked standard means the fast lane is a convenience layer on top of a boundary that already holds.

## What runs where

Two building blocks, not three. A plain Docker container is the default for quick Linux work: it starts in seconds, throws away cleanly, & its images already cover Ubuntu, Debian, & Rocky. When a container isn't enough, or the job is Windows, or the code is untrusted, the broker gives out a full KVM VM instead.

I dropped LXC on purpose. An LXC or a Docker container shares the Proxmox node's kernel, so a container escape is a node compromise; that's fine for trusted Linux tests but useless as a wall around hostile code. Only hardware virtualization is a real boundary, so untrusted work & all Windows run as full VMs. Untrusted code that needs Docker runs Docker nested inside a throwaway VM, behind the VM wall, never on a shared Docker host.

## Where it runs

purple-server is the default home. It's an Intel i5-8500T with 6 cores, 15.46 GiB of memory, & a single 238 GB NVMe, & it runs nothing else today, so a sandbox that misbehaves there hits an empty machine instead of production. grey-server absorbs the heavy boxes: it's a Ryzen 7 3700X with 62.72 GiB of memory, a 1.82 TiB SSD pool, a 1.82 TiB ZFS disk, & the GTX 1080 Ti, so anything that needs bulk disk, more memory, or the GPU lands there. A Windows VM's 80 GB won't fit purple's small drive next to templates, so Windows & other disk-heavy boxes route to grey automatically, while genuinely hostile code is forced back to purple's isolation even when it wants grey's disk.

I keep sandboxes off grey by default because grey carries every production VM & is already overcommitted. There's no shared storage on this cluster; each node runs off its own NVMe, & only grey has bulk disk. A sandbox is pinned to whatever node holds its disk, which is fine because these boxes are throwaway & never migrate. Templates live on both purple & grey so the broker can clone locally on either.

## The broker

One broker is the whole control plane, & it's the only thing holding keys. I build it once as a shared core engine, then expose it two ways: an MCP server so Claude Code & other agents call it as tools, & a CLI so I & shell-driven agents like Codex can run `sandbox create` by hand. Same brain, two faces.

The broker owns a scoped Proxmox API token whose role reaches only a dedicated `sandbox` resource pool, plus access to the sandbox Docker host. An agent never sees either. The broker exposes a small verb set: create a box of a given OS, kind, size, & lifetime; list what's running; run a command inside; extend a lifetime; destroy. It enforces the size caps, the lifetime, the node choice, the naming, & the isolation, & every call is logged.

## Network & isolation

The sandboxes get their own VLAN in a new custom firewall zone, cut off from every Internal network: my workstations on Secure (VLAN 50) & Secure Client (VLAN 60), the domain controllers on AD-SERVERS (VLAN 65), the app & data servers on SERVERS-A (VLAN 80), & the Proxmox management plane on MGMT-A (VLAN 70). The firewall runs default-deny outward to anything internal & drops sandbox-to-8006 on the nodes & sandbox-to-gateway on the locked net. Sandboxes can't see each other unless a job explicitly needs a small attacker-victim network.

Internet egress splits by lane. The trusted lane gets normal outbound so apt, pip, & npm work, routed through my existing ProtonVPN egress so sandbox traffic doesn't leave on my real WAN IP. The locked lane gets no internet at all by default, so unvetted code can't phone home or leak; when a specific untrusted job legitimately needs to fetch something, I open a filtered, logged path scoped to that one box. The VLAN ID & subnet come from the [UniFi network segmentation plan](../../../Infrastructure/Network/UniFi/Documentation/Change%20Plans/Network-Segmentation-TODO.md); I'll pull the live UniFi list & pick an unused pair.

## Lifetime & cleanup

Every box is throwaway. The default lifetime is 2 hours from the task finishing or going idle, an agent can request up to 24 hours for a longer job & extend while it's still working, & an idle box gets reclaimed early. A sweeper runs on a schedule & destroys anything past its lifetime or orphaned, so no sandbox strands the way CT 107 & CT 108 did in the [2026-07-20 HA stranding incident](../../../Security/Incidents/Galaxy-HA-Local-Storage-Stranding-2026-07-20/Galaxy-HA-Local-Storage-Stranding-Incident-2026-07-20.md).

Boxes are always freshly cloned from a template & never backed up, so they don't bloat my backup jobs & there's no stale state to roll back. Reclaim is destroy-and-reclone, not snapshot-and-restore.

## Size limits & concurrency

Every sandbox gets a hard cap, & the broker refuses to exceed it. The defaults:

| Kind | vCPU | Memory | Disk |
| --- | --- | --- | --- |
| Docker container | 2 | 2 GiB | 20 GB |
| Linux VM | 2 | 4 GiB | 40 GB |
| Windows VM | 4 | 8 GiB | 80 GB |

purple carries at most about 10 GiB of sandbox memory at once, which leaves headroom on its 15.46 GiB, so roughly a couple of Linux VMs or a pile of containers concurrently. When purple's budget is full or a bigger box is asked for, the broker spills to grey under its own budget cap so agent boxes can't starve production. purple's single 238 GB drive is the real ceiling on how many boxes run there; the cheapest fix later is adding an SSD to purple.

## Secrets & access

No production key, token, or password ever goes into a sandbox. The broker generates a throwaway SSH key for a Linux box or a random admin password for a Windows box, hands the agent only what that one box needs, & wipes it on destroy. Agents run commands inside through the broker's exec verb, which is the single logged path in; for interactive work I can take direct SSH or RDP over the isolated VLAN.

The broker is the only bridge between the agent side & the sandbox network, & the bridge is one-way in. A sandbox can't reach back into the agent's environment, the repo, or any credential store.

## Logging

The broker records every create, exec, extend, & destroy to Splunk: who asked, what they got, when, & on which node. Trusted-lane internet egress is logged too, so I can see what a box reached. The locked lane logs the same events plus every packet its opt-in filtered path carries.

## OS images

Day-one images are Ubuntu, Debian, & Rocky Linux, prepped as cloud-init templates on both purple & grey & as Docker base images. I picked Rocky for the Red Hat family because I already run it for the Splunk SIEM, so the tooling is familiar. Windows 11 & Kali Linux are supported too; the broker builds those templates the first time they're asked for, since a Windows image is 80 GB & I don't want it sitting idle.

## Phased build

1. Reserve the pieces: a sandbox VLAN & custom firewall zone in UniFi, a Proxmox `sandbox` resource pool with a scoped API token, & a VMID range for sandbox guests.
2. Build the golden templates on purple & grey: Ubuntu, Debian, & Rocky as cloud-init clones, plus a dedicated sandbox Docker host so agent containers never touch docker-main.
3. Write the broker core & CLI: create, list, exec, extend, & destroy for Docker containers & Linux VMs, with the size caps, the 2-hour lifetime, the sweeper, & Splunk logging.
4. Add the MCP interface over the same core & wire it into the agents.
5. Add Windows 11 & Kali templates on demand, the locked lane's no-egress net with its opt-in filtered path, & the ProtonVPN egress for the trusted lane.
6. Prove it's sealed: from inside a sandbox, confirm the must-fail tests fail before agents get the keys.

## How I'll prove it's sealed

Config isn't proof; I test from inside a box before any agent uses it. A ping to a LAN host, a Proxmox management IP, the gateway on the locked net, & another sandbox must all fail. A trusted-lane box must reach the internet only through ProtonVPN & still fail to reach anything internal. If a must-fail test passes, I stop & fix the firewall before the broker goes live.

## Open decisions

- Sandbox VLAN ID & subnet: pull the live UniFi list & pick an unused pair that doesn't collide with the security lab's planned segment.
- Docker host shape: a dedicated container on purple versus a small VM, & whether nested-Docker-in-VM for the untrusted case is a standing template or built per job.
- Concurrency ceilings: the exact per-node & per-agent limits above the 10 GiB purple budget.
- purple disk: whether to add an SSD now to raise concurrency past a couple of Windows VMs, or live with 238 GB & lean on grey.
- Broker stack & host: Python or Node, & which host runs the broker itself.
- GPU sandboxes on grey: out of scope for the first version; revisit if an agent needs CUDA.

## Related records

- [Galaxy cluster](../../../Infrastructure/Compute/Galaxy/README.md): the Proxmox nodes, storage, & templates the sandboxes clone from.
- [UniFi network segmentation plan](../../../Infrastructure/Network/UniFi/Documentation/Change%20Plans/Network-Segmentation-TODO.md): where the sandbox VLAN & firewall zone are assigned.
- [Isolated Security Lab](../../../Architecture/Isolated-Security-Lab.md): the malware-detonation range; the untrusted lane reuses its no-egress containment rules.
- [Galaxy HA local-storage stranding incident](../../../Security/Incidents/Galaxy-HA-Local-Storage-Stranding-2026-07-20/Galaxy-HA-Local-Storage-Stranding-Incident-2026-07-20.md): why the sweeper & destroy-and-reclone matter on a cluster with no shared storage.
