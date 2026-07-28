# S01 UniFi Final State Verification

**Created:** 2026-07-28  
**Last updated:** 2026-07-28

**Capture timestamp:** 2026-07-28T14:52:54-04:00  
**Target:** UniFi Network, site `default`  
**Mechanism:** UniFi Network MCP structured read requests

I retained the final readback requests below. The controller mutation payloads used during implementation were not retained.

## LAB-MGMT and VLAN 77

**Request**

```json
{"tool":"unifi_get_network_details","arguments":{"network_id":"6a68e020052792cd2140c6cd","summary":true,"include":"basic,dhcp"}}
```

**Complete structured result**

```json
{
  "success": true,
  "site": "default",
  "network_id": "6a68e020052792cd2140c6cd",
  "include": "basic,dhcp",
  "summary_mode": true,
  "details": {
    "_id": "6a68e020052792cd2140c6cd",
    "name": "LAB-MGMT",
    "enabled": true,
    "purpose": "corporate",
    "ip_subnet": "192.168.78.1/24",
    "vlan_enabled": true,
    "vlan": 78,
    "domain_name": null,
    "is_nat": null,
    "network_isolation_enabled": null,
    "dhcpd_enabled": false,
    "dhcpd_start": null,
    "dhcpd_stop": null,
    "dhcpd_leasetime": null,
    "dhcpd_dns_enabled": null,
    "dhcpd_gateway_enabled": null,
    "dhcpd_unifi_controller": null
  }
}
```

**Request**

```json
{"tool":"unifi_get_network_details","arguments":{"network_id":"6a616a0e2d027bb055268251","summary":true,"include":"basic,dhcp"}}
```

**Complete structured result**

```json
{
  "success": true,
  "site": "default",
  "network_id": "6a616a0e2d027bb055268251",
  "include": "basic,dhcp",
  "summary_mode": true,
  "details": {
    "_id": "6a616a0e2d027bb055268251",
    "name": "MALWARE-OFFLINE",
    "enabled": true,
    "purpose": "corporate",
    "ip_subnet": "192.168.77.1/24",
    "vlan_enabled": true,
    "vlan": 77,
    "domain_name": null,
    "is_nat": null,
    "network_isolation_enabled": null,
    "dhcpd_enabled": true,
    "dhcpd_start": "192.168.77.100",
    "dhcpd_stop": "192.168.77.199",
    "dhcpd_leasetime": 3600,
    "dhcpd_dns_enabled": false,
    "dhcpd_gateway_enabled": null,
    "dhcpd_unifi_controller": null
  }
}
```

## Firewall policy count and residue

**Request**

```json
{"tool":"unifi_list_firewall_policies","arguments":{"limit":1,"summary":true}}
```

**Complete structured result**

```json
{
  "success": true,
  "site": "default",
  "enabled_only": false,
  "total_count": 99,
  "returned_count": 1,
  "count": 1,
  "limit": 1,
  "policies": [
    {
      "id": "68b7d4bbe9f08f1e1b2a2c7f",
      "name": "Block DMZ to Internal",
      "enabled": true,
      "action": "BLOCK",
      "rule_index": 40000,
      "description": "Prevent DMZ workloads from laterally accessing Internal networks.",
      "source": {
        "zone_id": "68b788c0e9f08f1e1b2a228d",
        "matching_target": "ANY"
      },
      "destination": {
        "zone_id": "68b788c0e9f08f1e1b2a2288",
        "matching_target": "ANY"
      }
    }
  ]
}
```

**Request**

```json
{"tool":"unifi_list_firewall_policies","arguments":{"search":"TEST ","limit":100,"summary":true}}
```

**Complete structured result**

```json
{
  "success": true,
  "site": "default",
  "search": "TEST ",
  "enabled_only": false,
  "total_count": 0,
  "returned_count": 0,
  "count": 0,
  "limit": 100,
  "policies": []
}
```

## Narrow management allows and catchall blocks

**Requests**

```json
{"tool":"unifi_get_firewall_policy_details","arguments":{"policy_id":"6a68e079052792cd2140c720"}}
{"tool":"unifi_get_firewall_policy_details","arguments":{"policy_id":"6a68ef99052792cd2140caa5"}}
{"tool":"unifi_get_firewall_policy_details","arguments":{"policy_id":"6a68e09b052792cd2140c723"}}
{"tool":"unifi_get_firewall_policy_details","arguments":{"policy_id":"6a68ef99052792cd2140caa2"}}
```

**Complete structured results**

```json
[
  {
    "success": true,
    "policy_id": "6a68e079052792cd2140c720",
    "details": {
      "_id": "6a68e079052792cd2140c720",
      "action": "ALLOW",
      "connection_state_type": "ALL",
      "connection_states": [],
      "create_allow_respond": true,
      "destination": {
        "ips": ["192.168.78.10"],
        "match_opposite_ips": false,
        "match_opposite_ports": false,
        "matching_target": "IP",
        "matching_target_type": "SPECIFIC",
        "port": "22,443",
        "port_matching_type": "SPECIFIC",
        "zone_id": "6a68e033052792cd2140c6d8"
      },
      "enabled": true,
      "icmp_typename": "ANY",
      "icmp_v6_typename": "ANY",
      "index": 10000,
      "ip_version": "IPV4",
      "logging": true,
      "match_ip_sec": false,
      "match_opposite_protocol": false,
      "name": "LABMGMT Allow Trusted and Personal-A to kasm-01",
      "predefined": false,
      "protocol": "tcp",
      "schedule": {"mode": "ALWAYS"},
      "source": {
        "match_mac": false,
        "match_opposite_networks": false,
        "match_opposite_ports": false,
        "matching_target": "NETWORK",
        "matching_target_type": "OBJECT",
        "network_ids": ["68b78940e9f08f1e1b2a232b","68b78976e9f08f1e1b2a2331"],
        "port_matching_type": "ANY",
        "zone_id": "68b788c0e9f08f1e1b2a2288"
      }
    }
  },
  {
    "success": true,
    "policy_id": "6a68ef99052792cd2140caa5",
    "details": {
      "_id": "6a68ef99052792cd2140caa5",
      "action": "BLOCK",
      "connection_state_type": "ALL",
      "connection_states": [],
      "create_allow_respond": false,
      "description": "Keep LAB-MGMT reachable only from the Trusted and Personal-A network objects allowed above this policy.",
      "destination": {
        "match_opposite_ports": false,
        "matching_target": "ANY",
        "port_matching_type": "ANY",
        "zone_id": "6a68e033052792cd2140c6d8"
      },
      "enabled": true,
      "icmp_typename": "ANY",
      "icmp_v6_typename": "ANY",
      "index": 10001,
      "ip_version": "IPV4",
      "logging": true,
      "match_ip_sec": false,
      "match_opposite_protocol": false,
      "name": "LABMGMT Block Other Internal to LAB-MGMT",
      "predefined": false,
      "protocol": "all",
      "schedule": {"mode": "ALWAYS"},
      "source": {
        "match_opposite_ports": false,
        "matching_target": "ANY",
        "port_matching_type": "ANY",
        "zone_id": "68b788c0e9f08f1e1b2a2288"
      }
    }
  },
  {
    "success": true,
    "policy_id": "6a68e09b052792cd2140c723",
    "details": {
      "_id": "6a68e09b052792cd2140c723",
      "action": "ALLOW",
      "connection_state_type": "ALL",
      "connection_states": [],
      "create_allow_respond": true,
      "destination": {
        "ips": ["192.168.78.10"],
        "match_opposite_ips": false,
        "match_opposite_ports": false,
        "matching_target": "IP",
        "matching_target_type": "SPECIFIC",
        "port": "22,443",
        "port_matching_type": "SPECIFIC",
        "zone_id": "6a68e033052792cd2140c6d8"
      },
      "enabled": true,
      "icmp_typename": "ANY",
      "icmp_v6_typename": "ANY",
      "index": 10000,
      "ip_version": "IPV4",
      "logging": true,
      "match_ip_sec": false,
      "match_opposite_protocol": false,
      "name": "LABMGMT Allow Management Access to kasm-01",
      "predefined": false,
      "protocol": "tcp",
      "schedule": {"mode": "ALWAYS"},
      "source": {
        "match_mac": false,
        "match_opposite_networks": false,
        "match_opposite_ports": false,
        "matching_target": "NETWORK",
        "matching_target_type": "OBJECT",
        "network_ids": ["698cd56010cb5676c296e2d1"],
        "port_matching_type": "ANY",
        "zone_id": "68b788c0e9f08f1e1b2a228b"
      }
    }
  },
  {
    "success": true,
    "policy_id": "6a68ef99052792cd2140caa2",
    "details": {
      "_id": "6a68ef99052792cd2140caa2",
      "action": "BLOCK",
      "connection_state_type": "ALL",
      "connection_states": [],
      "create_allow_respond": false,
      "description": "Keep LAB-MGMT reachable only from the Management Access VPN network object allowed above this policy.",
      "destination": {
        "match_opposite_ports": false,
        "matching_target": "ANY",
        "port_matching_type": "ANY",
        "zone_id": "6a68e033052792cd2140c6d8"
      },
      "enabled": true,
      "icmp_typename": "ANY",
      "icmp_v6_typename": "ANY",
      "index": 10001,
      "ip_version": "IPV4",
      "logging": true,
      "match_ip_sec": false,
      "match_opposite_protocol": false,
      "name": "LABMGMT Block Other VPN to LAB-MGMT",
      "predefined": false,
      "protocol": "all",
      "schedule": {"mode": "ALWAYS"},
      "source": {
        "match_opposite_ports": false,
        "matching_target": "ANY",
        "port_matching_type": "ANY",
        "zone_id": "68b788c0e9f08f1e1b2a228b"
      }
    }
  }
]
```

The policy details prove the intended order because the narrow rules have index 10000 and their catchall blocks have index 10001. They prove the controller configuration only. I did not have an active Management Access VPN client for an end-to-end request.

## Stateful reverse block

**Request**

```json
{"tool":"unifi_get_firewall_policy_details","arguments":{"policy_id":"6a68e0e1052792cd2140c744"}}
```

**Complete structured result**

```json
{
  "success": true,
  "policy_id": "6a68e0e1052792cd2140c744",
  "details": {
    "_id": "6a68e0e1052792cd2140c744",
    "action": "BLOCK",
    "connection_state_type": "CUSTOM",
    "connection_states": ["NEW","INVALID"],
    "create_allow_respond": false,
    "destination": {
      "match_opposite_ports": false,
      "matching_target": "ANY",
      "port_matching_type": "ANY",
      "zone_id": "6a616d942d027bb055268c60"
    },
    "enabled": true,
    "icmp_typename": "ANY",
    "icmp_v6_typename": "ANY",
    "index": 10000,
    "ip_version": "IPV4",
    "logging": true,
    "match_ip_sec": false,
    "match_opposite_protocol": false,
    "name": "KASM Block MALWARE-OFFLINE to KASM-BROWSER",
    "predefined": false,
    "protocol": "all",
    "schedule": {"mode":"ALWAYS"},
    "source": {
      "match_opposite_ports": false,
      "matching_target": "ANY",
      "port_matching_type": "ANY",
      "zone_id": "6a616dbb2d027bb055268d8e"
    }
  }
}
```

## Proton route and client

**Requests**

```json
{"tool":"unifi_get_traffic_route_details","arguments":{"route_id":"6a6170cc2d027bb055269a6c"}}
{"tool":"unifi_list_vpn_clients","arguments":{}}
```

**Complete structured results**

```json
[
  {
    "success": true,
    "site": "default",
    "route_id": "6a6170cc2d027bb055269a6c",
    "details": {
      "_id": "6a6170cc2d027bb055269a6c",
      "description": "KASM Lab Proton Egress",
      "domains": [],
      "enabled": true,
      "ip_addresses": [],
      "ip_ranges": [],
      "kill_switch_enabled": true,
      "matching_target": "INTERNET",
      "network_id": "68b790fbe9f08f1e1b2a23fe",
      "next_hop": "",
      "regions": [],
      "target_devices": [
        {
          "network_id": "6a616a0d2d027bb055268248",
          "type": "NETWORK"
        }
      ]
    }
  },
  {
    "success": true,
    "site": "default",
    "count": 1,
    "vpn_clients": [
      {
        "wireguard_client_configuration_filename": "wg-US-GA-568.conf",
        "purpose": "vpn-client",
        "wireguard_client_mode": "file",
        "external_id": "945f59d5-becc-4c97-aa70-6d6272cf5f24",
        "interface_mtu_enabled": false,
        "routing_table_id": 178,
        "enabled": true,
        "vpn_type": "wireguard-client",
        "mss_clamp": "auto",
        "ip_subnet": "10.2.0.2/32",
        "wan_dhcpv6_pd_size_auto": false,
        "name": "ProtonVPN",
        "site_id": "68b7cc65620e3d7fdfd2f326",
        "wireguard_id": 1,
        "firewall_zone_id": "68b788c0e9f08f1e1b2a2289",
        "wireguard_client_configuration_file": "***REDACTED***",
        "_id": "68b790fbe9f08f1e1b2a23fe"
      }
    ]
  }
]
```

## Proxmox trunk

**Request**

```json
{"tool":"unifi_get_port_profile_details","arguments":{"profile_id":"698cc29d10cb5676c296c7c1"}}
```

**Complete structured result**

```json
{
  "success": true,
  "profile_id": "698cc29d10cb5676c296c7c1",
  "details": {
    "setting_preference": "manual",
    "port_security_enabled": false,
    "stormctrl_ucast_rate": 100,
    "egress_rate_limit_kbps_enabled": false,
    "stormctrl_mcast_enabled": false,
    "lldpmed_notify_enabled": false,
    "tagged_vlan_mgmt": "custom",
    "stormctrl_bcast_enabled": false,
    "multicast_router_mode": "NONE",
    "stp_uplink": true,
    "port_keepalive_enabled": false,
    "excluded_networkconf_ids": [
      "68b7cc68620e3d7fdfd2f341",
      "68b78866e9f08f1e1b2a227b",
      "68b789dbe9f08f1e1b2a2341",
      "68b78a68e9f08f1e1b2a2350",
      "68b78940e9f08f1e1b2a232b"
    ],
    "eee_enabled": false,
    "stp_bpdu_guard_enabled": false,
    "stormctrl_mcast_rate": 100,
    "native_networkconf_id": "",
    "qos_profile": {
      "qos_profile_mode": "custom",
      "qos_policies": []
    },
    "port_security_mac_address": [],
    "dot1x_idle_timeout": 300,
    "precision_time_protocol_enabled": true,
    "op_mode": "switch",
    "poe_mode": "off",
    "forward": "customize",
    "stormctrl_ucast_enabled": false,
    "stormctrl_bcast_rate": 100,
    "isolation": false,
    "voice_networkconf_id": "",
    "stp_port_mode": true,
    "name": "Proxmox-Trunk",
    "site_id": "68b7cc65620e3d7fdfd2f326",
    "_id": "698cc29d10cb5676c296c7c1",
    "autoneg": true,
    "flow_control_enabled": true,
    "stp_edge_state": "auto",
    "lldpmed_enabled": false,
    "dot1x_ctrl": "force_authorized"
  }
}
```

I resolved the five excluded network IDs through `unifi_list_networks`: Management, IoT, DMZ, Secure, and Trusted. LAB-MGMT and the three session networks are absent from the exclusion list.

Every structured request returned `success: true`; the API wrapper exposed no separate standard error or numeric process exit code.
