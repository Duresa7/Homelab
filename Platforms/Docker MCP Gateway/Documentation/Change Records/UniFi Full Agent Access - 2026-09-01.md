# UniFi Full Agent Access

**Created:** 2026-09-01  
**Last updated:** 2026-09-25

## Outcome

I gave agents the full UniFi Network mutation surface through Executor. Read, create, update, and delete operations are enabled, and mutation calls execute without a preview-confirm round trip. Executor still exposes the lazy five-tool gateway surface, with `unifi_tool_index` for discovery and `unifi_execute` for individual calls.

The Executor connection remains personal, bearer-backed, and healthy. It has no Executor tool-policy override. I changed its description from read-only to `Full UniFi Network read, create, update, and delete access.` The integration display name and connection identity label are both `UniFi MCP`; the `unifi-mcp-gateway` integration slug and `unifiMcpGateway` callable connection name did not change.

## Diagnosis

The initial Executor probe called `unifi_create_backup` with `confirm=false`. It returned `Create is disabled by policy for system. Set UNIFI_POLICY_NETWORK_SYSTEM_CREATE=true to enable.` Three DNS probes then reproduced the same hard boundary for create, update, and delete.

The catalog carried two independent restrictions. `UNIFI_POLICY_NETWORK_CREATE`, `UNIFI_POLICY_NETWORK_UPDATE`, and `UNIFI_POLICY_NETWORK_DELETE` were all `false`, and `UNIFI_NETWORK_TOOL_PERMISSION_MODE` was `confirm`. Changing those values to `true`, `true`, `true`, and `bypass` cleared the policy errors, but a no-confirm delete still returned `requires_confirmation: true`.

UniFi Network MCP 0.29.3 resolves bypass correctly, but its permission wrapper injects `confirm=true` only when `confirm` is absent from the handler arguments. FastMCP materializes the function's default `confirm=false` before that wrapper runs, so the condition never sees an omitted key. This transport-to-wrapper mismatch was the remaining confirmation gate.

## Implementation

1. I set the network server to bypass mode and enabled its server-wide create, update, and delete policy gates.
2. I added `Dockerfile.unifi-network`, pinned to the deployed 0.29.3 upstream image and manifest digest.
3. I added a build-time patch that changes only the bypass injection. In bypass mode, mutation handlers with a `confirm` parameter now receive `confirm=true` even when FastMCP supplied the default `false`. The build fails if the expected upstream block does not match exactly once.
4. I built `homelab/unifi-network-mcp:0.29.3-full-access` on `docker-blue`, changed the catalog to that image, validated Compose, and recreated only `docker-mcp-gateway`.
5. I updated the Executor integration and connection metadata through its authenticated console and refreshed the connection tool catalog.

I created no snapshot or backup. The public upstream image, Dockerfile, catalog, and build patch reproduce the deployment. The temporary upload files, authenticated API cookie, response files, and credential-reference file were removed after use.

## Verification

- The image build resolved `unifi-network-mcp` 0.29.3 and showed the full-access bypass block in the installed permission wrapper.
- Compose validation passed, and `docker-mcp-gateway` returned healthy on the pinned Docker MCP Gateway 0.43.3 image.
- The original create, update, and delete DNS probes all reached their real handlers with no policy error and no `requires_confirmation` field. Deliberately invalid data produced validation errors or a controller `404`, so those probes changed nothing.
- I created `executor-full-access-probe.alphasecunited.com` as an A record to `192.0.2.1` without sending `confirm`, read it back with the expected value and a controller record ID, deleted it without sending `confirm`, and read the DNS collection back with the record absent.
- A fresh managed session returned system information, 35 DPI categories, and 28 DNS records. The full-access probe record was absent.
- Executor refreshed five UniFi gateway tools and reported the connection healthy. Its saved description states the full read/create/update/delete scope, its display and connection labels read `UniFi MCP`, and the Executor policy list is empty.

I retained no standalone command transcript. These observed results are the verification record.

## Open State

Full UniFi access is deliberate. Any agent that can use the personal Executor connection can change or delete controller configuration without a confirmation step from me. The gateway still redacts sensitive response fields, limits the managed container to `192.168.1.1:443`, and keeps the controller credentials outside the repository.

The local bypass overlay remains tied to upstream 0.29.3. A future UniFi MCP update must verify whether upstream has made bypass authoritative after FastMCP supplies default arguments. If it has, I will retire the overlay instead of carrying it forward.
