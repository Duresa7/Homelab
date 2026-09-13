# Deployment

**Created:** 2026-09-12  
**Last updated:** 2026-09-12  
**Implementation:** 2026-09-12  
**Verification:** 2026-09-12

I deployed MeshCentral 1.2.5 as a Compose project on `docker-blue`, CT 108 at `192.168.40.39`, and opened the one firewall path that was missing. This is a pilot against RustDesk, which keeps running on the same host. The work ran from 11:44 PM to 11:48 PM EDT. The [log](../../Evidence/Deployment%20-%202026-09-12/Logs/Deployment-and-Verification-2026-09-12.md) holds the commands, their output, and their exit codes.

## Why a container on this host

I read the live sizing before choosing a shape. `blue-server` reported 5,811 MiB of memory with 2,772 MiB available and 1,876 MiB of swap in use, against 7,168 MiB already allocated across CTs 100, 104, 107, and 108. `docker-blue` reported 1,452 MiB available inside its 2 GiB and 8.3 GiB free on a 15 GiB root filesystem.

A new LXC on that node would have added a second Debian userspace, a Wazuh agent, and a node exporter before MeshCentral started. The existing container had room for the service itself, its documented role is remote access and lightweight integrations, and it is where RustDesk already runs, so the two products sit in the same network position while I compare them. `/opt/docker` on that host already holds `executor` and `rustdesk` in the same layout, and the host runs What's Up Docker and a Portainer Edge Agent, so a container is covered by the version tracking a native install would not be.

## What I deployed

The Compose file is the upstream container documentation's definition with three local additions: the published port binds to `192.168.40.39:443` instead of every interface, `no-new-privileges` is set, and the JSON log driver is capped at three 10 MiB files. Container port 80 is not published. The tracked copy is [`Configuration/docker-compose.yml`](../../Configuration/docker-compose.yml) and it matches `/opt/docker/meshcentral/docker-compose.yml` byte for byte, MD5 `3624c1a05e08eb3d08c6b0681c6376f1` at 711 bytes.

My first write of that file used `printf '%s'` with a quoted string, which wrote the whole definition to one line with literal backslash-n sequences. The detached `docker compose pull` that followed it failed with `go-yaml load error in scanner at L1.C93: mapping values are not allowed in this context` and pulled nothing, so no container existed at that point. I rewrote the file with `printf '%b'`, confirmed 27 lines, and validated it with `docker compose config --quiet` before starting anything.

The image is `ghcr.io/ylianst/meshcentral:latest` at digest `sha256:45873f56b1221cf4c33a65c6a9a8c2ae8b503bd4f605a19f8b1527fbb80a7b6c`. I pulled and started it detached and polled the log, because an Executor integration tool call dies at 60 seconds and the pull is larger than that budget.

MeshCentral generated its `config.json` on first start with `cert` set to the placeholder `myserver.mydomain.com`, and its log confirmed it: `MeshCentral HTTPS server running on myserver.mydomain.com:443`. That name is what the server hands to agents and puts in its certificate, so I changed it to `192.168.40.39` and restarted. The log then read `MeshCentral HTTPS server running on 192.168.40.39:443` and the served certificate read `subject=CN=192.168.40.39`. I left the other generated defaults as they were: `tlsOffload: false`, `SelfUpdate: false`, `WebRTC: false`, `port: 443`, `redirPort: 80`, `NewAccounts: true`, and `localSessionRecording: true`.

The four documented volumes were created as `meshcentral_meshcentral-data`, `-files`, `-web`, and `-backups`. `curl` against `https://192.168.40.39/` from the host returned HTTP 200.

## Firewall change

Before the change, `HQ-MGT01` at `192.168.65.12` could not open TCP 443 to `192.168.40.39`. Secure Client VLAN 60 needed nothing, because it and Personal-A are both in the `Internal` zone and no block policy covers that pair. IDENTITY-A VLAN 65 is its own `AlphaSec-Identity` zone and had no rule toward Personal-A.

I created one policy, `Allow Identity to MeshCentral`, policy ID `6aa61ccb80977b56f62ce0bc`:

| Field | Value |
|---|---|
| Action | ALLOW, enabled, IPv4, TCP |
| Source | `AlphaSec-Identity`, specific IPs `192.168.65.12` and `192.168.65.20` |
| Destination | `Internal`, specific IP `192.168.40.39`, specific port 443 |
| Index | 10002 |
| Logging | Enabled |
| Response companion | Enabled at creation |
| Schedule | Always |

I set the response companion at creation rather than afterwards. On this controller, enabling `create_allow_respond` on an existing policy changes the visible policy and does not materialise the return rule, which is recorded in [its own troubleshooting record](../../../../Infrastructure/Network/UniFi/Documentation/Troubleshooting/Enabling%20create_allow_respond%20after%20policy%20creation%20did%20not%20create%20a%20return%20rule%20-%202026-07-12.md).

The first create attempt was refused for unknown arguments, because this tool takes the whole policy inside a `policy_data` object. Nothing was created by that attempt; the controller total was 83 before and 84 after the successful call, split 76 allows to eight blocks.

I scoped the source to `HQ-MGT01` and `HQ-WS001` and left both domain controllers out. Controlling an agent on a domain controller grants console access to that controller, so enrolling `HQ-DC01` or `HQ-DC02` is a separate decision.

## Verification

| Check | Before | After |
|---|---|---|
| `HQ-MGT01` to `192.168.40.39:443` | `False` | `True` |
| `HQ-DC01` to `192.168.40.39:443`, control for scope | `False` | `False` |
| `ansible_01` to `192.168.40.39:443`, service reachability within Personal-A | Not run | `open` |
| MeshCentral HTTPS from the host | Not running | HTTP 200 |
| Served certificate | Placeholder name | `subject=CN=192.168.40.39` |
| User-defined UniFi policies | 83, 75 allows and eight blocks | 84, 76 allows and eight blocks |

`HQ-DC01` is the control that matters: it sits in the same zone as the two permitted hosts and is still refused, so the policy admits the two addresses it names rather than the zone.

I could not test from `ObiPC`. SSH to `192.168.60.102` returned `EHOSTUNREACH`, as it also had earlier the same day. The VLAN 60 path is therefore reasoned from zone membership and not demonstrated. I have no Linux host on Secure or Secure Client to substitute, so that test waits for `ObiPC` to be up.

## What remains open

Nobody has claimed the site administrator account. `NewAccounts` is `true` and the server log says the next new account will be site administrator, so until I claim it any host that can reach TCP 443 can take it. Claiming the account and then setting `NewAccounts` to `false` is the first step, and it is in the root TODO.

`localSessionRecording` is `true`. Session recordings are the only part of this deployment that grows without bound, and the container's root filesystem has 7.3 GiB free.

No agent is installed and no remote desktop session has been opened. Console access while logged out, Ctrl+Alt+Delete, UAC elevation, and reconnect after reboot are all unverified on this deployment, and RustDesk stays until they pass on `HQ-WS001` and `ObiPC`.

I took no snapshot and no backup for this work, and I removed the staging directory `/tmp/mc-stage` as part of placing the Compose file.
