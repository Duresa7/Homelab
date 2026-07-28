# UniFi zone membership is absent from the zone-matrix endpoint

**Created:** 2026-07-27  
**Last updated:** 2026-07-27

**Investigated:** 2026-07-27

## Symptom

`unifi_list_firewall_zones` returned all 16 zones with correct IDs and names, but every zone contained `"networks": []`. The call looked successful, so a membership table built from that result would have been silently empty.

## Exact error

The zone call returned no error or warning. Its incorrect-looking success payload contained `"networks": []` for every zone. A separate `unifi_list_networks` request for `firewall_zone_id` reported that field under `unknown_fields`.

## Failed attempts

- I first used `unifi_list_firewall_zones`, which returned the empty arrays.
- I asked `unifi_list_networks` for `firewall_zone_id`, but the tool rejected the field.
- I used `unifi_get_network_details` with `summary: true`; every `include` section, including `basic`, omitted the field.
- I considered patching the marketplace clone, but the configured server runs `uvx unifi-network-mcp==0.24.1` from PyPI, so the local clone isn't the executing code.

## Hypotheses

I tested three explanations: an authentication or site-selection failure, a serializer dropping a field that the endpoint supplied, and membership being stored on a different object.

## Tests

- Correct zone IDs and names proved that authentication and site selection worked.
- The V2 `/firewall/zone-matrix` response shape contained `_id`, `name`, `zone_key`, and policy counts, but no membership field.
- A raw `unifi_get_network_details` read with `summary: false` returned `firewall_zone_id` on each network.
- Inverting those raw network values produced a complete zone-to-network map.

## Root cause

Membership is stored on each network as `firewall_zone_id`, not on the zone. The plugin's zone serializer looks for `networks` or `network_ids` in a zone-matrix payload that contains neither, then returns an empty list instead of marking the data unavailable. The network summary model also omits `firewall_zone_id`.

## Corrective action

I read `firewall_zone_id` from each routed network with `unifi_get_network_details` at `summary: false`, then inverted the results into a zone-to-networks map. Nothing was patched. The running server remains pinned to `unifi-network-mcp` 0.24.1.

## Verification

The inverted map returned all 12 populated zones with their networks. Eleven matched the membership already recorded in [zone.md](../../Configuration/Zones/zone.md). The twelfth exposed `Secure-V`/VLAN 100 in the built-in `Untrusted` zone, which the prior records had omitted.

## Related limitation

The plugin exposes no zone create, rename, delete, or reassign operation and no network delete operation. `FirewallZone` is read-only with an empty mutable-field set, and `firewall_zone_id` isn't exposed by the network mutation tools. Zone restructuring and network deletion therefore require the controller UI. The [consolidation change](../Change%20Records/Zone%20and%20Object%20Consolidation%20-%202026-07-27.md) retained a snapshot before every zone step because no rollback call exists.
