# TeamSpeak Hosting on alpha-prod-01

**Created:** 2026-05-27  
**Last updated:** 2026-08-09

I run two TeamSpeak servers, one shared Playit agent, & TS3 Manager on `alpha-prod-01`. This record maps the VLAN address, container ports, Playit relays, Cloudflare SRV records, ServerQuery allowlists, Compose projects, & boot recovery.

## VM Details

| Property | Value |
|---|---|
| Hostname | `alpha-prod-01` |
| OS | Debian 13 |
| IP | `192.168.80.118` |
| VLAN | SERVERS-A (80) |
| Subnet | `192.168.80.0/24` |

## Service Map

| Server | Voice | ServerQuery | File transfer | Public name |
|---|---:|---:|---:|---|
| `ts-valorant-02` | 9988/udp | 10012/tcp | 30034/tcp | `ts02.alphasecunited.com` |
| `ts-valorant-03` | 9989/udp | 10013/tcp | 30035/tcp | `ts03.alphasecunited.com` |

Both containers use host networking. Playit forwards only the two UDP voice ports to loopback; ServerQuery & file transfer remain on the LAN.

## DNS Records

| Type | Name | Target | Port | Proxy |
|---|---|---|---:|---|
| CNAME | `ts02` | `<REDACTED_TEAMSPEAK_RELAY_TWO_HOST>` | | DNS only |
| SRV | `_ts3._udp.ts02` | `<REDACTED_TEAMSPEAK_RELAY_TWO_HOST>` | 53810 | DNS only |
| CNAME | `ts03` | `<REDACTED_TEAMSPEAK_RELAY_THREE_HOST>` | | DNS only |
| SRV | `_ts3._udp.ts03` | `<REDACTED_TEAMSPEAK_RELAY_THREE_HOST>` | 49125 | DNS only |
| CNAME | `ts-valorant-03` | `<REDACTED_TEAMSPEAK_RELAY_THREE_HOST>` | | DNS only |
| SRV | `_ts3._udp.ts-valorant-03` | `<REDACTED_TEAMSPEAK_RELAY_THREE_HOST>` | 49125 | DNS only |

The SRV records target the Playit hostnames directly. They don't target the `ts02` or `ts03` CNAME because some TeamSpeak clients reject an alias in the SRV target.

## Playit Tunnels

| TeamSpeak server | Tunnel name | Public address | Local target |
|---|---|---|---|
| `ts-valorant-02` | `ts-valorant-02` | `<REDACTED_TEAMSPEAK_RELAY_TWO_HOST>`:53810 | `127.0.0.1:9988/udp` |
| `ts-valorant-03` | `ts-valorant-03` | `<REDACTED_TEAMSPEAK_RELAY_THREE_HOST>`:49125 | `127.0.0.1:9989/udp` |

The `playit-agent` Compose project is independent of both TeamSpeak projects. Restarting or removing one voice server doesn't stop the agent or the other tunnel.

## TeamSpeak Containers

### ts-valorant-02

| Property | Value |
|---|---|
| Image | `teamspeak` |
| Compose project | `teamspeak-02` |
| Compose file | `~/teamspeak-02/docker-compose.yml` |
| Data volume | `teamspeak-02_ts-data` |
| Network mode | host |
| Voice | 9988/udp |
| ServerQuery | 10012/tcp |
| File transfer | 30034/tcp |
| Public address | `ts02.alphasecunited.com` |

### ts-valorant-03

| Property | Value |
|---|---|
| Image | `teamspeak` |
| Compose project | `teamspeak-03` |
| Compose file | `~/teamspeak-03/docker-compose.yml` |
| Data volume | `teamspeak-03_ts-data` |
| Network mode | host |
| Voice | 9989/udp |
| ServerQuery | 10013/tcp |
| File transfer | 30035/tcp |
| Public address | `ts03.alphasecunited.com` |
| Alternate address | `ts-valorant-03.alphasecunited.com` |

## Shared Services

### Playit Agent

| Property | Value |
|---|---|
| Image | `ghcr.io/playit-cloud/playit-agent:0.17` |
| Container | `playit-agent` |
| Compose project | `playit-agent` |
| Compose file | `~/playit-agent/docker-compose.yml` |
| Network mode | host |

The `dkadi` crontab runs `~/playit-agent/playit-boot-recover.sh` at reboot. The script waits 90 seconds, waits for Docker & `api.playit.gg` DNS, restarts `teamspeak-02` & `teamspeak-03`, then restarts `playit-agent`.

### TS3 Manager

| Property | Value |
|---|---|
| Image | `joni1802/ts3-manager` |
| Container | `ts3-manager` |
| Host port | 9000/tcp |
| Container port | 8080/tcp |
| Internal address | `https://ts3-manager.alphasecunited.com` |
| Direct fallback | `http://192.168.80.118:9000` |

TS3 Manager connects to `192.168.80.118:10012` & `192.168.80.118:10013`. It doesn't use either public Playit address.

## ServerQuery Allowlists

### ts-valorant-02

```text
127.0.0.1
::1
192.168.80.118
192.168.50.241
172.21.0.1
172.19.0.2
```

### ts-valorant-03

```text
127.0.0.1
::1
192.168.80.118
192.168.50.241
172.19.0.2
```

`172.19.0.2` is the TS3 Manager container address. `172.21.0.1` remains from the earlier bridge-mode TeamSpeak 2 deployment.

## Compose Files

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

## Monitoring

The `teamspeak-monitor` collector probes `ts02` & `ts03` every 60 seconds through their public SRV path & their local UDP ports. It also reads ServerQuery statistics on TCP 10012 & 10013. The collector writes Prometheus textfile metrics through the existing node_exporter scrape on port 9100; the provisioned Grafana dashboard uses metric labels rather than a fixed server list.

The [reachability monitoring record](Change%20Records/TeamSpeak%20Reachability%20Monitoring%20-%202026-07-28.md) preserves the original three-server implementation. The [server 01 retirement record](Change%20Records/Server%2001%20Retirement%20-%202026-08-09.md) records its removal from Docker, monitoring, boot recovery, & Cloudflare DNS.

## Constraints

- Future TeamSpeak servers need unique voice, ServerQuery, & file-transfer ports because every voice container uses host networking.
- Playit forwards UDP voice only. ServerQuery & file transfer stay on the LAN.
- TS3 Manager uses normal ServerQuery, not SSH.
- The boot-recovery script restarts TeamSpeak only after DNS answers so the containers can download the myTeamSpeak ID revocation list.
