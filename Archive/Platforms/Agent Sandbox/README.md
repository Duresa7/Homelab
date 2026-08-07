# Agent Sandbox

**Created:** 2026-07-20  
**Last updated:** 2026-08-06

> Cancelled on 2026-08-06. I dropped the project before any of it was built, so there is nothing to decommission: no broker, no sandbox VLAN, no templates, and no guests. The design below is kept as a record of the thinking, not as a plan I intend to run.

This platform is the design for a broker that provisions throwaway machines on demand. A caller asks for a Docker container or a full VM, the broker hands back a way in, then destroys the guest when the task ends so the memory & disk come back. Nothing is built yet as of 2026-07-20: no broker, no sandbox VLAN, & no templates past the two Linux ones already sitting on grey-server.

One broker holds every key. Agents reach it through an MCP interface or a CLI, & the broker is the only thing that talks to the Proxmox API or the Docker host, so an agent never gets direct control of the hypervisor. It enforces the size caps, the 2-hour default lifetime, & the network isolation, & it logs every create, exec, & destroy to Splunk.

## Status

Cancelled. The design was locked on 2026-07-20 and the build never started. Nothing was provisioned and nothing needs to come back out.

## Layout

| Path | What it holds |
| --- | --- |
| [Documentation/Agent Sandbox Plan.md](Documentation/Agent%20Sandbox%20Plan.md) | The locked design, the phased build I never ran, & the decisions left open |

## Related records

- [Galaxy cluster](../../../Infrastructure/Compute/Galaxy/README.md): the Proxmox nodes that host the sandboxes, purple-server by default & grey-server for the heavy ones.
- [UniFi network and zone inventories](../../../Infrastructure/Network/UniFi/Configuration/network-vlan.md): the live state I use to choose the sandbox VLAN and firewall zone.
- [Isolated Security Lab](../../../Architecture/Isolated-Security-Lab.md): the malware-detonation range whose no-egress containment model the untrusted lane reuses.
