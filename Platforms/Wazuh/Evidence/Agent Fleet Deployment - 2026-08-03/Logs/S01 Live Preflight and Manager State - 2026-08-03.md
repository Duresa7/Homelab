# S01 Live Preflight and Manager State

**Created:** 2026-08-03  
**Last updated:** 2026-08-03

**Captured:** 2026-08-03 02:26 through 02:31 EDT  
**Targets:** `security-01`, 11 requested endpoints, `app-01`, & `edge-01`  
**Mechanism:** SSH Manager MCP; Bash through one-shot SSH commands; privileged manager checks through `ansible-01`

## Commands

```bash
systemctl is-enabled wazuh-manager wazuh-indexer wazuh-dashboard
systemctl is-active wazuh-manager wazuh-indexer wazuh-dashboard
ss -lnt | grep -E ':(443|1514|1515|55000|9200)[[:space:]]'
dpkg-query -W wazuh-manager
sudo /var/ossec/bin/agent_control -l
sudo /var/ossec/bin/wazuh-control status
timeout 4 bash -c '>/dev/tcp/192.168.72.2/1514'
timeout 4 bash -c '>/dev/tcp/192.168.72.2/1515'
```

## Manager output

```text
HOST=wazuh-01
OS=ubuntu 24.04
WAZUH_PACKAGE=4.14.6-1
enabled
enabled
enabled
active
active
active
LISTEN 0 511  0.0.0.0:443   0.0.0.0:*
LISTEN 0 128  0.0.0.0:1514  0.0.0.0:*
LISTEN 0 128  0.0.0.0:1515  0.0.0.0:*
LISTEN 0 2048 0.0.0.0:55000 0.0.0.0:*

ID: 000, Name: wazuh-01 (server), IP: 127.0.0.1, Active/Local
ID: 004, Name: app-01, IP: any, Active
ID: 005, Name: edge-01, IP: any, Active

WAZUH_VERSION="v4.14.6"
WAZUH_REVISION="rc2"
WAZUH_TYPE="server"
```

`wazuh-authd`, `wazuh-remoted`, `wazuh-analysisd`, `wazuh-db`, `wazuh-apid`, & the expected supporting daemons reported running. The manager command exited `0`.

## Endpoint output

| Host | Package before change | TCP 1514 | TCP 1515 | Result |
|---|---|---:|---:|---|
| `monitor-01` | absent | timeout `124` | timeout `124` | blocked |
| `docker-network` | absent | timeout `124` | timeout `124` | blocked |
| `docker-blue` | absent | `0` | `0` | reachable |
| `alpha-prod-01` | absent | `0` | `0` | reachable |
| `kasm-01` | absent | timeout `124` | timeout `124` | blocked |
| `media-01` | absent | `0` | `0` | reachable |
| `ansible-01` | absent | `0` | `0` | reachable |
| `grey-server` | absent | timeout `124` | timeout `124` | blocked |
| `purple-server` | absent | timeout `124` | timeout `124` | blocked |
| `blue-server` | absent | timeout `124` | timeout `124` | blocked |
| `red-server` | absent | timeout `124` | timeout `124` | blocked |
| `app-01` | `4.14.6-1` | `0` | `0` | active |
| `edge-01` | `4.14.5-1` | `0` | `0` | active |

Every SSH command returned structured success. The TCP tests changed no endpoint configuration.

