# alpha-prod-01 Infrastructure Document

**Created:** 2026-05-27  
**Last updated:** 2026-07-17

**REDACTED_PRIVATE_ORG_LABEL United — Secure by design. United by purpose.**

---

## VM Details

| Property | Value |
|----------|-------|
| Hostname | alpha-prod-01 |
| OS | Debian 13 |
| IP | 192.168.80.118 |
| VLAN | SERVERS-A (80) |
| Subnet | 192.168.80.0/24 |

---

## Architecture Diagram

```
    End Users
       |
       | UDP voice via Cloudflare SRV records
       v
+------------------+
|   REDACTED_CUSTOM_DOMAIN_018      |  TS1: REDACTED_CUSTOM_DOMAIN_009:6255
|   Free Network   |  TS2: REDACTED_CUSTOM_DOMAIN_015:53810
|   NYC, New York  |  TS3: REDACTED_CUSTOM_DOMAIN_010:49125
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
REDACTED_CUSTOM_DOMAIN_022
       | SRV _ts3._udp.ts01 -> REDACTED_CUSTOM_DOMAIN_009:6255
       | CNAME ts01 -> REDACTED_CUSTOM_DOMAIN_009
       v
    REDACTED_CUSTOM_DOMAIN_018 -> alpha-prod-01:9987/udp

REDACTED_CUSTOM_DOMAIN_023
       | SRV _ts3._udp.ts02 -> REDACTED_CUSTOM_DOMAIN_015:53810
       | CNAME ts02 -> REDACTED_CUSTOM_DOMAIN_015
       v
    REDACTED_CUSTOM_DOMAIN_018 -> alpha-prod-01:9988/udp

REDACTED_CUSTOM_DOMAIN_024
       | SRV _ts3._udp.ts03 -> REDACTED_CUSTOM_DOMAIN_010:49125
       | CNAME ts03 -> REDACTED_CUSTOM_DOMAIN_010
       v
    REDACTED_CUSTOM_DOMAIN_018 -> alpha-prod-01:9989/udp
```

---

## DNS Records (REDACTED_CUSTOM_DOMAIN_001)

| Type | Name | Target | Port | Proxy |
|------|------|--------|------|-------|
| CNAME | ts01 | REDACTED_CUSTOM_DOMAIN_009 | - | DNS only |
| SRV | _ts3._udp.ts01 | REDACTED_CUSTOM_DOMAIN_009 | 6255 | DNS only |
| CNAME | ts02 | REDACTED_CUSTOM_DOMAIN_015 | - | DNS only |
| SRV | _ts3._udp.ts02 | REDACTED_CUSTOM_DOMAIN_015 | 53810 | DNS only |
| CNAME | ts03 | REDACTED_CUSTOM_DOMAIN_010 | - | DNS only |
| SRV | _ts3._udp.ts03 | REDACTED_CUSTOM_DOMAIN_010 | 49125 | DNS only |
| CNAME | ts-valorant-03 | REDACTED_CUSTOM_DOMAIN_010 | - | DNS only |
| SRV | _ts3._udp.ts-valorant-03 | REDACTED_CUSTOM_DOMAIN_010 | 49125 | DNS only |

**TeamSpeak 1 connect address:** `REDACTED_CUSTOM_DOMAIN_022` (no port needed)

**TeamSpeak 2 connect address:** `REDACTED_CUSTOM_DOMAIN_023` (no port needed)

**TeamSpeak 3 connect address:** `REDACTED_CUSTOM_DOMAIN_024` (no port needed)

**DNS note:** The SRV target points directly to the Playit hostname instead of the
`ts01` CNAME. SRV targets should not be aliases, and some TeamSpeak clients may
fail to connect when an SRV record points at a CNAME.

---

## Credentials



> **Credentials.** All ServerQuery passwords, API keys, ServerAdmin privilege keys, and server passwords below are stored in 1Password — item **"REDACTED_1PASSWORD_ITEM_TITLE_003"** in the `REDACTED_1PASSWORD_VAULT` vault. These credentials were last rotated on 2026-07-17.

### TeamSpeak 1 ServerQuery
| Field | Value |
|-------|-------|
| Container | ts-valorant-01 |
| Login | serveradmin |
| Password | *(stored in 1Password)* |
| API Key | *(stored in 1Password)* |

### TeamSpeak 1 ServerAdmin Privilege Key
```
*(stored in 1Password)*
```
*(Used once on first connect to claim admin — already claimed)*

### TeamSpeak 1 Community Access
| Field | Value |
|-------|-------|
| Connect Address | REDACTED_CUSTOM_DOMAIN_022 |
| Server Password | *(stored in 1Password)* |

### TeamSpeak 2 ServerQuery
| Field | Value |
|-------|-------|
| Container | ts-valorant-02 |
| Login | serveradmin |
| Password | *(stored in 1Password)* |
| API Key | *(stored in 1Password)* |

### TeamSpeak 2 ServerAdmin Privilege Key
```
*(stored in 1Password)*
```
*(Generated at first startup; already claimed.)*

### TeamSpeak 2 Community Access
| Field | Value |
|-------|-------|
| Connect Address | REDACTED_CUSTOM_DOMAIN_023 |
| Server Password | None intentionally configured; public to users who know the address |

### TeamSpeak 3 ServerQuery
| Field | Value |
|-------|-------|
| Container | ts-valorant-03 |
| Login | serveradmin |
| Password | *(stored in 1Password)* |
| API Key | *(stored in 1Password)* |

### TeamSpeak 3 ServerAdmin Privilege Key
```
*(stored in 1Password)*
```
*(Generated at first startup; not confirmed claimed.)*

### TeamSpeak 3 Community Access
| Field | Value |
|-------|-------|
| Connect Address | REDACTED_CUSTOM_DOMAIN_024 |
| Alternate Address | REDACTED_CUSTOM_DOMAIN_021 |
| Server Password | None intentionally configured; public to users who know the address |

### Playit Tunnels
| TeamSpeak Server | Tunnel Name | Public Address | Local Host Port |
|------------------|-------------|----------------|-----------------|
| ts-valorant-01 | ts-valorant-01 | REDACTED_CUSTOM_DOMAIN_009:6255 | 127.0.0.1:9987/udp |
| ts-valorant-02 | ts-valorant-02 | REDACTED_CUSTOM_DOMAIN_015:53810 | 127.0.0.1:9988/udp |
| ts-valorant-03 | ts-valorant-03 | REDACTED_CUSTOM_DOMAIN_010:49125 | 127.0.0.1:9989/udp |

---

## Services

### TeamSpeak 3 (ts-valorant-01)
- **Image**: `teamspeak`
- **Container**: `ts-valorant-01`
- **License**: Free (32 slots, expires July 2027)
- **Database**: SQLite (stored in named volume `ts-data`)
- **Network mode**: host
- **Ports**:
  - `9987/udp` — Voice
  - `10011/tcp` — ServerQuery
  - `30033/tcp` — File Transfer
- **Public server listing**: Disabled
- **Virtual server name**: `REDACTED_PRIVATE_ORG_LABEL x LYON`
- **Server password**: Enabled *(stored in 1Password)*

### TeamSpeak 3 (ts-valorant-02)
- **Image**: `teamspeak`
- **Container**: `ts-valorant-02`
- **Compose project**: `teamspeak-02`
- **Location**: `~/teamspeak-02/docker-compose.yml`
- **Database**: SQLite (stored in named volume `ts-data` under the
  `teamspeak-02` compose project)
- **Network mode**: host
- **Ports**:
  - `9988/udp` — Voice
  - `10012/tcp` — ServerQuery
  - `30034/tcp` — File Transfer
- **Public Playit address**: `REDACTED_CUSTOM_DOMAIN_015:53810`
- **Playit local target**: `127.0.0.1:9988/udp`
- **Cloudflare connect address**: `REDACTED_CUSTOM_DOMAIN_023`
- **Virtual server name**: `REDACTED_PRIVATE_ORG_LABEL United - Valorant Community`
- **Server password**: Disabled intentionally; public to users who know the address
- **Unique ID**: `REDACTED_TEAMSPEAK_UNIQUE_ID_001`

### TeamSpeak 3 (ts-valorant-03)
- **Image**: `teamspeak`
- **Container**: `ts-valorant-03`
- **Compose project**: `teamspeak-03`
- **Location**: `~/teamspeak-03/docker-compose.yml`
- **Database**: SQLite (stored in named volume `ts-data` under the
  `teamspeak-03` compose project)
- **Network mode**: host
- **Ports**:
  - `9989/udp` — Voice
  - `10013/tcp` — ServerQuery
  - `30035/tcp` — File Transfer
- **Public Playit address**: `REDACTED_CUSTOM_DOMAIN_010:49125`
- **Playit local target**: `127.0.0.1:9989/udp`
- **Cloudflare connect address**: `REDACTED_CUSTOM_DOMAIN_024`
- **Cloudflare alternate address**: `REDACTED_CUSTOM_DOMAIN_021`
- **Virtual server name**: `REDACTED_PRIVATE_ORG_LABEL United x Valorant 03`
- **Server password**: Disabled intentionally; public to users who know the address
- **Unique ID**: `REDACTED_TEAMSPEAK_UNIQUE_ID_002`

### Playit Agent (playit-agent)
- **Image**: `ghcr.io/playit-cloud/playit-agent:0.17`
- **Container**: `playit-agent`
- **Compose project**: `playit-agent`
- **Location**: `~/playit-agent/docker-compose.yml`
- **Network mode**: host
- **Secret key**: stored in `.env` file
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
- **Recommended TS2 entry**:
  - Name: `ts-valorant-02`
  - Host/IP: `192.168.80.118`
  - ServerQuery port: `10012`
  - Protocol: normal/raw ServerQuery, not SSH
  - Login: `serveradmin`
  - Password: TS2 - ServerQuery password documented above
- **Recommended TS3 entry**:
  - Name: `ts-valorant-03`
  - Host/IP: `192.168.80.118`
  - ServerQuery port: `10013`
  - Protocol: normal/raw ServerQuery, not SSH
  - Login: `serveradmin`
  - Password: TS3 - ServerQuery password documented above
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

---

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

### ~/playit-agent/.env
```
PLAYIT_SECRET_KEY=<your_secret_key>
```

### ~/playit-agent/playit-boot-recover.sh
```sh
# Runs from REDACTED_USER_001's crontab at reboot:
# @reboot /home/REDACTED_USER_001/playit-agent/playit-boot-recover.sh
#
# Purpose:
# - Waits 90 seconds after VM/host boot
# - Waits for Docker to respond
# - Waits for REDACTED_CUSTOM_DOMAIN_003 DNS resolution
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

---

## Notes
- Playit is intentionally decoupled from `~/teamspeak/docker-compose.yml`; running `docker compose down` in `~/teamspeak` will stop TeamSpeak 1 but will not stop `playit-agent`
- Playit tunnels TeamSpeak UDP voice only — TCP services such as ServerQuery and file transfer are LAN/internal only
- ts3-manager is not exposed through Playit — access it from the local network at `http://192.168.80.118:9000`
- To add future TeamSpeak servers to ts3-manager, connect via the host VLAN 80 IP and that server's unique ServerQuery host port
- Future TeamSpeak servers must use unique host ports. TeamSpeak 2 currently uses `9988/udp`, `10012/tcp`, and `30034/tcp`; TeamSpeak 3 uses `9989/udp`, `10013/tcp`, and `30035/tcp`
- Use normal/raw ServerQuery in TS3 Manager, not SSH
- Playit free plan uses Global Anycast routing
- After Proxmox VM/host reboot, Playit can start before DNS is ready and log
  `failed to lookup address information: Try again` for
  `https://REDACTED_CUSTOM_DOMAIN_003/agents/rundata`. The boot recovery cron job mitigates
  this by restarting only `playit-agent` after network and DNS are available.
- TeamSpeak can also start before DNS is ready and fail to download the
  myTeamSpeak ID revocation list. When this happens, clients can connect but may
  see `myTeamSpeak ID is invalid`. The boot recovery cron job restarts the
  TeamSpeak containers after DNS is available so the revocation list is loaded.
- TeamSpeak containers run with `network_mode: host` as of 2026-04-24 to keep
  Playit UDP voice traffic out of Docker's UDP userland proxy. This resolved
  TS3 client timeout behavior where packets reached the container but the
  client handshake failed to complete.
