# Docker MCP Gateway Runbook

**Created:** 2026-09-25  
**Last updated:** 2026-09-25

These are the operating steps for the two gateway endpoints on `docker-blue` (`192.168.40.39`). The current state is on the [platform front page](../README.md). Until 2026-09-25 these steps sat in that README.

## Routine Checks

Run on `docker-blue` with elevation:

```bash
cd /opt/docker/mcp-gateway
docker compose config --quiet
docker compose ps
docker compose logs --tail 100 gateway
docker compose logs --tail 100 ssh-manager-gateway
docker stats docker-mcp-gateway ssh-manager-mcp-gateway --no-stream
curl -fsS http://192.168.40.39:8811/health
curl -fsS http://192.168.40.39:8812/health
```

One `mcp-ssh-manager` process serves every caller. That keeps its pooled SSH connections, `ssh_session_*` interactive shells, tunnels and history shared across calls. The gateway holds one client session to it per Executor session, but those are HTTP sessions against one process, so no container accumulates:

```bash
docker ps --filter label=docker-mcp-name=ssh-manager   # expected: none
docker compose ps ssh-manager                          # expected: one, healthy
curl -fsS http://127.0.0.1:8080/status                  # from inside the container
```

Before the 2026-09-03 cutover the gateway kept one managed container per client session and released it only when the client closed that session, which Executor never does. The count reached 22 containers and 192 of the gateway's 256 processes on 2026-09-03, and 27 containers exhausted it on 2026-09-02. The [troubleshooting record](Troubleshooting/Managed%20SSH%20Manager%20Containers%20Accumulated%20Under%20long-lived%20-%202026-09-03.md) holds that diagnosis.

## Nightly SSH Manager Restart

Executor never signals the end of a session, so nothing restarts SSH Manager on its own. The systemd timer [mcp-ssh-manager-restart.timer](../Configuration/systemd/mcp-ssh-manager-restart.timer) restarts the service every day at 4 AM Eastern, a schedule I set on 2026-09-03. The restart takes about a second. The gateway is not touched and its forwarded sessions survive, and any interactive session or tunnel left open is cleared. The same restart by hand:

```bash
cd /opt/docker/mcp-gateway
docker compose restart ssh-manager          # or: systemctl start mcp-ssh-manager-restart.service
systemctl list-timers mcp-ssh-manager-restart.timer
```

## Updating the Gateway

The gateway stays on the 0.43.3 digest. The 2026-09-03 test of `:latest` was rolled back because it started one SSH Manager container per client session, but 0.43.3 did the same, so that test did not distinguish the two and the pin is not a compatibility requirement. An update needs `docker compose pull` and `docker compose up -d --wait`, both endpoint checks, real UniFi and SSH tool calls, and a count of `Client initialized` against `Running` lines in the log after several parallel calls.

## Updating the Two Server Images

Both server images are built on `docker-blue` from the tracked Dockerfiles and published to my Forgejo registry as `forgejo.alphasecunited.com/homelab-images/unifi-network-mcp:stable` and `forgejo.alphasecunited.com/homelab-images/mcp-ssh-manager:stable`. The Compose file names those tags beside each build context, so a Compose build produces the registry name directly. I moved them to the registry on 2026-09-15 in the [Dockhand registry cutover](../../Dockhand/Documentation/Change%20Records/Registry%20and%20Agent%20Cutover%20-%202026-09-15.md). Dockhand's update check compares published images and cannot build source changes, so a rebuild is always a manual step followed by a push.

UniFi Network MCP: change the pinned upstream version and digest in `Dockerfile.unifi-network`, confirm the build patch still matches exactly one permission-wrapper block, then rebuild and recreate:

```bash
cd /opt/docker/mcp-gateway
docker compose build --no-cache unifi-network
docker run --rm --network none --entrypoint python forgejo.alphasecunited.com/homelab-images/unifi-network-mcp:stable -c 'import importlib.metadata as m; print(m.version("unifi-network-mcp"))'
docker compose up -d --wait unifi-network gateway
```

If upstream makes bypass mode authoritative after FastMCP supplies default arguments, remove the overlay rather than carry a redundant patch. After the recreate, check health, bearer-token enforcement, an authenticated system-information read, an Integration API read, and a no-confirm mutation probe.

SSH Manager has no upstream image and tracks upstream `latest`:

```bash
cd /opt/docker/mcp-gateway
docker compose build --no-cache ssh-manager
docker run --rm --entrypoint sh forgejo.alphasecunited.com/homelab-images/mcp-ssh-manager:stable -c 'npm ls -g --depth=0 | grep mcp-ssh-manager'
docker compose up -d --force-recreate ssh-manager-gateway
```

I record the resolved version, then verify with an `ssh_list_servers` call and one `ssh_execute` against a reachable host.

After either rebuild, I publish the image to Forgejo with Dockhand's push control, so the registry copy matches what runs. Dockhand's imported definition of this stack, at `/opt/docker/dockhand/stacks/imported/docker_blue/docker-mcp-gateway/compose.yaml` on `docker-main`, has to receive any Compose edit made on the host, because the two files do not sync.

## Adding an SSH Manager Server

The live service reads its server definitions from resolved environment settings in the root-owned `/opt/docker/mcp-gateway/docker-compose.yml`. A new server goes into that file and into Dockhand's imported definition. A Windows host needs every host key type it offers enrolled in `known_hosts`, because the client may negotiate a type other than ed25519. An operating system reinstall regenerates those keys, so the host's lines are replaced, not appended to. [ObiPC Workstation Join - 2026-09-11](../../Active%20Directory/Documentation/Change%20Records/ObiPC%20Workstation%20Join%20-%202026-09-11.md) and [ObiPC Rebuild and Rejoin - 2026-09-18](../../Active%20Directory/Documentation/Change%20Records/ObiPC%20Rebuild%20and%20Rejoin%20-%202026-09-18.md) are the worked examples.
