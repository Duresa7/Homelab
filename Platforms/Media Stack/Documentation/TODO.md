# Media Stack TODO

**Created:** 2026-07-17  
**Last updated:** 2026-07-18

## Onboarding

Completed items are recorded with evidence in the [application onboarding change record](Change%20Records/Media%20Stack%20Application%20Onboarding%20-%202026-07-17.md).

- [x] 2026-07-17: Completed Jellyfin's guided setup and added the Movies and TV Shows libraries.
- [x] 2026-07-17: Applied the Intel Quick Sync transcoding selections per my media settings research; I verify the tone-mapping fields below the captured viewport during the end-to-end test.
- [x] 2026-07-17: Confirmed the migrated Seerr connections to Jellyfin, Sonarr, and Radarr through the completed setup wizard.
- [x] 2026-07-17: Added the first indexer to Prowlarr with the Standard sync profile.
- [x] 2026-07-17: Left the `flaresolverr` tag intentionally unapplied: the configured indexer needs no challenge handling; I apply it only when a compatible indexer does.
- [ ] Run one bounded television and movie test through request, search, qBittorrent, import, and Jellyfin visibility; during this test also verify Sonarr hard-link import, decide the season-folder and release-group naming refinements from the settings research, and confirm GPU-active playback.

## Operations

- [ ] Add backups for `/opt/media-stack/config` and `/data`; perform a restore test.
- [ ] Add capacity alerts before the 100 GiB local volume becomes constrained.
- [ ] Define a maintenance cadence for the intentionally floating `latest` image tags.
- [ ] Decide whether LAN management interfaces should move behind authenticated HTTPS ingress.
