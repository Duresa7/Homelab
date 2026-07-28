# PeaNUT Relocation to monitor-01 Plan

**Created:** 2026-07-26  
**Last updated:** 2026-07-28

**Status:** Completed on 2026-07-26. The observed results are in [PeaNUT Relocation to monitor-01 - 2026-07-26](../Change%20Records/PeaNUT%20Relocation%20to%20monitor-01%20-%202026-07-26.md).

I executed every step including the Nginx Proxy Manager cutover in Step 6, which this plan had reserved for me to do by hand after a hand-back. The Trusted (VLAN 10) zone question in Step 4 resolved to Internal, so `zone.md` was the file that needed correcting.

## Outcome

I'm moving PeaNUT off `docker-main` and onto `monitor-01`, so every UPS-facing component lives on one host. `monitor-01` already runs `prometheus-nut-exporter` against the same two NUT endpoints, so the dashboard and the metrics collector stop being split across two LXCs on two different nodes.

This is a clean rebuild, not a migration. No backup, no data copy, no export. PeaNUT's entire persistent state is a 554-byte `settings.yml` holding two NUT server entries and display preferences, with no secret in it. That file's exact contents are recorded in Step 3 below, so it gets retyped on the new host rather than moved. The three environment secrets are reused verbatim from the stored copy, so the login doesn't change and the stored copy needs no edit.

`docker-main` gets the container, image, directory, and both of its firewall openings removed once the new one is verified.

The work splits in two. An agent builds and verifies the new instance and opens the firewall paths, then stops at Step 6 and hands back. I do the Nginx Proxy Manager repoint myself. Teardown and documentation follow after that.

## Baseline verified on 2026-07-26

I checked all of this live before writing the plan. The executing agent should re-confirm anything it depends on rather than trusting these lines blindly, but nothing here should have moved.

| Fact | Value |
|---|---|
| Current host | `docker-main`, LXC 110 on `grey-server`, `192.168.40.35`, VLAN 40 |
| Target host | `monitor-01`, LXC 104 on `blue-server`, `192.168.73.2`, VLAN 73 |
| Image | `brandawg93/peanut:6.0.0@sha256:81c0511efa48728cedc7954a7ff8cff5f3069615d6925af66741029dc526f2a1` |
| Container memory in use | 154.8 MiB |
| Persistent state | `/opt/docker/peanut/config/settings.yml`, 554 bytes, no secret |
| Secrets | `WEB_USERNAME`, `WEB_PASSWORD`, `AUTH_SECRET` in `/opt/docker/peanut/.env`, mode 0600, sourced from the stored copy |
| NUT reachability from `monitor-01` | `192.168.70.13:3493` OPEN, `192.168.70.10:3493` OPEN, tested by TCP connect |
| `monitor-01` capacity | 2 cores, 2048 MB RAM (503 MB used), 16 GB rootfs at 27 percent, Docker 29.6.2, Compose v5.3.1 |
| `blue-server` headroom | 8 GB RAM available of 11 GB |
| Ansible references to PeaNUT | None. `grep -ril peanut` across `/opt/ansible` and `/home/ansible` on `ansible-01` returns nothing |

DNS needs no change. `peanut.<YOUR_BASE_DOMAIN>` is a UniFi local A record pointing at `192.168.85.2`, which is Nginx Proxy Manager, and that stays true. Only NPM's upstream changes.

The Prometheus blackbox job needs no change either. It probes `https://peanut.<YOUR_BASE_DOMAIN>/`, which keeps working once NPM is repointed. Expect that one probe to report `probe_success 0` for the length of the cutover window, which is normal and self-clearing.

## Steps

### Step 1: Grow monitor-01 memory

`monitor-01` runs 6 containers in 2048 MB with 503 MB used. PeaNUT needs about 155 MB, which fits, but the margin gets thin as the Prometheus TSDB grows. `blue-server` has 8 GB free.

- Run `pct set 104 -memory 3072` on `blue-server`. LXC memory is a cgroup limit, so it applies live with no restart and no interruption to Prometheus or Grafana.
- Confirm with `pct config 104 | grep memory` and `free -m` inside the container.
- Leave the 16 GB rootfs alone. Docker holds 2.0 GB total and 11 GB is free; the PeaNUT image adds roughly 500 MB. If rootfs use passes 70 percent at any point, grow it with `pct resize 104 rootfs +8G`.

### Step 2: Read the stored secrets

- Use the credential-retrieval skill for the mechanics. Do not improvise the CLI invocation.
- Retrieve the three existing values for `WEB_USERNAME`, `WEB_PASSWORD`, and `AUTH_SECRET`. Reuse them as-is. Reusing `AUTH_SECRET` is deliberate: it signs session cookies, so keeping it means no forced re-login.
- These values never enter a repository file, a plan, a change record, an evidence file, or captured terminal output.

### Step 3: Build the Compose project on monitor-01

Use `/opt/docker/peanut`, matching both the fleet convention and the existing `/opt/docker/cadvisor` project already on this host. The monitoring stack at `/home/<YOUR_ADMIN_USERNAME>/monitoring` stays a separate Compose project; PeaNUT isn't part of it and isn't scraped by it.

Create `/opt/docker/peanut/docker-compose.yml`:

```yaml
name: peanut

services:
  peanut:
    image: brandawg93/peanut:6.0.0@sha256:81c0511efa48728cedc7954a7ff8cff5f3069615d6925af66741029dc526f2a1
    platform: linux/amd64
    container_name: peanut
    environment:
      TZ: America/New_York
      WEB_PORT: "8080"
      WEB_USERNAME: ${WEB_USERNAME:?WEB_USERNAME must be injected}
      WEB_PASSWORD: ${WEB_PASSWORD:?WEB_PASSWORD must be injected}
      AUTH_SECRET: ${AUTH_SECRET:?AUTH_SECRET must be injected}
    volumes:
      - /opt/docker/peanut/config:/config
    ports:
      - 192.168.73.2:8090:8080
    restart: unless-stopped
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true
    healthcheck:
      test:
        - CMD
        - node
        - -e
        - "fetch('http://127.0.0.1:8080/api/ping').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 30s
```

The only line that differs from the `docker-main` file is the port bind, `192.168.40.35` becoming `192.168.73.2`. Keep the bind pinned to the host address rather than `0.0.0.0`. PeaNUT is the one service on this host behind a login, and the narrower bind is what it already had.

Create `/opt/docker/peanut/config/settings.yml` with exactly this content:

```yaml
NUT_SERVERS:
  - HOST: 192.168.70.13
    PORT: 3493
    NAME: red-server
    USERNAME: ''
    PASSWORD: ''
    DISABLED: false
  - HOST: 192.168.70.10
    PORT: 3493
    NAME: grey-server
    USERNAME: ''
    PASSWORD: ''
    DISABLED: false
INFLUX_HOST: ''
INFLUX_TOKEN: ''
INFLUX_ORG: ''
INFLUX_BUCKET: ''
INFLUX_INTERVAL: 10
DATE_FORMAT: MM/DD/YYYY
TIME_FORMAT: 12-hour
DASHBOARD_SECTIONS:
  - key: KPIS
    enabled: true
  - key: CHARTS
    enabled: true
  - key: VARIABLES
    enabled: true
DISABLE_VERSION_CHECK: false
TEMPERATURE_UNIT: fahrenheit
```

The empty `USERNAME` and `PASSWORD` fields are correct and intentional. `upsd.users` is empty on both Red and Grey, anonymous reads are permitted, and no command-capable NUT account exists anywhere in this deployment.

Write `/opt/docker/peanut/.env` with the three values from Step 2 and `chmod 0600` it. Do not version it. `Configuration/peanut.env.example` in the repository already carries the placeholder form.

### Step 3a: Confirm the container can write its own config

The PeaNUT image ships without a shell, so `docker exec peanut sh` and `docker exec peanut id` both fail. That's expected, not a fault. To find the runtime UID, read it from the host after the container starts:

```bash
ps -o user,uid -p $(docker inspect peanut --format '{{.State.Pid}}')
```

If that UID can't write `/opt/docker/peanut/config`, `chown` the directory to it. The real proof is functional: change the temperature unit in the web UI, save, restart the container, and confirm the change survived. If it didn't persist, the mount is read-only to the container and the ownership needs fixing before anything else is called done.

### Step 4: Open the firewall paths

Two of the five changes are additions that must land before cutover. All UniFi mutations go through the plugin's preview-then-confirm flow. The plugin silently drops the `description` field on policy updates, so re-read each policy after writing and restore the description through the UI if it was lost.

**Before cutover, add these:**

1. Update policy `6a66570a052792cd2140588e`, `Allow NPM to monitor-01 web UIs`. Destination port list goes from `3000,9090` to `3000,8090,9090`. This is the one change that actually unblocks the service.

2. Update policy `6a665727052792cd21405892`, `Allow Secure to monitor-01 break-glass`. Destination port list goes from `3000,9090` to `3000,8090,9090`. Source is Jedi PC at `192.168.50.241`, unchanged.

3. Create a new policy, `Allow VPN Management Access to PeaNUT`. Source zone `Vpn` (`68b788c0e9f08f1e1b2a228b`), targeting the `Management Access` WireGuard network by network object; look up its `network_id` with `unifi_list_networks`. That server is WireGuard on UDP 51822 with subnet `10.6.0.1/24`. Destination zone `<YOUR_ORG_NAME>`-Monitor (`6a665585052792cd214057cb`), IP `192.168.73.2`, TCP 8090. Enable the automatic return policy, matching every sibling. Scope it to 8090 only; widening it to 3000 and 9090 later is a one-field edit.

4. Create a new policy, `Allow <YOUR_ADMIN_USERNAME> MacBook Air M3 to PeaNUT`, source IP `192.168.10.27`, destination `192.168.73.2` TCP 8090. The machine is `<YOUR_ADMIN_USERNAME>-mb-air3`, controller name `<YOUR_ADMIN_USERNAME>-MBA-MAIN`. I confirmed on the controller on 2026-07-26 that it holds a fixed IP: `use_fixedip` is true and `fixed_ip` is `192.168.10.27`, so the policy can be pinned to that address safely.

**The Mac's source zone is the one thing left to resolve.** It sits on VLAN 10 Trusted (`network_id 68b78940e9f08f1e1b2a232b`), and my two inventory files disagree about which zone that is. `network-vlan.md` line 36 puts Trusted (10) in the Internal zone. `zone.md` line 12 lists the Internal zone as Management, Personal-A (40), Secure (50), Secure Client (60), and AD-SERVERS (65), with no VLAN 10. The V2 zone API returns empty `networks` arrays, so it can't settle this. Read the actual zone membership in the UniFi UI before creating the policy, use whatever the controller really says, and fix whichever repository file is wrong as part of Step 8.

One thing worth flagging rather than burying: `network-vlan.md` describes Trusted (10) as "personal devices I trust but that are not admin machines," and this policy points an admin workstation on that VLAN at a monitoring host. I asked for it and I want it, so build it. It's noted here so the next person reading the firewall inventory understands it's a deliberate exception and not drift.

**After cutover, remove these:**

5. Update the UniFi policy `Allow NPM to docker-main web UIs`, currently ports `2283,3000,3001,6060,8080,8090,8384,9443`. Drop `8090`, leaving seven. Its description says "NPM reaches only the eight approved Docker Main web interfaces," so the word "eight" becomes "seven". Look up the policy ID with `unifi_list_firewall_policies` filtered on `docker-main`.

6. Edit `/etc/pve/firewall/cluster.fw` on any node and delete these two rules from the `pve_mgmt` security group:

```
IN ACCEPT -source 192.168.40.35 -dest 192.168.70.10 -p tcp -dport 3493 -log nolog # PeaNUT to Grey NUT
IN ACCEPT -source 192.168.40.35 -dest 192.168.70.13 -p tcp -dport 3493 -log nolog # PeaNUT to Red NUT
```

Leave the two `192.168.73.2` NUT rules in place. Those serve both the NUT exporter and, after this move, PeaNUT itself. The file is order-sensitive and the trailing `IN DROP` entries for 22 and 8006 must stay last. Save a copy of `cluster.fw` before editing.

### Step 5: Start and verify on monitor-01

Run `docker compose up -d` from `/opt/docker/peanut`. Then confirm, in order:

- `docker ps` shows `peanut` as `healthy`, not merely `Up`. Allow the 30-second `start_period` plus one 30-second interval before judging.
- `curl -fsS -o /dev/null -w '%{http_code}' http://192.168.73.2:8090/api/ping` returns 200 from the host. Note that `127.0.0.1:8090` will refuse the connection because of the host-address bind, exactly as it did on `docker-main`. That refusal is correct behavior and is not a fault.
- The web UI enumerates both `red-server` and `grey-server`, and each returns identity, load, charge, runtime, voltage, and line state. One UPS appearing is a partial failure, not a success.
- Login with the stored credentials works.
- The temperature-unit save test from Step 3a persisted across a container restart.
- `docker logs peanut` holds no repeated connection errors against either NUT endpoint.

Both old and new containers are running at this point. That's intentional. Two readers on a NUT server is fine; `upsd` serves concurrent read clients and neither instance can issue a command.

### Step 6: Hand back for the Nginx Proxy Manager cutover

**I'm doing this one myself. The agent stops here and hands back.**

Repointing the domain is mine to do, so the agent's job ends after Step 5 passes and the Step 4 additions are in. It should report what it verified, name the direct URL, and wait. It must not touch NPM, and it must not start Step 7.

For my own reference when I get to it: proxy host ID 15 on `192.168.85.2` forwards `peanut.<YOUR_BASE_DOMAIN>` to `192.168.40.35:8090` over HTTP, and the forward host becomes `192.168.73.2`. I do it in the NPM web UI at `http://192.168.85.2:81`, not by editing `/opt/docker/nginx-proxy-manager/data/nginx/proxy_host/15.conf`, because NPM regenerates that file from its SQLite database and a hand edit gets overwritten. Scheme stays HTTP, port stays 8090, certificate ID 1, Force SSL, HTTP/2, Block Common Exploits, and WebSocket support all stay as they are, and HSTS stays disabled. Afterward `15.conf` should read `set $server "192.168.73.2";` and `https://peanut.<YOUR_BASE_DOMAIN>` should render both UPS units.

I said I'd do the domain last, so it's worth being blunt about the ordering: Step 7 tears down the old container, and the domain still points at that container until I've repointed it. Doing the NPM edit before teardown means no outage on the HTTPS name at all. Doing it strictly last, after teardown, means `peanut.<YOUR_BASE_DOMAIN>` returns a gateway error for however long I take to get to it, while `http://192.168.73.2:8090` keeps working the whole time. Either is fine and neither risks data. I just want to be choosing it rather than discovering it.

### Step 7: Remove PeaNUT from docker-main

Only after Step 5 passes and I've either completed the Step 6 cutover or explicitly said to proceed without it.

- `cd /opt/docker/peanut && docker compose down`
- Confirm nothing else on the host references the project: `docker ps -a | grep -i peanut` returns nothing.
- Remove the image by its pinned digest reference. Use the explicit `docker rmi` form. Do not run `docker image prune` on this host; it runs 15 other containers.
- Remove `/opt/docker/peanut` including the `.env`. Verify the directory is gone.
- Confirm TCP 8090 is no longer listening: `ss -ltn | grep 8090` returns nothing.
- Confirm every other container on `docker-main` is still running and healthy. Immich, Forgejo, the dashboard, Termix, Portainer, and Syncthing all live on this host and none of them should have been touched.
- Now do the two removals in Step 4, items 5 and 6.
- Re-verify NUT still answers from `monitor-01` after the `cluster.fw` edit. Removing the wrong two lines is the single most likely way to break this migration, and the symptom would be PeaNUT and the NUT exporter both going blind at once.

### Step 8: Update the documentation

Every one of these needs its `Last updated` line moved to the execution date.

| File | Change |
|---|---|
| `Platforms/PeaNUT/README.md` | Layout table row moves PeaNUT to `monitor-01`; direct fallback becomes `http://192.168.73.2:8090`; Operations paragraph keeps `/opt/docker/peanut` but names the new host |
| `Platforms/PeaNUT/Configuration/docker-compose.yml` | Port bind `192.168.40.35` becomes `192.168.73.2` |
| `Platforms/PeaNUT/Documentation/Change Records/PeaNUT Relocation to monitor-01 - 2026-07-26.md` | New record. Observed results and post-change verification, not a restatement of intent |
| `Platforms/PeaNUT/Documentation/Change Plans/PeaNUT Relocation to monitor-01 - 2026-07-26.md` | This file. Status becomes Completed with a link to the record |
| `Platforms/Nginx Proxy Manager/Configuration/internal-proxy-hosts.md` | Line 25 upstream `192.168.40.35:8090` becomes `192.168.73.2:8090`, once I've actually made the NPM change in Step 6 and not before |
| `Infrastructure/Network/UniFi/Configuration/Firewall/firewall.md` | Line 48 drops 8090 and "eight" becomes "seven"; lines 69 and 70 gain 8090; two new policy rows; policy count 59 becomes 61 |
| `Infrastructure/Network/UniFi/Configuration/Zones/zone.md` or `VLANs/network-vlan.md` | Fix whichever one contradicts the live Trusted (10) zone membership found in Step 4 |
| `Infrastructure/Compute/Galaxy/Configuration/Firewall/Galaxy Data Center Firewall.md` | Delete table rows 59 and 60; add a History entry for the removal |
| `Operations/Inventory/Galaxy/Services.md` | Line 13 drops PeaNUT from `docker-main`; line 14 adds it to `monitor-01`; the detail row at line 57 moves to the `monitor-01` section with the new address |
| `Infrastructure/Hardware/Power.md` | Line 30 address `http://192.168.40.35:8090` becomes `http://192.168.73.2:8090` |
| `TODO.md` | New completed entry |
| `Mission Control/index.html` | Board and project state in the embedded JSON data block |

Then run a case-insensitive `peanut` search across the workspace and confirm no file still claims the dashboard lives on `docker-main`.

## Stop conditions

- Stop if `monitor-01` can't reach both `192.168.70.13:3493` and `192.168.70.10:3493` before the container is built. That path is supposed to already work, and if it doesn't, something changed since 2026-07-26 and the cause needs finding first.
- Stop if the new container comes up but enumerates only one UPS. Both or neither.
- Stop before any UniFi mutation until its preview has been reviewed under the preview-and-confirm flow.
- Stop and hand back after Step 5 and the Step 4 additions. Do not touch Nginx Proxy Manager. The domain repoint is mine.
- Do not remove anything from `docker-main` until I've either finished the NPM cutover or told the agent to proceed without it.
- Do not edit `cluster.fw` without saving a copy first, and do not touch the two `192.168.73.2` NUT rules or either trailing `IN DROP`.
- Stop if any unrelated container or Proxmox guest changes state at any point.

## Rollback

Rollback is cheap right up until Step 7, and that's the reason Step 7 is last.

At the hand-back point, nothing has been rolled back because nothing has been taken away. The old stack on `docker-main` is still running, still healthy, and still serving `peanut.<YOUR_BASE_DOMAIN>`. Abandoning the move there costs one `docker compose down` on `monitor-01` and deleting `/opt/docker/peanut` on that host. If I've already repointed NPM by then, add one more edit to send proxy host 15 back to `192.168.40.35:8090`, and the dashboard returns immediately.

After Step 7, rebuilding on `docker-main` means recreating the Compose file with the `192.168.40.35:8090:8080` bind, retyping the same `settings.yml` from Step 3, pulling the pinned digest again, restoring the saved `cluster.fw`, and re-adding 8090 to the NPM-to-`docker-main` policy. That's roughly ten minutes of work and no data is at risk, because there is no data. The 554-byte config file in Step 3 is the whole of it.

The added firewall policies are independently reversible. Removing 8090 from the two updated policies and deleting the two new ones restores the exact pre-change state, and none of them affect Grafana, Prometheus, or SSH.
