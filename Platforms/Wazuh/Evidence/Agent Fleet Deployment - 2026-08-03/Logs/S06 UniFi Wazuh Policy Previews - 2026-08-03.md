# S06 UniFi Wazuh Policy Previews

**Created:** 2026-08-03  
**Last updated:** 2026-08-03

**Captured:** 2026-08-03 02:36 EDT  
**Target:** UniFi Network site `default`  
**Mechanism:** UniFi Network MCP; `unifi_create_firewall_policy` with `confirm=false`

## Snapshot

I captured all 121 user policies, 16 zones, & 15 firewall groups before previewing a mutation:

```text
C:/Users/dures/.local/state/unifi-mcp/skills/firewall-snapshots/firewall_20260803T063651Z.json
```

## Validated previews

All four previews returned `success=true` and `requires_confirmation=true`.

| Policy | Source | Destination | Protocol & ports |
|---|---|---|---|
| `Allow monitor-01 to Wazuh - Security-A` | AlphaSec-Observability; `192.168.73.2` | AlphaSec-Observability; `192.168.72.2` | IPv4 TCP; `Wazuh Ports` object 1514/1515 |
| `Allow docker-network to Wazuh - Security-A` | AlphaSec-Access; `192.168.85.2` | AlphaSec-Observability; `192.168.72.2` | IPv4 TCP; `Wazuh Ports` object 1514/1515 |
| `Allow kasm-01 to Wazuh - Security-A` | LAB-MGMT; `192.168.78.10` | AlphaSec-Observability; `192.168.72.2` | IPv4 TCP; `Wazuh Ports` object 1514/1515 |
| `Allow Galaxy nodes to Wazuh - Security-A` | AlphaSec-Mgmt; `.10`, `.11`, `.12`, `.13` | AlphaSec-Observability; `192.168.72.2` | IPv4 TCP; `Wazuh Ports` object 1514/1515 |

Each policy uses `ALLOW`, `connection_state_type=ALL`, `create_allow_respond=true`, `logging=true`, & an always-on schedule. No rule was created because the required confirmation hasn't been given.

