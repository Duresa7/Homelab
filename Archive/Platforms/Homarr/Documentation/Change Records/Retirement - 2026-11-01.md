# Retirement

**Created:** 2026-11-01  
**Last updated:** 2026-11-01

**Status:** Complete  
**Date:** 2026-11-01

I retired Homarr 1.77.2 from CT 110 `docker-main` (`192.168.40.35`) and removed everything I had created to run it or feed its widgets: the deployment and its data, the proxy host, the DNS name, both firewall changes, the Proxmox API account, the Gluetun control API on `media-01`, the fleet-update entry, and the credentials stored for its integrations. I kept no backup or snapshot of the application, its SQLite data or its encryption key. `dashboard.alphasecunited.com` is no longer published, and nothing replaces it.

## Removal

| Owner | Change and observed result |
|---|---|
| Docker Main | I ran `docker compose down --rmi all --volumes --remove-orphans` in `/opt/docker/homarr`. Compose reported the `homarr` container, the `homarr_default` network and the `ghcr.io/homarr-labs/homarr:v1.77.2` image removed. I then deleted `/opt/docker/homarr`, including `.env` with the encryption key and `appdata` with the embedded database, 6.8 MiB in total. Afterwards no Homarr container, image or network remained, nothing listened on TCP 7575, `docker compose ls -a` no longer listed the project, and the other 17 containers were still running. Dockhand holds no stack or schedule for it, only event history for the old container. |
| Nginx Proxy Manager | I deleted proxy host 34 through the authenticated API. The live host count went from 25 to 24, with every other ID kept; `34.conf` is gone, `nginx -t` passed, the container stayed healthy and no host reported offline. Certificate 1 is shared and still in use. |
| UniFi DNS | I read record `6ab90b1425574794b9328224` back as `dashboard.alphasecunited.com` A `192.168.85.2`, then deleted it. A full list returned 30 static records with no dashboard name. |
| UniFi firewall | I deleted `Allow Homarr to Grey Proxmox API` (`6ab919b425574794b932ace9`, TCP 8006 from `192.168.40.35` to `192.168.70.10`). I removed TCP 7575 from `Allow NPM to docker-main web UIs` (`6a60fd2c2d027bb05525a873`). Readback showed destination ports `2283,3000,3002,3003,3004,3005,6060` with the source object, destination address, zones and index 10002 unchanged. |
| Proxmox | I removed token `homarr@pve!dashboard` and then user `homarr@pve`. `pveum` printed `ignore invalid acl token 'homarr@pve!dashboard'` while the user was deleted, the same message the 2026-09-26 dashboard retirement produced. Readback listed `dkadi@pam`, `dkadi@pve`, `pve-exporter@pve` and `root@pam`, no ACL entry naming Homarr, and the monitoring token `pve-exporter@pve!monitor01` still in place. Prometheus still had `pve_up` series afterwards. |
| Media Stack | Homarr's VPN widget was the only client of Gluetun's control API. In `/opt/media-stack/compose.yml` I set `FIREWALL_INPUT_PORTS` back to `8080`, removed the `192.168.40.42:8000:8000/tcp` binding, and deleted `/opt/media-stack/config/gluetun/auth`, which held the GET-only role and its API key. `docker compose --profile vpn config --quiet` passed. I recreated only `gluetun` and `qbittorrent` with `--no-deps --force-recreate --pull never`, at 5:08 AM Eastern; Compose reported Gluetun healthy before starting qBittorrent. Details are under Verification. |
| Fleet updates | I removed the `homarr` project from `inventory/hosts.yml` and `tests/validate_project.py`, and lowered the validator's expected project count from 23 to 22, both in the repository and in the live `/home/ansible/fleet-updates` on `ansible-01`. The two copies have the same SHA-256 hashes, and the live validator passed with 12 OS-update hosts, six Compose hosts and 22 projects. |
| Credentials | I deleted `Homarr API Token - Proxmox Galaxy` and `Homarr API Token - Gluetun media-01` from the automation vault. I also deleted two items left from the 2026-09-26 Homelab Dashboard retirement once I had shown nothing used them. `API Credential: Prox Dashboard` held the `local-dash@pve!readonly` token, which Proxmox no longer has. `Homelab-Dashboard` held a UniFi API key. The controller's integration API answered that key with 401 while the UniFi MCP key got 200 on the same request, and its digest matched no key configured on `docker-blue`. The vault holds 92 items, and none is titled for Homarr. |

Homarr's other integrations used credentials that other things still use: the existing Sonarr, Radarr, Prowlarr and Seerr API keys, and the standard application login for qBittorrent, Jellyfin and PeaNUT. They went away with Homarr's encrypted database, and I left the keys themselves in place. Homarr was never added to Prometheus, the uptime dashboard or Grafana alerting, so monitoring needed no change.

## Verification

At 5:13 AM Eastern, the [final verification export](../../Evidence/Retirement%20-%202026-11-01/Exports/Final-Verification.json) showed:

- 24 live NPM proxy hosts, none for `dashboard.alphasecunited.com` and none offline.
- Every one of the 24 remaining HTTPS names answered with its usual response or redirect over verified TLS. App Portal returned its existing root-path 404; none returned a gateway or connection error.
- `dashboard.alphasecunited.com` gets no answer from the UniFi gateway at `192.168.1.1` or from `1.1.1.1`, and the system resolver on Ubuntu-dev fails to resolve it.

On `media-01`, Gluetun was healthy with zero restarts, and qBittorrent was running in Gluetun's network namespace (`container:<gluetun id>`) with zero restarts. Docker showed only `8080/tcp` published, nothing listened on TCP 8000, and a request to `192.168.40.42:8000` got no connection. The forwarded port in `/gluetun/forwarded_port` matched qBittorrent's `Session\Port`, 60737. Gluetun's port-forward up command logged `Connection refused` twice at 5:09 AM because it fired before qBittorrent had started. The listening port was already correct, so I made no change. `https://qbittorrent.alphasecunited.com` returned 200 through NPM.

Prometheus reported 49 of 51 active targets up after the work. The two down targets are `node` and `cadvisor` on `192.168.80.10`, which Homarr never touched.

The JSON export holds the NPM, HTTPS and DNS results. The Docker, Proxmox, UniFi, Gluetun, Ansible and vault steps have no retained transcript; the table above records what each one returned. I created no snapshot and no backup, and I copied no configuration file off a host before editing it. The scripts I staged on Ubuntu-dev to deploy, configure and now remove Homarr, along with the upstream source tree I had checked out for its API, are deleted. Nothing is open for this retirement.
