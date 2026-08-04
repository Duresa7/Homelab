# Secure-V Removal

**Created:** 2026-07-27  
**Last updated:** 2026-07-27

I removed the remaining `Secure-V` objects in dependency order.

The baseline held 26 networks, three traffic routes, four WLANs, and six exclusions in `Proxmox-Trunk`. The enabled `Non-tracking` route used the ProtonVPN interface with its kill switch enabled and targeted only network ID `6a5c5b620e10fae12278c51d`.

The UniFi API exposed traffic-route reads and updates but no delete operation. I removed `Non-tracking` through the signed-in Policy Engine UI, then confirmed its controller ID was absent and the route count was two.

I checked for live clients in `192.168.4.0/24` before deleting the network. The controller returned zero online clients. I then removed `Secure-V` through the Networks UI and confirmed:

- the network count fell from 26 to 25;
- network ID `6a5c5b620e10fae12278c51d` was absent;
- no WLAN referenced the retired network;
- traffic routes stayed at two;
- `Proxmox-Trunk` dropped the retired network automatically, leaving five exclusions.

The disabled `Alpha-Sec-IoT` WLAN was bound to untagged `Management`. I kept the SSID disabled and repointed it to the existing `IoT` network on VLAN 20. The final WLAN readback retained every other field and returned network ID `68b78866e9f08f1e1b2a227b`.

Custom firewall policies stayed at 59, zones at 14, and firewall groups at 13 throughout S07.

## Evidence boundary

I retained the dependency-order snapshots and final readback. I didn't retain screenshots or a raw interaction transcript for the UI-only route and network deletions or the disabled WLAN rebind.
