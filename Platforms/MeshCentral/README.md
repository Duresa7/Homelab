# MeshCentral

**Created:** 2026-09-12  
**Last updated:** 2026-09-13

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
| Accounts | Site administrator claimed 2026-09-13; `NewAccounts` is `false`, so the browser no longer offers registration |
| Enrolled devices | `HQ-MGT01` and `DuresaGamingPC`, both connected on 2026-09-13 |
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

`ObiPC` on Secure Client VLAN 60 needs no firewall policy, because Secure Client and Personal-A are both in the `Internal` zone and no block policy covers that pair. IDENTITY-A VLAN 65 sits in the `AlphaSec-Identity` zone and did need one. `Allow Identity to MeshCentral` admits `192.168.65.12` and `192.168.65.20` to `192.168.40.39:443` over IPv4 TCP, with logging and a response companion enabled and the Always schedule. It is recorded in the [firewall policy inventory](../../Infrastructure/Network/UniFi/Configuration/firewall.md). Both named hosts are demonstrated: `HQ-MGT01` on 2026-09-12 and `HQ-WS001` through its QEMU guest agent on 2026-09-13. `ObiPC` has not been tested, because it was unreachable on both days.

The two domain controllers are deliberately outside that policy. Controlling a MeshCentral agent on a domain controller grants console access to the controller, so if I enroll `HQ-DC01` or `HQ-DC02` later it will be a separate decision with its own record.

## Enrolled devices

I installed the agent by hand on two machines on 2026-09-13 and read the result back from the server at 12:19 AM EDT.

| Device | Address | VLAN | How it reaches the server |
|---|---|---|---|
| `HQ-MGT01` | `192.168.65.12` | IDENTITY-A 65 | The `Allow Identity to MeshCentral` policy |
| `DuresaGamingPC` | `192.168.50.241` | Secure 50 | No policy needed; Secure and Personal-A are both in the `Internal` zone |

`DuresaGamingPC` is the Windows hostname of the machine UniFi lists as `Jedi PC`. Both devices held four established TCP 443 sessions to the container at that reading, and the server's database holds a record for each.

That `DuresaGamingPC` needed no firewall change is the general case, not an exception: every network in the `Internal` zone except Trusted VLAN 10 already reaches Personal-A. Only IDENTITY-A sits outside it, which is why it was the one zone that needed a rule.

`HQ-WS001` is still unenrolled. Its network path is verified and the existing policy covers it, so it needs no further network work.

## Open items

I claimed the site administrator account on 2026-09-13 and set `NewAccounts` to `false`, so the server no longer hands administrator rights to the next visitor. The [change record](Documentation/Change%20Records/Registration%20Closed%20and%20Test%20Machine%20Path%20Verified%20-%202026-09-13.md) holds that work and the `HQ-WS001` path test.

`localSessionRecording` is `true` as generated, but nothing is being recorded. Server-side recording needs a `sessionRecording` block with a `filepath`, which this configuration does not have. I checked on 2026-09-13 after the first two desktop sessions: no recordings directory exists, no `.mcrec` files exist anywhere under `/opt/meshcentral`, and the event database holds no recording events. The line in the [deployment record](Documentation/Change%20Records/Deployment%20-%202026-09-12.md) calling recordings the one part that grows without bound was written from the setting name and is wrong as the server is configured. If I want an audit trail later, it is that config block plus a volume with room.

Two agents are enrolled and connected. I have not yet tested console access while logged out, Ctrl+Alt+Delete, UAC elevation, or reconnect after reboot, and those four are what decide whether MeshCentral replaces RustDesk. RustDesk stays until they pass.

I took no snapshot and no backup for this work.
