# Empty IOT Client Group Removal

**Created:** 2026-09-06  
**Last updated:** 2026-09-06

**Implementation date:** 2026-09-06  
**Status:** Complete  
**Affected systems:** UniFi Network controller, client groups

## Why

The [2026-09-06 audit](../../../../../Operations/Maintenance/Documentation%20Staleness%20Audit%20-%202026-09-06.md) returned 17 client groups where the record held 15. The two extra were `IOT`, with no members, and `IoT`, with one. Their object IDs place both at about 15:25 UTC on 2026-08-26, nine seconds apart, the same afternoon the `PG-Printing` group and `Allow Internal to Printer` policy were created. The one `IoT` member is the Brother printer at `192.168.20.212`, the destination that policy names. So `IoT` is the group made for the printer work and `IOT` is the empty first attempt at the same name, which is also the name of the empty group I deleted during the [2026-07-27 consolidation](Zone%20and%20Object%20Consolidation%20-%202026-07-27.md).

## What I did

I deleted `IOT` through `unifi_delete_client_group` with confirmation. I kept `IoT`: it holds a live client and was created on purpose with the printer policy. I did not fold the printer into `iot_device`, because that group's six members are the household IoT set and the printer had been given its own group deliberately.

## Verification

The controller returned `deleted successfully`, and the client-group list now has 16 entries: the 15 recorded on 2026-07-27 plus `IoT` with its one member. No OON policy targeted the deleted group, and the V2 firewall schema has no client-group selector, so nothing referenced it.
