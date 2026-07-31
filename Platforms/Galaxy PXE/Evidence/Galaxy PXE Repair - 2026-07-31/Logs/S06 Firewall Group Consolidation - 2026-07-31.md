# S06 Firewall Group Consolidation

**Created:** 2026-07-31  
**Last updated:** 2026-07-31

**Capture date:** 2026-07-31  
**Targets:** Ahsoka Gateway, `OBJ-Proxmox-Nodes`, `ansible-01`, Grey, and Green  
**Mechanisms:** UniFi Network controller readback and SSH Manager

## Starting State

Policy `6a6c36cc85e3cf84d3d71363` allowed only Green at `192.168.70.14` to reach `192.168.40.36:8080` after the port changed to `Proxmox-Trunk`. Existing address group `OBJ-Proxmox-Nodes`, ID `6a67a1eb052792cd214090f1`, already held the five Galaxy management addresses from `192.168.70.10` through `192.168.70.14`.

The separate pre-cutover policy used the `Server-Provision` network object. I found no need for a second node address group or a duplicate callback policy.

## Preview and Change

I previewed an update to the existing post-cutover policy. The preview showed one selector change:

```text
Current source: 192.168.70.14, matching target SPECIFIC
Proposed source: OBJ-Proxmox-Nodes, matching target OBJECT
Destination: unchanged at 192.168.40.36 TCP 8080
```

After applying that preview, I renamed the policy `Allow Proxmox Nodes to Galaxy PXE`. I did not delete a rule or group because the two callback policies cover different network phases and the existing address group was reusable.

## Readback

UniFi returned the policy enabled with:

```text
Policy ID: 6a6c36cc85e3cf84d3d71363
Source zone: <YOUR_ORG_NAME>-Mgmt
Source matching target: IP object
Source group ID: 6a67a1eb052792cd214090f1
Source group: OBJ-Proxmox-Nodes
Destination: 192.168.40.36
Protocol and port: IPv4 TCP 8080
Schedule: Always
Logging: enabled
```

The group readback returned the five expected management addresses. Grey and Green each requested `http://192.168.40.36:8080/health` and received `ok`. Both remote commands exited `0`.

I also checked all 13 reusable UniFi firewall groups against all 121 user-defined policies. Every group had at least one policy reference, and no two groups had the same type and member set. I removed none because the readback found no unreferenced or duplicate group.

Future Galaxy nodes need their management address added to `OBJ-Proxmox-Nodes`. They do not need another post-cutover callback policy.

## Second Pass: The Destination Was Still a Literal

The first pass grouped the source and left the destination alone. Both callback policies still carried the same hardcoded `192.168.40.36` with `port_matching_type: SPECIFIC` on port `8080`. That is the same duplication the source-side group removed, just on the other side of the rule: two policies naming one service, so moving the PXE service means editing both.

I created two groups and repointed both policies at them:

```text
OBJ-Galaxy-PXE-Service   address-group  192.168.40.36  id 6a6cbf5285e3cf84d3d82810
PG-Galaxy-PXE-Callback   port-group     8080           id 6a6cbf5585e3cf84d3d82813
```

The preview on policy `6a6c36cc85e3cf84d3d71363` showed only the destination changing:

```text
current:  matching_target_type SPECIFIC, ips [192.168.40.36], port_matching_type SPECIFIC, port 8080
proposed: matching_target_type OBJECT,   ip_group_id 6a6cbf52...,  port_matching_type OBJECT,   port_group_id 6a6cbf55...
```

Both policies returned `updated_fields: ["destination"]`. `unifi_update_firewall_policy` accepts only `[confirm, policy_id, update_data]` and silently drops a `description` passed inside `update_data`, so policy `6a6c36cc85e3cf84d3d71363` still carries its original Green-specific description text even though its selectors are now group-based. That is cosmetic and has to be edited in the controller UI.

### Five-Node Readback

```sh
curl -s -m 8 -w " http=%{http_code}\n" http://192.168.40.36:8080/health
```

```text
grey-server    health=ok http=200
purple-server  health=ok http=200
blue-server    health=ok http=200
red-server     health=ok http=200
green-server   health=ok http=200
```

Every node still reaches the service through the fully object-based policy. Both sides of both rules are now object references, so adding a node means editing `OBJ-Proxmox-Nodes`, and moving the service means editing `OBJ-Galaxy-PXE-Service`. Neither needs a policy change.

Group count went from 13 to 15. I deleted nothing, because the earlier audit already proved every existing group is referenced and no two share a type and member set.
