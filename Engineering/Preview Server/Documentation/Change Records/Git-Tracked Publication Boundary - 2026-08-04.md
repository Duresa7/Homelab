# Git-Tracked Publication Boundary

**Created:** 2026-08-04  
**Last updated:** 2026-08-04

**Implementation date:** 2026-08-04

## What Changed

I replaced the `Guides` and `Assets` folder allowlist with membership in `git ls-files -z`. The server refreshes that list on every request. This costs one local git process per request, but a tracking change takes effect immediately and cannot leave an untracked file readable until the server restarts. A failed git query returns HTTP 500 without opening a file.

I retained the loopback-only bind, the resolved-path re-check after `path.resolve`, dotfile rejection, the informational `/` response instead of a default page, file-only serving, and `cache-control: no-store`. I updated the README and added a dated note to the 2026-07-25 incident report without changing its history or timeline.

## Verification

`node --check` returned exit code 0 with no output.

Before starting the server, I confirmed that the ignored Documentation Standard existed and that `git check-ignore -v` matched its root ignore rule. I created `preview-untracked-verification.txt`, confirmed that it existed, that `git ls-files` returned no path for it, and that `git status --short` reported it with `??`.

The request checks returned these status codes:

| Request | Status |
|---|---:|
| Tracked guide, `/Guides/README.md` | 200 |
| Tracked screenshot embedded by `Guides/Galaxy-Proxmox-Cluster.md`, `S02-Docker-Network-LXC-Created-2026-07-10.jpg` | 200 |
| Tracked diagram, `/Assets/Diagrams/galaxy-cluster.svg` | 200 |
| Existing ignored Documentation Standard | 404 |
| Existing untracked `preview-untracked-verification.txt` | 404 |
| `..` traversal from `Guides` into the ignored Documentation Standard | 404 |
| Tracked dotfile, `/.gitignore` | 404 |
| `/`, the informational response with no default file | 200 |

The root response identified `git ls-files` as the serving rule and reported `currently visible: 874 files`.

`netstat -ano` showed one listener while the checks ran:

```text
TCP    127.0.0.1:8123         0.0.0.0:0              LISTENING       11444
```

After shutdown, the listener check returned `post_stop_listener_count=0`.

I replayed the 100 guide references that the former folder allowlist rejected. Each reference was requested from the running server.

| Guide | HTTP 200 |
|---|---:|
| `Ansible-SSH-Identity-Automation.md` | 6/6 |
| `Galaxy-Proxmox-Cluster.md` | 10/10 |
| `Immich-Storage-Migration.md` | 1/1 |
| `Linux-Host-Baseline.md` | 3/3 |
| `Media-Stack.md` | 13/13 |
| `NetBird.md` | 11/11 |
| `Nginx-Proxy-Manager.md` | 8/8 |
| `Portainer.md` | 2/2 |
| `Prometheus.md` | 6/6 |
| `README.md` | 2/2 |
| `SSH-Key-Lifecycle.md` | 3/3 |
| `Security-Incident-Response.md` | 4/4 |
| `Splunk.md` | 12/12 |
| `TeamSpeak.md` | 1/1 |
| `UniFi-Network.md` | 11/11 |
| `Wazuh.md` | 7/7 |
| **Total** | **100/100** |

The replay returned `reference_status_200=100` and `reference_non_200=0`, so it exposed no broken guide reference and produced no separate documentation finding.

## What Remains Open

No implementation or documentation finding remains open. I deleted the temporary untracked file and stopped the server.

One thing to know if this file changes again: `fs.statSync` follows symbolic links, so a tracked symlink pointing outside the repository would be served through it. The repository contains zero tracked symlinks today, which I confirmed with `git ls-files -s` against mode `120000`, so nothing exploits that now. Anyone adding the first tracked symlink should re-check this.
