# Docker MCP Gateway Runbook

**Created:** 2026-09-25  
**Last updated:** 2026-10-31

These are the operating steps for the gateway endpoint on `docker-blue` (`192.168.40.39`). SSH Manager's procedures went with it on 2026-10-31; [ssh-mcp's runbook](../../SSH%20MCP/Documentation/Runbook.md) covers SSH now. The current state is on the [platform front page](../README.md). Until 2026-09-25 these steps sat in that README.

## Routine Checks

Run on `docker-blue` with elevation:

```bash
cd /opt/docker/mcp-gateway
docker compose config --quiet
docker compose ps
docker compose logs --tail 100 gateway
docker stats docker-mcp-gateway mcp-unifi-network --no-stream
curl -fsS http://192.168.40.39:8811/health
```

The project runs two containers, `docker-mcp-gateway` and `mcp-unifi-network`. One UniFi process serves every caller.

## Updating the Gateway

The gateway stays on the 0.43.3 digest. The 2026-09-03 test of `:latest` was rolled back because it started one SSH Manager container per client session, but 0.43.3 did the same, so that test did not distinguish the two and the pin is not a compatibility requirement. An update needs `docker compose pull` and `docker compose up -d --wait`, the endpoint check, real UniFi tool calls through Executor's `unifi` app, and a count of `Client initialized` against `Running` lines in the log after several parallel calls.

## Updating the UniFi Server Image

The server image is built on `docker-blue` from the tracked Dockerfile and published to my Forgejo registry as `forgejo.alphasecunited.com/homelab-images/unifi-network-mcp:stable`. The Compose file names that tag beside the build context, so a Compose build produces the registry name directly. I moved it to the registry on 2026-09-15 in the [Dockhand registry cutover](../../Dockhand/Documentation/Change%20Records/Registry%20and%20Agent%20Cutover%20-%202026-09-15.md). Dockhand's update check compares published images and cannot build source changes, so a rebuild is always a manual step followed by a push.

UniFi Network MCP: change the pinned upstream version and digest in `Dockerfile.unifi-network`, confirm the build patch still matches exactly one permission-wrapper block, then rebuild and recreate:

```bash
cd /opt/docker/mcp-gateway
docker compose build --no-cache unifi-network
docker run --rm --network none --entrypoint python forgejo.alphasecunited.com/homelab-images/unifi-network-mcp:stable -c 'import importlib.metadata as m; print(m.version("unifi-network-mcp"))'
docker compose up -d --wait unifi-network gateway
```

If upstream makes bypass mode authoritative after FastMCP supplies default arguments, remove the overlay rather than carry a redundant patch. After the recreate, check health, bearer-token enforcement, an authenticated system-information read, an Integration API read, and a no-confirm mutation probe.

After a rebuild, I publish the image to Forgejo with Dockhand's push control, so the registry copy matches what runs. Dockhand's imported definition of this stack, at `/opt/docker/dockhand/stacks/imported/docker_blue/docker-mcp-gateway/compose.yaml` on `docker-main`, has to receive any Compose edit made on the host, because the two files do not sync.
