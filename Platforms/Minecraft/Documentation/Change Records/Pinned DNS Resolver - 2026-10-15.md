# Pinned DNS resolver

**Created:** 2026-10-15  
**Last updated:** 2026-10-15

On 2026-10-15 I pinned the `minecraft` container's DNS server to `192.168.80.1` in its Compose definition. A slow boot of `alpha-prod-01` can no longer leave the container without an external resolver. This closes the open item from the [Purple NIC outage](../../../../Security/Incidents/Galaxy/Purple%20Server%20NIC%20Transmit%20Hang%20-%202026-10-14.md#minecraft-inherited-an-empty-external-resolver-list-at-boot).

## Why

Docker copies the host's resolvers into a container once, when it starts the container. Minecraft hit the same boot race twice on 2026-10-15:

- At 12:37 AM, after the outage power cycle.
- At 9:08 AM, after the [offload verification reboot](../../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/nic0%20Offloads%20Disabled%20on%20Purple,%20Green%20and%20Red%20-%202026-10-15.md#purples-guests).

Both times the container started about four seconds before Alpha wrote `/etc/resolv.conf`, so its resolver file read `# NO EXTERNAL NAMESERVERS DEFINED`. It could not resolve Mojang's authentication names until I restarted it. Online-mode logins depend on those names.

This is the same fix I applied to the TeamSpeak collector on 2026-08-27 ([record](../../../Teamspeak%20Hosting/Documentation/Change%20Records/Collector%20DNS%20Failure%20After%20a%20Boot%20Race%20-%202026-08-27.md)). I chose it over adding Minecraft to the TeamSpeak boot-recovery script. A pinned server removes the dependency on the host file at start time, whereas the script only repairs the container after the race. `192.168.80.1` is the resolver Alpha itself uses.

## What changed

Two lines under the `minecraft` service:

```yaml
    ports:
      - "25565:25565/tcp"
    dns:
      - 192.168.80.1
```

I updated all three copies of the definition to the same bytes, SHA-256 `84f0b50aa8eca298853cafb057600669d738f951edb6a9d9a037af939cf46b63`. Before the change, all three were identical at `34b6f49e959e45a80bec5775ffb30e62b4014ea0ab2a5165bda2f7208a9855c3`.

- Dockhand's saved definition on `docker-main`, `/opt/docker/dockhand/stacks/alpha_prod_01/minecraft/compose.yaml`. Dockhand's `stack_sources` row for the stack points at this file and holds no copy of the Compose content, so writing the file is the same as saving the stack in Dockhand.
- The runtime file on `alpha-prod-01`, `/opt/docker/hawser/stacks/minecraft/compose.yaml`.
- The repository [Compose reference](../../Configuration/compose.yaml).

I wrote the files over SSH rather than through Dockhand's web interface or API, because this session had no Dockhand login. Each host keeps its original as `/root/minecraft-compose.pre-dns-2026-10-15.yaml`. `docker compose config -q` passed on Alpha.

The LAN status probe showed 0 of 20 players at 9:18:56 AM. At 9:19:01 AM I ran `docker compose -p minecraft up -d --no-build --pull never` in the runtime directory on Alpha. That recreated the container from the existing image. The project, working-directory and config-file labels are the same as Dockhand's deployment, so Dockhand still sees the same stack. Minecraft was unavailable for about 12 seconds.

## Verification

- The container was healthy at 9:19:18 AM, with restart count 0 and `HostConfig.Dns` `[192.168.80.1]`.
- Its resolver file reads:

  ```text
  nameserver 127.0.0.11
  # ExtServers: [192.168.80.1]
  # Overrides: [nameservers]
  ```

  `Overrides: [nameservers]` means Docker took the server from the Compose file, not the host's file. Before this change the line read `# ExtServers: [host(192.168.80.1)]` after a restart, or `# NO EXTERNAL NAMESERVERS DEFINED` after the boot race.
- `sessionserver.mojang.com`, `api.minecraftservices.com` and `discovery.minecraftservices.com` all resolve inside the container. The new container's log has no `UnknownHostException`.
- At 9:19:13 AM the log shows `Preparing level "world"` and `Done (0.220s)`, loading the existing world rather than generating a new one.
- At 9:19:24 AM, server-list pings on the LAN and through the Cloudflare SRV record and Playit both returned 26.3 / 777 / 0/20 with pong OK.

## Not yet tested

I have not rebooted `alpha-prod-01` since the change. After its next boot, the resolver file should show `Overrides: [nameservers]` and the three names should resolve without a restart. An authenticated player join also remains untested.

## Rollback

Delete the two `dns:` lines from both live files, or copy each host's backup back if nothing else has changed. Then run `docker compose -p minecraft up -d` in `/opt/docker/hawser/stacks/minecraft` on Alpha, and revert the repository reference.
