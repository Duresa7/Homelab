# UniFi Network MCP Integration

**Created:** 2026-08-31  
**Last updated:** 2026-08-31

## Outcome

I added UniFi Network MCP 0.29.3 to the Docker MCP Gateway on `docker-blue`. The gateway now launches the server on demand, authenticates to the UniFi controller at `192.168.1.1:443`, and exposes it through the existing bearer-protected MCP endpoint at `http://192.168.40.39:8811/mcp`.

## Source Selection

The upstream project listed `network/v0.29.3` as its newest UniFi Network release. I pinned the matching multi-architecture image manifest `ghcr.io/sirkirby/unifi-network-mcp:0.29.3@sha256:4ebc2582d7c85f08fc52dc8f988abd7cf1c0350837fe84ca35f4c7884eab2f0b`.

## Implementation

1. I added a homelab catalog entry for `unifi-network`, restricted its allowed destination to `192.168.1.1:443`, and configured UniFi OS proxy mode for site `default`.
2. I enabled lazy tool registration, adaptive response content, sensitive-field redaction, and confirmation mode. I disabled create, update, and delete through the server's policy switches.
3. I loaded the existing local administrator credentials and Integration API key from the approved credential store. The live values are in `/opt/docker/mcp-gateway/mcp-secrets.env`, owned by root with mode `0600`, and enter the gateway through a Compose secret.
4. I configured the gateway to load only the versioned UniFi catalog entry. Managed MCP containers are limited to one CPU and 512 MiB.
5. I installed the catalog and Compose changes under `/opt/docker/mcp-gateway`, pulled the pinned image, and recreated the gateway.

I retired the combined `mcp-secrets.env` later on 2026-08-31 when I split UniFi and SSH Manager onto separate endpoints. UniFi now reads `unifi-secrets.env`; the split and the removal of the combined file are recorded in [MCP Integration Separation](../../../Executor/Documentation/Change%20Records/MCP%20Integration%20Separation%20-%202026-08-31.md).

I first tested Docker MCP Gateway profiles as the organizational boundary. Gateway 0.43.3 profiles accept only Docker Desktop's secret store, which is unavailable on this headless Docker Engine host. The unresolved secret references reached the UniFi server as literal values and authentication returned HTTP 403. I confirmed the stored credentials against the pinned image, removed the abandoned profile state, and used the gateway's supported headless catalog plus secret-file mode.

A verbose diagnostic startup logged a short password prefix while masking the rest of the value. I disabled verbose output and force-recreated the gateway, which removed that container log. The current log contains no password or API-key prefix. Credential rotation remains the owner's decision after the partial prefix exposure.

## Verification

- Compose validation passed and `docker-mcp-gateway` returned to healthy from the pinned 0.43.3 gateway image.
- An authenticated `unifi_get_system_info` call through the HTTP gateway succeeded against `Ahsoka Gateway`, running UniFi Network 10.6.101 on site `default`.
- An authenticated `unifi_list_dpi_categories` call succeeded, confirming the Integration API key reached the managed server.
- An unauthenticated MCP initialization returned HTTP 401.
- A controlled `unifi_create_voucher` call without confirmation returned the configured create-disabled policy response and made no change.
- The live MCP secret file was root-owned with mode `0600`. The gateway retained its read-only root filesystem, dropped capabilities, resource limits, and bounded logs.
- One idle sample showed 0.00 percent gateway CPU and 21.04 MiB of its 256 MiB memory limit.
- Docker Blue already had controller reachability on TCP 443, so I made no UniFi firewall or routing change.

No snapshot or backup was created. The deployment is reproducible from the versioned Compose and catalog files; secret values remain outside the repository.

## Open State

The UniFi MCP is read-only by policy. The gateway still uses its internal HTTP listener with bearer authentication; DNS, TLS proxying for `mcp.alphasecunited.com`, and Executor integration remain separate future changes.

The gateway's Docker socket remains the primary trust boundary. The owner may rotate the UniFi local administrator password because a short prefix appeared during the diagnostic startup before I recreated the container.
