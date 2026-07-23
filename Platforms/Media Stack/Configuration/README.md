# Media Stack Configuration Reference

**Created:** 2026-07-17  
**Last updated:** 2026-07-22

[`compose.example.yml`](compose.example.yml) shows the service relationships, mounts, ports, VPN isolation, & automatic Proton port synchronization used by `/opt/media-stack/compose.yml`.

[`media-stack.env.example`](media-stack.env.example) lists the required deployment-specific variables. Both examples require editing before use.

The request service intentionally retains the Compose key and configuration path name `jellyseerr` so the existing database is reused, but it runs the successor image `ghcr.io/seerr-team/seerr:latest` with `init: true`.

## qBittorrent Callback Requirements

The Gluetun port-forward callback reaches qBittorrent over `127.0.0.1` inside their shared network namespace. qBittorrent's persistent configuration must keep local authentication bypass enabled for that callback. Sonarr and Radarr reach qBittorrent from the private Docker network, so the live Docker subnet is also present in qBittorrent's authentication-bypass whitelist. I omit the live subnet here intentionally because Docker may allocate a different subnet during reconstruction.

After restore or recreation, I verify through the qBittorrent preferences API that:

```text
bypass_local_auth=True
bypass_auth_subnet_whitelist_enabled=True
bypass_auth_subnet_whitelist includes 127.0.0.1/32 and the active media Docker subnet
random_port=False
upnp=False
```

Then I compare qBittorrent's listening port with Gluetun's `/gluetun/forwarded_port`. I do not weaken authentication for other source networks.

The live qBittorrent configuration also enables `excluded_file_names_enabled` with the 100-pattern baseline documented in my [payload-filtering research](../Documentation/Download%20Payload%20Filtering%20Research%20-%202026-07-17.md). This setting belongs to qBittorrent rather than Compose because the Web API and WebUI serialize it.

## Internal HTTPS

Jellyfin advertises `JELLYFIN_PUBLISHED_SERVER_URL` as its internal HTTPS URL and trusts NPM at `192.168.85.2`. qBittorrent's persistent `WebUI\ServerDomains` value is the semicolon-separated `qbittorrent.<YOUR_BASE_DOMAIN>;gluetun;192.168.40.42`. Those entries preserve the NPM hostname, the Arr clients' Docker path, & direct access without disabling Host-header validation. UniFi resolves all six media UI names to NPM and permits NPM only to TCP 5055, 7878, 8080, 8096, 8989, & 9696 on `media-01`.

The names, upstreams, verification, & rollback points are in [Internal HTTPS Service Onboarding - 2026-07-22](../../Nginx%20Proxy%20Manager/Documentation/Change%20Records/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22.md). The [qBittorrent Host Validation issue](../Documentation/Troubleshooting/qBittorrent%20Host%20Validation%20Blocked%20Arr%20Clients%20-%202026-07-22.md) records why all three entries are required.
