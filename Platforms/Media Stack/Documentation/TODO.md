# Media Stack TODO

**Created:** 2026-07-17  
**Last updated:** 2026-07-21

## Acquisition Test

Completed items are recorded with evidence in the [application onboarding change record](Change%20Records/Media%20Stack%20Application%20Onboarding%20-%202026-07-17.md).

- [x] 2026-07-17: Completed Jellyfin's guided setup and added the Movies and TV Shows libraries.
- [x] 2026-07-17: Applied the Intel Quick Sync transcoding selections per my media settings research; I verify the tone-mapping fields below the captured viewport during the end-to-end test.
- [x] 2026-07-17: Confirmed the migrated Seerr connections to Jellyfin, Sonarr, and Radarr through the completed setup wizard.
- [x] 2026-07-17: Added the first indexer to Prowlarr with the Standard sync profile.
- [x] 2026-07-17: Left the `flaresolverr` tag intentionally unapplied: the configured indexer needs no challenge handling; I apply it only when a compatible indexer does.
- [x] 2026-07-21: Ran the bounded end-to-end acquisition test in full. I requested a television episode and a movie, watched both acquire through the Prowlarr and VPN-isolated qBittorrent path, compared qBittorrent's Content list against the payload filter during transfer, confirmed the Sonarr and Radarr hard-link imports, and confirmed GPU-active playback in Jellyfin. The one retained capture is the Jellyfin Movies library (`Evidence/Media Stack End-to-End Acquisition Test - 2026-07-21/`), kept local because it shows an acquired title.
- [x] 2026-07-21: Kept the onboarding Sonarr naming (`Season {season}` folders, no `{Release Group}` token). The episode imported and hard-linked correctly under that scheme during the test, so I declined the [media settings research](Media%20Settings%20Research%20-%202026-07-17.md) refinement.

## Backups, Capacity & Updates

- [ ] Add backups for `/opt/media-stack/config` and `/data`; perform a restore test.
- [ ] Add capacity alerts before the 100 GiB local volume becomes constrained.
- [ ] Define a maintenance cadence for the intentionally floating `latest` image tags.
- [ ] Decide whether LAN management interfaces should move behind authenticated HTTPS ingress.
