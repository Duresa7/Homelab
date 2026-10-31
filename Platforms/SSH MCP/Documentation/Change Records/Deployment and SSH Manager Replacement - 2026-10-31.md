# Deployment and SSH Manager Replacement

**Created:** 2026-10-31  
**Last updated:** 2026-10-31  
**Change date:** 2026-10-31  
**Status:** Complete. Six hosts were powered off and are untested; see Open Items.

I replaced SSH Manager MCP 3.8.5, which ran behind its own Docker MCP Gateway on `docker-blue`, with ssh-mcp 2.22.0 on the same host. I moved all 26 servers across under their existing names, tested the new server directly and then through Executor 2, and only then removed SSH Manager.

## Why the Shape Changed

ssh-mcp speaks Streamable HTTP with its own bearer token, so it needs neither mcp-proxy nor a Docker MCP Gateway in front. One container replaces the `ssh-manager` service and the `ssh-manager-gateway` instance, and Executor's `ssh` app talks to it directly.

The 26 servers, read from the live SSH Manager container on 2026-10-31, were one more than its records said: `ci_k3s_01` had been added on 2026-10-30.

## What I Did

1. I created the bearer token in my password manager as `SSH MCP Bearer Token - docker-blue` before anything used it, and copied it to `docker-blue` as a mode-0600 file over `scp`.
2. [install-on-docker-blue.sh](../../Scripts/install-on-docker-blue.sh) built `/opt/docker/ssh-mcp` from material already on the host, so no secret left it. It decoded the SSH key from the SSH Manager container's environment into `keys/id_ed25519` (UID 65532, mode 0400), wrote the eleven `SSH_SERVER_<NAME>_SUDO_PASSWORD` values as `SSH_MCP_<NAME>_SUDO_PASSWORD` into `ssh-mcp.env`, and copied SSH Manager's `known_hosts`. [pin-host-keys.py](../../Scripts/pin-host-keys.py) then wrote the live config with a pin for every profile. The script reported `profiles: 26`, `pins: 26`, `sudo passwords: 11` and `key bytes: 411`.
3. I built `homelab/ssh-mcp:2.22.0` and started it. It reported `Up 9 seconds (healthy)` on `192.168.40.39:8813` and logged `SSH MCP Server v2 (HTTP) listening on http://0.0.0.0:8813`.
4. `/health` returned `{"healthy":true,"configured":true}` and an unauthenticated POST returned `401`.

## Direct Test from ubuntu-dev

[fleet-smoke.mjs](../../Tests/fleet-smoke.mjs) listed 15 tools and checked every profile.

| Result | Profiles |
|---|---|
| Pass | `alpha_prod_01`, `ansible_01`, `blue_server`, `ci_k3s_01`, `docker_blue`, `docker_main`, `docker_network`, `edge_01`, `green_server`, `grey_server`, `hq_dc01`, `hq_dc02`, `media_01`, `purple_server`, `red_server`, `security_01`, `splunk_siem`, `ubuntu_dev`, `win11_dev` |
| Pass after a fix | `monitor_01` |
| Powered off | `andor_parrot_os_pc`, `app_01`, `hq_mgt01`, `obipc`, `parrot_os_mac`, `surface_pro` |

Every Linux profile that does not log in as root returned `0` from `id -u` through `privileged-command`. The Windows profiles returned `alphasec\administrator` and `win11-dev\dkadi`.

The six powered-off hosts failed with `connect EHOSTUNREACH`. SSH Manager failed on the same six with the same error at the same time, so the failure was the hosts, not the new server.

`monitor_01` failed with `SSH connection ended during handshake`, alone and in parallel. SSH Manager reached it through `ProxyJump=ansible_01`, and ssh-mcp's `via = "ansible_01"` produced `ssh_dispatch_run_fatal: Connection from 192.168.40.36 ... incomplete message [preauth]` in monitor-01's sshd log. `ansible-01` allows TCP forwarding (`allowtcpforwarding yes`, `permitopen any`). `docker-blue` reaches `192.168.73.2:22` directly, and a direct login with the ssh-mcp key against the pinned `known_hosts` returned `monitor-01` and `dkadi`. I removed `via` from the profile and reloaded with SIGHUP. The log reported `Profiles: changed monitor_01 (via)`, and the profile then passed with `id -u` returning `0`.

Further checks, all through ssh-mcp:

- `sftp-upload` of 19 bytes to `docker-blue` and `sftp-download` returned the same content, with SHA-256 `566a3a0dfa6bbad4...`, the hash of the uploaded string.
- `sleep 75; echo slept-75` completed in 75.1 seconds.
- PowerShell variables survive: `$PSVersionTable.PSVersion.ToString()` on `hq_dc01` returned `5.1.26100.33296`, and `$x = 6 * 7` on `win11_dev` returned `answer=42`.
- `reboot` and `tee /etc/systemd/system/x.service` were refused with `POLICY_DENIED: Command matches a built-in never-allowed rule`.

## Test through Executor 2

Executor's `ssh` app discovered all 15 tools. Three concurrent calls returned `grey-server` with `pve-manager/9.2.21`, `0` from `privileged-command` on `security_01`, and `HQ-DC02` from `$env:COMPUTERNAME`. `sleep 70` returned after 70,176 ms, past the 60-second limit Executor 1 had. The [Executor 2 migration](../../../Executor/Documentation/Change%20Records/Executor%202%20Migration%20-%202026-10-31.md) records the app.

## SSH Manager Removal

The retirement of SSH Manager from the Docker MCP Gateway project is recorded with that platform in [SSH Manager Retirement](../../../Docker%20MCP%20Gateway/Documentation/Change%20Records/SSH%20Manager%20Retirement%20-%202026-10-31.md).

## Open Items

- `andor_parrot_os_pc`, `app_01`, `hq_mgt01`, `obipc`, `parrot_os_mac` and `surface_pro` were off and are untested. Their profiles, keys, sudo passwords and host-key pins were carried over from SSH Manager's store, which had verified them, so I am not scheduling a separate test. If one fails when next used, rerun `PROFILES=<name> node fleet-smoke.mjs ...`; for `obipc` the Windows `whoami` should return `local-obipc`.
