# S02 VLAN 75 Guest and Docker State

**Created:** 2026-07-28  
**Last updated:** 2026-07-29

**Capture time:** 2026-07-28 EDT  
**Target:** `purple-server`, VM 122 `kasm-01`  
**Mechanism:** SSH Manager MCP with QEMU guest-agent commands

## Action

I added VM 122 `net4` as a VirtIO interface on `vmbr0`, tagged VLAN 75, with Proxmox firewall filtering disabled. The controller assigned MAC `<REDACTED_KASM_LANE_75_MAC>`, and Ubuntu named the interface `enp6s22`.

I added an addressless, optional netplan stanza for `enp6s22`, extended `kasm-lab-shims.service` with `shim75` at `192.168.75.201/32`, and created Docker macvlan network `lab75`:

```text
parent: enp6s22
subnet: 192.168.75.0/24
gateway: 192.168.75.1
ip-range: 192.168.75.208/28
shim route: 192.168.75.208/28 via shim75
```

The plan did not include the netplan stanza. Without it, the addressless parent did not remain up after network configuration. I added the stanza because Docker macvlan requires an active parent.

## Verification

The final VM configuration returned `net4` with VLAN 75 and the recorded MAC. `ip -br link` showed `enp6s22` up with no host address. `ip -br addr show shim75` returned `192.168.75.201/32`, and the route table sent `192.168.75.208/28` through `shim75`.

`docker network inspect lab75` returned the subnet, gateway, range, and parent above. The existing `lab74`, `lab77`, and `lab79` networks and shims stayed unchanged.
