# Firewall Group Creation

**Created:** 2026-07-27  
**Last updated:** 2026-07-27

I created the five IPv4 address groups and three port groups through the UniFi Network MCP. Each create ran through its own preview and confirmed execution. I took a full 61-policy, 16-zone, and group snapshot before every mutation; the snapshot after one create also serves as the rollback baseline before the next.

| Substep | Group | Type | Members | Group count |
|---|---|---|---|---:|
| S02.1 | `OBJ-Monitor-Collector` | address | `192.168.73.2` | 5 to 6 |
| S02.2 | `OBJ-Reverse-Proxy` | address | `192.168.85.2` | 6 to 7 |
| S02.3 | `OBJ-Security-Stack` | address | `192.168.72.2`, `192.168.72.3` | 7 to 8 |
| S02.4 | `OBJ-Proxmox-Nodes` | address | `192.168.70.10` through `.13` | 8 to 9 |
| S02.5 | `OBJ-Observability-Hosts` | address | `192.168.72.2`, `192.168.72.3`, `192.168.73.2` | 9 to 10 |
| S02.6 | `PG-Node-Exporter` | port | `9100`, `9101` | 10 to 11 |
| S02.7 | `PG-Egress-Web` | port | `80`, `443` | 11 to 12 |
| S02.8 | `PG-NTP` | port | `123` | 12 to 13 |

Every structural diff contained one added group, zero removed groups, 61 custom policies before and after, & 16 zones before and after. The final group list returned all eight expected names with the exact type and member set shown above.

The rollback snapshots are `Exports/S02.1-Before-OBJ-Monitor-Collector-Firewall-Snapshot.json` through `Exports/S02.8-After-Firewall-Snapshot.json`. S02 completed without changing a policy, zone, or traffic path.

## Evidence boundary

I retained each before-and-after controller snapshot, but I didn't retain the original MCP preview request, confirmed create request, or create response for the eight mutations. I won't recreate those historical transcripts after the fact.
