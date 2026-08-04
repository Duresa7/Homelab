# S01 Snapshot and Reference Inventory

**Created:** 2026-07-27  
**Last updated:** 2026-08-04

## Capture

- Timestamp: `2026-07-27T13:16:29-04:00`; the later batched reads carry their own UTC timestamps
- Target: UniFi Network site `default`
- Execution mechanism: UniFi Network MCP
- Shell & working directory: no shell executed against the controller; local records live under `D:\Documents\Homelab`
- Mutation count: zero

## Requests and results

### Firewall policies

I issued `unifi_list_firewall_policies` with `include_predefined: true`, `limit: 1000`, and `summary: false`. The request succeeded with `total_count: 431` & `returned_count: 431`.

The local-only `Exports/S01-Firewall-Policies.json` holds the full structured response. Its SHA-256 digest is `E050489C42FDED95BF43CA7B83D01A36B4ACA6BA484C4823968EC4AF31F8BD61`.

### Zones and networks

I issued `unifi_list_firewall_zones`, `unifi_list_networks` with `limit: 100`, then `unifi_get_network_details` with `summary: false` for each of the 26 returned network IDs. The reads returned 16 zones & 26 networks. The detail responses retain each network's `firewall_zone_id`, which the zone-list endpoint omits.

The local-only `Exports/S01-Firewall-Zones.json` and `Exports/S01-Networks-With-Zone-IDs.json` hold the complete responses. Their SHA-256 digests are `F30CE7BDFE31C01CEABC7B583B393A1C6E1802A50B1965262759AFFD2D3A3380` & `FA5E330ADC84DC9D17D34DAC03F08DC2C95DFE2BC8975A889E2355C8D34E0B00`.

### Firewall and client groups

I issued `unifi_list_firewall_groups`, `unifi_list_client_groups`, and `unifi_list_oon_policies`. The controller returned five firewall groups, all port groups; 14 client groups; & four OON policies.

I compared every one of the 14 client-group IDs against all 61 custom firewall policy objects and all four OON policy objects. `D_devices` is the only referenced group. The enabled `QoS for D` OON policy targets it; the other 13 groups have no firewall-policy or OON-policy reference.

The local-only `Exports/S01-Firewall-Groups.json`, `Exports/S01-Client-Groups.json`, `Exports/S01-OON-Policies.json`, and `Exports/S01-Client-Group-Reference-Inventory.json` hold the full results.

## Verification

The stop condition required 61 custom policies. I counted 61 custom & 370 predefined entries in the same 431-policy response, so S01 passed. I captured the rollback baseline before issuing any controller mutation or starting the Active Directory decommission.
