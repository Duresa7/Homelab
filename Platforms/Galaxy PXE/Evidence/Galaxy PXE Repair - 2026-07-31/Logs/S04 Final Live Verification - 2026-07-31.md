# S04 Final Live Verification

**Created:** 2026-07-31  
**Last updated:** 2026-07-31

**Capture timestamp:** 2026-07-31T06:02:44+00:00  
**Targets:** `ansible-01`, `grey-server`, `red-server`, and UniFi  
**Mechanisms:** SSH Manager and UniFi Network controller readback  
**Working directory:** `/home/ansible/proxmox-pxe-provisioning` where applicable
**Transcript boundary:** The SSH commands and results below are complete. I retained the exact callback-policy request and complete structured response. The switch inspection tools returned every field for all 18 ports or the complete controller objects for both profiles. I retained their exact requests and the result fields used for this verification. I did not retain the unrelated ports and controller fields because they add no evidence about Green or either named profile.

## Service and Cluster Command

```bash
date --iso-8601=seconds
hostname
systemctl is-enabled galaxy-pxe tftpd-hpa
systemctl is-active galaxy-pxe tftpd-hpa
curl --fail --silent --show-error http://127.0.0.1:8080/health
grep 'proxmox-start-auto-installer' /srv/galaxy-pxe/boot.ipxe
ssh -i /etc/galaxy-pxe/cluster-join-key \
  -o BatchMode=yes \
  -o StrictHostKeyChecking=yes \
  root@192.168.70.10 \
  'hostname; pvecm status | grep -E "^(Name|Nodes|Quorate):"'
```

## Service and Cluster Result

```text
2026-07-31T05:58:34+00:00
ansible-01
enabled
enabled
active
active
ok
kernel vmlinuz ramdisk_size=16777216 rw quiet initrd=initrd.img splash=silent proxmox-start-auto-installer nomodeset
grey-server
Name:             Galaxy
Nodes:            4
Quorate:          Yes
```

The command exited `0`.

## Machine State Commands

```bash
python3 /usr/local/lib/galaxy-pxe/state.py \
  --machines /etc/galaxy-pxe/machines.json \
  --state-file /var/lib/galaxy-pxe/state.json \
  --json \
  <GREEN_NODE_MAC>

python3 /usr/local/lib/galaxy-pxe/state.py \
  --machines /etc/galaxy-pxe/machines.json \
  --state-file /var/lib/galaxy-pxe/state.json \
  --json \
  02:00:00:00:09:99
```

## Machine State Results

Green returned:

```json
{
  "attempt_id": null,
  "detail": {},
  "history": [
    {
      "at": "2026-07-31T05:15:01+00:00",
      "phase": "disabled"
    }
  ],
  "phase": "disabled",
  "started_at": null,
  "updated_at": "2026-07-31T05:15:01+00:00"
}
```

The acceptance identity returned:

```json
{
  "attempt_id": null,
  "detail": {},
  "history": [
    {
      "at": "2026-07-31T05:51:48+00:00",
      "phase": "disabled"
    }
  ],
  "phase": "disabled",
  "started_at": null,
  "updated_at": "2026-07-31T05:51:48+00:00"
}
```

Both commands exited `0`.

## Cluster Link Readback

I read `pvecm nodes` and `corosync-cfgtool -s` on Grey:

```text
Membership information
----------------------
    Nodeid      Votes Name
         1          1 grey-server (local)
         2          1 purple-server
         3          1 blue-server
         4          1 red-server

LINK ID 0 udp
    addr = 192.168.70.10
    nodeid: 1: localhost
    nodeid: 2: connected
    nodeid: 3: connected
    nodeid: 4: connected

LINK ID 1 udp
    addr = 192.168.71.10
    nodeid: 1: localhost
    nodeid: 2: connected
    nodeid: 3: connected
    nodeid: 4: connected
```

The command exited `0`. Galaxy had four members before the Green install, and all three remote peers were connected on each current Corosync link.

## UniFi Callback Policy Readback

I issued this UniFi operation:

```json
{
  "operation": "unifi_get_firewall_policy_details",
  "arguments": {
    "policy_id": "6a6c36cc85e3cf84d3d71363"
  }
}
```

The complete structured result was:

```json
{
  "success": true,
  "policy_id": "6a6c36cc85e3cf84d3d71363",
  "details": {
    "_id": "6a6c36cc85e3cf84d3d71363",
    "action": "ALLOW",
    "connection_state_type": "ALL",
    "connection_states": [],
    "create_allow_respond": true,
    "description": "Allow green-server first-boot state and join-key callbacks to Galaxy PXE.",
    "destination": {
      "ips": [
        "192.168.40.36"
      ],
      "match_opposite_ips": false,
      "match_opposite_ports": false,
      "matching_target": "IP",
      "matching_target_type": "SPECIFIC",
      "port": "8080",
      "port_matching_type": "SPECIFIC",
      "zone_id": "68b788c0e9f08f1e1b2a2288"
    },
    "enabled": true,
    "icmp_typename": "ANY",
    "icmp_v6_typename": "ANY",
    "index": 10000,
    "ip_version": "IPV4",
    "logging": true,
    "match_ip_sec": false,
    "match_opposite_protocol": false,
    "name": "Allow Galaxy PXE callbacks to ansible-01",
    "predefined": false,
    "protocol": "tcp",
    "schedule": {
      "mode": "ALWAYS"
    },
    "source": {
      "ips": [
        "192.168.70.14"
      ],
      "match_mac": false,
      "match_opposite_ips": false,
      "match_opposite_ports": false,
      "matching_target": "IP",
      "matching_target_type": "SPECIFIC",
      "port_matching_type": "ANY",
      "zone_id": "699cfa5fc9d00a2842cceb51"
    }
  }
}
```

The policy readback matched the confirmed change. It permits Green's post-cutover callbacks without opening TCP 8080 to another source or destination.

## Switch Port and Profile Readback

I issued:

```json
[
  {
    "operation": "unifi_get_switch_ports",
    "arguments": {
      "device_mac": "<BANE_SWITCH_MAC>"
    }
  },
  {
    "operation": "unifi_get_port_stats",
    "arguments": {
      "device_mac": "<BANE_SWITCH_MAC>"
    }
  },
  {
    "operation": "unifi_get_port_profile_details",
    "arguments": {
      "profile_id": "6a6be74e052792cd21414aff"
    }
  },
  {
    "operation": "unifi_get_port_profile_details",
    "arguments": {
      "profile_id": "698cc29d10cb5676c296c7c1"
    }
  }
]
```

All four structured results returned `"success": true`. These are the exact result fields used for the verification:

```json
{
  "switch": {
    "name": "Bane Switch POE",
    "port_override": {
      "port_idx": 4,
      "setting_preference": "manual",
      "poe_mode": "off",
      "name": "Port 4",
      "portconf_id": "6a6be74e052792cd21414aff"
    },
    "port_stats": {
      "port_idx": 4,
      "last_connection": {
        "connected": true,
        "mac": "<GREEN_NODE_MAC>",
        "ip": "192.168.5.18"
      },
      "enable": true,
      "full_duplex": true,
      "speed": 1000,
      "up": true,
      "rx_dropped": 0,
      "rx_errors": 0,
      "tx_dropped": 0,
      "tx_errors": 0,
      "portconf_id": "6a6be74e052792cd21414aff"
    }
  },
  "server_provision": {
    "_id": "6a6be74e052792cd21414aff",
    "name": "Server-Provision",
    "forward": "customize",
    "tagged_vlan_mgmt": "custom",
    "native_networkconf_id": "6a6be56f052792cd21414a99",
    "excluded_networkconf_ids": [
      "68b7cc68620e3d7fdfd2f341",
      "68b78866e9f08f1e1b2a227b",
      "68b78940e9f08f1e1b2a232b",
      "68b789dbe9f08f1e1b2a2341",
      "68b78a68e9f08f1e1b2a2350"
    ]
  },
  "proxmox_trunk": {
    "_id": "698cc29d10cb5676c296c7c1",
    "name": "Proxmox-Trunk",
    "forward": "customize",
    "tagged_vlan_mgmt": "custom",
    "native_networkconf_id": "",
    "excluded_networkconf_ids": [
      "68b7cc68620e3d7fdfd2f341",
      "68b78866e9f08f1e1b2a227b",
      "68b78940e9f08f1e1b2a232b",
      "68b789dbe9f08f1e1b2a2341",
      "68b78a68e9f08f1e1b2a2350"
    ]
  }
}
```

UniFi reported Bane switch port 4 enabled, linked at 1 Gbps full duplex, and assigned to `Server-Provision`. The live MAC table identified Green as `<GREEN_NODE_MAC>` with its current VLAN 5 lease at `192.168.5.18`. Receive and transmit error and drop counters were zero.

`Server-Provision` had native VLAN 5 and a custom tagged set that excluded only Management, IoT, Trusted, DMZ, and Secure. MGMT-A and Cluster-Net were not excluded, so the installed node can create its two tagged interfaces while the port keeps the provisioning profile.

`Proxmox-Trunk` had no native network and the same five exclusions. VLAN 5 was not excluded. This matches the disposable acceptance path and leaves the final profile ready for the post-join change.

## Disposable VM Cleanup Readback

I checked Red after the successful acceptance run:

```text
2026-07-31T01:58:35-04:00
VM999_ABSENT
VM999_LVS_ABSENT
```

The command exited `0`. VM 999 and logical volumes whose names begin with `vm-999-disk` were absent.

## Idempotency Command

```bash
sudo ansible-playbook playbooks/deploy.yml
```

## Idempotency Result

```text
PLAY RECAP
ansible-01 : ok=30 changed=0 unreachable=0 failed=0 skipped=1 rescued=0 ignored=0
```

The command exited `0`. The live deployment matched the repaired source without changing state.
