# TeamSpeak Hosting on alpha-prod-01

**Created:** 2026-05-27  
**Last updated:** 2026-07-20

I run three TeamSpeak servers, one Playit agent, & TS3 Manager on `alpha-prod-01`. This record maps the VLAN address, container ports, Playit relays, Cloudflare SRV records, ServerQuery allowlists, & Compose projects.

## VM Details

| Property | Value |
|----------|-------|
| Hostname | alpha-prod-01 |
| OS | Debian 13 |
| IP | 192.168.80.118 |
| VLAN | SERVERS-A (80) |
| Subnet | 192.168.80.0/24 |

## Architecture Diagram

```
    End Users
       |
       | UDP voice via Cloudflare SRV records
       v
+------------------+
|   <YOUR_PLAYIT_RELAY_DOMAIN>      |  TS1: <YOUR_TEAMSPEAK_RELAY_ONE_HOST>:6255
|   Free Network   |  TS2: <YOUR_TEAMSPEAK_RELAY_TWO_HOST>:53810
|   NYC, New York  |  TS3: <YOUR_TEAMSPEAK_RELAY_THREE_HOST>:49125
+------------------+
       |
       | UDP forwarded to alpha-prod-01 host ports
       | TS1 -> 9987/udp, TS2 -> 9988/udp, TS3 -> 9989/udp
       v
+-----------------------------------------------+
|              alpha-prod-01                    |
|           192.168.80.118 (VLAN 80)            |
|                                               |
|  +----------------+                          |
|  | ts-valorant-01 |                          |
|  | TeamSpeak      |                          |
|  | UDP 9987       |                          |
|  | TCP 10011      |                          |
|  | TCP 30033      |                          |
|  +----------------+                          |
|                                               |
|  +----------------+                          |
|  | ts-valorant-02 |                          |
|  | TeamSpeak      |                          |
|  | UDP 9988       |                          |
|  | TCP 10012      |                          |
|  | TCP 30034      |                          |
|  +----------------+                          |
|                                               |
|  +----------------+                          |
|  | ts-valorant-03 |                          |
|  | TeamSpeak      |                          |
|  | UDP 9989       |                          |
|  | TCP 10013      |                          |
|  | TCP 30035      |                          |
|  +----------------+                          |
|                                               |
|  +----------------+                          |
|  | playit-agent   |  Shared Playit Docker    |
|  | host network   |  project: playit-agent   |
|  +----------------+                          |
|                                               |
|  +----------------+                          |
|  | ts3-manager    |                          |
|  | Web Admin UI   |                          |
|  | Port 9000      |                          |
|  +----------------+                          |
+-----------------------------------------------+
       |
       | ServerQuery TCP 10011
       v
+------------------+
|   ts3-manager    |  http://192.168.80.118:9000
|   Local access   |  
+------------------+

DNS Chain (for end-users):
<YOUR_TEAMSPEAK_ONE_DOMAIN>
       | SRV _ts3._udp.ts01 -> <YOUR_TEAMSPEAK_RELAY_ONE_HOST>:6255
       | CNAME ts01 -> <YOUR_TEAMSPEAK_RELAY_ONE_HOST>
       v
    <YOUR_PLAYIT_RELAY_DOMAIN> -> alpha-prod-01:9987/udp

<YOUR_TEAMSPEAK_TWO_DOMAIN>
       | SRV _ts3._udp.ts02 -> <YOUR_TEAMSPEAK_RELAY_TWO_HOST>:53810
       | CNAME ts02 -> <YOUR_TEAMSPEAK_RELAY_TWO_HOST>
       v
    <YOUR_PLAYIT_RELAY_DOMAIN> -> alpha-prod-01:9988/udp

<YOUR_TEAMSPEAK_THREE_DOMAIN>
       | SRV _ts3._udp.ts03 -> <YOUR_TEAMSPEAK_RELAY_THREE_HOST>:49125
       | CNAME ts03 -> <YOUR_TEAMSPEAK_RELAY_THREE_HOST>
       v
    <YOUR_PLAYIT_RELAY_DOMAIN> -> alpha-prod-01:9989/udp
```

## DNS Records (`<YOUR_BASE_DOMAIN>`)

| Type | Name | Target | Port | Proxy |
|------|------|--------|------|-------|
| CNAME | ts01 | `<YOUR_TEAMSPEAK_RELAY_ONE_HOST>` | - | DNS only |
| SRV | _ts3._udp.ts01 | `<YOUR_TEAMSPEAK_RELAY_ONE_HOST>` | 6255 | DNS only |
| CNAME | ts02 | `<YOUR_TEAMSPEAK_RELAY_TWO_HOST>` | - | DNS only |
| SRV | _ts3._udp.ts02 | `<YOUR_TEAMSPEAK_RELAY_TWO_HOST>` | 53810 | DNS only |
| CNAME | ts03 | `<YOUR_TEAMSPEAK_RELAY_THREE_HOST>` | - | DNS only |
| SRV | _ts3._udp.ts03 | `<YOUR_TEAMSPEAK_RELAY_THREE_HOST>` | 49125 | DNS only |
| CNAME | ts-valorant-03 | `<YOUR_TEAMSPEAK_RELAY_THREE_HOST>` | - | DNS only |
| SRV | _ts3._udp.ts-valorant-03 | `<YOUR_TEAMSPEAK_RELAY_THREE_HOST>` | 49125 | DNS only |

**TeamSpeak 1 connect address:** `<YOUR_TEAMSPEAK_ONE_DOMAIN>` (no port needed)

**TeamSpeak 2 connect address:** `<YOUR_TEAMSPEAK_TWO_DOMAIN>` (no port needed)

**TeamSpeak 3 connect address:** `<YOUR_TEAMSPEAK_THREE_DOMAIN>` (no port needed)

**DNS note:** The SRV target points directly to the Playit hostname instead of the
`ts01` CNAME. SRV targets should not be aliases, and some TeamSpeak clients may
fail to connect when an SRV record points at a CNAME.

## Playit Tunnels

| TeamSpeak Server | Tunnel Name | Public Address | Local Host Port |
|------------------|-------------|----------------|-----------------|
| ts-valorant-01 | ts-valorant-01 | `<YOUR_TEAMSPEAK_RELAY_ONE_HOST>`:6255 | 127.0.0.1:9987/udp |
| ts-valorant-02 | ts-valorant-02 | `<YOUR_TEAMSPEAK_RELAY_TWO_HOST>`:53810 | 127.0.0.1:9988/udp |
| ts-valorant-03 | ts-valorant-03 | `<YOUR_TEAMSPEAK_RELAY_THREE_HOST>`:49125 | 127.0.0.1:9989/udp |

## Services

### TeamSpeak 3 (ts-valorant-01)
- **Image**: `teamspeak`
- **Container**: `ts-valorant-01`
- **License**: Free (32 slots, expires July 2027)
- **Database**: SQLite (stored in named volume `ts-data`)
- **Network mode**: host
- **Ports**:
  - `9987/udp` - Voice
  - `10011/tcp` - ServerQuery
  - `30033/tcp` - File Transfer
- **Public server listing**: Disabled
- **Virtual server name**: `<YOUR_ORG_NAME> x LYON`
- **Server password**: Enabled

### TeamSpeak 3 (ts-valorant-02)
- **Image**: `teamspeak`
- **Container**: `ts-valorant-02`
- **Compose project**: `teamspeak-02`
- **Location**: `~/teamspeak-02/docker-compose.yml`
- **Database**: SQLite (stored in named volume `ts-data` under the
  `teamspeak-02` compose project)
- **Network mode**: host
- **Ports**:
  - `9988/udp` - Voice
  - `10012/tcp` - ServerQuery
  - `30034/tcp` - File Transfer
- **Public Playit address**: `<YOUR_TEAMSPEAK_RELAY_TWO_HOST>:53810`
- **Playit local target**: `127.0.0.1:9988/udp`
- **Cloudflare connect address**: `<YOUR_TEAMSPEAK_TWO_DOMAIN>`
- **Virtual server name**: `<YOUR_ORG_NAME> United - Valorant Community`
- **Server password**: Disabled intentionally; public to users who know the address
- **Unique ID**: `<YOUR_TEAMSPEAK_ONE_UNIQUE_ID>`

### TeamSpeak 3 (ts-valorant-03)
- **Image**: `teamspeak`
- **Container**: `ts-valorant-03`
- **Compose project**: `teamspeak-03`
- **Location**: `~/teamspeak-03/docker-compose.yml`
- **Database**: SQLite (stored in named volume `ts-data` under the
  `teamspeak-03` compose project)
- **Network mode**: host
- **Ports**:
  - `9989/udp` - Voice
  - `10013/tcp` - ServerQuery
  - `30035/tcp` - File Transfer
- **Public Playit address**: `<YOUR_TEAMSPEAK_RELAY_THREE_HOST>:49125`
- **Playit local target**: `127.0.0.1:9989/udp`
- **Cloudflare connect address**: `<YOUR_TEAMSPEAK_THREE_DOMAIN>`
- **Cloudflare alternate address**: `<YOUR_TEAMSPEAK_ALTERNATE_DOMAIN>`
- **Virtual server name**: `<YOUR_ORG_NAME> United x Valorant 03`
- **Server password**: Disabled intentionally; public to users who know the address
- **Unique ID**: `<YOUR_TEAMSPEAK_THREE_UNIQUE_ID>`

### Playit Agent (playit-agent)
- **Image**: `ghcr.io/playit-cloud/playit-agent:0.17`
- **Container**: `playit-agent`
- **Compose project**: `playit-agent`
- **Location**: `~/playit-agent/docker-compose.yml`
- **Network mode**: host
- **Lifecycle**: independent from individual TeamSpeak compose projects
- **Purpose**: shared Playit agent for TeamSpeak tunnels
- **Current tunnel count**: 4 registered tunnels
- **Boot recovery**: user crontab runs
  `~/playit-agent/playit-boot-recover.sh` at reboot to wait for Docker/DNS,
  then restart TeamSpeak and `playit-agent`

### TS3 Manager (ts3-manager)
- **Image**: `joni1802/ts3-manager`
- **Host port**: `9000`
- **Container port**: `8080`
- **Access**: `http://192.168.80.118:9000`
- **Location**: `~/ts3-manager/docker-compose.yml`
- **ServerQuery targets**: use LAN/internal host ports, not public Playit DNS.
  - TeamSpeak 1: `192.168.80.118:10011`
  - TeamSpeak 2: `192.168.80.118:10012`
  - TeamSpeak 3: `192.168.80.118:10013`
- **Query allowlists**: each TeamSpeak server includes trusted local and
  management sources so TS3 Manager does not trigger ServerQuery flood
  protection.

### TeamSpeak 1 ServerQuery Allowlist
Effective allowed ServerQuery sources for `ts-valorant-01`:
```text
127.0.0.1
::1
192.168.80.118
192.168.50.241
172.18.0.1
172.19.0.2
```

`172.19.0.2` is the current TS3 Manager container address. `172.18.0.1`
is retained from the earlier bridge-mode TeamSpeak deployment.

### TeamSpeak 2 ServerQuery Allowlist
Effective allowed ServerQuery sources for `ts-valorant-02`:
```text
127.0.0.1
::1
192.168.80.118
192.168.50.241
172.21.0.1
172.19.0.2
```

`172.19.0.2` is the current TS3 Manager container address. `172.21.0.1`
is retained from the earlier bridge-mode TeamSpeak 2 deployment.

### TeamSpeak 3 ServerQuery Allowlist
Effective allowed ServerQuery sources for `ts-valorant-03`:
```text
127.0.0.1
::1
192.168.80.118
192.168.50.241
172.19.0.2
```

`172.19.0.2` is the current TS3 Manager container address.

## Docker Compose Files

### ~/teamspeak/docker-compose.yml
```yaml
services:
  teamspeak:
    image: teamspeak
    container_name: ts-valorant-01
    restart: unless-stopped
    network_mode: host
    environment:
      TS3SERVER_LICENSE: accept
    volumes:
      - ts-data:/var/ts3server

volumes:
  ts-data:
```

### ~/playit-agent/docker-compose.yml
```yaml
services:
  playit:
    image: ghcr.io/playit-cloud/playit-agent:0.17
    container_name: playit-agent
    restart: unless-stopped
    network_mode: host
    environment:
      - SECRET_KEY=${PLAYIT_SECRET_KEY}
```

### ~/playit-agent/playit-boot-recover.sh
```sh
# Runs from <YOUR_ADMIN_USERNAME>'s crontab at reboot:
# @reboot /home/<YOUR_ADMIN_USERNAME>/playit-agent/playit-boot-recover.sh
#
# Purpose:
# - Waits 90 seconds after VM/host boot
# - Waits for Docker to respond
# - Waits for <YOUR_PLAYIT_API_DOMAIN> DNS resolution
# - Restarts TeamSpeak so myTeamSpeak revocation data loads after DNS is ready
# - Starts playit-agent if missing
# - Restarts playit-agent so it registers after network/DNS is stable
# - Logs to ~/playit-agent/boot-recover.log
```

### ~/teamspeak-02/docker-compose.yml
```yaml
services:
  teamspeak:
    image: teamspeak
    container_name: ts-valorant-02
    restart: unless-stopped
    network_mode: host
    environment:
      TS3SERVER_LICENSE: accept
      TS3SERVER_DEFAULT_VOICE_PORT: 9988
      TS3SERVER_QUERY_PORT: 10012
      TS3SERVER_FILETRANSFER_PORT: 30034
    volumes:
      - ts-data:/var/ts3server

volumes:
  ts-data:
```

### ~/teamspeak-03/docker-compose.yml
```yaml
services:
  teamspeak:
    image: teamspeak
    container_name: ts-valorant-03
    restart: unless-stopped
    network_mode: host
    environment:
      TS3SERVER_LICENSE: accept
      TS3SERVER_DEFAULT_VOICE_PORT: 9989
      TS3SERVER_QUERY_PORT: 10013
      TS3SERVER_FILETRANSFER_PORT: 30035
    volumes:
      - ts-data:/var/ts3server

volumes:
  ts-data:
```

### ~/ts3-manager/docker-compose.yml
```yaml
services:
  ts3-manager:
    image: joni1802/ts3-manager
    container_name: ts3-manager
    restart: unless-stopped
    ports:
      - "9000:8080"
```

## Behavior and Constraints
- Playit is intentionally decoupled from `~/teamspeak/docker-compose.yml`; running `docker compose down` in `~/teamspeak` will stop TeamSpeak 1 but will not stop `playit-agent`
- Playit tunnels TeamSpeak UDP voice only; TCP services such as ServerQuery and file transfer stay LAN/internal only
- ts3-manager is not exposed through Playit; I access it from the local network at `http://192.168.80.118:9000`
- To add future TeamSpeak servers to ts3-manager, connect via the host VLAN 80 IP and that server's unique ServerQuery host port
- Future TeamSpeak servers must use unique host ports. TeamSpeak 2 currently uses `9988/udp`, `10012/tcp`, and `30034/tcp`; TeamSpeak 3 uses `9989/udp`, `10013/tcp`, and `30035/tcp`
- Use normal/raw ServerQuery in TS3 Manager, not SSH
- Playit free plan uses Global Anycast routing
- After Proxmox VM/host reboot, Playit can start before DNS is ready and log
  `failed to lookup address information: Try again` for
  `https://<YOUR_PLAYIT_API_DOMAIN>/agents/rundata`. The boot recovery cron job mitigates
  this by restarting only `playit-agent` after network and DNS are available.
- TeamSpeak can also start before DNS is ready and fail to download the
  myTeamSpeak ID revocation list. When this happens, clients can connect but may
  see `myTeamSpeak ID is invalid`. The boot recovery cron job restarts the
  TeamSpeak containers after DNS is available so the revocation list is loaded.
- I moved the TeamSpeak containers to `network_mode: host` on 2026-04-24 to keep
  Playit UDP voice traffic out of Docker's UDP userland proxy. That resolved
  TS3 client timeouts where packets reached the container but the client
  handshake never completed.
