# Jellyfin Plugins

**Created:** 2026-09-27  
**Last updated:** 2026-09-27

I installed Jellyfin Enhanced, Intro Skipper, Media Bar, and the File Transformation dependency on Jellyfin 12.1.0, `Jelly-Media`, on `media-01` (`192.168.40.42`, CT 842 on `red-server`). Activation is pending approval for a Jellyfin restart.

## Installation

I checked the maintainers' installation instructions and the manifests served to Jellyfin 12.1.0. Media Bar and File Transformation supplied builds targeting 12.1.0. Enhanced and Intro Skipper supplied builds targeting 12.0.0. I used Jellyfin's authenticated package API to install the compatible versions from its catalog.

| Plugin | Installed version | Target ABI | Observed status |
| --- | --- | --- | --- |
| Jellyfin Enhanced | 12.9.0.0 | 12.0.0.0 | Restart |
| Intro Skipper | 12.0.4.0 | 12.0.0.0 | Restart |
| Media Bar | 3.0.0.0 | 12.1.0.0 | Restart |
| File Transformation | 3.0.1.0 | 12.1.0.0 | Restart |

I added three enabled repositories, preserving the existing Jellyfin Stable and Moonbase repositories:

- Jellyfin Enhanced: `https://raw.githubusercontent.com/n00bcodr/jellyfin-plugins/main/manifest.json`
- IAmParadox27: `https://www.iamparadox.dev/jellyfin/plugins/manifest.json`
- Intro Skipper: `https://intro-skipper.org/manifest.json`

I installed File Transformation first, followed by Enhanced, Intro Skipper, and Media Bar. The repository readback contained all five repositories, and the plugin readback contained all four requested packages and versions. I made no Compose or media-library changes and created no snapshot or backup.

## Verification and remaining work

Before installation, the public server API reported 12.1.0 and Docker reported Jellyfin healthy with nine days of uptime. Authenticated session checks before and after installation found zero active playback sessions. AniList 15.0.0.0 and Moonbase 2.3.0.0 were already awaiting restart before this work; the next restart will activate those updates too.

All four installation requests succeeded. The plugin API reported `Restart` for each afterward. I have not restarted Jellyfin, changed plugin settings, started intro detection, or verified the rendered interface and playback behavior. Those steps remain pending restart approval under the workspace's disruptive-change rule.

After restart, I need to verify all four plugins are active, check their effective settings, run Intro Skipper's Detect and Analyze task, and confirm media segments are produced. The clients then need a hard refresh to load the new web features. Actual skip-button behavior still needs a playback check.

The initial direct SSH check on `media_01` could not run Docker through passwordless sudo. I completed the Docker inspection through SSH Manager target `red_server` using `pct exec 842`. Authentication succeeded with the standard application account; authenticated API calls required the MediaBrowser Authorization header. I retained no separate terminal capture for research, preflight, installation, or verification; this record reflects the live API and SSH Manager responses.

## References

- [Jellyfin Enhanced installation](https://github.com/n00bcodr/Jellyfin-Enhanced/blob/main/docs/installation/installation.md)
- [Media Bar installation and dependency](https://github.com/IAmParadox27/jellyfin-plugin-media-bar)
- [File Transformation installation](https://github.com/IAmParadox27/jellyfin-plugin-file-transformation)
- [Intro Skipper installation and initial analysis](https://github.com/intro-skipper/intro-skipper/wiki/Installation)
