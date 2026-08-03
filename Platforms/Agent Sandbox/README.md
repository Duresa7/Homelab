# Agent Sandbox

**Created:** 2026-07-20  
**Last updated:** 2026-08-03

This platform is the design for a broker that provisions throwaway machines on demand. A caller asks for a Docker container or a full VM, the broker hands back a way in, then destroys the guest when the task ends so the memory & disk come back. Nothing is built yet as of 2026-07-20: no broker, no sandbox VLAN, & no templates past the two Linux ones already sitting on grey-server.

One broker holds every key. Agents reach it through an MCP interface or a CLI, & the broker is the only thing that talks to the Proxmox API or the Docker host, so an agent never gets direct control of the hypervisor. It enforces the size caps, the 2-hour default lifetime, & the network isolation, & it logs every create, exec, & destroy to Splunk.

## Status

Planning. The locked design, the phased build, & the decisions I still owe live in the [Agent Sandbox Plan](Documentation/Agent%20Sandbox%20Plan.md). When I build it, the command-level steps & the post-change tests go in a dated record under `Documentation/Change Records/`, & the new guests & templates get added to the inventories under `Operations/Inventory/Galaxy/`.

## Layout

| Path | What it holds |
| --- | --- |
| [Documentation/Agent Sandbox Plan.md](Documentation/Agent%20Sandbox%20Plan.md) | The locked design, the phased build, & the open decisions |
| `Documentation/Diagrams/` | The architecture diagram |
| `Source/` | The broker: the shared core, its MCP server, & its CLI, once I start building |
| `Documentation/Change Records/` | Dated build & change records, once work starts |

## Related records

- [Galaxy cluster](../../Infrastructure/Compute/Galaxy/README.md): the Proxmox nodes that host the sandboxes, purple-server by default & grey-server for the heavy ones.
- [UniFi network and zone inventories](../../Infrastructure/Network/UniFi/Configuration/network-vlan.md): the live state I use to choose the sandbox VLAN and firewall zone.
- [Isolated Security Lab](../../Architecture/Isolated-Security-Lab.md): the malware-detonation range whose no-egress containment model the untrusted lane reuses.
