# Media Stack Configuration Reference

**Created:** 2026-07-17  
**Last updated:** 2026-07-17

[`compose.example.yml`](compose.example.yml) is a secret-free structural reference for the live project at `/opt/media-stack/compose.yml`. It documents service relationships, mounts, ports, VPN isolation, and automatic Proton port synchronization without containing the live guest address, LAN subnet, WireGuard key, passwords, API keys, or provider endpoint.

[`media-stack.env.example`](media-stack.env.example) lists the required variable names. Copying either reference directly to production is intentionally insufficient until protected values are supplied through the approved secret workflow.

The live `.env` is `root:root` mode `0600`. Never replace it with the example, print it through `docker compose config`, or commit a populated variant.

The request service intentionally retains the Compose key and configuration path name `jellyseerr` so the existing database is reused, but it runs the successor image `ghcr.io/seerr-team/seerr:latest` with `init: true`.

## qBittorrent Callback Requirements

The Gluetun port-forward callback reaches qBittorrent over `127.0.0.1` inside their shared network namespace. qBittorrent's persistent configuration must keep local authentication bypass enabled for that callback. Sonarr and Radarr reach qBittorrent from the private Docker network, so the live Docker subnet is also present in qBittorrent's authentication-bypass whitelist. The live subnet is intentionally omitted here because Docker may allocate a different subnet during reconstruction.

After restore or recreation, verify through the qBittorrent preferences API that:

```text
bypass_local_auth=True
bypass_auth_subnet_whitelist_enabled=True
bypass_auth_subnet_whitelist includes 127.0.0.1/32 and the active media Docker subnet
random_port=False
upnp=False
```

Then compare qBittorrent's listening port with Gluetun's `/gluetun/forwarded_port`. Do not weaken authentication for other source networks.

The live qBittorrent configuration also enables `excluded_file_names_enabled` with the 100-pattern media-stack baseline documented in the [payload-filtering research](../Documentation/Download%20Payload%20Filtering%20Research%20-%202026-07-17.md). This application preference remains in qBittorrent's protected live configuration rather than Compose because the official Web API and WebUI own its serialization.
