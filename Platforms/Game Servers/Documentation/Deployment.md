# Game Servers Deployment

**Created:** 2026-08-07  
**Last updated:** 2026-08-09

**Implemented:** 2026-08-07  
**Owner:** Platforms / Game Servers  
**Host:** `game-01`, LXC 123 on `green-server`, `192.168.80.30`  
**Status:** Complete. Pelican Panel v1.0.0-beta36 and Wings v1.0.0-beta27 remain the live platform. The original NeoForge workload documented below was retired, Better Realism replaced it and was later retained offline, and the current Vanilla workload is recorded in [Better Realism Shutdown and Vanilla Minecraft Deployment - 2026-08-09](Change%20Records/Better%20Realism%20Shutdown%20and%20Vanilla%20Minecraft%20Deployment%20-%202026-08-09.md).

This record preserves the original 2026-08-07 platform deployment and its troubleshooting trail. It is not the current server inventory.

## Scope

I deployed the panel, the daemon, and the first game server. I did not publish anything to the internet, did not add Valheim, and did not configure alerting.

The guest build is a separate record: [Galaxy Game-01 LXC Deployment - 2026-08-07](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Galaxy%20Game-01%20LXC%20Deployment%20-%202026-08-07.md). This file starts after that host was baselined.

## Why Pelican, and why an LXC

I wanted a web UI, per-server resource limits, a file manager and a console, so the next modpack is a few clicks instead of a hand-written Compose service. Pelican is the actively developed fork of Pterodactyl and its egg library covers every Minecraft loader plus most other game servers.

Pelican's own documentation says that with `LXC` virtualization "you will most likely be unable to run Wings", and `systemd-detect-virt` on this host returns `lxc`. That warning targets VPS customers who cannot turn on nesting. On Proxmox I control the container features, and five other guests here already run Docker the same way. I went ahead knowing a VM on green was the fallback if it fought me. It did not.

What made it work, confirmed on the host:

| Check | Result |
|---|---|
| `systemd-detect-virt` | `lxc` |
| Container features | `nesting=1,keyctl=1` |
| Docker storage driver | `overlayfs` |
| Cgroup version and driver | v2, systemd |
| Delegated cgroup controllers | `cpuset cpu io memory hugetlb pids rdma misc dmem` |
| Swap limit warning | none |

The delegated `cpu`, `memory` and `pids` controllers are the part that matters. Without them Wings cannot enforce a per-server limit, and one runaway Minecraft server takes the host with it.

## Panel

Docker Compose project at `/opt/docker/pelican-panel`, SQLite, no separate database container. The versioned copy is [Configuration/docker-compose.yml](../Configuration/docker-compose.yml).

Two things about the stock upstream Compose file needed changing.

**The `subpath: plugins` mount fails on a fresh volume.** The container refused to start with `cannot access path /var/lib/docker/volumes/pelican-panel_pelican-data/_data/plugins: no such file or directory`. Docker's `subpath` option does not create the directory it points at. I created it once with a throwaway container:

```bash
docker run --rm -v pelican-panel_pelican-data:/d alpine mkdir -p /d/plugins
```

**`DB_CONNECTION` must be set explicitly, even for SQLite.** This one only appears after the install completes. Laravel defaults the connection to sqlite in `config/database.php` through `env('DB_CONNECTION', 'sqlite')`, but the entrypoint is shell and does not read PHP config. Once `APP_INSTALLED=true`, it runs `if [ "${DB_CONNECTION}" != "sqlite" ]`, an unset variable takes the TCP branch, and the container loops on `nc: bad port ''` and `Waiting for database connection...` forever while NPM serves 502. Setting `DB_CONNECTION: sqlite` in the Compose environment fixes it. I hit this on the first restart after switching `APP_INSTALLED` to true.

**An https `APP_URL` needs `BEHIND_PROXY`.** With `APP_URL` set to the real hostname the entrypoint exited 1 with `when app url is https a lets encrypt email must be set when not behind a proxy`. Reading `/entrypoint.sh` line 76 showed the condition is `[ -z "${LE_EMAIL}" ] && [ "${BEHIND_PROXY}" != "true" ]`. Setting `BEHIND_PROXY: "true"` makes the bundled Caddy listen on `:80` with `auto_https off` and sets `ASSET_URL` from `APP_URL`, which is exactly right behind NPM. I publish only port 80 and only on the LXC address.

## Install without the web installer

Migrations run from the entrypoint only when `APP_INSTALLED=true`; on a new install the web installer does the first pass. I did it from the CLI instead, so the whole build is scriptable and leaves a readable command trail:

```bash
docker exec pelican-panel sh -c "touch /pelican-data/database/database.sqlite"
docker exec pelican-panel php artisan migrate --force --seed
docker exec pelican-panel php artisan p:user:make --email=... --username=dkadi --admin=1 --password="$(tr -d '\r\n' < /tmp/.pw)"
docker exec pelican-panel sed -i 's/^APP_INSTALLED=false/APP_INSTALLED=true/' /pelican-data/.env
```

Flipping `APP_INSTALLED` needs a `config:clear` and a container recreate to take effect. Until then the app keeps serving `/installer` from cached config, and the installer's Next button does nothing because the database is already migrated and the admin already exists. After the restart `/` redirects to `/login` and `/installer` returns 404.

The admin password was staged into a mode-0600 file, read by the shell rather than typed into the command, and shredded on the host and inside the container afterwards. No credential value appears in any command string in this record.

## Wings

Native systemd binary, not a container. Running Wings inside Docker inside an LXC adds a nesting layer for nothing, and Wings needs deep access to the Docker socket regardless.

```bash
curl -fsSL -o /usr/local/bin/wings \
  "https://github.com/pelican-dev/wings/releases/latest/download/wings_linux_amd64"
chmod u+x /usr/local/bin/wings
```

The node was created with `p:node:make`, then its configuration written straight to `/etc/pelican/config.yml` so the token never printed:

```bash
docker exec pelican-panel php artisan p:node:configuration 1 > /etc/pelican/config.yml
chmod 600 /etc/pelican/config.yml
```

Wings creates the `pelican` system user itself on first start, uid 999 gid 988, and the `pelican0` bridge interface.

### Two node settings the create command got wrong

`p:node:make` takes a listening port and a connecting port, and I set both to 8080. Behind a reverse proxy those are different numbers: Wings binds 8080, but the panel and the browser reach it on NPM's 443. Left alone, the node registered as `https://wings.alphasecunited.com:8080`, which nothing serves.

The SFTP port has the same shape of problem in reverse. The panel advertises SFTP at the node FQDN, and NPM does not proxy SFTP, so `wings.alphasecunited.com:2022` would never connect.

```
daemon_connect     = 443              (was 8080)
daemon_sftp_alias  = 192.168.80.30    (was empty, so it fell back to the FQDN)
```

SFTP works to the alias because `Allow Internal to AlphaSec-Servers` already permits it.

## The firewall rule I missed

I opened `AlphaSec-Access` to `AlphaSec-Servers` for the panel and Wings, then Wings refused to start:

```
FATAL: failed to load server configurations
error=Get "https://games.alphasecunited.com/api/remote/servers?page=0&per_page=50":
dial tcp 192.168.85.2:443: i/o timeout
```

Both processes on this host call *out* to NPM as well as receiving from it. Wings fetches its server list from the panel's public URL, and the panel calls Wings at the node FQDN. Both paths hairpin out to `192.168.85.2:443` and back. `Allow game-01 to NPM HTTPS` is the return direction, scoped to this one host and port 443.

## Verification

| Check | Result |
|---|---|
| `pct config 123` | `unprivileged: 1`, `features: keyctl=1,nesting=1` |
| Gateway reachable from the guest | `ping 192.168.80.1`, 0 percent loss |
| `docker run --rm hello-world` | succeeded, proving nesting and egress |
| Panel over HTTPS | `https://games.alphasecunited.com/` returns 200 |
| Wings over HTTPS | `https://wings.alphasecunited.com/` returns 401, which is the API rejecting an unauthenticated request rather than a 502 |
| Wings to panel | `curl` from the guest returns 302 |
| Panel to Wings | `curl` from inside the panel container returns 401 |
| `systemctl is-active wings` | `active`, SFTP listening on `0.0.0.0:2022`, API on `0.0.0.0:8080` |
| Minecraft boot | `Done (11.053s)!` on MC 26.1.2 with 103 active mods |
| Memory at idle | container 6.51 GiB of its 10.5 GiB limit, green swap `0B` used |
| Game port from Secure VLAN 50 | TCP 25565 open from `192.168.50.241` |
| Game port from Personal-A VLAN 40 | TCP 25565 open from `192.168.40.35` |
| Prometheus targets | 51 expected targets present and all UP |
| Wazuh | agent `018 game-01`, `wazuh-agent.service` active, SCA and rootcheck completed |

Trusted (10) and Secure Client (60) are not separately tested. I have no host of my own on either network to test from, and all three networks are admitted by the same zone-level `Allow Internal to AlphaSec-Servers` policy that Secure and Personal-A were proven against.

## Deploying the modpack

The pack is a ServerPackCreator build: `mods/`, `config/`, `defaultconfigs/`, plus `start.sh`, `variables.txt` and `install_java.sh`.

I used the NeoForge egg to install the loader, then extracted only the three content directories over the top:

```bash
cd /var/lib/pelican/volumes/<uuid>
unzip -o -q /root/pack262.zip 'mods/*' 'config/*' 'defaultconfigs/*'
echo 'eula=true' > eula.txt
chown -R 999:988 .
```

The pack's own start scripts are deliberately discarded. They exist to bootstrap a JDK and NeoForge on a bare machine through the ServerStarterJar, and the egg already installs the loader and provides a managed Java runtime with the `unix_args.txt` symlink the startup command reads. Keeping both would mean two things trying to install the same loader.

The 215 MB archive was pulled straight to the node from the CurseForge CDN with `curl`, then moved in with `pct push`. Not through the panel's browser uploader.

## The pack metadata is wrong in three ways

This is the part that cost the most time, so it is worth writing down. **Do not trust this pack's stated versions.** Every number below had to be derived from the mod filenames instead.

**The CurseForge label is wrong.** The file is published as `Best Vanilla World 2 Serverpack MC 26.2-1.0.0` and CurseForge tags it game version 26.2. Every mod inside is named `+mc26.1.2`. NeoForge maintains separate `26.1.x` and `26.2.x` lines, so this distinction decides which loader installs. The pack is Minecraft **26.1.2**.

**`variables.txt` is wrong.** It declares:

```
MINECRAFT_VERSION=26.1.2
MODLOADER_VERSION=21.2.1-beta
RECOMMENDED_JAVA_VERSION=25
```

NeoForge `21.2.1-beta` is the loader for Minecraft **1.21.2**, which the install proves: its `unix_args.txt` references `libraries/net/minecraft/server/1.21.2-20241022.151510/`, and ModLauncher starts with `--fml.mcVersion, 1.21.2`. That contradicts the `MINECRAFT_VERSION` two lines above it in the same file. The correct loader for MC 26.1.2 is the `26.1.2.x` line, and I used **26.1.2.94**.

**A client-only mod ships enabled.** ServerPackCreator disabled 18 client mods, including `iris`, `BetterF3`, `Controlling` and `ImmediatelyFast`, but left `sodium-neoforge-0.8.12+mc26.1.2.jar` active. Sodium is a rendering mod. NeoForge's `GraphicsBootstrapper` service loader picks it up on a dedicated server and the process dies before any world loads. Renaming it to `.disabled` fixed it, leaving 103 active mods of the 122 shipped.

The failures in order, each one masking the next:

| Loader | Java | Failure |
|---|---|---|
| 21.2.1-beta | 25 | `NoClassDefFoundError: org/lwjgl/Version`. Sodium loaded and tried to bootstrap graphics on a headless server. |
| 21.2.1-beta | 21 | `UnsupportedClassVersionError: class file version 69.0`. The mods are compiled for Java 25, so the loader's own Java version was also wrong. |
| **26.1.2.94** | **25** | `Done (11.053s)!` after disabling Sodium. Booted clean, and still refused every player: see below. |

Two benign errors remain in the log and are not worth chasing. `Only supported on OSX/BSD` is netty probing for the kqueue transport before falling back to epoll on Linux. `Expected BEGIN_OBJECT but was STRING` is one mod's config parse, caught and non-fatal.

I keep the 19 `.disabled` jars rather than deleting them, so the next pack release can be diffed against what the author actually shipped.

## A server that boots is not a server anyone can join

The 26.2 build above ran perfectly and rejected all eleven connection attempts from the first player. The server log named the reason plainly:

```
starzply_k lost connection: Incompatible client! Please use NeoForge 26.1.2.94
```

The player reported it as "GlitchCore sync config is missing", which sent me looking at GlitchCore. That was the wrong end. GlitchCore is `26.1.2.0.2` in both packs, byte for byte. A NeoForge loader mismatch fails the configuration handshake 8 ms after login, and whichever mod owns the first sync channel is what the client names. **The mod named in a client-side error is a symptom of the handshake failing, not its cause.**

The cause was that I matched the Minecraft version and ignored the release. CurseForge publishes this pack in parallel lines, and the client and server files only pair within a line:

| What | Release | Loader |
|---|---|---|
| What I deployed | Serverpack MC 26.2-1.0.0, file 8501133 | 26.1.2.94, derived by me from mod filenames |
| What the players installed | MC 26.1.2-2.1.0, file 8480538 | 26.1.2.78, pinned by the pack |

Because the 26.2 pack's `variables.txt` was unusable, I had picked a loader myself. Any `26.1.2.x` build runs that mod set, so the server booted and looked correct. Only a client proves the loader is right.

The matching serverpack is file 8480546, and its metadata is honest: `MINECRAFT_VERSION=26.1.2`, `MODLOADER_VERSION=26.1.2.78`, `RECOMMENDED_JAVA_VERSION=25`. I stopped the server, set `NEOFORGE_VERSION` to `26.1.2.78` in the panel, replaced `mods/`, `config/` and `datapacks/` from that pack, disabled Sodium again because it ships enabled there too, installed the loader, and repointed the launch symlink:

```bash
ln -sfn libraries/net/neoforged/neoforge/26.1.2.78/unix_args.txt unix_args.txt
chown -R 999:988 .
```

`unix_args.txt` is the whole switch. The startup command ends in `@unix_args.txt`, so the symlink decides which loader actually runs regardless of what the panel variable says.

One trap on the way: Wings restarted the server by itself between my `docker stop` and the symlink edit, so the next boot still logged `26.1.2.94` and I briefly read that as the change failing. Crash detection is enabled, so a stopped container comes back. Verify the loader line in a boot that starts *after* the edit, not the newest boot in the log.

Result: `NeoForge mod loading, version 26.1.2.78, for MC 26.1.2`, `Done (1.375s)!`, zero fatal errors, 103 active mods, 5.74 GiB of the 10.5 GiB limit, listening on `192.168.80.30:25565`.

Nobody had joined before the switch, so the world carried no player data and I replaced the mod set without migrating anything. That will not be true next time.

## Credentials

The panel administrator is `dkadi`, with a generated 32-character password. Neither that password nor any other credential value is recorded in this repository.

## Follow-up state

- The Fabric egg was added on 2026-08-09. The Vanilla egg was imported and deployed later that day; Paper and Valheim remain imports for the point when I need them. See [the current workload record](Change%20Records/Better%20Realism%20Shutdown%20and%20Vanilla%20Minecraft%20Deployment%20-%202026-08-09.md).
- No alert rules, because the platform has none anywhere yet.
- `check_permissions_on_boot` is still `true`. It chowns both retained server volumes on start and should be reviewed if more worlds are added.
