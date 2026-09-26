# S10 Green Node Enrollment and Final Fleet Verification

**Created:** 2026-08-03  
**Last updated:** 2026-08-03

**Captured:** 2026-08-03 13:54 through 14:16 EDT  
**Targets:** `green-server`, UniFi site `default`, `ansible-01`, Wazuh dashboard  
**Mechanism:** SSH Manager MCP, UniFi Network MCP, Ansible Core 2.21.2, & in-app browser

## Scope extension

I added Green after the original four-node deployment was complete. The existing Galaxy Wazuh policy ID `6a70d24fe0ee2d5b4b154510` already allowed Grey, Purple, Blue, & Red to `192.168.72.2` through the `Wazuh Ports` object.

The UniFi update preview changed only the policy source list:

```text
before: 192.168.70.10, .11, .12, .13
after:  192.168.70.10, .11, .12, .13, .14
```

The applied readback kept `ALLOW`, IPv4 TCP, index 10000, logging enabled, response policy enabled, destination `192.168.72.2`, and the existing port-group object. Direct tests from `green-server` returned TCP 1514 open and TCP 1515 open.

## SSH and deployment

I added `green_server` as `root@192.168.70.14` to both the TOML manager and the `.env` manager. The TOML manager reloaded the record, and the first SSH command returned hostname `green-server`.

I added `green-server` to the versioned Ansible inventory with groups `default,proxmox`, deployed the inventory to `/home/ansible/wazuh-agent-deployment`, and passed the syntax check. The bounded first run completed:

```text
green-server  ok=22  changed=9  unreachable=0  failed=0  skipped=0
```

The post-change endpoint check returned package `4.14.6-1`, enabled, active, held, and an established session from `192.168.70.14` to `192.168.72.2:1514`. The second bounded run completed:

```text
green-server  ok=15  changed=0  unreachable=0  failed=0  skipped=7
```

## Dashboard verification

The signed-in Wazuh dashboard showed 14 active agents, zero disconnected, zero pending, and zero never connected. ID `017` named `green-server` at `192.168.70.14` reported active on version 4.14.6 in `default` and `proxmox`.

Filtering on `proxmox (5)` returned Grey, Purple, Blue, Red, & Green. All five rows were active on version 4.14.6 and belonged to both `default` and `proxmox`. The page-rendered screenshots contain no mouse cursor.
