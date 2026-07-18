# NetBird Troubleshooting Log

**Created:** 2026-07-11  
**Last updated:** 2026-07-17

This is the chronological troubleshooting record for the combined `docker-network` access-stack deployment. Configuration remains owned by its platform or infrastructure system; the combined deployment narrative is recorded here and linked from the [evidence index](../Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Evidence-Index.md).

## Quick Index

| # | Step | Symptom | Resolution | Status |
|---:|---|---|---|---|
| 1 | Preflight | `pvestatd` failed on `blue-server` | Restart restored status temporarily; recurring issue transferred to Galaxy | Recurring / transferred |
| 2 | S08 | Official NetBird installer stopped because `jq` was missing | Installed Debian `jq` and reran from a clean state | Resolved |
| 3 | S08 | First embedded identity-provider probe reset during recreation | Two-second retry returned HTTP `200` | Resolved |
| 4 | S05A | UniFi rejected the first web-egress policy create | Set `create_allow_respond` to `false` and reapplied | Resolved |
| 5 | S05A | Handcrafted NTP probe returned no conclusive response | Installed `ntpsec-ntpdig` and verified Cloudflare NTP | Resolved |
| 6 | S07 | NPM Advanced gear dismissed the proxy-host modal | Saved the basic host first, then applied Advanced configuration | Resolved |
| 7 | S07 | 1Password CLI session was signed out during token storage | Reauthenticated and stored the zone-scoped token in REDACTED_1PASSWORD_VAULT_002 | Resolved |
| 8 | S07 | One-time token required secure recovery and staging cleanup | Used ephemeral staging, stored the item, and cleared the staging path | Resolved |
| 9 | S09 | First post-restart screenshot was black | Re-rendered the authenticated dashboard and recaptured the step | Resolved |
| 10 | Audit | Early step records contained summaries without every automation envelope | Recovered secret-free source records and documented upstream limits | Resolved with exceptions noted |
| 11 | Operational follow-up | Routing peer Management channel returned HTTP `502` after sequential container recreation | Reloaded validated NPM configuration to refresh the changed NetBird upstream address | Resolved |

## 1. `pvestatd` Was Failed on `blue-server`

**Date:** 2026-07-10  
**Owner:** Galaxy / Proxmox

**Symptom:** Preflight inspection found the Proxmox `pvestatd` service in a failed state on `blue-server`.

**Investigation:** The service state was checked before continuing with guest provisioning. No application deployment action could explain the pre-existing failure, and no root cause was established during this bounded task.

**Corrective action:** `pvestatd` was restarted on `blue-server`.

**Verification:** A follow-up service check returned `active`. LXC state and Proxmox statistics were available afterward.

**Follow-up:** The service failed again after this temporary recovery. The 2026-07-13 investigation confirmed recurring crashes and transferred the open issue to the authoritative [Galaxy troubleshooting log](../../../Infrastructure/Compute/Galaxy/Documentation/Troubleshooting-Log.md#1-recurring-pvestatd-failure-on-blue-server) and [Galaxy TODO](../../../Infrastructure/Compute/Galaxy/Documentation/TODO.md#blue-server-recurring-pvestatd-crashes).

## 2. NetBird Installer Required `jq`

**Date:** 2026-07-10  
**Step:** S08

**Symptom and exact error:** The official installer exited `1` before generating configuration:

```text
jq is not installed or not in PATH, please install with your package manager. e.g. sudo apt install jq
installer_exit=1
```

**Investigation:** The generated `config.yaml` and `docker-compose.yml` were checked and confirmed absent, proving the failure occurred before partial initialization.

**Corrective action:** Debian's `jq` 1.7 package was installed and the official v0.74.3 installer was rerun with the approved Nginx Proxy Manager option.

**Verification:** The second run exited `0`, generated the expected files, and started both NetBird containers. See [S08](../Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Logs/S08-NetBird-Control-Plane-2026-07-10.md).

## 3. Embedded Identity-Provider Probe Raced Container Recreation

**Date:** 2026-07-10  
**Step:** S08

**Symptom:** The first embedded identity-provider request immediately after recreating `netbird-server` returned `Recv failure: Connection reset by peer`.

**Hypothesis and test:** The request reached the container during its startup transition. The same health check was repeated two seconds later.

**Verification:** The retry returned HTTP `200`; subsequent direct and Nginx Proxy Manager network-path checks also returned `200`. No configuration change was required.

## 4. UniFi Rejected the First Web-Egress Policy Create

**Date:** 2026-07-11  
**Step:** S05A  
**Owner:** UniFi

**Symptom and exact error:** The first create request for the web-egress policy failed:

```text
api.err.FirewallPolicyCreateRespondTrafficPolicyNotAllowed
Firewall policy create respond traffic not allowed
```

**Failed attempt:** The initial payload used the tool's default `create_allow_respond: true` for an REDACTED_PRIVATE_ORG_LABEL-Access-to-External policy. UniFi did not create the rule.

**Hypothesis and test:** Respond-traffic generation is not allowed for this policy direction. The same payload was previewed again with `create_allow_respond: false`.

**Corrective action:** The corrected payload was applied. The web, NTP, and catch-all block policies were then created in this order:

1. `Allow docker-network Web Egress` — TCP 80 and 443 from `192.168.85.2`.
2. `Allow docker-network NTP Egress` — UDP 123 from `192.168.85.2`.
3. `Block REDACTED_PRIVATE_ORG_LABEL-Access Other External Egress` — remaining IPv4 traffic.

All three policies have logging enabled.

**Verification:** UniFi returned the three policies at indexes 10000, 10001, and 10002. HTTP returned `200`, the Docker Registry HTTPS endpoint returned its expected unauthenticated `401`, and external TCP DNS to `REDACTED_IPV4_001:53` timed out as intended. The [policy screenshot](../Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S05A-UniFi-Access-A-Egress-Policies-After-2026-07-11.jpg) shows the final ordered rules.

## 5. Handcrafted NTP Probe Was Inconclusive

**Date:** 2026-07-11  
**Step:** S05A

**Symptom:** A handcrafted UDP NTP packet produced an empty response, so it could not prove either successful NTP egress or a firewall failure.

**Investigation:** Web egress and the expected blocked external DNS test behaved correctly, which narrowed the uncertainty to the test method rather than the overall ruleset. An empty UDP result alone was not treated as proof.

**Corrective action:** `ntpsec-ntpdig` and its `python3-ntp` dependency were installed from Debian. The purpose-built client queried `time.cloudflare.com` over IPv4 with a five-second timeout.

**Verification:** `ntpdig` exited `0` and returned a valid response from `REDACTED_IPV4_012`, stratum 3, with measured delay. UDP 123 egress is therefore verified.

## 6. NPM Advanced Gear Dismissed the Proxy-Host Modal

**Date:** 2026-07-11  
**Step:** S07  
**Owner:** Nginx Proxy Manager

**Symptom:** The NetBird proxy-host form was populated with the intended domain, upstream dashboard container, WebSocket support, and common-exploit blocking. Selecting the gear control intended for Advanced configuration dismissed the modal.

**Observed result:** The Proxy Hosts page still showed no saved NetBird host. No partial proxy-host change was claimed or retained.

**Root cause:** Not established. The interaction may have targeted a dismiss control or encountered an NPM UI behavior that requires saving the basic host before editing Advanced settings.

**Corrective action:** The form was reopened and the basic proxy host was saved first with upstream `http://netbird-dashboard:80`, Block Common Exploits, and WebSocket Support. After the Online host row appeared, it was reopened and the 1,296-character [checked-in advanced configuration](../../Nginx%20Proxy%20Manager/Configuration/netbird-advanced-config.conf) was applied.

**Verification:** The proxy host reports Online, `nginx -t` succeeds, and a Host-header request through NPM returns the NetBird dashboard with HTTP `200`. The original modal issue is resolved. Subsequent S07 work issued and assigned the Let's Encrypt certificate, enabled Force SSL and HTTP/2, and validated the HTTPS endpoint.

## 7. 1Password CLI Session Was Signed Out During Token Storage

**Date:** 2026-07-11  
**Step:** S07  
**Owner:** Credential storage

**Symptom and exact error:** The 1Password CLI was no longer authenticated when the Cloudflare DNS token was ready to be stored. `op whoami --format json` returned:

```text
[ERROR] 2026/07/11 02:15:05 account is not signed in
```

**Investigation:** The failed attempt was stopped before writing an incomplete item or printing the token. The non-secret `whoami` result confirmed that reauthentication was required.

**Corrective action:** The operator ran `op signin --account my.1password.com`, which exited `0`. An API Credential item for the zone-scoped token was then created in the REDACTED_1PASSWORD_VAULT_002 vault as `REDACTED_1PASSWORD_ITEM_TITLE`; the token value was supplied without placing it in a visible command, transcript, screenshot, or repository file.

**Verification:** Non-secret item metadata confirmed that `REDACTED_1PASSWORD_ITEM_TITLE` exists in the REDACTED_1PASSWORD_VAULT_002 vault. Nginx Proxy Manager used the credential to complete DNS-01 issuance for the wildcard/apex certificate.

## 8. Cloudflare Token Recovery and Staging Cleanup

**Date:** 2026-07-11  
**Step:** S07  
**Owner:** Credential handling

**Symptom:** The token was already present in Nginx Proxy Manager's local SQLite metadata, but the interrupted 1Password step required it to be transferred into protected storage without printing it or copying it into repository content or retained evidence.

**Investigation:** The 53-byte value was read from Nginx Proxy Manager's local SQLite metadata and staged in a mode-`0600` task temporary file without printing it. SSH Manager transferred it to a matching mode-`0600` local task temporary file.

**Corrective action:** The local staging file was piped to `op item create --vault REDACTED_1PASSWORD_VAULT_002 - --format json`, creating `REDACTED_1PASSWORD_ITEM_TITLE`. The remote and local staging files were then shredded and removed. The live Nginx Proxy Manager credential remained outside Git as application data.

**Verification:** Non-secret metadata confirmed the 1Password item, and follow-up checks verified that both staging paths were absent. Certificate issuance succeeded, and retained documentation, screenshots, and repository configuration contain only the token's non-secret name and scope.

## 9. First S09 Screenshot Was Black

**Date:** 2026-07-11  
**Step:** S09

**Symptom:** The first Windows computer-control capture after the controlled Compose restarts was black and did not provide usable evidence of the resulting state.

**Investigation:** The application health checks and HTTPS request had already passed, which isolated the problem to screenshot capture rather than the NetBird service.

**Corrective action:** The authenticated NetBird dashboard was brought back to the foreground and allowed to render before the step was captured again. The unusable image was replaced rather than retained as successful evidence.

**Verification:** The recaptured S09 screenshot shows the authenticated, healthy NetBird dashboard after both Compose projects restarted. Independent post-restart checks showed Nginx Proxy Manager healthy, both NetBird containers running, `nginx -t` successful, and HTTPS returning `200`.

## 10. Pre-Commit Audit Found Summary-Only Early Evidence

**Date:** 2026-07-11  
**Steps:** S01, S03, S04, S05, S05A, S06, and S08

**Symptom:** A standards review found that several early Markdown transcripts retained readable summaries and final verification but did not preserve every original automation envelope and tool-returned result in the task evidence folder.

**Investigation:** The original requests and results remained available in the local Codex rollout record for this task. Each affected call was correlated by call ID, including deferred wait results for long-running SSH operations. The selected records were scanned for private keys, Cloudflare credential values, NetBird secret fields, and password assignments before retention.

**Corrective action:** Exact selected `response_item` records were exported as step-specific JSON files under the deployment `Evidence/.../Logs/` folder and linked from the affected Markdown transcripts and evidence index. No redaction was required because the selected records passed the secret scan. Where SSH Manager had already replaced verbose output with an explicit truncation marker, the gap was disclosed instead of reconstructed.

**Verification:** All recovered files parse as JSON, all new local links resolve, and secret-pattern checks remain clear. S04's truncated wrapper output is supplemented by its separately retained complete raw install log. S03, S05, and S08 preserve their exact upstream truncation markers plus complete exit results and independent post-change verification.

## 11. NPM Retained a Stale NetBird Upstream Address After Recreation

**Date:** 2026-07-12  
**Step:** Operational follow-up / bounded logging

**Symptom and exact error:** Immediately after NPM was recreated and then the NetBird containers were recreated to apply bounded logging, direct dashboard and identity-provider probes returned HTTP `200`, NPM was healthy, HTTPS returned `200`, and Signal was connected, but `netbird status` reported:

```text
Management: Disconnected, reason: rpc error: code = Unavailable desc = unexpected HTTP status code received from server: 502 (Bad Gateway)
```

**Investigation:** The failure reproduced for more than 90 seconds. NPM's proxy error log showed management and signal requests still being sent to `grpc://172.31.85.2:80`. Docker inspection showed that after recreation `172.31.85.2` belonged to `netbird-dashboard`, while `netbird-server` had moved to `172.31.85.3`. NPM had started before the NetBird recreation and Nginx retained the address resolved at its earlier configuration load.

**Root cause:** Sequential recreation changed the dynamic NetBird container addresses after Nginx had resolved the service names. The Compose definitions and advanced proxy routes were correct; the loaded Nginx upstream address was stale.

**Corrective action:** `nginx -t` was run successfully inside `nginx-proxy-manager`, followed by a non-disruptive Nginx reload to refresh service-name resolution. No Compose, network, port, or NetBird configuration was changed.

**Verification:** The original `netbird status` check then returned both `Management: Connected` and `Signal: Connected`. Direct dashboard and identity-provider probes, NPM-to-NetBird probes, and the HTTPS client path all returned HTTP `200`; NPM remained `healthy`, and Docker inspection still showed `max-size=10m` and `max-file=3` on all three containers. See the [operational follow-up evidence](../Evidence/Operational%20Follow-ups%20-%202026-07-12/Evidence-Index.md).
