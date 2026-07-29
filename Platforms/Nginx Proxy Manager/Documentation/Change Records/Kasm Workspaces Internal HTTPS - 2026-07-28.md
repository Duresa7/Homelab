# Kasm Workspaces Internal HTTPS

**Created:** 2026-07-28  
**Last updated:** 2026-07-28

**Date:** 2026-07-28  
**Status:** Complete

## Scope

I published Kasm Workspaces at `https://kasm.<YOUR_BASE_DOMAIN>` through internal Nginx Proxy Manager. UniFi resolves the name to `192.168.85.2`; NPM forwards HTTPS to `192.168.78.10:443` and presents certificate ID 1.

I did not expose SSH, `node_exporter`, any Kasm database or service port, or session VLANs 74, 75, 77, & 79. Direct fallback remains `https://192.168.78.10/`, and the change added no public DNS record or WAN ingress.

## Starting State

Kasm 1.19.0 returned HTTP `200` and `{"ok": true}` on its self-signed HTTPS listener. NPM had 20 enabled proxy hosts, UniFi had no `kasm` A record, & `docker-network` timed out when connecting to `192.168.78.10:443`.

The timeout was intentional network state. LAB-MGMT accepted only the existing Trusted, Personal-A, Jedi PC, Management Access VPN, & monitoring paths.

## Step 1: Add the UniFi path

I previewed and created DNS record `6a69768d052792cd2140e39f`, which maps `kasm.<YOUR_BASE_DOMAIN>` to `192.168.85.2` with TTL 300. I also previewed and created firewall policy `6a69768a052792cd2140e39c`, which permits only `192.168.85.2` to reach `192.168.78.10` on TCP 443 and logs matches.

The first connection still timed out. A packet capture on `kasm-01` showed its SYN-ACK leaving for `192.168.85.2`, which proved the new allow admitted NPM's SYN but the return packet was dropped.

Evidence: [UniFi path and packet trace](../../Evidence/Kasm%20Workspaces%20Internal%20HTTPS%20-%202026-07-28/Logs/S01-UniFi-Path-and-Packet-Trace-2026-07-28.md).

## Step 2: Repair the stateful return path

`LABMGMT Block to <YOUR_ORG_NAME>-Access` matched `ALL` connection states. That block dropped Kasm's reply even though the forward policy had `create_allow_respond` enabled.

I previewed and changed only its state selector from `ALL` to `NEW, INVALID`. This keeps LAB-MGMT from initiating a new connection toward the Access zone while permitting replies to connections admitted in the opposite direction. The same return-path model was already active on LAB-MGMT blocks toward Internal and Observability.

After the update, NPM's host received HTTP `200` from the backend and `https://192.168.78.10/api/__healthcheck` returned `{"ok": true}`.

Evidence: [return-path repair](../../Evidence/Kasm%20Workspaces%20Internal%20HTTPS%20-%202026-07-28/Logs/S02-Return-Path-Repair-2026-07-28.md).

## Step 3: Create the NPM host

I retrieved the NPM administrator fields through 1Password secret references and passed them directly to `POST /api/tokens`. The password and bearer token stayed in process variables.

I created proxy host ID `23` with HTTPS upstream `192.168.78.10:443`, certificate ID 1, Force SSL, HTTP/2, Block Common Exploits, & WebSocket support enabled. HSTS and the NPM access list remain disabled.

NPM generated `data/nginx/proxy_host/23.conf`, & `nginx -t` passed. HTTP returned `301` to the HTTPS name; HTTPS returned `200` with certificate verification result `0`; `/api/__healthcheck` returned `{"ok": true}`.

Evidence: [NPM host and route verification](../../Evidence/Kasm%20Workspaces%20Internal%20HTTPS%20-%202026-07-28/Logs/S03-NPM-Host-and-Route-Verification-2026-07-28.md).

## Step 4: Add monitoring

I added `https://kasm.<YOUR_BASE_DOMAIN>/` to the 60-second blackbox job. This raises the Prometheus target set from 47 to 48 and the NPM probe set from 19 to 20.

Prometheus accepted the changed host file after `promtool check config`, but the host-side `sed -i` replaced its inode. The running container retained an older inode with 19 placeholder targets, so `up=1` only proved blackbox_exporter answered while `probe_success=0` proved those service probes failed. I wrote the validated host file through the existing mount, matched the host and container SHA-256 digests, passed `promtool` again, & reloaded without a container restart.

The active-target check returned 20 blackbox targets, each with `probe_success=1`. The [existing inode troubleshooting record](../../../Prometheus/Documentation/Troubleshooting/Single-File%20Bind%20Mount%20Retained%20the%20Old%20Inode%20-%202026-07-13.md) now records the recurrence and the no-restart correction.

Evidence: [Prometheus probe](../../Evidence/Kasm%20Workspaces%20Internal%20HTTPS%20-%202026-07-28/Logs/S04-Prometheus-Probe-2026-07-28.md).

## Resulting Configuration

- NPM proxy host ID `23` serves `kasm.<YOUR_BASE_DOMAIN>` through HTTPS on both proxy legs.
- UniFi DNS record `6a69768d052792cd2140e39f` points the internal name to NPM.
- UniFi firewall policy `6a69768a052792cd2140e39c` permits one source, one destination, & TCP 443.
- The LAB-MGMT-to-Access block still rejects `NEW` and `INVALID` traffic.
- Prometheus probes 20 NPM names once per minute.

## Verification

An Internal-zone Windows client resolved the name to `192.168.85.2`. HTTP returned `301`, HTTPS returned `200`, certificate verification returned `0`, & the Kasm health endpoint returned `{"ok": true}`. NPM's generated configuration passed `nginx -t`. Cloudflare's public resolver returned NXDOMAIN, UniFi listed zero port forwards, & Prometheus reported 48 of 48 scrape targets `up`. All 20 active blackbox targets also returned `probe_success=1`.

## Rollback Points

Route rollback means deleting NPM proxy host ID `23`, DNS record `6a69768d052792cd2140e39f`, & firewall policy `6a69768a052792cd2140e39c`. Direct access remains available.

Monitoring rollback means removing the Kasm target, validating Prometheus, & reloading it. Restoring the LAB-MGMT-to-Access block to `ALL` would also break any approved Access-zone connection into LAB-MGMT, so that state repair is not part of route rollback.

## Remaining Work

None.
