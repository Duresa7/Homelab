# TeamSpeak Service Incident Report

**Created:** 2026-04-24  
**Last updated:** 2026-07-19

**REDACTED_PRIVATE_ORG_LABEL United - Internal IT / Cybersecurity Operations**

---

## Document Metadata

| Field | Value |
|-------|-------|
| Incident ID | TS3-INC-2026-04-24-001 |
| Document Classification | Internal |
| Report Date | 2026-04-24 |
| Report Timezone | America/New_York |
| Environment | REDACTED_PRIVATE_ORG_LABEL United Production |
| Service | TeamSpeak 3 Voice Services |
| Primary Host | alpha-prod-01 |
| Host IP | 192.168.80.118 |
| VLAN | SERVERS-A (80) |
| Report Owner | REDACTED_USER_001 REDACTED_NAME_003 / REDACTED_USER_001 |
| Organization | REDACTED_PRIVATE_ORG_LABEL United |
| Status | Resolved / Monitoring |
| Severity | SEV-3 - Service Degradation |

---

## Executive Summary

On 2026-04-24, REDACTED_PRIVATE_ORG_LABEL United observed intermittent TeamSpeak client connection
failures against the community TeamSpeak endpoint `REDACTED_CUSTOM_DOMAIN_022`. I began
triage with the service layer: the TeamSpeak server process, Docker containers,
and Playit tunnel were all online. The connection fragility for end users and
administrative tooling traced instead to DNS and management-plane configuration.

I identified the primary issue as a non-compliant SRV DNS chain in Cloudflare.
The TeamSpeak SRV record pointed to `REDACTED_CUSTOM_DOMAIN_022`, which was
itself a CNAME. SRV targets should resolve directly to the service hostname, not
to an alias. Some clients and resolvers tolerate this behavior, while others can
fail resolution or connection setup.

I also found a secondary operational issue with TS3 Manager. The TS3 Manager
container generated ServerQuery command bursts and triggered TeamSpeak
ServerQuery flood protection because the Docker bridge gateway IP was not in the
TeamSpeak `query_ip_allowlist.txt` file.

I corrected both: I updated the Cloudflare SRV target to point directly at the
Playit hostname and added the Docker bridge gateway IP to the TeamSpeak
ServerQuery allowlist.

---

## Impact Assessment

| Area | Impact |
|------|--------|
| End Users | Some users received "failed to connect to server" when joining TeamSpeak. |
| Voice Service | TeamSpeak voice service remained online during investigation. |
| DNS Resolution | SRV resolution path was fragile due to SRV target aliasing. |
| Management Plane | TS3 Manager triggered ServerQuery flood protection and previously crashed. |
| Security Exposure | No evidence of compromise was observed during this investigation. |
| Data Loss | None identified. |

---

## Affected Assets

| Asset | Role | Observed State |
|-------|------|----------------|
| alpha-prod-01 | Production Docker host | Online |
| ts-valorant-01 | TeamSpeak 3 container | Online |
| ts-valorant-02 | TeamSpeak 3 container | Online |
| playit-agent | Shared Playit tunnel agent | Online |
| ts3-manager | Web-based TeamSpeak administration UI | Online after restart |
| REDACTED_CUSTOM_DOMAIN_001 | Cloudflare-managed DNS zone | Active |
| REDACTED_CUSTOM_DOMAIN_022 | Community connection endpoint | Active |
| REDACTED_CUSTOM_DOMAIN_023 | Community connection endpoint | Active |

---

## Technical Findings

### Finding 1 - SRV Record Targeted a CNAME

Previous DNS behavior:

```text
_ts3._udp.REDACTED_CUSTOM_DOMAIN_022
  -> REDACTED_CUSTOM_DOMAIN_022:6255
  -> CNAME REDACTED_CUSTOM_DOMAIN_009
```

This introduced resolver/client compatibility risk because the SRV target was an
alias. I corrected the record to point directly at the Playit hostname.

Current DNS behavior:

```text
_ts3._udp.REDACTED_CUSTOM_DOMAIN_022
  -> REDACTED_CUSTOM_DOMAIN_009:6255

REDACTED_CUSTOM_DOMAIN_022
  -> CNAME REDACTED_CUSTOM_DOMAIN_009
```

End users still connect with:

```text
REDACTED_CUSTOM_DOMAIN_022
```

### Finding 2 - TS3 Manager Triggered ServerQuery Flood Protection

I observed the TeamSpeak ServerQuery flood thresholds as:

```text
serverinstance_serverquery_flood_commands=10
serverinstance_serverquery_flood_time=3
serverinstance_serverquery_ban_time=600
```

TS3 Manager logs showed repeated flood warnings during administrative activity:

```text
WARN | Flooding
```

TeamSpeak observed TS3 Manager ServerQuery traffic from Docker gateway IP:

```text
172.18.0.1
```

That IP was not previously allowlisted. I updated the allowlist to include the
Docker bridge gateway used by TS3 Manager.

### Finding 3 - TS3 Manager Should Use LAN ServerQuery

TS3 Manager must use the LAN ServerQuery endpoint:

```text
192.168.80.118:10011
```

It should not use:

```text
REDACTED_CUSTOM_DOMAIN_022
```

Playit forwards the public UDP voice service. It does not expose TeamSpeak
ServerQuery TCP or file transfer TCP externally.

---

## Root Cause Analysis

### Primary Root Cause

The Cloudflare TeamSpeak SRV record used an alias target. This created a
standards-compliance and client-compatibility issue where some TeamSpeak clients
or DNS resolvers could fail to complete connection resolution.

### Contributing Factors

- The public connection path depends on DNS SRV behavior.
- The Playit hostname publishes public tunnel records that clients must resolve
  correctly.
- TS3 Manager issued multiple ServerQuery commands rapidly and was not exempted
  from ServerQuery anti-flood controls.
- TS3 Manager was previously configured or used in a way that attempted invalid
  connection modes, including SSH-like behavior and public hostname usage.

### Not Root Cause

I checked the following and ruled each out as the primary cause:

- TeamSpeak process failure
- TeamSpeak virtual server offline state
- Container port publishing failure
- Playit agent offline state
- Cloudflare proxying
- Slot exhaustion
- Docker host outage

---

## Corrective Actions Completed

| Action | Status | Notes |
|--------|--------|-------|
| Verified Docker service state | Complete | `ts-valorant-01`, `playit-agent`, and `ts3-manager` were checked. |
| Verified TeamSpeak virtual server state | Complete | Virtual server reported `online`. |
| Corrected Cloudflare SRV target | Complete | SRV now targets `REDACTED_CUSTOM_DOMAIN_009:6255`. |
| Confirmed DNS propagation | Complete | Public resolvers returned corrected SRV target. |
| Added TS3 Manager Docker gateway to ServerQuery allowlist | Complete | Added `172.18.0.1`. |
| Confirmed allowlist reload | Complete | TeamSpeak logged updated allowlist with `172.18.0.1/32`. |
| Restarted TS3 Manager container only | Complete | Manager was stopped and was started. |
| Verified ServerQuery burst from manager path | Complete | Returned `error id=0 msg=ok`; no flood error observed. |
| Updated deployment documentation | Complete | `Teamspeak-deployment.md` was corrected. |

---

## Current Known-Good Configuration

### DNS

| Type | Name | Target | Port | Proxy |
|------|------|--------|------|-------|
| CNAME | ts01 | REDACTED_CUSTOM_DOMAIN_009 | N/A | DNS only |
| SRV | _ts3._udp.ts01 | REDACTED_CUSTOM_DOMAIN_009 | 6255 | DNS only |
| CNAME | ts02 | REDACTED_CUSTOM_DOMAIN_015 | N/A | DNS only |
| SRV | _ts3._udp.ts02 | REDACTED_CUSTOM_DOMAIN_015 | 53810 | DNS only |

### Runtime Services

| Container | Image | Purpose | State |
|-----------|-------|---------|-------|
| ts-valorant-01 | teamspeak | TeamSpeak 3 server | Running |
| ts-valorant-02 | teamspeak | TeamSpeak 3 server | Running |
| playit-agent | ghcr.io/playit-cloud/playit-agent:0.17 | Shared public UDP tunnel agent | Running |
| ts3-manager | joni1802/ts3-manager | Web administration UI | Running |

### Published Ports

| Service | Host Port | Container Port | Protocol | Exposure |
|---------|-----------|----------------|----------|----------|
| TeamSpeak 1 Voice | 9987 | 9987 | UDP | Local host / Playit tunnel |
| TeamSpeak 1 ServerQuery | 10011 | 10011 | TCP | LAN/internal |
| TeamSpeak 1 File Transfer | 30033 | 30033 | TCP | LAN/internal |
| TeamSpeak 2 Voice | 9988 | 9987 | UDP | Local host / Playit tunnel |
| TeamSpeak 2 ServerQuery | 10012 | 10011 | TCP | LAN/internal |
| TeamSpeak 2 File Transfer | 30034 | 30033 | TCP | LAN/internal |
| TS3 Manager UI | 9000 | 8080 | TCP | LAN/internal |

### ServerQuery Allowlist - TeamSpeak 1

Effective allowed ServerQuery sources for `ts-valorant-01`:

```text
127.0.0.1
::1
192.168.80.118
192.168.50.241
172.18.0.1
```

### ServerQuery Allowlist - TeamSpeak 2

Effective allowed ServerQuery sources for `ts-valorant-02`:

```text
127.0.0.1
::1
192.168.80.118
192.168.50.241
172.21.0.1
```

---

## Validation Evidence

### TeamSpeak 1 Virtual Server

Observed state:

```text
virtualserver_name=REDACTED_PRIVATE_ORG_LABEL x LYON
virtualserver_status=online
virtualserver_port=9987
virtualserver_maxclients=32
virtualserver_flag_password=1
virtualserver_weblist_enabled=0
```

### TeamSpeak 2 Virtual Server

Observed state:

```text
virtualserver_name=REDACTED_PRIVATE_ORG_LABEL United - Valorant Community
virtualserver_status=online
virtualserver_port=9987
virtualserver_maxclients=32
virtualserver_flag_password=0
virtualserver_weblist_enabled=0
```

TS2 password status is intentional. The server is public to users who know the
connection address.

### Playit Agent

Observed state:

```text
tunnel running, 2 tunnels registered
```

### Cloudflare DNS

Observed SRV state:

```text
_ts3._udp.REDACTED_CUSTOM_DOMAIN_022
NameTarget: REDACTED_CUSTOM_DOMAIN_009
Port: 6255
TTL: 300

_ts3._udp.REDACTED_CUSTOM_DOMAIN_023
NameTarget: REDACTED_CUSTOM_DOMAIN_015
Port: 53810
TTL: 300
```

---

## Security Considerations

- No secrets, API keys, or ServerQuery credentials should be stored in incident
  reports.
- TS3 Manager should remain LAN-only and should not be exposed through Playit or
  public DNS.
- ServerQuery TCP ports `10011` and `10012` should remain internal only.
- File transfer TCP ports `30033` and `30034` should remain internal unless a
  formal exposure requirement is approved.
- ServerQuery should use a least-privilege administrative account where possible
  instead of broad-use serveradmin credentials.

---

## Recommendations

1. Keep the SRV target pointed directly at the Playit hostname.
2. Keep TS3 Manager configured to LAN/internal ServerQuery ports using normal/raw
   ServerQuery: `192.168.80.118:10011` for TS1 and `192.168.80.118:10012` for
   TS2.
3. Do not use SSH mode in TS3 Manager for TeamSpeak ServerQuery.
4. Keep Docker gateway addresses in `query_ip_allowlist.txt` while TS3 Manager
   runs in the current Docker network topology: `172.18.0.1` for TS1 and
   `172.21.0.1` for TS2.
5. Add a lightweight operational check for:
   - Docker container state
   - TeamSpeak ServerQuery response
   - Cloudflare SRV target correctness
   - Playit tunnel registration
6. Consider pinning Docker image versions after stability validation.
7. Maintain a change log for DNS, Playit tunnel, and TeamSpeak ServerQuery
   changes.

---

## Closure Statement

As of 2026-04-24, the TeamSpeak production service is operational. I corrected
the public connection path, mitigated the TS3 Manager ServerQuery flood risk,
decoupled Playit into a shared standalone compose project, and updated the
deployment documentation to reflect the known-good state.

I am keeping the incident in monitoring status until external users confirm
successful connection through `REDACTED_CUSTOM_DOMAIN_022` and
`REDACTED_CUSTOM_DOMAIN_023`.
