# PeaNUT Relocation to monitor-01

**Created:** 2026-07-26  
**Last updated:** 2026-07-28

## Date

I completed this relocation on 2026-07-26.

## Scope

I moved PeaNUT 6.0.0 off `docker-main` and onto `monitor-01`, so the UPS dashboard and `prometheus-nut-exporter` now read the same two NUT endpoints from one LXC. This was a clean rebuild, not a migration. Nothing was backed up or copied, because the entire persistent state is a 554-byte `settings.yml` that holds two NUT server entries & display preferences.

## Starting State

`peanut` had been up 3 days & healthy on `docker-main` at `192.168.40.35:8090`, one of 14 running containers on that LXC. `monitor-01` ran 6 containers in 2048 MB with 495 MB used, on Docker 29.6.2 & Compose v5.3.1, with a 16 GB rootfs at 27 percent. TCP connects from `monitor-01` to `192.168.70.13:3493` & `192.168.70.10:3493` both succeeded before I touched anything. The `.env` on `docker-main` was 130 bytes holding `WEB_USERNAME`, `WEB_PASSWORD`, & `AUTH_SECRET` at mode `0600`.

## Actions

### Step 1: Grow monitor-01 memory

`blue-server` had 8,643 MB available, so I ran `pct set 104 -memory 3072`. LXC memory is a cgroup limit, so `free -m` inside the container reported 3072 MB total without a restart. All 6 containers kept their existing uptimes.

### Step 2: Read the stored secrets

I read the three values from their stored copy and reused all three verbatim, including `AUTH_SECRET`, so existing session cookies stayed valid.

The old `.env` turned out to be CRLF, not LF. Its 130 bytes were 127 bytes of content plus 3 carriage returns. Docker Compose strips a trailing `\r` when it parses `.env`, which I confirmed by reading the running container's environment: `WEB_USERNAME` was 5 characters, `WEB_PASSWORD` 17, & `AUTH_SECRET` 64, none with a trailing CR. I wrote the replacement file LF-only at 127 bytes so the parsed values would be byte-identical. Had I copied the CRLF file blindly onto a host where Compose behaved differently, the password & the cookie-signing secret would both have gained a stray character.

I staged the file through `/home/<YOUR_ADMIN_USERNAME>`, which is mode `0700`, then used `install -o root -g root -m 0600` to place it and `shred -u` to destroy the staging copy. No secret value entered a command argument, a repository file, or captured output.

### Step 3: Build the Compose project

I created `/opt/docker/peanut` on `monitor-01` with the same layout the old host used. The Compose file came to 965 bytes against the 966 on `docker-main`; the single-byte difference is `192.168.73.2` replacing `192.168.40.35` in the port bind. I retyped `settings.yml` from the plan rather than copying it, and it hashed to SHA256 `69bd5eb272ccbcc3d2a8d21b6a8858deeafa1dc0301aa4e58c4770b48c9343d3`, matching the file on `docker-main` byte for byte.

### Step 3a: Confirm the container can write its own config

The PeaNUT image ships without a shell, so `docker exec peanut sh` fails and the runtime UID has to be read from the host. `ps` against the container PID returned UID 1000, which maps to `ansible` on `docker-main` & to `<YOUR_ADMIN_USERNAME>` on `monitor-01`. The config directory was already owned by `<YOUR_ADMIN_USERNAME>:<YOUR_ADMIN_USERNAME>`, so no `chown` was needed.

I proved writability twice. First with the image's own Node runtime, running `fs.accessSync` with `W_OK` against `/config` & `/config/settings.yml` plus a write, read-back, & unlink round trip at UID 1000. Then functionally, after the domain was cut over: I changed the temperature unit to Celsius in the web UI, watched `settings.yml` update on the host mount at 21:26:37, restarted the container, & confirmed the value survived. Setting it back to Fahrenheit returned the file to hash `69bd5eb2`, which also confirms PeaNUT's serializer produces the same bytes I typed by hand.

### Step 4: Open the firewall paths

All four UniFi changes went through the plugin's preview-then-confirm flow, & I reviewed each preview before confirming.

I added 8090 to the destination port list on `Allow NPM to monitor-01 web UIs` (`6a66570a052792cd2140588e`) & `Allow Secure to monitor-01 break-glass` (`6a665727052792cd21405892`), taking both from `3000,9090` to `3000,8090,9090`. Neither policy carried a description, so nothing was lost to the plugin's habit of dropping that field.

I created `Allow VPN Management Access to PeaNUT` (`6a66ad76052792cd214067ca`) from the `Vpn` zone, targeting the `Management Access` WireGuard network object `698cd56010cb5676c296e2d1` on subnet `10.6.0.1/24`, to `192.168.73.2` on TCP 8090 with the automatic return policy enabled. I scoped it to 8090 alone.

I created `Allow <YOUR_ADMIN_USERNAME> MacBook Air M3 to PeaNUT` (`6a66adb3052792cd214067fe`) from `192.168.10.27` to the same destination & port. The controller confirmed the client `<YOUR_ADMIN_USERNAME>-MBA-MAIN` still holds that address as a fixed reservation, so pinning the policy to it is safe.

The plan flagged one open question: my two inventory files disagreed about which zone holds Trusted (VLAN 10). The controller settled it. The Internal zone contains Management, Trusted, Personal-A, Secure, Secure Client, & AD-SERVERS, so `network-vlan.md` was right & `zone.md` was missing Trusted. I fixed `zone.md`. The laptop policy therefore sources from Internal, the same zone the Jedi PC break-glass rule already uses.

That policy points an admin laptop on a personal-device VLAN at a monitoring host. I asked for it deliberately; it isn't drift.

### Step 5: Start and verify on monitor-01

`docker compose up -d` pulled the pinned digest & started the container. It reached `healthy` rather than merely `Up`, and `curl http://192.168.73.2:8090/api/ping` returned 200 with a body of `"pong"`. `127.0.0.1:8090` refused the connection, which is correct for a host-address bind & matched the old host's behavior. `ss -ltn` showed the listener on `192.168.73.2:8090` only.

The device API returned both units over HTTP Basic auth: `ups01` on `red-server` & `ups02` on `grey-server`, each reporting model, serial, load, charge, runtime, input voltage, & `OL` line state. A NextAuth login with the stored credential issued a session for user `<YOUR_ADMIN_USERNAME>`. The container log held 6 lines with no NUT connection errors. The one line matching an error grep is a Node `DEP0169` deprecation warning about `url.parse()`, which carries the word "errors" in its text & comes from the image, not this deployment.

### Step 6: Repoint Nginx Proxy Manager

The plan reserved this step for me to do by hand, and I did it in the NPM web UI at `http://192.168.85.2:81` rather than editing `15.conf`, because NPM regenerates that file from its SQLite database. I changed proxy host 15's forward host from `192.168.40.35` to `192.168.73.2` & left everything else alone: scheme HTTP, port 8090, the `*.<YOUR_BASE_DOMAIN>` certificate, Force SSL, HTTP/2, Block Common Exploits, & WebSocket support all on, HSTS off.

`15.conf` regenerated at 21:06:15 with `set $server "192.168.73.2";`. Two nginx worker processes started in that same second, which is the proof the reload actually took rather than the file just changing on disk.

### Step 7: Remove PeaNUT from docker-main

`docker compose down` removed the container & the `peanut_default` network. I then loaded `https://peanut.<YOUR_BASE_DOMAIN>` with the old container already gone and got both UPS units, which settles any doubt about which backend was serving.

The image was referenced only by digest, so it showed with a `<none>` tag. `docker rmi brandawg93/peanut@sha256:81c0511e...` untagged it & deleted 16 layers. I didn't run `docker image prune`; this host runs 13 other containers and had 9 unrelated dangling images at the time. Removing `/opt/docker/peanut` took the `.env` with it, `ss -ltn` showed nothing on 8090, and all 13 remaining containers held their prior uptimes.

I dropped 8090 from `Allow NPM to docker-main web UIs` (`6a60fd2c2d027bb05525a873`), leaving `2283,3000,3001,6060,8080,8384,9443`. Passing the description back in the same update preserved it.

For `cluster.fw` I copied the live file to `/root/cluster.fw.bak.peanut-relocation-20260726`, built the candidate with a `sed` pattern anchored on source `192.168.40.35`, & diffed it before writing. The diff showed exactly two deletions & nothing else, taking the file from 51 lines to 49. Both `192.168.73.2` NUT accepts stayed, & both terminal `IN DROP` entries stayed last. `pve-firewall compile` passed, and after the reload `iptables-save` held exactly two TCP/3493 accepts, both sourced from `192.168.73.2`.

## Decisions

- I reused `AUTH_SECRET` instead of rotating it, so nobody gets signed out. Rotating it would have been a second change riding along on a move.
- I wrote the new `.env` LF-only rather than copying the CRLF original, after checking what the running container actually received.
- I kept the bind pinned to the host address instead of `0.0.0.0`. PeaNUT is the one service on this host behind a login, & the narrower bind is what it already had.
- I scoped both new policies to 8090 alone. Widening either to 3000 & 9090 later is a one-field edit.
- I did the NPM cutover before the teardown, so the HTTPS name never returned an error.

## Resulting Configuration

| Component | Result |
| --- | --- |
| PeaNUT | 6.0.0 pinned by digest; healthy on `192.168.73.2:8090`; Compose under `/opt/docker/peanut` on `monitor-01` |
| monitor-01 memory | 3072 MB, raised live from 2048 MB |
| Persistent state | `settings.yml`, 554 bytes, SHA256 `69bd5eb2...`, owned `<YOUR_ADMIN_USERNAME>:<YOUR_ADMIN_USERNAME>` |
| Secrets | `.env` mode `0600` root-owned, 127 bytes, LF endings, values unchanged from the stored copy |
| Public route | `peanut.<YOUR_BASE_DOMAIN>` through NPM proxy host 15 to `192.168.73.2:8090` |
| UniFi policies | 61 custom policies; 8090 added to two monitor-01 entries, removed from the docker-main entry, two new 8090 policies |
| Galaxy firewall | 49 lines, SHA256 `6847426a...` on all four nodes; two TCP/3493 accepts, both from `192.168.73.2` |
| docker-main | 13 containers, no `peanut` container, image, directory, or listener |

## Verification

The dashboard renders both units at `https://peanut.<YOUR_BASE_DOMAIN>` with the `docker-main` container deleted. Prometheus reports the `nut` job targets `up` & returns `nut_battery_charge` for `ups01` at `192.168.70.13:3493` & `ups02` at `192.168.70.10:3493`, so the exporter kept working through the `cluster.fw` edit. The temperature-unit change survived a container restart. All four Proxmox nodes hold the same firewall hash & report `enabled/running`. Every container on `docker-main` & `monitor-01` other than `peanut` itself kept its prior uptime.

I didn't pull utility power or test shutdown behavior. `nut-monitor.service` stays disabled on Red & Grey.

## Rollback Points

Rebuilding on `docker-main` means recreating the Compose file with the `192.168.40.35:8090:8080` bind, retyping the same `settings.yml`, pulling the pinned digest, re-adding 8090 to the NPM-to-`docker-main` policy, & pointing proxy host 15 back at `192.168.40.35:8090`. No data is at risk, because there is no data beyond the 554-byte config.

The pre-change `cluster.fw` was saved to `/root/cluster.fw.bak.peanut-relocation-20260726` on Grey during the work & removed afterward, once all four nodes verified. The file's prior content is recoverable from this record: it was the current 49 lines plus the two `192.168.40.35` TCP/3493 accepts above the `10.6.0.0/24` entries.

The four UniFi changes reverse independently. None of them affect Grafana, Prometheus, or SSH.

## Remaining Work

The stored credential is still titled for the old host. It works & the plan called for no edit to it, so I left the rename as a separate decision.
