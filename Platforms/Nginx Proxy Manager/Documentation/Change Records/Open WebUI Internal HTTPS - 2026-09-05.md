# Open WebUI Internal HTTPS

**Created:** 2026-09-05  
**Last updated:** 2026-09-05  
**Implementation date:** 2026-09-05  
**Status:** Complete

## Outcome

I published the existing Open WebUI frontend at `https://openwebui.alphasecunited.com` for internal clients. The direct `http://192.168.40.35:3002` listener remains the recovery path. I did not add public DNS or WAN ingress.

The direct plaintext path had a side effect worth recording. When Jedi PC used `http://192.168.40.35:3002`, the UniFi intrusion prevention engine dropped Open WebUI's own folder listing, because Emerging Threats signature 2046195 (`MOVEit File Transfer - Folder Request - CVE-2023-34362 Stage 4`) matches any `GET /api/v1/folders` carrying an `Authorization: Bearer` header, and Open WebUI's frontend makes exactly that call. Splunk recorded three blocked events from Jedi PC to `192.168.40.35:3002` on 2026-09-05. Moving the browser onto the HTTPS name hides the URI from the gateway, so the false positive stops without suppressing the signature. Over HTTPS the same folder call returns `401` for an unauthenticated probe and no IPS event.

## Change

I reused the UniFi local A record pointing at NPM `192.168.85.2` and the narrow firewall path from NPM to `docker-main` TCP/3002. Through the NPM API I created enabled proxy host 28 with:

- domain `openwebui.alphasecunited.com`;
- HTTP upstream `192.168.40.35:3002`;
- wildcard certificate ID 1;
- Force SSL, HTTP/2, WebSockets, and Block Common Exploits enabled;
- caching, HSTS, and the NPM access list disabled.

I used the centralized web-account credential through the password-manager workflow. The password and short-lived NPM bearer token stayed in variables or a mode-controlled temporary directory, never appeared in command output, and the temporary material was shredded and removed after use.

I also added `https://openwebui.alphasecunited.com/` to the Prometheus blackbox job and its approved-target assertion, matching the root-path probe every other NPM name uses. My first pass at this on 2026-09-05 wrote a `/health` target into the versioned file only: the live Prometheus configuration on `monitor-01` never received it and stayed at 56 targets. I found the gap when I re-checked the target API, deployed the root-path target to the live file, validated it with `promtool`, and reloaded Prometheus with `SIGHUP`. The versioned and live files now have the same checksum.

## Verification

- NPM's database returned proxy host ID 28 with the intended domain, upstream, certificate, and feature flags, and reported 24 enabled proxy hosts.
- `/data/nginx/proxy_host/28.conf` exists and names the intended upstream, TLS certificate, HTTP/2, WebSocket, exploit-blocking, and Force SSL configuration.
- `nginx -t` passed; the NPM container remained healthy with zero restarts.
- Internal DNS resolved the name to `192.168.85.2`.
- HTTP `/` returned `301` to `https://openwebui.alphasecunited.com/`.
- HTTPS `/` returned `200`, `/health` returned `{"status":true}`, and `/api/version` returned Open WebUI 0.11.3.
- The presented wildcard certificate expires `2026-10-08 23:49:46 UTC`.
- Cloudflare's public resolver returned NXDOMAIN.
- Prometheus reported the new target in its running configuration after the reload, and the target API returned 57 of 57 targets `up` with `probe_success` of `1` for `https://openwebui.alphasecunited.com/`.

No snapshot or backup was created for this additive change.

## Rollback

Delete NPM proxy host 28 and remove the Open WebUI blackbox target. The frontend remains reachable at `http://192.168.40.35:3002`. If I abandon the internal name entirely, I also remove UniFi local DNS record `6a9b3fe6f9e5db2485a29667` and TCP/3002 from the `Allow NPM to docker-main web UIs` destination port group.
