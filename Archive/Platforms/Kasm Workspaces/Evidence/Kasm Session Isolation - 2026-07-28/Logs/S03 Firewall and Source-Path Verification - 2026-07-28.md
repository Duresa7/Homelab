# S03 Firewall and Source-Path Verification

**Created:** 2026-07-28  
**Last updated:** 2026-07-29

**Capture window:** 2026-07-28T15:14:47-04:00 through 2026-07-28T15:26:08-04:00  
**Targets:** UniFi firewall and `https://192.168.78.10/`  
**Mechanism:** UniFi Network MCP and SSH Manager MCP  
**Shell:** Remote `/bin/bash`  
**Working directory:** Each server's configured SSH Manager default, captured in standard output

## Controller State

I read the final policy details and order from UniFi. The complete structured controller requests and results are retained in [S01 UniFi Final State Verification](S01%20UniFi%20Final%20State%20Verification%20-%202026-07-28.md).

The final controller state has 99 user policies, including the 38 policies added for this change, and no policy whose name starts with `TEST `. The narrow Internal and VPN allows use index 10000. Their catchall blocks use index 10001. The reverse MALWARE-OFFLINE to KASM-BROWSER block matches only `NEW` and `INVALID`, so reply traffic for a connection initiated from KASM-BROWSER remains valid.

## Source-Path Command

I issued this read-only command through SSH Manager on six configured hosts:

```bash
printf 'timestamp='
date -Is
printf 'shell=%s\n' "$SHELL"
printf 'cwd='
pwd
printf 'source_ip='
hostname -I | awk '{print $1}'
curl -k -sS -o /dev/null --connect-timeout 5 --max-time 8 \
  -w 'http_code=%{http_code} remote_ip=%{remote_ip} curl_exit=%{exitcode}\n' \
  https://192.168.78.10/
probe_rc=$?
printf 'recorded_curl_exit=%s\n' "$probe_rc"
exit 0
```

## Complete Standard Output

```text
docker_main | Personal-A VLAN 40
timestamp=2026-07-28T19:14:47+00:00
shell=/bin/bash
cwd=/root
source_ip=192.168.40.35
http_code=200 remote_ip=192.168.78.10 curl_exit=0
recorded_curl_exit=0

purple_server | Management VLAN 70
timestamp=2026-07-28T15:14:47-04:00
shell=/bin/bash
cwd=/root
source_ip=192.168.70.11
http_code=000 remote_ip= curl_exit=28
recorded_curl_exit=28

app_01 | Server VLAN 80
timestamp=2026-07-28T15:14:52-04:00
shell=/bin/bash
cwd=/home/dkadi
source_ip=192.168.80.10
http_code=000 remote_ip= curl_exit=28
recorded_curl_exit=28

monitor_01 | Observability VLAN 73
timestamp=2026-07-28T15:14:57-04:00
shell=/bin/bash
cwd=/home/dkadi
source_ip=192.168.73.2
http_code=000 remote_ip= curl_exit=28
recorded_curl_exit=28

security_01 | Security VLAN 72
timestamp=2026-07-28T19:15:02+00:00
shell=/bin/bash
cwd=/home/dkadi
source_ip=192.168.72.2
http_code=000 remote_ip= curl_exit=28
recorded_curl_exit=28

docker_network | Access VLAN 85
timestamp=2026-07-28T15:16:26-04:00
shell=/bin/bash
cwd=/home/dkadi
source_ip=192.168.85.2
http_code=000 remote_ip= curl_exit=28
recorded_curl_exit=28
```

## Complete Standard Error

```text
docker_main | Personal-A VLAN 40
<empty>

purple_server | Management VLAN 70
curl: (28) Connection timed out after 5002 milliseconds

app_01 | Server VLAN 80
curl: (28) Connection timed out after 5002 milliseconds

monitor_01 | Observability VLAN 73
curl: (28) Connection timed out after 5002 milliseconds

security_01 | Security VLAN 72
curl: (28) Failed to connect to 192.168.78.10 port 443 after 5002 ms: Timeout was reached

docker_network | Access VLAN 85
curl: (28) Connection timed out after 5002 milliseconds
```

**SSH Manager exit code for each call:** 0  
**Structured result for each call:** `success: true`

The command records curl's exit code before returning wrapper exit code 0. Curl's `curl_exit` and `recorded_curl_exit` fields carry each probe result.

Personal-A is one of the two named Internal networks allowed by policy, and it returned HTTP 200. Management, Server, Observability, Security, and Access sources timed out.

## Trusted Temporary-Interface Check

I temporarily admitted Trusted VLAN 10 through this authenticated UniFi Network 10.4.57 path:

```text
Settings
  -> Overview
  -> Port Profiles
  -> Proxmox-Trunk
  -> Tagged VLAN Management: Custom
  -> Edit
  -> select Trusted (10)
  -> Save
  -> Apply Changes
```

I used the same path to clear Trusted immediately after the probe. The browser action transcript and controller mutation payloads and results were not retained. I retained the exact path, the full probe transcript, the complete final controller readback, and a separate interface-residue check.

I then issued this command through SSH Manager on `purple-server`:

```bash
set -u
cleanup(){ ip link del nic0.10 >/dev/null 2>&1 || true; }
trap cleanup EXIT
cleanup
printf 'timestamp='; date -Is
printf 'shell=%s\n' "$SHELL"
printf 'cwd='; pwd
ip link add link nic0 name nic0.10 type vlan id 10
ip addr add 192.168.10.250/24 dev nic0.10
ip link set nic0.10 up
ip route add 192.168.78.0/24 via 192.168.10.1 dev nic0.10
sleep 2
printf 'interface='; ip -brief addr show nic0.10
printf 'route='; ip route get 192.168.78.10 from 192.168.10.250
curl -k -sS -o /dev/null --interface 192.168.10.250 \
  --connect-timeout 5 --max-time 8 \
  -w 'http_code=%{http_code} remote_ip=%{remote_ip} curl_exit=%{exitcode}\n' \
  https://192.168.78.10/
probe_rc=$?
printf 'recorded_curl_exit=%s\n' "$probe_rc"
cleanup
trap - EXIT
printf 'residue='
ip link show nic0.10 >/dev/null 2>&1
residue_rc=$?
if [ "$residue_rc" -eq 1 ]; then echo none; else echo present; fi
exit 0
```

### Complete Standard Output

```text
timestamp=2026-07-28T15:25:30-04:00
shell=/bin/bash
cwd=/root
interface=nic0.10@nic0     UP             192.168.10.250/24 fe80::ea6a:64ff:fee3:c9df/64
route=192.168.78.10 from 192.168.10.250 via 192.168.10.1 dev nic0.10 uid 0
    cache
http_code=200 remote_ip=192.168.78.10 curl_exit=0
recorded_curl_exit=0
residue=none
```

### Complete Standard Error

```text
<empty>
```

**SSH Manager exit code:** 0  
**Structured result:** `success: true`

The Trusted path returned HTTP 200. The command removed `nic0.10` before returning.

## Final Restoration Check

I removed Trusted from the tagged VLAN selection immediately after the probe. I read the final profile through UniFi Network MCP with:

```text
unifi_get_port_profile_details({"profile_id":"698cc29d10cb5676c296c7c1"})
```

The complete structured result was:

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
      "68b78940e9f08f1e1b2a232b",
      "68b789dbe9f08f1e1b2a2341",
      "68b78a68e9f08f1e1b2a2350"
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

The five excluded IDs map to Management, IoT, Trusted, DMZ, and Secure. The result contained no error field because `success` was true.

I issued this final residue command through SSH Manager on `purple-server`:

```bash
printf 'timestamp='; date -Is
printf 'nic0.10='
if ip link show nic0.10 >/dev/null 2>&1; then echo present; else echo absent; fi
```

Its complete standard output was:

```text
timestamp=2026-07-28T15:26:08-04:00
nic0.10=absent
```

Standard error was empty, the SSH Manager exit code was 0, and the structured result reported `success: true`.

The configured Management Access VPN allow precedes its catchall block. I could not run its client-path check because no remote Management Access VPN client was connected.
