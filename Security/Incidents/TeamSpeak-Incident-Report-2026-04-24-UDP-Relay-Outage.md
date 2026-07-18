# TeamSpeak Service Incident Report

**Created:** 2026-04-24  
**Last updated:** 2026-07-17

## Document Control

| Field | Value |
|-------|-------|
| Organization | REDACTED_PRIVATE_ORG_LABEL United |
| Environment | Production |
| Asset | alpha-prod-01 |
| Service | TeamSpeak 3 voice services |
| Report Owner | REDACTED_USER_001 REDACTED_NAME_003 |
| Prepared By | Codex |
| Report Date | 2026-04-24 |
| Time Zone | America/New_York |
| Classification | Internal Use |
| Credential Handling | No passwords, API keys, privilege keys, or Playit secrets are included |

---

## Executive Summary

On 2026-04-24, users reported repeated TeamSpeak connection failures against the
public Playit endpoints and Cloudflare DNS names for REDACTED_PRIVATE_ORG_LABEL United TeamSpeak
services. Initial checks showed that TeamSpeak, Docker, DNS, and Playit were all
nominal at a basic health-check level. Deeper testing showed that UDP packets
were reaching the TeamSpeak path, but the TeamSpeak client handshake was not
completing.

The issue was mitigated by removing Docker's UDP port proxy from the voice path.
Both TeamSpeak containers were moved to host networking with unique native
ports. After the change, TeamSpeak logs recorded successful client connections
through the Playit path.

---

## Incident Metadata

| Field | Value |
|-------|-------|
| Incident ID | ASU-TS3-20260424-002 |
| Detected By | User report |
| Detection Time | 2026-04-24 22:49 EDT |
| Mitigation Time | 2026-04-24 23:04 EDT |
| Status | Mitigated |
| Severity | SEV-2 |
| Priority | High |
| Impact Type | Availability |
| Affected Users | External TeamSpeak users attempting public connection |
| Affected Services | ts-valorant-01, ts-valorant-02 |
| Unaffected Services | TS3 Manager web UI, ServerQuery control plane, Docker host |

---

## Affected Endpoints

| Service | Public DNS | Playit Endpoint | Host Port |
|---------|------------|-----------------|-----------|
| TeamSpeak 1 | REDACTED_CUSTOM_DOMAIN_022 | REDACTED_CUSTOM_DOMAIN_009:6255 | 9987/udp |
| TeamSpeak 2 | REDACTED_CUSTOM_DOMAIN_023 | REDACTED_CUSTOM_DOMAIN_015:53810 | 9988/udp |

---

## User-Visible Symptoms

Users observed repeated TeamSpeak client failures similar to:

```text
Trying to resolve hostname REDACTED_CUSTOM_DOMAIN_022
Trying to connect to server on REDACTED_CUSTOM_DOMAIN_022
Failed to connect to server
```

Direct Playit IPv4 testing also failed before mitigation:

```text
Trying to connect to server on REDACTED_IPV4_011:6255
Failed to connect to server
```

---

## Technical Findings

| Control Point | Finding |
|---------------|---------|
| Docker container state | TeamSpeak 1, TeamSpeak 2, Playit agent, and TS3 Manager were running |
| DNS | Cloudflare CNAME and SRV records resolved correctly for `ts01` and `ts02` |
| Playit agent | Agent reported two registered tunnels |
| TeamSpeak ServerQuery | Both TeamSpeak query interfaces responded locally |
| Ban lists | No active TeamSpeak bans were present |
| TS3 Manager | No current flood, ban, or query-abuse indicators were observed |
| Packet path | Public UDP attempts changed TeamSpeak network counters |
| Client logging | Failed attempts did not complete as normal TeamSpeak client sessions |

---

## Root Cause

The most likely root cause was a UDP relay compatibility issue across this path:

```text
TeamSpeak client
  -> Playit UDP relay
  -> alpha-prod-01
  -> Docker UDP port proxy / bridge networking
  -> TeamSpeak container
```

The TeamSpeak service itself was not offline. Evidence showed UDP traffic
reaching the server path, but the TeamSpeak client handshake did not complete
while the containers were using Docker UDP port publishing. After moving the
TeamSpeak containers to host networking, the server recorded successful client
connections through the Playit path.

---

## Corrective Actions Performed

1. Enabled temporary TeamSpeak client logging for troubleshooting.
2. Verified Docker service health and listener state.
3. Verified Cloudflare DNS and SRV resolution.
4. Verified Playit agent status and tunnel registration.
5. Restarted the Playit agent to clear any stale relay session state.
6. Moved `ts-valorant-01` to host networking.
7. Moved `ts-valorant-02` to host networking.
8. Changed TeamSpeak 2's native virtual server voice port to `9988/udp`.
9. Verified listeners:
   - `9987/udp`
   - `9988/udp`
   - `10011/tcp`
   - `10012/tcp`
   - `30033/tcp`
   - `30034/tcp`
10. Updated ServerQuery allowlists for TS3 Manager source traffic.
11. Updated the deployment document to reflect the host-network architecture.

---

## Current State

| Service | State | Notes |
|---------|-------|-------|
| ts-valorant-01 | Online | Host networking, voice on `9987/udp` |
| ts-valorant-02 | Online | Host networking, voice on `9988/udp` |
| playit-agent | Online | Shared standalone agent, two tunnels registered |
| ts3-manager | Online | Web UI available on LAN port `9000` |

---

## Security Assessment

No evidence indicated credential compromise, malicious authentication attempts,
or unauthorized administrative activity. The incident was assessed as an
availability and network-path failure, not a confirmed security breach.

No passwords, API keys, ServerQuery credentials, privilege keys, or Playit
secrets are included in this report.

---

## Lessons Learned

- UDP health requires more than container uptime and port listener checks.
- Docker UDP publishing can introduce behavior that is difficult to distinguish
  from upstream relay failure.
- For latency-sensitive UDP services behind a relay, host networking is a
  simpler and more deterministic architecture.
- Client connection logs should be enabled temporarily during incidents to
  distinguish application-layer rejection from network-path timeout.

---

## Follow-Up Actions

| Action | Owner | Priority | Status |
|--------|-------|----------|--------|
| Confirm multiple external users can join TS1 | REDACTED_PRIVATE_ORG_LABEL United | High | Pending |
| Confirm multiple external users can join TS2 | REDACTED_PRIVATE_ORG_LABEL United | High | Pending |
| Add Cloudflare aliases for `ts-valorant-01` and `ts-valorant-02` after Cloudflare API re-authentication | REDACTED_PRIVATE_ORG_LABEL United | Medium | Pending |
| Consider direct UDP firewall/NAT exposure as a long-term alternative to Playit | REDACTED_PRIVATE_ORG_LABEL United | Medium | Open |
| Keep TeamSpeak containers on host networking for future voice servers | REDACTED_PRIVATE_ORG_LABEL United | Medium | In Progress |

---

## References

- Deployment document: `Teamspeak-deployment.md`
- Host: `alpha-prod-01`
- TS3 Manager: `http://192.168.80.118:9000`

