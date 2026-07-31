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
Source zone: AlphaSec-Mgmt
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
