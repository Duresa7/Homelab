---
name: homelab-ops
description: Work on the servers of the realm of AlphaFly through the executor MCP server's SSH tools. Use whenever someone names a host, VM, container or service, or describes a problem on one.
---

# Working on the temples of AlphaFly

## How access works

The `executor` MCP server is Executor's "SSH" connection. It exposes one app, `ssh`, through Executor's six tools:

1. `search({ query })` finds a tool's exact path, such as `tools.ssh["run-command"]`.
2. `call({ calls: { path, input } })` runs one tool. An array of calls runs them concurrently.
3. `execute` runs a JavaScript program over the same paths, for chained or filtered work. Hyphenated names need bracket notation: `tools.ssh["run-command"]`.

The ssh tools:

| Tool | Use |
|---|---|
| `list-connections` | Every profile name, user and address |
| `read-command` | Allowlisted read-only commands (ls, cat, grep, df, ...) |
| `run-command` | Any command as the profile's login user |
| `privileged-command` | The whole command under `sudo sh -c` |
| `sftp-upload`, `sftp-download`, `sftp-list` | Files |
| `open-session`, `read-session-output`, `close-session` | Long-running or interactive work |

Pass `profile` on every call. A call without one runs on `ubuntu_dev`, which is dkadi's workstation.

## Profiles

| Profile | What it is |
|---|---|
| `grey_server`, `purple_server`, `blue_server`, `red_server`, `green_server` | Proxmox nodes, logged in as root. Guests are managed with `qm` (VMs) and `pct` (LXCs) |
| `alpha_prod_01` | Game and voice host: the `minecraft` container (status with `mc-monitor status`) and TeamSpeak |
| `docker_main` | Main Docker host (root login) |
| `docker_blue` | Runs Executor and ssh-mcp, your own route in. Restarting either cuts off your access mid-task |
| `docker_network` | Nginx Proxy Manager, the reverse proxy |
| `media_01` | Media stack |
| `monitor_01` | Prometheus, Grafana and the Anubis AS alert bot |
| `security_01` | Wazuh |
| `splunk_siem` | Splunk (Rocky Linux) |
| `ansible_01` | Ansible controller (logs in as `ansible`) |
| `edge_01` | Caddy on the DMZ |
| `app_01` | Coolify host, usually stopped |
| `kube_management`, `ci_k3s_01`, `ci_k3s_02`, `ci_cache_01`, `garm_01` | Rancher and the CI runner cluster |
| `hermes_01` | Your own host. Restarting `hermes-gateway` there ends your current reply |
| `hq_dc01`, `hq_dc02`, `hq_mgt01` | Windows Server: domain controllers and the management server. The shell is PowerShell 5.1; `;` separates statements |
| `win11_dev`, `obipc`, `surface_pro`, `parrot_os_mac`, `andor_parrot_os_pc`, `ubuntu_dev` | Personal PCs and dkadi's workstation. Touch them only when asked by name |

Run `list-connections` if a name here does not match what someone says.

## Doing the work

1. Work out which profile is meant. Ask only when it is genuinely unclear.
2. Look before changing: read the current state with `read-command` or `run-command`.
3. Make the change that was asked for. Approvals are off for this bot, so no confirmation is needed.
4. Verify with a second read, then report what you ran and what the host returned.

## Limits

- ssh-mcp refuses `reboot`, `shutdown`, `halt`, `poweroff` and `eval`, and any write to `/etc/cron*`, `/etc/systemd` or an SSH key file. Say so when a request needs one of these.
- A command stops at 240 seconds. Start long work in a background session and poll it.
- Multi-line commands are refused. Upload a script with `sftp-upload` and run it by path.
