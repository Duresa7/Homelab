# Jellyfin Plugins

**Created:** 2026-09-27  
**Last updated:** 2026-09-27

I installed Jellyfin Enhanced, Intro Skipper, Media Bar, and the File Transformation dependency on Jellyfin 12.1.0, `Jelly-Media`, on `media-01` (`192.168.40.42`, CT 842 on `red-server`). I restarted Jellyfin after approval and verified that all four plugins are active.

## Installation

I checked the maintainers' installation instructions and the manifests served to Jellyfin 12.1.0. Media Bar and File Transformation supplied builds targeting 12.1.0. Enhanced and Intro Skipper supplied builds targeting 12.0.0. I used Jellyfin's authenticated package API to install the compatible versions from its catalog.

| Plugin | Installed version | Target ABI | Observed status |
| --- | --- | --- | --- |
| Jellyfin Enhanced | 12.9.0.0 | 12.0.0.0 | Active |
| Intro Skipper | 12.0.4.0 | 12.0.0.0 | Active |
| Media Bar | 3.0.0.0 | 12.1.0.0 | Active |
| File Transformation | 3.0.1.0 | 12.1.0.0 | Active |

I added three enabled repositories, preserving the existing Jellyfin Stable and Moonbase repositories:

- Jellyfin Enhanced: `https://raw.githubusercontent.com/n00bcodr/jellyfin-plugins/main/manifest.json`
- IAmParadox27: `https://www.iamparadox.dev/jellyfin/plugins/manifest.json`
- Intro Skipper: `https://intro-skipper.org/manifest.json`

I installed File Transformation first, followed by Enhanced, Intro Skipper, and Media Bar. The repository readback contained all five repositories, and the plugin readback contained all four requested packages and versions. I made no Compose or media-library changes and created no snapshot or backup.

## Activation and settings

After approval, I rechecked that no playback was active and ran `pct exec 842 -- docker restart jellyfin` through SSH Manager target `red_server`. It exited 0. Startup completed in 7.75 seconds, Docker reported healthy, and the plugin API reported all four plugins active. AniList 15.0.0.0 and Moonbase 2.3.0.0, which were already queued before installation, also became active. The startup and initial-analysis log check contained zero error or fatal entries.

I kept Enhanced's default enabled bookmarks, random button, pause screen, and script injection. Its automatic intro/outro skipping and Seerr integration remain off. Media Bar is enabled with its embedded assets, and unpinned remote assets remain disabled. File Transformation requires no additional settings.

I set Intro Skipper's `MaxParallelism` and `ProcessThreads` to 1 and verified both values through the configuration API, limiting analysis load on the 2-vCPU media host. Automatic detection and media-segment updates are enabled. Automatic intro and credit skipping remain off, preserving client-controlled skipping. Its configuration confirms File Transformation is available.

## Verification and remaining work

I started **Detect and Analyze Media Segments** through the scheduled-task API. Its state changed to Running, and logs showed introduction analysis of 14 files from Mushoku Tensei: Jobless Reincarnation season 3. The task retains its daily trigger. The initial scan is still running; full-library completion and actual skip-button playback have not been verified. A sample of 30 episodes returned media segments for 12 episodes, but the pre-existing Chapter Segments Provider means that sample alone does not prove those segments came from the new scan.

Through `https://jellyfin.alphasecunited.com`, `/web/`, `/MediaBar/slideshowpure.css`, `/MediaBar/slideshowpure.js`, and `/JellyfinEnhanced/script` returned HTTP 200 with the expected HTML, CSS, or JavaScript content types. The served web HTML contains both Media Bar assets and the Enhanced script. I did not perform an authenticated visual browser or playback test. Clients need a hard refresh to load the new assets.

The separate `/Moonfin/Web/` client also receives injected asset references, but its base URL resolves them under `/Moonfin/`. Checks of `/Moonfin/MediaBar/slideshowpure.js` and `/Moonfin/JellyfinEnhanced/script` returned 404. I left that client's routing unchanged. Enhanced and Media Bar should be accessed through the standard `/web/` client; Moonfin compatibility remains open.

The initial direct SSH check on `media_01` could not run Docker through passwordless sudo. I completed the Docker inspection through SSH Manager target `red_server` using `pct exec 842`. Authentication succeeded with the standard application account; authenticated API calls required the MediaBrowser Authorization header. I retained no separate terminal capture for research, preflight, installation, restart, configuration, or verification; this record reflects the live API and SSH Manager responses.

## References

- [Jellyfin Enhanced installation](https://github.com/n00bcodr/Jellyfin-Enhanced/blob/main/docs/installation/installation.md)
- [Media Bar installation and dependency](https://github.com/IAmParadox27/jellyfin-plugin-media-bar)
- [File Transformation installation](https://github.com/IAmParadox27/jellyfin-plugin-file-transformation)
- [Intro Skipper installation and initial analysis](https://github.com/intro-skipper/intro-skipper/wiki/Installation)

## Plugin Pages and Custom Tabs follow-up

I installed Plugin Pages 3.0.1.0 from the existing IAmParadox27 repository. Its manifest targets Jellyfin 12.1.0. After restarting Jellyfin, its status was Active and Docker reported healthy. `/PluginPages/inject.js` returned HTTP 200 with JavaScript content.

Custom Tabs was absent from the compatible server catalog. I checked its latest upstream release, 0.2.10.0: its assets target 10.10.7 and 10.11.7 through 10.11.11, with no Jellyfin 12 build. I did not install an incompatible build. [Custom Tabs releases](https://github.com/IAmParadox27/jellyfin-plugin-custom-tabs/releases/latest) and [Plugin Pages installation](https://github.com/IAmParadox27/jellyfin-plugin-pages) were the upstream references.

The live Enhanced configuration had Bookmarks and Requests enabled as native Jellyfin 12 tabs. I preserved those settings and enabled `BookmarksUsePluginPages` and `DownloadsUsePluginPages`. Hidden Content and Calendar were disabled, and I left them disabled. Immediately after saving, the Plugin Pages user endpoint returned no pages. A second restart registered the two links: `/PluginPages/User` returned Requests at `/JellyfinEnhanced/downloadsPage` and Bookmarks at `/JellyfinEnhanced/bookmarksPage`, with a total count of 2. On Jellyfin 12 these links appear through the profile menu rather than a legacy sidebar.

I used the restart approval from this installation session. No playback was active before activation, and Intro Skipper's analysis task was idle. These checks came from live API and SSH Manager responses; I retained no separate terminal capture. I did not perform a rendered browser test. Custom Tabs remains uninstalled pending a compatible release; the existing native tabs remain enabled.

## Seerr browsing tab

I enabled `RecommendationsPageEnabled` and `RecommendationsUseNativeTab` in Enhanced to provide Seerr browsing inside Jellyfin without the Custom Tabs plugin. The existing Seerr integration was already enabled and configured. I preserved the remaining configuration and did not restart Jellyfin.

Both the administrative configuration readback and `/JellyfinEnhanced/public-config` returned the two settings as true. Authenticated GET requests to `/JellyfinEnhanced/jellyseerr/discover/trending?page=1`, `/JellyfinEnhanced/jellyseerr/discover/movies?page=1`, and `/JellyfinEnhanced/jellyseerr/discover/tv?page=1` each returned 20 results. These were read-only discovery checks; I submitted no media request. The browser needs a refresh to load the native Recommendations tab. I did not perform a rendered browser test or retain a separate terminal capture; verification came from the live API responses.
