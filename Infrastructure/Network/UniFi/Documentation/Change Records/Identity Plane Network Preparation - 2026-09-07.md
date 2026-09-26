# Identity Plane Network Preparation

**Created:** 2026-09-25  
**Last updated:** 2026-09-25

**Implementation date:** 2026-09-07  
**Status:** Complete  
**Affected systems:** IDENTITY-A (VLAN 65), zone `AlphaSec-Identity`, port profile `Proxmox-Trunk`, Bane Switch POE port 14, firewall policies for the identity plane

On 2026-09-07 I prepared the UniFi side of the Active Directory identity plane before the domain controllers were built. I verified the network and zone, admitted VLAN 65 on the trunk to `grey-server`, checked the eight identity policies, and added one policy for syslog to Splunk. I wrote this record on 2026-09-25 from the paragraphs the configuration views carried and from the five retained exports.

## What changed

1. **Network readback.** IDENTITY-A was enabled on VLAN 65 with gateway `192.168.65.1/24`, DHCP `192.168.65.100` to `192.168.65.120`, and zone `AlphaSec-Identity`, resolved from the network's `firewall_zone_id`. The network reported `mdns_enabled: false`, `ipv6_interface_type: none` and `ipv6_ra_enabled: false`. The mDNS field mirrors a site-wide setting and does not verify it. Secure and Secure Client stayed in Internal. The controller returned 23 networks, 16 of them routed corporate LANs.
2. **Trunk.** I removed IDENTITY-A from the `Proxmox-Trunk` exclusion list and changed nothing else in the profile. The readback showed one persisted field, VLANs 65 and 60 admitted, and `grey-server` online at `192.168.70.10` on Bane Switch POE port 14 at 2.5 GbE.
3. **Existing identity policies.** I compared the eight identity policies with the controller and found no mismatch in action, enabled state, protocol, zone or selector: `Allow Workstations to AD`, `Allow PAW to Windows Admin`, `Allow Identity DNS to Gateway` (TCP and UDP 53), `Allow Identity NTP to Gateway` (UDP 123), `Allow Identity to Wazuh - Security-A` (TCP 1514 and 1515 to `192.168.72.2`), `Allow Identity Web Egress` (TCP 80 and 443), `Allow Monitor to Windows Exporter`, and `Block Identity Other External Egress`.
4. **Splunk path.** On `splunk-siem` SC4S was active with host networking and listening on TCP and UDP 514, with the CEF listeners on 1514. No policy admitted the identity zone to Splunk, so I created `Allow Identity to Splunk - Security-A`: an allow from `AlphaSec-Identity` to `192.168.72.3` on TCP and UDP 514, index 10001, with its response companion at index 30001.

## Policy details

- `Allow Workstations to AD` selects exactly Secure and Secure Client in Internal, with no other source network.
- All nine identity policies are enabled, use both IP versions and the Always schedule, and carry no source port restriction.
- Identity-to-External ran `Allow Identity Web Egress` at index 10000 and `Block Identity Other External Egress` at 10001. The ordering endpoint returned two before-system entries and no after-system entries. The web rule binds explicit TCP ports 80 and 443, not `PG-Egress-Web`, because the controller had earlier rejected a port group with an any-in-zone destination. I did not reproduce that failed write. On 2026-09-09 `Allow Identity NTP Egress` took index 10001 and the block moved to 10002 ([Identity NTP and Client DNS](Identity%20NTP%20and%20Client%20DNS%20-%202026-09-09.md)).
- The workstation AD, PAW administration, Wazuh, exporter and Splunk rules have `create_allow_respond: true`. DNS, NTP, web egress and the external block have it false. Only the external block logs matches.
- `Allow Identity to Splunk - Security-A` has ID `6a9f71f1f9e5db2485af6cce`, logging off, and no address or port group bound. I used the standard syslog port 514; the CEF listeners on 1514 serve UniFi.
- The 349-policy inventory before the change held no SERVERS-A-to-Splunk policy. The only custom rule from `AlphaSec-Servers` to `AlphaSec-Observability` targets Wazuh at `192.168.72.2`. I left that gap as it was.

I left Secure and Secure Client DHCP DNS unchanged and created no VPN access on this day. The result verifies the controller preparation and the Splunk listener, not event delivery from the Windows guests, which did not exist yet.

## Address group rename the same day

Before the identity work I renamed the six `OBJ-` address groups to `AG-`, changing only their names. IDs and members were unchanged (1, 1, 2, 5, 3 and 1 members), no `OBJ-` name remained, and the ten existing port groups were unchanged. All 23 policies that referenced the groups returned the same group IDs and configuration. No raw transcript was retained for the rename.

The follow-up readback returned 22 Network Lists and 349 policies, 76 of them user-defined. Six lists had appeared between the two checks: `AG-Domain-Controllers`, `AG-Identity-Servers`, `AG-PAW`, `PG-AD-Client`, `PG-Windows-Admin` and `PG-Windows-Exporter`, and a new `Allow Monitor to Windows Exporter` policy referenced `AG-Monitor-Collector`. The rename did not create or change any of them; they are the identity lists and policies verified above.

## Verification

At 10:25 PM Eastern the controller returned 351 policies: 77 user-defined (69 allows and eight blocks) and 274 generated. The other 76 user-defined policies were unchanged. The zone list held 12 zones and the Network Lists numbered 22.

Retained exports:

- [Initial Controller Readback](../../Evidence/Identity%20Plane%20Network%20Preparation%20-%202026-09-07/Exports/Initial%20Controller%20Readback.json), 10:23 PM
- [Trunk Update and Readback](../../Evidence/Identity%20Plane%20Network%20Preparation%20-%202026-09-07/Exports/Trunk%20Update%20and%20Readback.json)
- [Splunk Listener Checks](../../Evidence/Identity%20Plane%20Network%20Preparation%20-%202026-09-07/Exports/Splunk%20Listener%20Checks.json)
- [Splunk Policy Creation and Readback](../../Evidence/Identity%20Plane%20Network%20Preparation%20-%202026-09-07/Exports/Splunk%20Policy%20Creation%20and%20Readback.json)
- [Final Identity Policy Readback](../../Evidence/Identity%20Plane%20Network%20Preparation%20-%202026-09-07/Exports/Final%20Identity%20Policy%20Readback.json), 10:25 PM, all nine identity policies and their response companions

The first listener check failed because `sudo` needed a terminal; the unprivileged `ss -lntu` and `systemctl show sc4s.service` checks that followed are the ones the result rests on.

## Follow-up

The domain controllers were built on 2026-09-09 ([Forest Build](../../../../../Platforms/Active%20Directory/Documentation/Change%20Records/Forest%20Build%20-%202026-09-09.md)), and the same day I moved client DNS on Secure and Secure Client to them ([Identity NTP and Client DNS](Identity%20NTP%20and%20Client%20DNS%20-%202026-09-09.md)).
