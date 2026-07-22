# TeamSpeak UDP Relay Outage - 2026-04-24

**Created:** 2026-04-24  
**Last updated:** 2026-07-20

## Incident Summary

On 2026-04-24, users reported repeated TeamSpeak connection failures against the
public Playit endpoints and Cloudflare DNS names for `<YOUR_ORG_NAME>` United TeamSpeak
services. I began triage with basic health checks, which showed TeamSpeak,
Docker, DNS, and Playit all nominal. My deeper testing showed that UDP packets
were reaching the TeamSpeak path, but the TeamSpeak client handshake was not
completing.

I mitigated the issue by removing Docker's UDP port proxy from the voice path:
I moved both TeamSpeak containers to host networking with unique native ports.
After the change, TeamSpeak logs recorded successful client connections through
the Playit path.

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

## Affected Endpoints

| Service | Public DNS | Playit Endpoint | Host Port |
|---------|------------|-----------------|-----------|
| TeamSpeak 1 | `<YOUR_TEAMSPEAK_ONE_DOMAIN>` | `<YOUR_TEAMSPEAK_RELAY_ONE_HOST>`:6255 | 9987/udp |
| TeamSpeak 2 | `<YOUR_TEAMSPEAK_TWO_DOMAIN>` | `<YOUR_TEAMSPEAK_RELAY_TWO_HOST>`:53810 | 9988/udp |

## User-Visible Symptoms

Users observed repeated TeamSpeak client failures similar to:

```text
Trying to resolve hostname <YOUR_TEAMSPEAK_ONE_DOMAIN>
Trying to connect to server on <YOUR_TEAMSPEAK_ONE_DOMAIN>
Failed to connect to server
```

My direct Playit IPv4 testing also failed before mitigation:

```text
Trying to connect to server on <YOUR_RELAY_IP>:6255
Failed to connect to server
```

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

## Root Cause

I identified the most likely root cause as a UDP relay compatibility issue
across this path:

```text
TeamSpeak client
  -> Playit UDP relay
  -> alpha-prod-01
  -> Docker UDP port proxy / bridge networking
  -> TeamSpeak container
```

The TeamSpeak service itself was not offline. Evidence showed UDP traffic
reaching the server path, but the TeamSpeak client handshake did not complete
while the containers were using Docker UDP port publishing. After I moved the
TeamSpeak containers to host networking, the server recorded successful client
connections through the Playit path.

## Corrective Actions Performed

1. I enabled temporary TeamSpeak client logging for troubleshooting.
2. I verified Docker service health and listener state.
3. I verified Cloudflare DNS and SRV resolution.
4. I verified Playit agent status and tunnel registration.
5. I restarted the Playit agent to clear any stale relay session state.
6. I moved `ts-valorant-01` to host networking.
7. I moved `ts-valorant-02` to host networking.
8. I changed TeamSpeak 2's native virtual server voice port to `9988/udp`.
9. I verified listeners:
   - `9987/udp`
   - `9988/udp`
   - `10011/tcp`
   - `10012/tcp`
   - `30033/tcp`
   - `30034/tcp`
10. I updated ServerQuery allowlists for TS3 Manager source traffic.
11. I updated the deployment document to reflect the host-network architecture.

## Current State

| Service | State | Notes |
|---------|-------|-------|
| ts-valorant-01 | Online | Host networking, voice on `9987/udp` |
| ts-valorant-02 | Online | Host networking, voice on `9988/udp` |
| playit-agent | Online | Shared standalone agent, two tunnels registered |
| ts3-manager | Online | Web UI available on LAN port `9000` |

## Security Assessment

I found no evidence of credential compromise, malicious authentication attempts,
or unauthorized administrative activity. The observed failure was in the UDP
network path, so I classified this as an availability incident rather than a
confirmed security breach.

## Operational Findings

- Container uptime and open listeners didn't prove the TeamSpeak handshake worked.
- The failure disappeared when I removed Docker's UDP proxy from the path and moved both containers to host networking.
- Client connection logs distinguished the incomplete handshake from an application rejection.

## Follow-Up Actions

| Action | Owner | Priority | Status |
|--------|-------|----------|--------|
| Confirm multiple external users can join TS1 | `<YOUR_ORG_NAME>` United | High | Pending |
| Confirm multiple external users can join TS2 | `<YOUR_ORG_NAME>` United | High | Pending |
| Add Cloudflare aliases for `ts-valorant-01` and `ts-valorant-02` after Cloudflare API re-authentication | `<YOUR_ORG_NAME>` United | Medium | Pending |
| Consider direct UDP firewall/NAT exposure as a long-term alternative to Playit | `<YOUR_ORG_NAME>` United | Medium | Open |
| Keep TeamSpeak containers on host networking for future voice servers | `<YOUR_ORG_NAME>` United | Medium | In Progress |

## Linked Records

- [TeamSpeak deployment](../../Platforms/Teamspeak%20Hosting/Documentation/Teamspeak-deployment.md)
- Host: `alpha-prod-01`
- TS3 Manager: `http://192.168.80.118:9000`

