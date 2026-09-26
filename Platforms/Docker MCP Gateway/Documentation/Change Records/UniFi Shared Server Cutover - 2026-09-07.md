# UniFi Shared Server Cutover

**Created:** 2026-09-07  
**Last updated:** 2026-09-25

## Change

At 5:00 PM Eastern I moved UniFi Network MCP on `docker-blue` from gateway-managed containers to one persistent Compose service. Each Executor session previously caused a fresh container and controller login, which produced the [login-limit failures](../Troubleshooting/UniFi%20Parallel%20Reads%20Hit%20Controller%20Login%20Limit%20-%202026-09-07.md). I used the [SSH Manager pattern](SSH%20Manager%20Shared%20Server%20Cutover%20-%202026-09-03.md), keeping the gateway at its existing 0.43.3 digest without `--long-lived`.

I extended the existing full-access Dockerfile and built `homelab/unifi-network-mcp:0.29.3-full-access-proxy`. The pinned upstream UniFi 0.29.3 image and permission patch are unchanged. mcp-proxy 0.12.0 and MCP SDK 1.29.1 live in `/opt/mcp-proxy`, separate from UniFi's application environment, whose SDK remains 1.28.1. The bridge help smoke test passed during the build.

The `unifi-network` Compose service runs container `mcp-unifi-network` with one stdio child behind stateless Streamable HTTP. The catalog now has `type: remote`, URL `http://unifi-network:8080/mcp`, and transport `streamable-http`. Port 8080 is available only on the Compose network. The gateway permits this private HTTP remote and depends on the service becoming healthy. The existing external endpoint, `http://192.168.40.39:8811/mcp`, keeps its bearer authentication.

I moved controller settings and full-access permission flags from the catalog to the Compose service. I mapped all three existing credential entries into `unifi-network.env` on the host, root-owned mode 0600. Compose reads that file in raw format. A comparison against the resolved Compose environment proved all three values were preserved before activation. I removed the gateway secret mount and managed-container resource arguments; the persistent service has a 512 MiB memory limit, one CPU, 256-process limit, dropped capabilities, no-new-privileges, bounded logs, and an init process.

## Verification

I checked the live Compose file, catalog, and original Dockerfile against their tracked SHA-256 hashes before editing; all three matched. I validated the staged Compose with `config --quiet`, built the image successfully, then ran `up -d --wait --wait-timeout 90 unifi-network gateway`. Both containers became healthy. The initial unprivileged catalog hash read returned permission denied; the elevated read succeeded.

A first Executor network-list call returned success with 23 networks. I then issued six concurrent reads as six separate Executor executions. Every call returned success with 23 networks and no connection error. Before and after that burst:

- The container ID remained `c4e3fd7d68da0968db8861e5f7616555f3460073b2889a589f7b8ba27cbada1e`.
- The UniFi child PID remained 2911426, beneath mcp-proxy PID 2911425.
- The container start time remained 5:00:22 PM Eastern, with zero restarts.
- The gateway-managed UniFi container count stayed at zero.
- UniFi logs contained one successful global connection initialization, zero login-attempt-limit errors, and zero `Not connected to controller` errors.

The gateway health endpoint returned HTTP 200; an unauthenticated MCP request returned HTTP 401. Docker reported no host port bindings for the UniFi service. Both SSH Manager containers stayed healthy, and SSH Manager continued to execute the verification commands. All four MCP containers were healthy with zero restarts at cleanup. This verifies process and connection reuse during the test; I did not independently count controller-side login audit events.

## Cleanup and Open State

Before committing, I repeated live Compose validation and checked the deployed Compose file, Dockerfile, and UniFi catalog against the repository references. All three SHA-256 hashes matched, and all four MCP containers remained healthy with zero restarts. The first verification request used `docker-blue` as the SSH Manager server key and failed before execution; retrying with the registered key `docker_blue` succeeded with exit code 0.

I removed the superseded `unifi-secrets.env`, temporary staging directory, and build log after verification. Compose validation passed again after cleanup. No snapshot or backup copy was created. The old full-access image remains available locally; the new service uses the distinct proxy tag.

Controller configuration and credential values are unchanged. Authentication can still renew when a controller session expires or the service restarts; the fix removes per-caller process creation. The generic firewall-tool error remains unchanged. I did not add a nightly restart timer for UniFi.

The [Compose reference](../../Configuration/docker-compose.yml), [Dockerfile](../../Configuration/Dockerfile.unifi-network), [catalog](../../Configuration/catalogs/unifi-network.yaml), [credential template](../../Configuration/unifi-network.env.example), platform README, troubleshooting record, and services inventory describe the deployed state.
