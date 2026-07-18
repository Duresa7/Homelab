# Media Stack Troubleshooting Log

**Created:** 2026-07-17  
**Last updated:** 2026-07-17

## 2026-07-17 — Arr Indexer Health Findings

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

No indexers had been added to Prowlarr. Prowlarr-to-Arr application links and the qBittorrent download clients were present, so the messages accurately described incomplete onboarding rather than a failed integration.

### Hypothesis, Test, and Current Verification

The hypothesis was that no indexers existed rather than Prowlarr-to-Arr or download-client failure. Prowlarr's application links were present, both Arr root paths existed, and the Sonarr and Radarr qBittorrent client-test APIs passed after the final Web UI credential was applied. This isolates the findings to the intentionally empty indexer inventory.

No artificial indexer was added during infrastructure validation. The issue remains open and is tracked in the platform TODO. Add intended indexers, use the `flaresolverr` tag only where needed, sync them to Sonarr/Radarr, and confirm both health pages clear before running an end-to-end test.

## 2026-07-17 — Verification Formatter Quoting Error

### Symptom

Two read-only Python formatters invoked through nested SSH, `pct exec`, and shell quoting failed:

```text
NameError: name 'ip' is not defined. Did you mean: 'id'?
NameError: name 'source' is not defined
```

### Root Cause

Single-quoted Python dictionary keys were consumed by the enclosing shell quoting layer.

### Failed Attempt, Hypothesis, Corrective Action, and Verification

The failed attempts used single-quoted dictionary keys inside an outer single-quoted shell command. The hypothesis was verified by observing that the enclosing shell removed those quotes before Python parsed the script. The formatter was rewritten to assign dictionary values to variables using double-quoted keys before interpolation.

The corrected VPN check returned a provider exit, matching provider-assigned and qBittorrent listening ports, `random_port=False`, `upnp=False`, and qBittorrent's Gluetun container network mode. The corrected Arr health formatter returned the exact messages recorded above. Both corrected commands exited `0`. No container or configuration mutation occurred during the failed formatting attempts.

## 2026-07-17 — qBittorrent API Read During Recreation

### Symptom

The first post-recreation verification reached qBittorrent immediately after Docker reported the container running and failed with:

```text
ConnectionResetError: [Errno 104] Connection reset by peer
```

### Hypothesis and Test

The hypothesis was an application-readiness race: the container process was running, but the Web UI socket had not completed initialization. Gluetun was already healthy and Docker had started qBittorrent successfully. No active torrents existed before the controlled restart.

### Corrective Action and Verification

The read-only verification was repeated with an HTTP-ready loop before parsing preferences. It then confirmed provider/qBittorrent port equality, `random_port=False`, `upnp=False`, local-auth bypass, enabled Docker-subnet bypass, Gluetun healthy, qBittorrent running, and qBittorrent attached to Gluetun's exact container namespace. The corrected command exited `0`. No service configuration change was required.
