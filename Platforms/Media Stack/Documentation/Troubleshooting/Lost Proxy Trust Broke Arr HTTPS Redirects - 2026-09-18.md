# Lost Proxy Trust Broke Arr HTTPS Redirects

**Created:** 2026-09-18  
**Last updated:** 2026-09-18

## Symptom

Grafana raised three alerts together, one each for Prowlarr, Radarr and Sonarr:

```text
WARNING: Internal service is responding slowly
https://sonarr.alphasecunited.com/ is taking 9.501s to respond.
```

Jellyfin, Seerr and qBittorrent run on the same host and stayed healthy.

The alert text describes the wrong state. `probe_success` was `0` for all three, so the probes were failing rather than answering slowly. 9.5 seconds is a deadline and not a measurement: Prometheus' default 10 second `scrape_timeout` less blackbox_exporter's default 0.5 second `--timeout-offset`. Three targets landing within a millisecond of each other is that deadline, not three backends that happen to be equally slow.

## What the probe was doing

The phase breakdown accounted for almost none of the elapsed time:

```text
sonarr  resolve 0.0022  connect 0.00076  tls 0.0077  processing 0.0052  transfer 0
```

Those phases sum to about 16 ms against a 9.5 second total. The missing time was a second TCP connection. Sonarr answered `/` with an absolute redirect carrying the wrong scheme:

```text
HTTP/2 302
location: http://sonarr.alphasecunited.com/login?returnUrl=%2F
```

The `http_2xx` module sets `follow_redirects: true`, so blackbox opened a connection to `192.168.85.2:80`. The UniFi policy "Allow Monitor to A-Access monitoring" permits `192.168.73.2` to `192.168.85.2` on TCP 9100, 9101, 9102 and 443 only, so port 80 falls through to the zone default deny and the SYN is dropped rather than refused. Blackbox blocked in connect until its deadline.

From monitor-01, 443 opened and 80 timed out. From docker-main on VLAN 40 both opened, which is why a browser never showed the fault: port 80 there reaches NPM, Force SSL answers 301 back to HTTPS, and the chain finishes in about 0.1 second with a 200. The service was never down for a person using it.

## Root cause

Sonarr, Radarr and Prowlarr do honour `X-Forwarded-Proto`. They honour it only from a proxy they have been told to trust, and they had not been told. Each app logged the cause once a minute, matching the 60 second blackbox scrape interval:

```text
2026-09-18 22:30:37.0|Debug|Microsoft.AspNetCore.HttpOverrides.ForwardedHeadersMiddleware|Unknown proxy: [::ffff:192.168.85.2]:47802
```

A .NET 8 and .NET 9 servicing change made `ForwardedHeadersMiddleware` ignore forwarded headers from any source not listed in `KnownProxies` or `KnownNetworks`. Servarr exposes that list as `TrustedNetworks` in `config.xml`, and it ships empty. With NPM untrusted, the apps discarded its `X-Forwarded-Proto: https` and built the login redirect from the scheme they were actually served on, which is HTTP.

The three containers were recreated at 12:25:06, 12:25:15 and 12:25:23 PM on images built 2026-09-16: Sonarr 4.0.20.3014-ls325, Radarr 6.4.4.10685-ls317, Prowlarr 2.6.5.5623-ls161. The first failing scrape was 12:26:39 PM.

Nothing on the monitoring or proxy side moved. blackbox-exporter and Prometheus had been running 9 days, `blackbox.yml` on monitor-01 was last written 2026-07-26, the NPM container had been running 9 days, and the UniFi policy showed 5,807,514 hits, so it long predates the fault. I could not diff the previous image, because the retained-image cleanup had already removed it.

## Fix

I set `TrustedNetworks` to `192.168.85.2`, the NPM address the apps were rejecting, through Compose environment variables in `/opt/media-stack/compose.yml`:

```yaml
      SONARR__SERVER__TRUSTEDNETWORKS: "192.168.85.2"
      RADARR__SERVER__TRUSTEDNETWORKS: "192.168.85.2"
      PROWLARR__SERVER__TRUSTEDNETWORKS: "192.168.85.2"
```

`Bootstrap.cs` binds `ServerOptions` from the app's `Server` configuration section, so the double-underscore environment form reaches the same setting the UI writes. I took the value format from `IPNetworkParser` rather than guessing it: the string is comma separated, a bare address is treated as a single host at `/32`, surrounding whitespace is tolerated, and `0.0.0.0/0` is rejected.

I recreated the three services with `docker compose up -d --pull never sonarr radarr prowlarr`. `--pull never` was deliberate, because `pull_policy: always` would otherwise have fetched images again and put a second variable into the change. The image IDs were identical before and after, so the setting was the only thing that moved.

## Verification

Each app logged the trust at startup, 10:31:39 PM for Sonarr and 10:31:40 PM for the other two:

```text
Info|ForwardedHeadersConfigurator|Trusting forwarded headers from 192.168.85.2/32
```

The redirect now carries the right scheme:

```text
location: https://sonarr.alphasecunited.com/login?returnUrl=%2F
```

From monitor-01 the full chain returns 200 in one redirect, in 0.069 s for Sonarr, 0.071 s for Radarr and 0.068 s for Prowlarr. Prometheus reports `probe_success` of `1` for all three and `probe_duration_seconds` of 0.034, 0.035 and 0.032, against the 5 second alert threshold and the 9.5 second deadline they had been hitting. All 23 blackbox targets pass, so nothing regressed. Each app's `config/host` API returns `trustedNetworks: 192.168.85.2`. The last `Unknown proxy` line was 10:31:19 PM, before the 10:31:36 PM restart, and none has appeared since.

The middleware configures `X-Forwarded-For` alongside `X-Forwarded-Proto`, so trusting NPM also restores real client addresses in the three apps' logs. Every request had been attributed to 192.168.85.2.

## Recovery point

I copied `/opt/media-stack/compose.yml` before editing it. The copy holds no withheld value, because the VPN key is a variable reference rather than a literal. It is committed as [media-01-docker-compose-2026-09-18.yml](../../../../Backups/media-01-docker-compose-2026-09-18.yml) and removed from the host.

## Follow-up

- The alert that fired said "responding slowly" for a probe that was failing outright, because a probe that times out reports its deadline as its duration and clears the 5 second threshold by definition. Corrected the same day: the latency rule is now multiplied by `probe_success`, so a failed probe is zeroed and `Internal service is unreachable` reports it at critical instead. The rule defect, which applied to all 23 blackbox targets rather than only these three, is recorded in [Latency Rule Fired on Failed Probes](../../../Prometheus/Documentation/Troubleshooting/Latency%20Rule%20Fired%20on%20Failed%20Probes%20-%202026-09-18.md).
- The blackbox target for each of these three stays at `/`. Probing the root is what caught this fault, and `/ping` would have answered 200 throughout it. The cross-VLAN hop that made the failure slow came from the broken redirect scheme and not from the target path, and with the scheme corrected the chain is one TCP connection on 443. I recorded that decision as a comment in the blackbox job in `prometheus.yml` so it is answered where it would next be asked.
- Jellyfin, Seerr and qBittorrent probe clean without this setting, so I left them alone. Jellyfin redirects relatively, to `/web/`, and never leaves HTTPS.
