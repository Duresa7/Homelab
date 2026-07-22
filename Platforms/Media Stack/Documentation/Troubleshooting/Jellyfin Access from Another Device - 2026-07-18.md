# Jellyfin Access from Another Device

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Investigated:** 2026-07-18

## Symptom

Someone in the house reported that another device could not add or connect to the Jellyfin server. I had no client-side error text or source-device identity during the initial diagnosis.

## Tests

I ran read-only service checks on `media-01` and confirmed CT 842 was running, the Jellyfin container was `running` and `healthy`, TCP port `8096` was listening on IPv4 and IPv6 wildcard addresses, and `http://127.0.0.1:8096/System/Info/Public` returned Jellyfin 10.11.11 with `LocalAddress` set to `http://192.168.40.42:8096`. Jellyfin's active network configuration had `EnableRemoteAccess` set to `true` and no base URL.

A TCP connection test I ran from `Jedi PC` (`192.168.50.241`, Secure VLAN 50) to `192.168.40.42:8096` succeeded. UniFi reported `media-01` online on Personal-A VLAN 40 and showed no blocked flows to `192.168.40.42` during the preceding seven days.

Inspecting the firewall, I found the enabled `Block Trusted to Personal-A` policy. The higher-priority `Allow Devices to Personal-A` policy permits only a defined client list, and the separate `Allow Device --> media-01` policy explicitly permits the two known Fire TV clients. A different device on the Trusted network that is absent from the allowlist is therefore expected to be blocked. Automatic Jellyfin discovery may also fail across VLAN boundaries even when TCP access is allowed because discovery depends on local broadcast behavior.

## Current Finding

The Jellyfin service and host listener are healthy; my leading hypothesis is source-device firewall eligibility or cross-VLAN discovery rather than a Jellyfin outage. I have not changed any network or application configuration. Next I will identify the failing device by UniFi client name, IP address, or MAC address, confirm its source network and policy match, and test the manually entered server URL `http://192.168.40.42:8096`. If the device should have access, I will preview a narrowly scoped allow policy or allowlist addition before making any UniFi change.
