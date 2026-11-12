# Extra Templates and Disk Growth

**Created:** 2026-11-11  
**Last updated:** 2026-11-11

**Implementation date:** 2026-11-11, 9:00 PM to 10:00 PM Eastern  
**Status:** Complete.  
**Affected systems:** `e2b-01` (VM 113 on `grey-server`), `ubuntu-dev`, Nginx Proxy Manager on `docker-network`, UniFi local DNS

After the [deployment](Embed%20Trial%20Deployment%20-%202026-11-11.md) I probed which optional E2B features work on Embed, then added E2B's Code Interpreter and Desktop templates, secured the dashboard cookie and taught the `e2b-sandbox` skill the features that work. The builds exposed three limits Embed ships with, and filling the disk made me grow it from 120 to 300 GiB.

## 1. Feature probe

With SDK 2.63.0 against Embed 0.30.0, each in a throwaway sandbox that I killed afterwards:

| Feature | Result |
|---|---|
| Egress allow and deny lists | Works. `network={"deny_out": ["0.0.0.0/0"], "allow_out": ["pypi.org"]}`: `pypi.org` answered `200`, `github.com` failed with curl exit 35. |
| Pause on timeout, auto-resume | Works. With `lifecycle={"on_timeout": "pause", "auto_resume": True}` and a 10-second timeout, `get_info` read `paused` after 25 seconds, and `connect` resumed it with `/tmp/k` intact. |
| Volumes | `501: volumes content token signing is not supported by this deployment`. Embed's compose file sets `VOLUME_TOKEN_ENABLED: "false"`; the API needs an issuer, signing method, key and key name to turn it on. |
| Secrets | `403: Secrets are not available for this team`. `handlers/secrets.go` refuses unless a secrets backend is configured and LaunchDarkly's customer-secrets flag is on. |
| MCP gateway | `404: template 'mcp-gateway' not found`. |

The dashboard's "Create a Sandbox" button is a link to `/docs/quickstart` in `e2b-dev/dashboard` (`src/features/dashboard/sandboxes/list/table-body.tsx`, unchanged in v0.5.2), which resolves only on `e2b.dev`; here NPM logged it as `404`. The dashboard has no create action.

## 2. Dashboard cookie and sandbox memory pool

I added a second line to the dashboard patch, `DASHBOARD_COOKIE_SECURE: "true"`, because the dashboard is served over HTTPS ([compose-dashboard.patch](../../Configuration/compose-dashboard.patch)), and raised `HUGEPAGES` in `.env` from 2048 to 4096 for the 2 GiB templates. `docker compose up -d --wait` at 9:10 PM failed: `host-setup: only 2060 of 4096 2 MiB hugepages could be reserved`. The page cache held about 9 GB and only 0.5 GB was free. `host-setup` exited 1, and Compose left the recreated dashboard container stopped.

`sync`, `echo 3 > /proc/sys/vm/drop_caches` and `echo 1 > /proc/sys/vm/compact_memory` raised free memory to 4.6 GB, and the next `up` reserved 3508 pages, still short. I set `HUGEPAGES=3072`, and `up` completed at 9:11 PM. The dashboard was down from about 9:10:50 to 9:11:46 PM. The orchestrator was not restarted (its start time stayed at the deployment's), and the API stayed healthy. Afterwards: `HugePages_Total: 3072`, the dashboard container reads `DASHBOARD_COOKIE_SECURE=true`, and every service is healthy. [setup-embed.sh](../../Scripts/setup-embed.sh) and [env.additions](../../Configuration/env.additions) now carry both patches and `HUGEPAGES=3072`.

## 3. Build disk limit

[build-upstream-template.py](../../Scripts/build-upstream-template.py) builds a template from a clone of its upstream repository, using upstream's own `template.py`: `e2b-dev/code-interpreter` at `c49b78602c29e44d07e196604de515dfa6b12744` and `e2b-dev/desktop` at `91f23acaab7312e847596acc44e6f7763f56917f`. Both copy local files in, so the builds ran with `ssh -N -L 5008:127.0.0.1:5008 dkadi@192.168.80.30` open from `ubuntu-dev`, which I closed afterwards.

Code Interpreter failed twice at step 11 of 34, `pip install --no-cache-dir -r requirements.txt`, with `[Errno 28] No space left on device`. The second attempt asked for `min_free_disk_mb=10240` and its build row recorded `free_disk_size_mb 10240`, but that is the free-space target after the steps. The build config's `DiskSizeMB`, "free rootfs working space provided before build steps", comes from the team's `disk_mb` limit, and Embed's `default_limits` row holds 512. Our team (`local-dev team`) has no `project_limits` row, so `default_limits` applies; the `tiers` table is legacy and unread. At 9:17:16 PM:

```sql
update default_limits set disk_mb = 10240 where disk_mb = 512;
```

The API caches team lookups for up to five minutes, so I retried after 9:22 PM. The same row also holds `max_length_hours 1`, `concurrent_sandboxes 20`, `max_vcpu 8` and `max_ram_mb 8192`; a create with `--timeout 7200` is refused with `400: Timeout cannot be greater than 1 hours`.

## 4. Templates

| Template | Size | Result |
|---|---|---|
| `code-interpreter-v1` | 2 vCPU, 2048 MiB, `min_free_disk_mb` 10240 | Built in 7m54s, template `4xuy5aah8ryhqs0mjudq`. Upstream's size and alias, which the `e2b-code-interpreter` SDK uses by default. |
| `dev` (rebuilt) | 2 vCPU, 1024 MiB, `min_free_disk_mb` 4096 | Built in 1m3s. The first `dev` build left 396 MB free on `/`; the rebuild leaves 9.4 GB. |
| `desktop` | 4 vCPU, 2048 MiB, `min_free_disk_mb` 8192 | Built in 2m20s on the third try, template `sy8jv5fcwn5cn7ewpnrk`. Upstream uses 8 vCPU and 8192 MiB. |

The first Desktop attempt, at 4096 MiB, died at 9:30 PM when `e2b-01`'s own disk filled (section 5). The second, at 9:43 PM, failed at step 7 with `resume sandbox: failed to start FC: error loading snapshot: ... mmap memfd: cannot allocate memory`. Each step restores the previous step's snapshot while the old build VM still holds its hugepages, so a 4096 MiB build briefly needs 4096 pages from the 3072-page pool. At 2048 MiB it fits.

Tests through NPM, each sandbox killed afterwards:

- `e2b-code-interpreter` 2.11.9: create in 0.77 seconds; `run_code("x = 21\nx * 2")` returned `42`, a second call `x + 1` returned `22`, a matplotlib plot came back with `png` and `chart` results, and the JavaScript kernel printed `42`.
- `e2b-desktop` 2.7.2: create in 2.90 seconds, screen 1024 x 768; it launched `xfce4-terminal`, typed a command and pressed Enter, and the next screenshot showed the command and its output. noVNC answered `200` on port 6080 inside. `stream.get_url()` returns `https://6080-<sandbox id>.e2b.alphasecunited.com/vnc.html`, which UniFi local DNS cannot resolve.

## 5. Disk growth

At 9:30 PM the Desktop build failed with `500: Error when updating build: ERROR: could not extend file "base/5/16706_fsm": No space left on device (SQLSTATE 53100)`: `e2b-01`'s 115 GB root filesystem had filled. The failed build's cleanup brought it back to 99 GB used, 11 GB free. Template layers took 55 GB in `/var/lib/e2b/storage/templates`, one directory per cached build step, and `/orchestrator/build` held another 32 GB, a local copy of the same layers. Embed's preflight requires 20 GiB free (`PF_MIN_FREE_GIB`), so the next `up` would have refused to start. Postgres logged that one `ERROR` and no `FATAL` or `PANIC`, and both Postgres and ClickHouse answered `SELECT 1` afterwards.

I grew the disk online:

```sh
qm resize 113 scsi0 300G                          # on grey-server
growpart /dev/sda 3; pvresize /dev/sda3            # in e2b-01
lvextend -l +100%FREE -r /dev/ubuntu-vg/ubuntu-lv
```

`df` read 292 GB with 188 GB free. After the remaining builds it read 149 GB used: 84 GB of layers and 54 GB in `/orchestrator/build`. Nothing in Embed removes layers of failed or superseded builds. `fstrim -v /` returned 142.9 GiB to Grey's thin pool, and `fstrim.timer` is enabled weekly. On Grey, `local-lvm` read 67.91% used with 267,103,153 KiB available, and `vm-113-disk-1` 50.37% of 300 GiB. `qm resize` warned that the sum of thin volume sizes (830.01 GiB) exceeds the pool.

## 6. Sandbox lifetime and Desktop viewer

At 9:57:13 PM I raised the one-hour cap: `update default_limits set max_length_hours = 24 where max_length_hours = 1;`.

A browser cannot add the `E2b-Sandbox-Id` and `E2b-Sandbox-Port` headers client-proxy routes on, so I added a viewer that takes the sandbox ID from the path:

- UniFi local DNS `desktop.e2b.alphasecunited.com` (`16d6e343-18a2-4cec-b806-a041542cc524`) to `192.168.85.2`.
- NPM proxy host 42 for that name to `192.168.80.30:3002`, certificate 3, with [npm-desktop-viewer.conf](../../Configuration/npm-desktop-viewer.conf) as its advanced configuration: a regex location that sets both headers from the first path segment, port 6080, and passes WebSocket upgrades. The existing `Allow NPM to e2b-01 E2B` policy already covers port 3002.

The first version failed nginx's test, `pcre2_compile() failed: missing closing parenthesis`, because the `{15,40}` in an unquoted regex reads as a block; NPM marked only host 42 offline, and hosts 37, 39 and 40 kept answering `200`. With the regex quoted, client-proxy answered `400` and logged `invalid host` for `desktop.e2b.alphasecunited.com`: it rejects that Host before reading the routing headers. Sent straight to client-proxy with the headers and its default Host, the same request returned `200`. The location now sends `Host: sandbox.e2b.alphasecunited.com`.

With a Desktop sandbox running `stream.start()`, `https://desktop.e2b.alphasecunited.com/<id>/vnc.html` returned `200` with title `E2B VNC`, `app/ui.js` `200`, and a WebSocket upgrade on `/<id>/websockify` `101 Switching Protocols`. The page to open is `/<id>/vnc.html?autoconnect=1&resize=scale&path=<id>/websockify`. noVNC runs without a password, so anyone who reaches NPM and knows a sandbox's ID can watch and control it.

## 7. Skill

The [e2b-sandbox skill](../../Configuration/skills/e2b-sandbox/SKILL.md) now lists the four templates, the 24-hour cap, the small in-memory `/tmp`, egress allow lists through the SDK, `--lifecycle.ontimeout pause --lifecycle.autoresume`, how to use the Code Interpreter and Desktop SDKs, and the viewer address.

## Left open

- **Layer storage grows with every build.** Three templates and their failed attempts used about 140 GB. Before more builds, I need a cleanup method that keeps the layers live templates depend on.
- **Grey's thin pool.** `e2b-01` can grow to 300 GiB, and the pool had 267 GB free afterwards.
