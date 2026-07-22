# Arr Indexer Health Findings

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Investigated:** 2026-07-17

## Symptom

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

## Finding

I had not added any indexers to Prowlarr yet. The Prowlarr-to-Arr application links and the qBittorrent download clients were present, so the messages accurately described my incomplete onboarding rather than a failed integration.

## Isolated Cause

My hypothesis was that no indexers existed rather than a Prowlarr-to-Arr or download-client failure. Prowlarr's application links were present, both Arr root paths existed, and the Sonarr and Radarr qBittorrent client-test APIs passed after I applied the final Web UI credential. That isolates the findings to the intentionally empty indexer inventory.

I did not add an artificial indexer during infrastructure validation. The issue remains open and is tracked in the platform TODO: add the intended indexers, use the `flaresolverr` tag only where needed, sync them to Sonarr/Radarr, and confirm both health pages clear before running an end-to-end test.
