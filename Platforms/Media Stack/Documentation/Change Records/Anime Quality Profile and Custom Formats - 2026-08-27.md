# Anime Quality Profile and Custom Formats

**Created:** 2026-08-27  
**Last updated:** 2026-08-27

**Implementation date:** 2026-08-27  
**System:** Galaxy Proxmox cluster, `red-server`, CT 842 `media-01`  
**Status:** Complete. Sonarr 4.0.19.2979 carries the TRaSH Guides anime quality profile, the 40 custom formats it scores, and Nyaa.si as an anime indexer. Standard television, Radarr, and the Movies and TV Shows libraries are unchanged and verified so.

I built this from the [TRaSH Guides Sonarr anime quality profile guide](https://trash-guides.info/Sonarr/sonarr-setup-quality-profiles-anime/), taking the scores from the `docs/json/sonarr/cf/` and `docs/json/sonarr/quality-profiles/anime-remux-1080p.json` definitions in the guides repository rather than from the rendered page, because the page renders its score tables from those files through template variables.

## Why

Anime release names do not carry reliable source or quality information, so the `HD-1080p` profile that serves standard television ranks anime releases by resolution and file size, which are close to meaningless on that content. The guide replaces that with release-group tiers derived from [SeaDex](https://releases.moe/) ratings: a top-tier group's 1080p encode outranks a generic remux, and known low-quality groups are rejected outright.

## Sonarr Custom Formats

I imported 40 custom formats, which took Sonarr's `customformat` IDs 2 through 41. The pre-existing `Block AV1` format keeps ID 1 and is untouched.

The TRaSH definitions store each specification's fields as a JSON object, `"fields": {"value": x}`, while Sonarr's API requires an array, `"fields": [{"name": "value", "value": x}]`. Posting the definitions unmodified returns HTTP 400 with `$.specifications[0].fields` cited, so the import converts that shape. Every field across all 40 definitions carries the single key `value`, so the conversion is uniform. The 40 formats hold 537 specifications between them, 137 of which belong to `Anime LQ Groups`.

Adding a custom format enters it in every existing quality profile at score 0, which has no effect. I confirmed after the import that `Any`, `SD`, `HD-720p`, `HD-1080p`, `Ultra-HD`, and `HD - 720p/1080p` each held 41 format entries with `Block AV1` at −10000 in `HD-1080p` as their only non-zero score, and that their enabled qualities and cutoffs were unchanged.

## Quality Profile

`[Anime] Remux-1080p` is Sonarr quality profile ID 7.

| Setting | Value |
| --- | --- |
| Upgrades Allowed | Yes |
| Upgrade Until | `Bluray 1080p` group, profile item ID 1004 |
| Upgrade Until Custom Format Score | 10000 |
| Minimum Custom Format Score | 100 |
| Minimum Custom Format Score Increment | 1 |

The 10000 cutoff score is unreachable by design, so Sonarr keeps looking for a better-tiered release instead of settling. The minimum of 100 is the value the guide's own profile export carries and the page's prose omits. It matters because `Anime Web Tier 06` scores exactly 100, so the floor rejects any release from a group absent from the tier lists.

Qualities are grouped as the guide requires, listed here best first as the interface shows them:

| Rung | Members |
| --- | --- |
| Bluray 1080p | `Bluray-1080p`, `Bluray-1080p Remux` |
| WEB 1080p | `WEBDL-1080p`, `WEBRip-1080p`, `HDTV-1080p` |
| Bluray-720p | |
| WEB 720p | `WEBDL-720p`, `WEBRip-720p`, `HDTV-720p` |
| Bluray-480p | |
| WEB 480p | `WEBDL-480p`, `WEBRip-480p` |
| DVD | |
| SDTV | |

`Bluray-2160p Remux`, `Bluray-2160p`, `WEB 2160p`, `HDTV-2160p`, `Raw-HD`, `Bluray-576p`, and `Unknown` are disabled and sit below SDTV, which is where the guide's export places them.

### Scores

| Custom format | Score |
| --- | --- |
| Anime BD Tier 01 through 08 | 1400, 1300, 1200, 1100, 1000, 900, 800, 700 |
| Anime Web Tier 01 through 03 | 600, 500, 400 |
| Remux Tier 01, Remux Tier 02 | 975, 950 |
| Anime Web Tier 04 through 06 | 300, 200, 100 |
| Anime Raws, Anime LQ Groups, AV1, Dubs Only, VOSTFR | −10000 |
| v0, v1, v2, v3, v4 | −51, 1, 2, 3, 4 |
| CR, DSNP, NF, AMZN, VRV, FUNi, ABEMA, ADN | 6, 5, 4, 3, 3, 2, 1, 1 |
| Uncensored, 10bit, Anime Dual Audio, B-Global, Bilibili, HIDIVE | 0 |

The two Remux tiers are half their main-guide values of 1900 and 1850. That is the guide's `anime-sonarr` score set, and it is what puts a tier 01 through 05 group encode above a remux.

`Block AV1` stays at 0 in this profile. The imported `AV1` format covers the same releases at −10000, and scoring both would apply the penalty twice for no gain.

The optional preferences are left at the guide's defaults. `Anime Dual Audio` and `Uncensored` sit at 0, so tier ranking wins over either attribute. Raising `Anime Dual Audio` to 10 prefers dual audio inside a tier, 101 prefers it one tier up, and 2000 with a matching Minimum Custom Format Score makes it mandatory.

## Quality Definitions Left Alone

The guide points at its anime quality definitions, which set every quality to a minimum of 5 and a maximum of 1000 MB per minute. Quality definitions are one set per Sonarr instance rather than per profile, and this is a single instance that also serves standard television, so applying them would remove the size limits from the `HD-1080p` profile as well. The guide states the same carve-out: on a single instance, keep the standard definitions. The live definitions are unchanged, and the tier scores carry the ranking instead.

## Series Assignment

The three anime-type series moved from profile 4 to profile 7 through the `series/editor` endpoint. Sonarr holds one more anime series than the [2026-08-23 routing record](Anime%20Library%20Routing%20-%202026-08-23.md) describes, because a third was added after it.

| Series | ID | Type | Profile |
| --- | --- | --- | --- |
| Star Wars: Visions Presents - The Ninth Jedi | 19 | anime | 7 |
| Mushoku Tensei: Jobless Reincarnation | 26 | anime | 7 |
| Third anime series added since 2026-08-23 | 27 | anime | 7 |

The eleven standard series on profile 4 and Superman and Lois on profile 1 were not touched.

## Naming

I set `animeEpisodeFormat` to the guide's scheme and changed nothing else:

```text
{Series CleanTitleWithoutYear} {(Series Year)} - S{season:00}E{episode:00} - {absolute:000} - {Episode CleanTitle:90} {[Custom Formats]}{[Quality Full]}{[Mediainfo AudioCodec}{ Mediainfo AudioChannels]}{MediaInfo AudioLanguages}{[MediaInfo VideoDynamicRangeType]}[{Mediainfo VideoCodec }{MediaInfo VideoBitDepth}bit]{-Release Group}
```

Sonarr applies that field only to anime-type series, so standard television keeps `{Series Title} - S{season:00}E{episode:00} - {Episode Title} {Quality Full}`.

The guide also asks for a series folder format of `{Series CleanTitleWithoutYear} {(Series Year)}` and a season folder format of `Season {season:00}`. Both fields are shared with standard television, so applying them would rename every television folder as well. I left them at `{Series Title}` and `Season {season}`. `Multi-Episode Style` was already `Prefixed Range`, which is what the guide asks for.

Pre-change values, as the rollback point:

| Field | Previous value |
| --- | --- |
| `animeEpisodeFormat` | `{Series Title} - S{season:00}E{episode:00} - {Episode Title} {Quality Full}` |
| `standardEpisodeFormat` | `{Series Title} - S{season:00}E{episode:00} - {Episode Title} {Quality Full}` |
| `seriesFolderFormat` | `{Series Title}` |
| `seasonFolderFormat` | `Season {season}` |
| `multiEpisodeStyle` | 5 |

Note that `/api/v3/config/naming/examples` ignores query parameters on this build. Passing a deliberately distinct format returned the saved one, so it cannot preview an unsaved change. I validated against `/api/v3/rename` instead, which renders real files.

## Seerr

Seerr's default Sonarr server now routes anime requests to profile 7. Its standard television route, both root folders, and `animeSeriesType` are unchanged. Seerr rejects a body containing the read-only `id` field, which the [2026-08-23 record](Anime%20Library%20Routing%20-%202026-08-23.md) also hit, so the update sends the settings without it and keeps the ID in the route.

| Setting | Value |
| --- | --- |
| `activeProfileId` / `activeProfileName` | 4, `HD-1080p` |
| `activeDirectory` | `/data/media/tv` |
| `activeAnimeProfileId` / `activeAnimeProfileName` | 7, `[Anime] Remux-1080p` |
| `activeAnimeDirectory` | `/data/media/anime` |
| `animeSeriesType` | anime |

## Prowlarr

The two existing indexers were 1337x and EZTV. Neither carries the fansub and Blu-ray groups the tier lists rank, so the profile had almost nothing to rank. I added the public `nyaasi` definition as `Nyaa.si`, indexer ID 3, which maps to Torznab category 5070.

| Field | Value | Reason |
| --- | --- | --- |
| `sonarr_compatibility` | true | Folds season information into release titles so Sonarr parses them. Confirmed in output: a result arrived as `[Fuchs] Mushoku Tensei - S03E05 (CR WEB-DL ...)` |
| `cat-id` | 1, Anime | Queries Nyaa's Anime category only, dropping its audio, books, and games results |
| `strip_s01` | false | Default. It removes first-season keywords, which can break multi-season matching |
| `prefer_magnet_links` | true | Default |

Nyaa also advertises movie categories 2000 and 2020, and Prowlarr sends every indexer to an application that carries no tags, so adding it would have pushed Nyaa into Radarr as well. To prevent that without altering what Radarr already receives:

- Created tag `movies`, tag ID 2.
- Added `movies` to the 1337x indexer, taking its tags from `[1]` to `[1, 2]`. The existing `flaresolverr` tag is preserved, and the FlareSolverr proxy matches on tag 1 only, so its routing is unaffected.
- Set the Radarr application's tags to `[2]`, so it syncs only indexers carrying `movies`.
- Left the Sonarr application's tags empty, so it continues to receive every indexer.

EZTV needed no tag. It advertises no movie categories, so Prowlarr never sent it to Radarr.

## Verification

- Sonarr reported version 4.0.19.2979 on branch `main`, and `/api/v3/health` returned zero messages after the work.
- All 40 custom formats imported with no failures. The six pre-existing quality profiles each held 41 format entries, `Block AV1` at −10000 in `HD-1080p` as the only non-zero score across all six, and unchanged enabled qualities and cutoffs.
- Profile 7 read back with `upgradeAllowed` true, cutoff 1004, `minFormatScore` 100, `cutoffFormatScore` 10000, `minUpgradeFormatScore` 1, the eight enabled rungs in the order above, and every score matching the table above.
- The three anime series read back on profile 7. The eleven standard series stayed on profile 4 and Superman and Lois on profile 1.
- A rename preview against standard series 5, 6, and 17 returned zero pending renames, so no television file moved.
- 27 anime files renamed. The set of inodes under `/data/media/anime` was identical before and after, 27 in each case, proving a rename rather than a copy with no data rewritten. Link counts were 1 on every file beforehand, so no download-tree hard link existed to break. A follow-up rename preview on series 19, 26, and 27 returned zero pending.
- Neither Jellyfin user held played state or a playback position on any anime episode before the rename, so none could be lost. Jellyfin created new item GUIDs for all 27, which is expected when paths change.
- After a targeted refresh of the Anime library, all three Jellyfin libraries reconciled exactly against the filesystem with no broken paths: Anime 27 and 27, TV Shows 286 and 286, Movies 6 and 6.
- Prowlarr's Nyaa.si test returned HTTP 200, and a category 5070 search returned 75 results.
- After an `ApplicationIndexerSync`, Sonarr held three indexers with Nyaa.si carrying anime categories `[5070]`. Radarr's indexer list was `['1337x (Prowlarr)']` both before and after, so Nyaa did not reach it.
- Seerr enumerated profile 7 as `[Anime] Remux-1080p` and both root folders through `/api/v1/service/sonarr/0`, so the request path resolves.
- An interactive search on one Mushoku Tensei episode returned 280 releases, 273 from Nyaa.si and 7 from 1337x, which is the measure of how little the previous indexer set carried. Scoring behaved as the guide intends. A `[Cytox]` release scored 506 as `Anime Web Tier 02` plus `CR`, `[MTBB]` scored 500 on the tier alone, and `[Erai-raws]` and `[ToonsHub]` scored 306 as `Anime Web Tier 04` plus `CR`. The rejections were the guard rails working: 44 releases rejected with "Custom Formats have score 0 below Series profile minimum 100", 25 more rejected at −10000 for `Anime LQ Groups`, and existing `EMBER` files at 700 correctly refused replacement by lower-tier web releases.
- `wanted/cutoff` reported 16 episodes, all Mushoku Tensei, and zero for any standard series, which confirms the change did not open upgrades on television.
- All eight Compose services remained running, with Gluetun and Jellyfin healthy. `/data` sat at 377 GB used of 916 GB.

None of the profile, custom format, naming, or indexer work above triggered a search, so none of it started a download.

I kept no evidence folder. Every state above was read back from the live Sonarr, Prowlarr, Seerr, and Jellyfin APIs and from the filesystem during the session. The scripts and the four staged API keys lived in `/tmp/anime-setup` on `media-01` and were removed at the end; the directory is gone.

## What Remains Open

- 16 Mushoku Tensei episodes are cutoff-unmet. Twelve of them are the files that previously parsed with no release group: they are Italian-audio `WEBDL-1080p` and score 0, which is below the profile minimum of 100. Nothing will replace them until a search runs, and the guide is explicit that it is built for acquisition going forward rather than for backfilling. A season search on series 26 is the way to act on it.
- Radarr keeps `HD-1080p` and no anime handling. Seerr has no anime route for Radarr the way it does for Sonarr, so an anime film would need its profile set per movie or a second Radarr instance. Nothing was changed there.
- The tier lists move as SeaDex ratings change, and this import is a point-in-time copy. Recyclarr against the `sonarr/templates/anime-remux-1080p.yml` template would keep the formats and scores current, with the template's `quality_definition: type: anime` block removed for the single-instance reason above.

Nothing else. Jellyfin user `IK-user` sees 0 of the 27 anime episodes, which I checked because it looked like a library access gap and is not one: both users still hold `EnableAllFolders`, and `IK-user` carries `MaxParentalRating` 14, which also filters that account to 137 of 286 television episodes and 4 of 6 movies. That is a deliberate setting and I left it alone.
