# Wazuh MCP Server and Executor Integration

**Created:** 2026-09-03  
**Last updated:** 2026-09-03

## Outcome

I deployed Wazuh MCP Server 4.3.0 on `security-01` and connected it to Executor on `docker-blue`. Executor now has a healthy user connection named `localWazuh` at `tools.wazuh-mcp-server.user.localWazuh` with 41 read-only tools backed by the local Wazuh 4.14.7 Manager and Indexer. The optional `search_external_context` tool also has a You.com API credential and returns public web context through the same Executor connection.

The MCP server listens at `192.168.72.2:3000`; its Streamable HTTP endpoint is `/mcp`. Docker Blue already had a working routed path to this listener, so I did not add or widen a firewall rule. Indexer port 9200 remains loopback-only and unpublished.

## Placement and image

I placed the container on `security-01`, not `docker-blue`, because the Wazuh Indexer listens only on `127.0.0.1:9200`. The container uses host networking to reach that loopback listener and binds its own service only to the host's Security-A address.

The local image `wazuh-mcp-server-local:4.3.0-compat` starts from this pinned upstream image:

```text
ghcr.io/gensecaihq/wazuh-mcp-server:4.3.0@sha256:4b3dc5e031f79d113cdb1f14ba03620499461f0d9c713e8e34cd3a047d7319d8
```

The Compose project is `/opt/docker/wazuh-mcp-server`. It uses a read-only root filesystem, drops every Linux capability, enables `no-new-privileges`, bounds processes, memory, CPU, and JSON logs, and provides only `/tmp` and `/app/logs` as bounded temporary filesystems.

## Least-privilege Wazuh access

I created Manager API identity `wazuh-mcp-api` and assigned only Wazuh's built-in `readonly` role. A fresh token from that account successfully read `/agents`.

I created Indexer identity `wazuh-mcp-indexer` and role `wazuh_mcp_readonly`. The role has:

- `read` on `wazuh-alerts-*`;
- `read` on `wazuh-states-vulnerabilities-*`;
- `cluster_composite_ops_ro`; and
- `cluster:monitor/health`, the one additional cluster action called by MCP readiness.

The dedicated account successfully queried both index patterns over verified TLS. The MCP bearer credential has only `wazuh:read`, so the server withholds all 14 active-response, rollback, and restart tools before Executor discovers the catalog.

Credentials and signing material are stored outside the repository. The live `.env` is root-owned at mode `0600`. The repository contains only placeholders and public CA certificates.

## Compatibility problems and fixes

### Indexer cluster health returned 403

Wazuh's documented `cluster_composite_ops_ro` action group does not include `cluster:monitor/health` in this installed build. The Indexer account could search the required indexes but received HTTP `403` from `/_cluster/health`, which the MCP readiness path calls. I added only that exact action to the custom role. The same account then returned healthy cluster status and retained its two-pattern index restriction.

### Python 3.13 rejected Wazuh's Indexer CA

The upstream container's Python 3.13/OpenSSL verifier returned:

```text
CERTIFICATE_VERIFY_FAILED: CA cert does not include key usage extension
```

Wazuh's generated Indexer root CA lacks the modern X.509 `keyUsage` extension. Disabling TLS verification would have hidden the problem, so I instead patched only `WazuhIndexerClient` to clear Python 3.13's additional `VERIFY_X509_STRICT` flag. Normal chain validation and hostname verification remain enabled. `/ready` changed from Indexer `unknown` to `healthy`, and alert and vulnerability searches passed.

### The documented static API key was rejected by `/mcp`

Upstream's quick start tells remote MCP clients to send `MCP_API_KEY` as a bearer credential, but the middleware accepted only a JWT minted by `/auth/token`. That JWT expires after 24 hours, so storing it in Executor would create a daily outage.

I patched the bearer verifier to accept the configured `wazuh_` API key directly. It still uses the existing constant-time key validation and copies the key's configured scopes, which are read-only here. Unauthenticated MCP POST requests still return HTTP `401`.

### Deployment and Executor API validation errors

The first local-image bootstrap ran `docker compose pull`, which tried to pull the local image name from a registry and failed. I changed the reproducible path to `docker compose build --pull` so only the pinned base is pulled.

Executor's integration-create API rejected the normalized auth representation returned by its read API. Its log identified the required create representation as an `apiKey` template with a variable-bearing Authorization header. I resubmitted that exact schema; no partial integration had been created by the HTTP `400` response.

Executor's documented connection-inventory helper was also non-callable in the running 1.6.7 runtime. Primary `tools.search()` discovery worked and returned the exact Wazuh path, so this did not block tool invocation.

### You.com failed against the local-only CA bundle

I added the You.com API credential to the root-owned live `.env` and recreated the MCP container. Local Wazuh calls continued to pass, but the first `search_external_context` call failed with:

```text
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1032)
```

`SSL_CERT_FILE` pointed at a bundle containing only the Wazuh Manager and Indexer trust anchors. HTTPX therefore had the private Wazuh roots but not the public root needed for `ydc-index.io`. I changed the image build to append the Wazuh anchors to the base image's system CA bundle and pointed `SSL_CERT_FILE` at that combined file. I kept TLS verification enabled for Wazuh and You.com.

The first encrypted credential transfer was rejected before `.env` changed because the command-line secret reader added a trailing newline to its output file. The validation error was `You.com credential contains an unsafe line break or NUL`. I confirmed the stored value itself had no internal line break, rewrote the staging step to hold it in a variable, and emitted it without the trailing newline. Temporary plaintext, ciphertext, and keypair files were removed after each attempt.

## Executor registration

I registered integration `wazuh-mcp-server` with endpoint `http://192.168.72.2:3000/mcp` and a per-connection `Authorization: Bearer` template. User connection `localWazuh` stores the secret in Executor's encrypted provider; the integration itself has no static credential header.

The endpoint probe connected and discovered 41 tools. Refresh returned the same 41-tool read-only catalog, and Executor's connection health endpoint returned `healthy`.

## Verification

| Check | Result |
|---|---|
| Container state | `running/healthy` |
| `/health` | HTTP `200`, version 4.3.0 |
| `/ready` | HTTP `200`; Manager, Indexer, and MCP all `healthy` |
| Unauthenticated MCP POST | HTTP `401` |
| Docker Blue to `192.168.72.2:3000` | HTTP `200` |
| Direct MCP negotiation | Protocol 2025-11-25, session established |
| Direct catalog | 41 read tools, zero write tools |
| Executor connection | `healthy` |
| Executor runtime discovery | `wazuh-mcp-server.user.localWazuh.validate_wazuh_connection` found |
| Manager data path | `validate_wazuh_connection` and `get_wazuh_agents` succeeded |
| Indexer alert path | `get_wazuh_alert_summary` succeeded |
| Indexer vulnerability path | `get_wazuh_vulnerability_summary` succeeded |
| External context | `search_external_context` returned `enabled: true` with two You.com results |
| Combined trust bundle | Local Wazuh and You.com TLS calls both succeeded after the image rebuild |

Each Executor runtime call returned `executorOk=true`, `mcpIsError=false`, and one content block.

## Cleanup and remaining work

I removed the one-time SSH transfer key, remote staging directory, local secret staging directory, encrypted credential transfer, temporary asymmetric keypair, and temporary Executor session files after verification. I took no snapshot and created no backup.

No Wazuh-specific integration work remains open. The separate Executor connection-inventory helper mismatch remains unrelated to Wazuh tool operation.
