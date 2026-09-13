# MeshCentral

**Created:** 2026-09-12  
**Last updated:** 2026-09-12

I run MeshCentral on `docker-blue`, CT 108 at `192.168.40.39` in Personal-A, VLAN 40. I deployed it on 2026-09-12 as a pilot, so RustDesk `hbbs` and `hbbr` keep running on the same host until I decide between them. I picked it over the alternatives because it is free and self-hosted, it serves the browser console and the endpoint agents from one port, and it supports LDAP and OIDC console login without a subscription. RustDesk's OSS backend has no central permissions or directory login, and those sit behind a paid plan.

| Item | Verified state on 2026-09-12 |
|---|---|
| Browser address | `https://192.168.40.39` |
| Version | MeshCentral 1.2.5, Hybrid (LAN + WAN) mode, Production mode |
| Image | `ghcr.io/ylianst/meshcentral:latest`, digest `sha256:45873f56b1221cf4c33a65c6a9a8c2ae8b503bd4f605a19f8b1527fbb80a7b6c` |
| Compose project | `/opt/docker/meshcentral` on `docker-blue` |
| Published port | `192.168.40.39:443` only. Container port 80 is not published |
| Certificate | Self-signed, `CN=192.168.40.39` |
| Database | NeDB, the built-in default |
| Volumes | `meshcentral_meshcentral-data`, `-files`, `-web`, and `-backups` |
| Accounts | None. The next account created through the browser becomes site administrator |
| Memory cost | `docker-blue` went from 595 MiB used to 716 MiB with MeshCentral running, leaving 1,331 MiB available of its 2 GiB |
| Disk cost | The image took the container's root filesystem from 5.7 GiB used to 6.7 GiB, leaving 7.3 GiB free of 15 GiB |

I chose a container on an existing Docker host rather than a new LXC because `blue-server` has 5,811 MiB of physical memory with 7,168 MiB already allocated across CTs 100, 104, 107, and 108. A new guest would have added a second Debian userspace, a Wazuh agent, and a node exporter before MeshCentral started. The [deployment record](Documentation/Change%20Records/Deployment%20-%202026-09-12.md) holds the sizing readback and the verification.

## Configuration

[`Configuration/docker-compose.yml`](Configuration/docker-compose.yml) is the file the host reads, copied from `/opt/docker/meshcentral/docker-compose.yml`. It follows the upstream container documentation with three local additions: the published port binds the container's 443 to the LXC address instead of every interface, `no-new-privileges` is set, and the JSON log driver is capped at three 10 MiB files.

MeshCentral writes its own `config.json` into the `meshcentral-data` volume on first start. I changed one value from the generated default: `cert`, from the placeholder `myserver.mydomain.com` to `192.168.40.39`. That name is what the server issues to agents and what it puts in its certificate, so an agent installed while the placeholder was live would have tried to reach a domain that does not exist. The generated defaults I kept are `tlsOffload: false`, `SelfUpdate: false`, `WebRTC: false`, `port: 443`, and `redirPort: 80`.

`SelfUpdate` stays false because the upstream container documentation says not to use the built-in updater in a container. Upgrades are a `docker compose pull` and `docker compose up -d`, which is also how What's Up Docker on this host reports the image.

There is no reverse proxy in front of it. Agents pin the server certificate hash, so putting Nginx Proxy Manager in the path means setting `certUrl`, `tlsOffload`, and `trustedProxy` together and enabling WebSocket support, and getting that wrong shows up as agents that connect and then drop. I will add ingress if the pilot succeeds, not during it.

## Network access

MeshCentral serves the browser and the agents over the same TCP 443.

`ObiPC` on Secure Client VLAN 60 needs no firewall policy, because Secure Client and Personal-A are both in the `Internal` zone and no block policy covers that pair. IDENTITY-A VLAN 65 sits in the `AlphaSec-Identity` zone and did need one. `Allow Identity to MeshCentral` admits `192.168.65.12` and `192.168.65.20` to `192.168.40.39:443` over IPv4 TCP, with logging and a response companion enabled and the Always schedule. It is recorded in the [firewall policy inventory](../../Infrastructure/Network/UniFi/Configuration/firewall.md).

The two domain controllers are deliberately outside that policy. Controlling a MeshCentral agent on a domain controller grants console access to the controller, so if I enroll `HQ-DC01` or `HQ-DC02` later it will be a separate decision with its own record.

## Open items

Nobody has claimed the site administrator account yet, and `NewAccounts` is still `true`, so any host that can reach TCP 443 can create the first account and hold it. Claiming the account and then setting `NewAccounts` to `false` is the first thing to do, and it is tracked in the root [TODO](../../TODO.md).

`localSessionRecording` is `true` as generated. Recorded sessions are the one part of this deployment that grows without bound, and the container's root filesystem has 7.3 GiB free, so I will either point recordings at a larger volume or turn the setting off before it matters.

I have not installed an agent, opened a remote desktop session, or tested console access while logged out, Ctrl+Alt+Delete, UAC elevation, or reconnect after reboot. Until those pass on `HQ-WS001` and `ObiPC`, this is a running server and nothing more, and RustDesk stays.

I took no snapshot and no backup for this work.
