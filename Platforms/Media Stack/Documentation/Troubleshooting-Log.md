# Media Stack Troubleshooting Log

**Created:** 2026-07-17  
**Last updated:** 2026-07-20

## 2026-07-18: Jellyfin Access from Another Device

### Symptom

Someone in the house reported that another device could not add or connect to the Jellyfin server. I had no client-side error text or source-device identity during the initial diagnosis.

### Tests

I ran read-only service checks on `media-01` and confirmed CT 842 was running, the Jellyfin container was `running` and `healthy`, TCP port `8096` was listening on IPv4 and IPv6 wildcard addresses, and `http://127.0.0.1:8096/System/Info/Public` returned Jellyfin 10.11.11 with `LocalAddress` set to `http://192.168.40.42:8096`. Jellyfin's active network configuration had `EnableRemoteAccess` set to `true` and no base URL.

A TCP connection test I ran from `Jedi PC` (`192.168.50.241`, Secure VLAN 50) to `192.168.40.42:8096` succeeded. UniFi reported `media-01` online on Personal-A VLAN 40 and showed no blocked flows to `192.168.40.42` during the preceding seven days.

Inspecting the firewall, I found the enabled `Block Trusted to Personal-A` policy. The higher-priority `Allow Devices to Personal-A` policy permits only a defined client list, and the separate `Allow Device --> media-01` policy explicitly permits the two known Fire TV clients. A different device on the Trusted network that is absent from the allowlist is therefore expected to be blocked. Automatic Jellyfin discovery may also fail across VLAN boundaries even when TCP access is allowed because discovery depends on local broadcast behavior.

### Current Finding

The Jellyfin service and host listener are healthy; my leading hypothesis is source-device firewall eligibility or cross-VLAN discovery rather than a Jellyfin outage. I have not changed any network or application configuration. Next I will identify the failing device by UniFi client name, IP address, or MAC address, confirm its source network and policy match, and test the manually entered server URL `http://192.168.40.42:8096`. If the device should have access, I will preview a narrowly scoped allow policy or allowlist addition before making any UniFi change.

## 2026-07-17: Arr Indexer Health Findings

### Symptom

Sonarr reported:

```text
type=warning source=IndexerSearchCheck message=No indexers available with Automatic Search enabled, Sonarr will not provide any automatic search results
type=error source=IndexerRssCheck message=No indexers available with RSS sync enabled, Sonarr will not grab new releases automatically
```

Radarr reported:

```text
type=error source=IndexerRssCheck message=No indexers available with RSS sync enabled, Radarr will not grab new releases automatically
type=warning source=IndexerSearchCheck message=No indexers available with Automatic Search enabled, Radarr will not provide any automatic search results
```

### Finding

I had not added any indexers to Prowlarr yet. The Prowlarr-to-Arr application links and the qBittorrent download clients were present, so the messages accurately described my incomplete onboarding rather than a failed integration.

### Isolated Cause

My hypothesis was that no indexers existed rather than a Prowlarr-to-Arr or download-client failure. Prowlarr's application links were present, both Arr root paths existed, and the Sonarr and Radarr qBittorrent client-test APIs passed after I applied the final Web UI credential. That isolates the findings to the intentionally empty indexer inventory.

I did not add an artificial indexer during infrastructure validation. The issue remains open and is tracked in the platform TODO: add the intended indexers, use the `flaresolverr` tag only where needed, sync them to Sonarr/Radarr, and confirm both health pages clear before running an end-to-end test.

## 2026-07-17: Verification Formatter Quoting Error

### Symptom

Two read-only Python formatters I invoked through nested SSH, `pct exec`, and shell quoting failed:

```text
NameError: name 'ip' is not defined. Did you mean: 'id'?
NameError: name 'source' is not defined
```

### Root Cause

Single-quoted Python dictionary keys were consumed by the enclosing shell quoting layer.

### Correction and Verification

My failed attempts used single-quoted dictionary keys inside an outer single-quoted shell command. I verified the hypothesis by observing that the enclosing shell removed those quotes before Python parsed the script. I rewrote the formatter to assign dictionary values to variables using double-quoted keys before interpolation.

The corrected VPN check returned a provider exit, matching provider-assigned and qBittorrent listening ports, `random_port=False`, `upnp=False`, and qBittorrent's Gluetun container network mode. The corrected Arr health formatter returned the exact messages recorded above. Both corrected commands exited `0`. No container or configuration mutation occurred during the failed formatting attempts.

## 2026-07-17: qBittorrent API Read During Recreation

### Symptom

My first post-recreation verification reached qBittorrent immediately after Docker reported the container running and failed with:

```text
ConnectionResetError: [Errno 104] Connection reset by peer
```

### Readiness Check

I suspected an application-readiness race: the container process was running, but the Web UI socket had not completed initialization. Gluetun was already healthy and Docker had started qBittorrent successfully. No active torrents existed before the controlled restart.

### Corrective Action and Verification

I repeated the read-only verification with an HTTP-ready loop before parsing preferences. It then confirmed provider/qBittorrent port equality, `random_port=False`, `upnp=False`, local-auth bypass, enabled Docker-subnet bypass, Gluetun healthy, qBittorrent running, and qBittorrent attached to Gluetun's exact container namespace. The corrected command exited `0`. No service configuration change was required.
