# Retirement

**Created:** 2026-11-12  
**Last updated:** 2026-11-12

**Status:** Complete  
**Date:** 2026-11-12

I retired NetBird from CT 107 `docker-network` (`192.168.85.2`) and removed everything I had created to run it: the control plane and its data, the routing-peer client on the guest, the proxy host, the internal DNS name, the uptime probe and the fleet-update entry. I kept no backup or snapshot of the management store, the embedded identity-provider database or the setup keys. `netbird.alphasecunited.com` is no longer published. Remote access into the lab is now the UniFi `Management Access` WireGuard server alone, described in [Access Paths](../../../../../Architecture/Access-Paths.md).

Before removal, the management store listed three peers: `docker-network` on client 0.82.0 as the Access-A routing peer, and two of my own devices on client 0.74.4, `DuresaGamingPC` (Windows) and `dkadi-mb-air3.local` (macOS). I had already uninstalled the NetBird app from both, so their peer entries were stale. The server ran management 0.80.0 and dashboard v2.94.0; a pull at 10:40 PM Eastern had newer `latest` images waiting for both, and I did not deploy them.

## Removal

Done between 10:55 PM and 11:15 PM Eastern.

| Owner | Change and observed result |
|---|---|
| Nginx Proxy Manager | I deleted proxy host 1 through the authenticated API before stopping the containers, so Nginx never held an upstream that could not resolve. The API returned `true`; the live host count went from 29 to 28 with every other ID kept, and `1.conf` is gone. Certificate 1 is shared and still assigned to hosts 10, 26, 31, 32, 37 and others. The NetBird advanced snippet moved here as [netbird-advanced-config.conf](../../Configuration/netbird-advanced-config.conf). |
| docker-network, stack | I ran `docker compose down --rmi all --volumes --remove-orphans` in `/opt/docker/netbird`. Compose reported `netbird-server` and `netbird-dashboard` removed, the `netbird_netbird` network removed, volume `netbird_netbird_data` removed, and both `netbirdio` images removed. I then deleted `/opt/docker/netbird`, which held `config.yaml`, `dashboard.env`, the Compose file and the NPM snippet copy. |
| docker-network, client | `netbird down` printed `Disconnected`, `netbird service stop` and `netbird service uninstall` reported the service stopped and uninstalled, and `apt-get purge -y netbird` removed package 0.82.0. I deleted `/etc/apt/sources.list.d/netbird.list`, `/usr/share/keyrings/netbird-archive-keyring.gpg`, `/etc/netbird` and `/var/lib/netbird`. |
| UniFi DNS | The record ID in [local DNS](../../../../../Infrastructure/Network/UniFi/Configuration/local-dns.md) no longer matched the controller. `unifi_list_dns_records` showed `netbird.alphasecunited.com` A `192.168.85.2` as `ce051b27-3f7d-499c-9bbb-c059ee33b565`, and I deleted that record. A full list afterwards returned 34 static records with no NetBird name. |
| UniFi firewall | Nothing to remove. None of the 90 firewall policies and no port forward names NetBird or UDP 3478. The Access-A egress policies serve NPM as well and stay. |
| Prometheus | I removed `https://netbird.alphasecunited.com/` from the blackbox HTTP targets and `netbird` from `Tools/uptime.py` and `Tests/assert_targets.py`, rebuilt the dashboards (the Uptime dashboard went to 108 panels), and copied `prometheus.yml` and the three changed dashboards to `monitor-01`. The live files matched the repository before the copy. `promtool check config` reported the new file valid before I swapped it in and sent HUP. |
| Ansible | I removed the `netbird` project from `docker_compose_targets` in the fleet-update inventory and from `tests/validate_project.py`, which now expects 21 projects. The validator returned `Validation passed: 12 OS-update hosts, 6 compose hosts, 21 projects.` |
| Records | I moved the platform folder and the [NetBird guide](../../../../Guides/NetBird.md) under `Archive/` and updated the living records that described NetBird as current. |

## Verification

- On `docker-network` afterwards: no package, binary, `wt0` interface or UDP 3478 listener; no NetBird container, image, volume or network. `cadvisor`, `hawser` and `nginx-proxy-manager` were running and healthy, `nginx -t` reported the configuration test successful, and `/opt/docker` holds only `cadvisor`, `hawser` and `nginx-proxy-manager`.
- Prometheus reported 49 active targets with no NetBird instance. The two down targets were `node` and `cadvisor` on `192.168.80.10`, `app-01`, which is stopped and which this work did not touch. Grafana logged no error after the dashboard files changed.
- The UniFi DNS list and the NPM host list above are the readbacks for those two removals.

No transcript is retained; the table records what each step returned. I created no snapshot and no backup, and I copied no configuration file off a host before editing it. The staging scripts I used for the NPM API call are deleted.

## Open items

- The overview, Galaxy, lab map, NPM and UniFi diagrams under `Assets/Diagrams/` still draw NetBird on `docker-network`; they need a regeneration pass.
