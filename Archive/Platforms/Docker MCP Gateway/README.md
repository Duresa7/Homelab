# Docker MCP Gateway: Retired SSH Manager Files

**Created:** 2026-10-31  
**Last updated:** 2026-10-31

These are the tracked SSH Manager MCP files from [Docker MCP Gateway](../../../Platforms/Docker%20MCP%20Gateway/README.md), kept under their original paths. SSH Manager 3.8.5 ran on `docker-blue` from 2026-08-31 until I replaced it with [ssh-mcp](../../../Platforms/SSH%20MCP/README.md) and removed it on 2026-10-31: [SSH Manager Retirement](../../../Platforms/Docker%20MCP%20Gateway/Documentation/Change%20Records/SSH%20Manager%20Retirement%20-%202026-10-31.md).

- `Configuration/Dockerfile.ssh-manager`, the image built around mcp-proxy 0.12.0
- `Configuration/patches/mcp-ssh-manager-3.8.5-homelab.patch`, bounded inline transfers and real host-key comparison
- `Configuration/catalogs/ssh-manager.yaml`, the gateway's remote catalog entry
- `Configuration/ssh-manager.env.example`, the secret template
- `Configuration/systemd/`, the nightly restart timer and its service
- `Scripts/ssh-manager-shared-server-cutover.sh`, the 2026-09-03 cutover to one shared process

The UniFi gateway still runs from the live platform folder.
