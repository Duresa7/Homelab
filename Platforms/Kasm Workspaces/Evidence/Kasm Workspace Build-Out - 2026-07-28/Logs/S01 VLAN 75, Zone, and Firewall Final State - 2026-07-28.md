# S01 VLAN 75, Zone, and Firewall Final State

**Created:** 2026-07-28  
**Last updated:** 2026-07-28

**Capture time:** 2026-07-28 23:37:14 through 23:50:22 UTC  
**Target:** UniFi site `default` on Ahsoka Gateway  
**Mechanism:** UniFi Network MCP for the network and policies; UniFi Site Manager for the custom zone

## Network and zone

I created `KASM-TRUSTED` as a corporate network with VLAN 75, gateway `192.168.75.1/24`, DHCP from `192.168.75.100` through `192.168.75.199`, a 3600-second lease, and UPnP disabled. The controller assigned network ID `6a693e6a052792cd2140d7f5`.

The MCP had no custom-zone creation operation, so I used UniFi Site Manager to create the `KASM-TRUSTED` zone and put only the VLAN 75 network in it. Site Manager showed 16 zones after the change. The controller read-back returned zone ID `6a693f69052792cd2140d82f`, and the full network record carried:

```text
name: KASM-TRUSTED
purpose: corporate
ip_subnet: 192.168.75.1/24
vlan_enabled: true
vlan: 75
dhcpd_enabled: true
dhcpd_start: 192.168.75.100
dhcpd_stop: 192.168.75.199
dhcpd_leasetime: 3600
upnp_lan_enabled: false
firewall_zone_id: 6a693f69052792cd2140d82f
```

The pre-change read showed `KASM Lab Proton Egress` still targeted only network ID `6a616a0d2d027bb055268248`, the VLAN 74 `KASM-BROWSER` network. VLAN 75 was absent.

## Firewall work

The first confirmed DHCP policy create failed before writing a policy:

```text
api.err.FirewallPolicyCreateRespondTrafficPolicyNotAllowed
Firewall policy create respond traffic not allowed
```

The preview did not expose that controller behavior. I confirmed no partial policy existed, added `create_allow_respond: false`, took a fresh snapshot, and retried. The controller then created `KASM Allow KASM-TRUSTED DHCP to Gateway` at index 10000 with UDP source port 68 and destination port 67. The post-change structural diff contained one added policy and no changed or removed policies.

The second preview requested index 10002 for `KASM Allow KASM-TRUSTED NTP to Gateway`. The confirmed create succeeded, but the read-back returned index 10001:

```text
name: KASM Allow KASM-TRUSTED NTP to Gateway
action: ALLOW
enabled: true
index: 10001
protocol: udp
ip_version: IPV4
connection_state_type: ALL
create_allow_respond: false
source.zone_id: 6a693f69052792cd2140d82f
destination.zone_id: 68b788c0e9f08f1e1b2a228a
destination.port: 123
```

The before and after snapshots for that mutation are:

```text
C:\Users\dures\.local\state\unifi-mcp\skills\firewall-snapshots\firewall_20260728T235020Z_02_before.json
C:\Users\dures\.local\state\unifi-mcp\skills\firewall-snapshots\firewall_20260728T235022Z_02_after.json
```

That difference triggered the plan's original stop condition. I had already authorized completion of the full plan, so I treated the controller-assigned index as an observed platform behavior and continued. The effective order remained DHCP, NTP, then the gateway catchall.

## Final firewall readback

I created the gateway catchall at index 10002 and the remaining 14 inter-zone policies. The final controller readback reported 118 user-defined policies, up from the 101-policy live baseline. The 17 new policies were:

```text
KASM Allow KASM-TRUSTED DHCP to Gateway
KASM Allow KASM-TRUSTED NTP to Gateway
KASM Block KASM-TRUSTED Other Gateway
KASM Allow KASM-TRUSTED to External
KASM Block KASM-TRUSTED to KASM-BROWSER
KASM Block KASM-TRUSTED to MALWARE-OFFLINE
KASM Block KASM-TRUSTED to EVIDENCE-QUARANTINE
KASM Block KASM-TRUSTED to LAB-MGMT
KASM Block KASM-TRUSTED to Internal
KASM Block KASM-TRUSTED to AlphaSec-Servers
KASM Block KASM-TRUSTED to AlphaSec-Mgmt
KASM Block KASM-TRUSTED to AlphaSec-Access
KASM Block KASM-TRUSTED to AlphaSec-Observability
KASM Block KASM-BROWSER to KASM-TRUSTED
KASM Block MALWARE-OFFLINE to KASM-TRUSTED
KASM Block EVIDENCE-QUARANTINE to KASM-TRUSTED
LABMGMT Block to KASM-TRUSTED
```

Each policy was enabled for IPv4. The external allow and every inter-zone block read back at index 10000 within its distinct source and destination zone pair. The KASM Lab Proton Egress route still targeted only KASM-BROWSER/VLAN 74.

UniFi automatically placed the new VLAN in the `Proxmox-Trunk` exclusion list. I opened UniFi Site Manager, selected the `Proxmox-Trunk` port profile, and admitted KASM-TRUSTED as a tagged VLAN. The controller then returned the original five exclusions only: Management, IoT, Trusted, DMZ, and Secure. VLAN 75 was absent from the exclusion set, and the guest lane received gateway ARP replies.

## Final MCP readback

I repeated the read-only controller queries after the full build. All five MCP operations returned `success: true`. The network result was:

```text
total_count: 1
name: KASM-TRUSTED
enabled: true
purpose: corporate
ip_subnet: 192.168.75.1/24
vlan_enabled: true
vlan: 75
dhcpd_enabled: true
dhcpd_start: 192.168.75.100
dhcpd_stop: 192.168.75.199
dhcpd_leasetime: 3600
```

The zone query returned 16 zones and one KASM-TRUSTED zone at ID `6a693f69052792cd2140d82f`. The zone endpoint returned an empty `networks` array, as it does for every zone. The network object's `firewall_zone_id` above remains the membership proof.

The full user-defined policy query returned `total_count: 118`. Filtering for enabled KASM-TRUSTED policies returned exactly 17:

```text
KASM Allow KASM-TRUSTED DHCP to Gateway|ALLOW|true|10000|udp|IPV4
KASM Allow KASM-TRUSTED NTP to Gateway|ALLOW|true|10001|udp|IPV4
KASM Block KASM-TRUSTED Other Gateway|BLOCK|true|10002|all|IPV4
KASM Allow KASM-TRUSTED to External|ALLOW|true|10000|all|IPV4
KASM Block KASM-TRUSTED to KASM-BROWSER|BLOCK|true|10000|all|IPV4
KASM Block KASM-TRUSTED to MALWARE-OFFLINE|BLOCK|true|10000|all|IPV4
KASM Block KASM-TRUSTED to EVIDENCE-QUARANTINE|BLOCK|true|10000|all|IPV4
KASM Block KASM-TRUSTED to LAB-MGMT|BLOCK|true|10000|all|IPV4
KASM Block KASM-BROWSER to KASM-TRUSTED|BLOCK|true|10000|all|IPV4
KASM Block MALWARE-OFFLINE to KASM-TRUSTED|BLOCK|true|10000|all|IPV4
KASM Block EVIDENCE-QUARANTINE to KASM-TRUSTED|BLOCK|true|10000|all|IPV4
LABMGMT Block to KASM-TRUSTED|BLOCK|true|10000|all|IPV4
KASM Block KASM-TRUSTED to Internal|BLOCK|true|10000|all|IPV4
KASM Block KASM-TRUSTED to AlphaSec-Servers|BLOCK|true|10000|all|IPV4
KASM Block KASM-TRUSTED to AlphaSec-Mgmt|BLOCK|true|10000|all|IPV4
KASM Block KASM-TRUSTED to AlphaSec-Access|BLOCK|true|10000|all|IPV4
KASM Block KASM-TRUSTED to AlphaSec-Observability|BLOCK|true|10000|all|IPV4
```

Every row also returned `connection_state_type: ALL`, `create_allow_respond: false`, `schedule.mode: ALWAYS`, and `logging: true`. The DHCP row returned source port 68 and destination port 67. The NTP row returned destination port 123.
