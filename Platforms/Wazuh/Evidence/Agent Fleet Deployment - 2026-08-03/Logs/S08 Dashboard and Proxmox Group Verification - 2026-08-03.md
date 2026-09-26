# S08 Dashboard and Proxmox Group Verification

**Created:** 2026-08-03  
**Last updated:** 2026-08-03

**Captured:** 2026-08-03 07:46 through 07:51 EDT  
**Target:** `https://wazuh.alphasecunited.com/`; `security-01:/var/ossec/etc/shared/proxmox`  
**Mechanism:** In-app browser; SSH Manager MCP through `ansible-01`; Wazuh `agent_groups`

## Dashboard sign-in

The in-app browser opened the internal Wazuh login page. I filled the `dkadi` password straight into the form, then cleared the local value without printing it or retaining it in this record.

The dashboard authenticated as `dkadi`, selected API host `default`, & completed its API, alert-index, monitoring-index, and statistics-index checks. The Overview page reported:

```text
Active: 6
Disconnected: 0
```

## Visible agents

The Endpoints table contained six rows out of six. Each row showed status `active`:

| ID | Name | Address | Version | Groups |
|---:|---|---|---:|---|
| 004 | `app-01` | `192.168.80.10` | 4.14.6 | `default` |
| 005 | `edge-01` | `192.168.90.10` | 4.14.5 | `default`, `edge` |
| 006 | `alpha-prod-01` | `192.168.80.118` | 4.14.6 | `default` |
| 007 | `docker-blue` | `192.168.40.39` | 4.14.6 | `default` |
| 008 | `media-01` | `192.168.40.42` | 4.14.6 | `default` |
| 009 | `ansible-01` | `192.168.40.36` | 4.14.6 | `default` |

The same page reported `Pending: 0` and `Never connected: 0`. The seven requested but blocked systems had no manager identities, which matches the pre-install TCP gate.

## Proxmox group

I created manager group `proxmox` with `agent_groups -a -g proxmox -q`. The generated directory is owned by `wazuh:wazuh` with mode `0700`; its `agent.conf` is mode `0660` and passed `verify-agent-conf`.

The dashboard Groups page then showed three groups:

```text
default  6
edge     1
proxmox  0
```

The versioned deployment sets `WAZUH_AGENT_GROUP=default,proxmox` for Grey, Purple, Blue, & Red. Its syntax check passed, its host list remained eleven, & `ansible-inventory --host grey-server` returned the intended group value. The `proxmox` count remains zero until the four node enrollment path is approved and those agents are installed.
