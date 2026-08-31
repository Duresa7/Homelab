# Docker MCP Gateway Initial Deployment

**Created:** 2026-08-30  
**Last updated:** 2026-08-30

## Outcome

I deployed Docker MCP Gateway 0.43.3 on `docker-blue` from Docker's official image. It is healthy at `192.168.40.39:8811`, requires bearer authentication for MCP requests, and currently manages no MCP server containers.

## Source Selection

GitHub listed 0.43.3 as the newest published release, and the official container package carried the matching versioned tag. I pinned its multi-architecture manifest digest `sha256:e3ee13818cb067a506c5e9acdb2bb4fe0e601caef7d116fc329755782f1a3cfa`. This version includes the current HTTP authentication, guarded configuration paths, bind-mount validation, image verification, and tool-collision protections.

## Implementation

1. Confirmed Docker Engine 29.6.2 and Compose 5.3.1 were healthy on `docker-blue`, port 8811 was unused, and `/opt/docker/mcp-gateway` did not exist.
2. Validated that the pinned image remains running with an empty default profile. The empty state starts no managed MCP server container.
3. Created a 64-hex-character bearer token, stored it in the approved credential store, and installed it only in the root-owned mode-`0600` live `.env`.
4. Installed the Compose project under `/opt/docker/mcp-gateway` and its persistent configuration directory under `/opt/docker/mcp-gateway/config`.
5. Configured Streamable HTTP on `192.168.40.39:8811`, the official Docker socket mount, bearer authentication, health checking, restart behavior, resource limits, a read-only root filesystem, dropped capabilities, `no-new-privileges`, and bounded logs.
6. Validated the expanded Compose configuration, pulled the pinned image, and started the project.

The first privileged file-install command stopped after creating the top-level directory because elevation covered only its first chained command. No container had started. I reran the complete install inside one elevated shell, confirmed the intended owners and modes, and continued from the Compose validation step.

## Verification

- Compose reported `docker-mcp-gateway` running and healthy from the pinned 0.43.3 image.
- `GET /health` returned HTTP 200.
- An MCP initialization without a bearer token returned HTTP 401.
- The same initialization with the stored bearer token returned HTTP 200 and valid server metadata.
- A controlled restart returned to healthy, retained the same token file, and continued rejecting unauthenticated MCP requests.
- Docker reported zero managed MCP server containers.
- The container had a read-only root filesystem, a 256 MiB memory limit, a half-CPU limit, and `unless-stopped` restart behavior.
- One post-restart idle sample showed 0.00 percent CPU, 7.996 MiB memory, and six processes.

No snapshot or backup was created. The empty gateway is reproducible from the versioned Compose file; the bearer token remains in the credential store.

## Open State

No catalog, UniFi MCP server, other MCP server, Executor integration, DNS record, TLS proxy, or new network policy is present. Those remain separate future changes. The direct listener is internal HTTP protected by bearer authentication.

The mounted Docker socket gives the gateway broad control over Docker Engine on `docker-blue`. It is required by Docker's official container deployment so the gateway can start managed MCP server containers.
