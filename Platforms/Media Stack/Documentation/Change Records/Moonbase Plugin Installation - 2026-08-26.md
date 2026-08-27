# Moonbase Plugin Installation

**Created:** 2026-08-26  
**Last updated:** 2026-08-26

**Implementation date:** 2026-08-26  
**System:** Galaxy Proxmox cluster, `red-server`, CT 842 `media-01`  
**Status:** Complete for the plugin and the Seerr single sign-on path. Moonbase 2.1.0.0 is active on Jellyfin 10.11.11, the hosted Moonfin web app answers on the LAN and through the published hostname, and a Seerr SSO session is established. Seerr's webhook back to Jellyfin is not provisioned and is carried as an open item.

## What Changed

Moonbase is the server-side companion plugin for the Moonfin Jellyfin clients. It carries settings sync across devices, hosts the Moonfin web app under `/Moonfin/Web/`, serves home screen and media bar data, adds rating sources, and proxies Seerr behind a server-side single sign-on session.

I added a second plugin repository to Jellyfin alongside `Jellyfin Stable`:

| Name | Manifest URL |
| --- | --- |
| Moonbase | `https://raw.githubusercontent.com/Moonfin-Client/Plugin/refs/heads/master/manifest.json` |

Moonbase then appeared in the catalogue as GUID `8c5d0e914f2a4b6d9e3f1a7c8d9e0f2b`, latest version 2.1.0.0, target ABI 10.10.0.0. The server runs 10.11.11, so the build applies.

I installed 2.1.0.0 through Jellyfin's own plugin API rather than by dropping files in the plugins directory, so Jellyfin owns the download and future catalogue updates. It extracted to `/opt/media-stack/config/jellyfin/plugins/Moonbase_2.1.0.0`, holding `Moonfin.Server.dll`, `SharpCompress.dll`, `meta.json`, `logo.png`, and the `frontend` tree that serves the web app. Ownership is `dkadi:dkadi`, matching the `user: "1000:1000"` the Compose service runs as.

No session was playing anything, so I restarted the `jellyfin` container at 11:16 PM to load the assembly. I then ran the `Moonfin Startup` task, which the plugin requires once after install.

The install registered six scheduled tasks: `Moonfin Startup`, `Moonfin Settings File Repair`, `Moonfin IMDb Lists Sync`, `Moonfin MDBList Official Lists Sync`, `Moonfin MDBList Ratings Sync`, and `Moonfin Studio Images Sync`.

I triggered `Moonfin IMDb Lists Sync` first by mistake, because I selected the first entry of the filtered task list instead of matching the name. It returned `Completed` against an unconfigured list source and changed nothing. I then ran `Moonfin Startup` by its task ID and it also returned `Completed`.

I made no change to `compose.yml`, to the Jellyfin service definition, or to any library, user, or transcoding setting.

## Seerr Integration

I enabled the Seerr integration on Moonbase's configuration page at 11:32 PM. The resulting values in `plugins/configurations/Moonfin.Server.xml`:

| Setting | Value |
| --- | --- |
| `SeerrEnabled` | `true` |
| `SeerrUrl` | `https://seerr.alphasecunited.com/` |
| `PublicServerUrl` | `http://192.168.40.42:8096` |
| `JellyseerrEnabled` | `false` |

`SeerrEnabled` is the correct toggle rather than `JellyseerrEnabled`, because the container runs `ghcr.io/seerr-team/seerr:latest` 3.4.1. The container name `jellyseerr` is a leftover from the migration off Jellyseerr and does not indicate the product.

The Seerr URL is the internal HTTPS hostname rather than the container address on the Compose `media` network. That path stays inside the network. UniFi [local DNS](../../../../Infrastructure/Network/UniFi/Configuration/local-dns.md) answers `seerr.alphasecunited.com` with `192.168.85.2`, and Nginx Proxy Manager on CT 107 `docker-network` forwards it to `192.168.40.42:5055` per the [internal proxy-host inventory](../../../Nginx%20Proxy%20Manager/Configuration/internal-proxy-hosts.md). Public DNS holds no A record for the name, and Caddy on `edge-01` fronts public traffic only, so neither the WAN, Cloudflare, nor Caddy is on this path.

The call does leave the guest. Jellyfin on VLAN 40 reaches NPM on VLAN 85, NPM terminates TLS on the wildcard certificate, and the request is proxied back to VLAN 40 to a container sitting beside the one that made it. Against `http://jellyseerr:5055` on the Compose bridge, the cost is internal DNS, inter-VLAN routing and firewall policy, and NPM all being in the request path.

The `PublicServerUrl` is the guest's LAN address, so Seerr's callback to Jellyfin stays on the host.

Push is off. The relay URL keeps its shipped default and no Firebase service account is configured, so backgrounded mobile clients receive no push.

Signing in to a Moonfin client as the Jellyfin administrator created the server-side Seerr session that the SSO proxy needs. Jellyfin logged it at 11:33:02 PM:

```
[2026-08-26 23:33:02.058 -04:00] [INF] [27] Moonfin.Server.Services.SeerrSessionService:
Seerr SSO session created for user "dkadi"
```

## Verification

- `GET /Repositories` returned both `Jellyfin Stable` and `Moonbase`, each enabled.
- `GET /Plugins` returned `Moonbase 2.1.0.0 Active` after the restart, alongside the nine plugins that were already loaded.
- `docker inspect` reported the `jellyfin` container `healthy` after the restart and again at 11:48 PM.
- `Moonfin Startup` finished at 11:17 PM with `LastExecutionResult.Status` of `Completed` and no error message.
- `http://127.0.0.1:8096/Moonfin/Web/` returned HTTP 200 with a 5537 byte body.
- `https://jellyfin.alphasecunited.com/Moonfin/Web/` returned HTTP 200 with no redirect away from the path, so the reverse proxy passes the plugin route through unchanged.
- `https://jellyfin.alphasecunited.com/web/` still returned HTTP 200, so the stock Jellyfin client is unaffected.
- One session file exists under `plugins/configurations/Moonfin/seerr-sessions/`, written 11:33 PM, matching the SSO log line above.
- A per-user settings document appeared under `plugins/configurations/Moonfin/` at 11:32 PM, so settings sync is writing.
- From CT 842, `seerr.alphasecunited.com` and `jellyfin.alphasecunited.com` both resolved to `192.168.85.2` through the gateway resolver at `192.168.70.1`. `https://seerr.alphasecunited.com/api/v1/status` returned HTTP 200 with the connection terminating on `192.168.85.2:443`, a `server: openresty` response header, and a passing certificate verification, confirming Nginx Proxy Manager served it and the path never left the network.
- `https://jellyfin.alphasecunited.com/Moonfin/Seerr/Api/status` returned HTTP 401 to an unauthenticated request, which is the expected refusal for a proxy route that requires a Jellyfin session.
- No `[ERR]`, `[FTL]`, warning, or exception line mentioning Moonfin or Seerr appears in the Jellyfin logs.

I kept no separate evidence folder. I verified each state through the live Jellyfin API, the container runtime, the guest filesystem, and the Jellyfin log during the session.

## Open Items

- **Seerr's webhook to Jellyfin is not provisioned.** Seerr's webhook notification agent is still `enabled: false` with an empty URL and no auth header, and no provisioning line appears in the Jellyfin log. Moonbase generated a webhook secret at install and reported `NoAdminSession` before sign-in, but creating the SSO session did not result in a configured agent on the Seerr side. Requests placed from a Moonfin client work; request status notifications flowing back to Jellyfin do not. Fix by adding the webhook by hand in Seerr under Settings, Notifications, Webhook, using the callback URL and secret shown on the Moonbase configuration page.
- **Several plugin defaults reach external services and are already running.** The IMDb list cache is 365 KiB on disk and the studio logo directory was written at 11:41 PM, so those syncs are live. MDBList official lists capped at 250 items, a LaunchBox metadata URL, a jsDelivr LibreTro database base URL, the `push.moonfin.io` relay, and a WebRTC scan in the web app are all enabled out of the box. None are required for playback. Review them against the outbound posture I want for this guest.
- **The Seerr URL hairpins through Nginx Proxy Manager.** Switching `SeerrUrl` to `http://jellyseerr:5055` would keep the call on the Compose bridge and drop internal DNS, the VLAN 40 to VLAN 85 round trip, and NPM out of the request path. Latency and resilience only. The current path is entirely internal and verified working.
- **The plugin holds a Seerr webhook secret** in its configuration file on the host. It is not published here.
- **The header shortcut is not installed.** Moonbase's optional one-click Moonfin button in the Jellyfin header needs the separate File Transformation plugin, which I did not add.
- **Moonfin clients are separate applications** on mobile, desktop, Android TV, Apple TV, smart TV, and Roku. The plugin is the server half only.
