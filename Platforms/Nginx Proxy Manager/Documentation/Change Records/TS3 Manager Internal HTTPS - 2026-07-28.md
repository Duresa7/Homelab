# TS3 Manager Internal HTTPS

**Created:** 2026-07-28  
**Last updated:** 2026-07-28

**Date:** 2026-07-28  
**Status:** Complete

## Scope

I published the existing TS3 Manager interface at `https://ts3-manager.<YOUR_BASE_DOMAIN>` through internal Nginx Proxy Manager. UniFi resolves the name to `192.168.85.2`; NPM forwards HTTP to `192.168.80.118:9000` and presents certificate ID 1.

I did not publish TeamSpeak voice, ServerQuery, file-transfer, Playit, SSH, exporter, or Portainer Edge Agent ports. Direct fallback remains `http://192.168.80.118:9000`, and UniFi still has zero port-forward rules.

## Starting State

- TS3 Manager returned HTTP `200` on `192.168.80.118:9000`.
- NPM held 19 enabled proxy hosts: NetBird plus 18 application interfaces.
- UniFi had no `ts3-manager.<YOUR_BASE_DOMAIN>` record and no NPM policy to TCP 9000 on `alpha-prod-01`.
- A probe from `docker-network` to `192.168.80.118:9000` timed out before the firewall change.
- Prometheus held 45 targets, including 18 blackbox probes after Termix retirement.

## Decisions

- I used `ts3-manager.<YOUR_BASE_DOMAIN>` because certificate ID 1 covers one label beneath the base domain.
- I kept the upstream on HTTP. TS3 Manager already listens on HTTP 9000, while NPM terminates the client TLS session.
- I gave the route the same baseline as the other internal interfaces: Force SSL, HTTP/2, Block Common Exploits, WebSocket support, no HSTS, & no NPM access list.
- I created a separate firewall policy instead of adding TCP 9000 to another host's policy. The saved rule names one source, one destination, & one port.

## Step 1: Capture the Starting State

I queried the NPM SQLite database read-only, listed UniFi DNS and NPM policies, checked the live listeners on `alpha-prod-01`, & tested the blocked backend path from `docker-network`.

I created a mode-0600 SQLite copy during the change, then deleted the file and its empty directory at the owner's request. No NPM backup from this work remains.

Evidence: [preflight and backup removal](../../Evidence/TS3%20Manager%20Internal%20HTTPS%20-%202026-07-28/Logs/S01-Preflight-and-Recovery-2026-07-28.md).

## Step 2: Add UniFi DNS and Firewall State

I previewed both additions before applying them. The firewall preview named source `192.168.85.2`, destination `192.168.80.118`, protocol TCP, destination port `9000`, & logging enabled. The DNS preview named one TTL-300 A record pointing to NPM.

| Item | Result |
|---|---|
| Firewall policy | `Allow NPM to alpha-prod-01 TS3 Manager` |
| Policy ID | `6a68b26e052792cd2140bfd9` |
| DNS record ID | `6a68b26f052792cd2140bfdc` |
| Local A result | `ts3-manager.<YOUR_BASE_DOMAIN>` to `192.168.85.2` |

The saved policy readback returned one exact IPv4 source, one exact IPv4 destination, TCP 9000, `enabled: true`, & `logging: true`. After the rule landed, `docker-network` opened TCP 9000 and the backend returned HTTP `200`.

Evidence: [UniFi preview, application, and readback](../../Evidence/TS3%20Manager%20Internal%20HTTPS%20-%202026-07-28/Logs/S02-UniFi-DNS-and-Firewall-2026-07-28.md).

## Step 3: Create the NPM Proxy Host

I retrieved the NPM administrator fields through 1Password references and passed them directly to `POST /api/tokens`. The password and bearer token stayed in process variables; neither value appeared in output, a file, or this repository.

I created proxy host ID `22` with:

| Setting | Value |
|---|---|
| Domain | `ts3-manager.<YOUR_BASE_DOMAIN>` |
| Upstream | `http://192.168.80.118:9000` |
| Certificate | ID 1 |
| Force SSL | Enabled |
| HTTP/2 | Enabled |
| Block Common Exploits | Enabled |
| WebSocket support | Enabled |
| HSTS | Disabled |
| Access list | None |

NPM generated `data/nginx/proxy_host/22.conf`, and `nginx -t` passed. HTTP returned `301` to HTTPS, HTTPS returned `200`, & the presented wildcard certificate expires `2026-10-08 23:49:46 UTC`.

Evidence: [NPM creation and route verification](../../Evidence/TS3%20Manager%20Internal%20HTTPS%20-%202026-07-28/Logs/S03-NPM-Proxy-Host-2026-07-28.md).

## Step 4: Add Monitoring and Verify Recovery

I added `https://ts3-manager.<YOUR_BASE_DOMAIN>/` to the 60-second blackbox job. The candidate differed from the live Prometheus file by that one target line and passed `promtool check config`.

The intended pre-change copy failed because `/home/<YOUR_ADMIN_USERNAME>/monitoring/backups/` did not exist. I preserved the live file's inode when deploying the candidate, sent Prometheus `SIGHUP`, & confirmed readiness. I later deleted the deployment candidate, temporary validator, reconstructed rollback file, & empty backup directory at the owner's request. No Prometheus backup from this work remains.

The target validator returned 46 expected targets present and all `up`: 27 exporter targets and 19 blackbox services. The TS3 Manager blackbox target reported `up` with no last error.

I restarted the NPM container. It returned to `running` and `healthy` with restart policy `unless-stopped`; the administrator UI returned `200`, `nginx -t` passed, & TS3 Manager still returned `301` over HTTP and `200` over HTTPS. All 20 saved proxy hosts returned an expected application status after the restart, with zero failed routes.

UniFi DNS returned `192.168.85.2`, Cloudflare's public resolver returned no A answer, & UniFi reported zero port-forward rules.

Evidence: [monitoring and final verification](../../Evidence/TS3%20Manager%20Internal%20HTTPS%20-%202026-07-28/Logs/S04-Monitoring-and-Final-Verification-2026-07-28.md).

## Resulting Configuration

- NPM has 20 enabled proxy hosts: NetBird plus 19 application interfaces.
- UniFi has 20 enabled application and NetBird A records pointing to `192.168.85.2`, plus one unrelated disabled apex record.
- One logged firewall policy permits only NPM to reach TS3 Manager on TCP 9000.
- Prometheus has 46 targets, all `up`, including 19 blackbox probes through NPM.
- Public DNS has no TS3 Manager A record, and UniFi has no port forward.
- No backup or temporary deployment file from this change remains.

## Rollback Points

For the route, I can delete NPM proxy host ID `22`, DNS record ID `6a68b26f052792cd2140bfdc`, & firewall policy ID `6a68b26e052792cd2140bfd9`. Direct access at `http://192.168.80.118:9000` remains available.

Monitoring rollback means removing the TS3 Manager target from the versioned and live Prometheus files, validating with `promtool`, & sending Prometheus `SIGHUP`. There is no backup file to restore.

## Remaining Work

None. I kept Kasm, Coolify, Proxmox, NPM administration, exporters, & every other direct interface outside this change.
