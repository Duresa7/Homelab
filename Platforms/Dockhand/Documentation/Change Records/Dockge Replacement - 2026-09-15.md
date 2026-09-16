# Dockge Replacement

**Created:** 2026-09-15  
**Last updated:** 2026-09-15

**Implemented:** 2026-09-15  
**Verified:** 2026-09-15

I replaced the Dockge deployment from earlier today with Finsys Dockhand on `docker-main`. I kept Coolify excluded and left Portainer running for later retirement.

## Removed

I removed the seven Dockge containers, images, networks, `/opt/dockge` directories, and generated `/opt/stacks` definitions. The original applications and their Compose files remain. I removed the old credential, UniFi DNS record `6aa9c03e25574794b9085754`, and NPM proxy host 30. NPM retains its normal deleted database row, but no active Dockge configuration remains. I removed TCP 5001 from the NPM-to-docker-main allow rule. No Dockge-specific network or volume remains on any selected host. I removed the unpublished Dockge platform files after replacing their references with this record.

## Installed

I deployed `fnsys/dockhand:v1.0.48` and six `ghcr.io/finsys/hawser:0.2.48` agents, pinned by digest. The [platform record](../../README.md) lists hosts, paths, access, and the remote Compose import limitation. Each manager has `restart: unless-stopped`. The local Docker socket connects the hub; remote agents use outbound authenticated WSS through NPM.

NPM proxy host 31 forwards `dockhand.alphasecunited.com` to `http://192.168.40.35:3003`. It uses certificate 1, Force SSL, HTTP/2, Block Common Exploits, and WebSocket upgrade support. Proxy buffering is off; read and send timeouts are 3,600 seconds. UniFi record `6aa9de4e25574794b908a860` is an enabled A record to `192.168.85.2`, TTL 300. The controller has 30 DNS records and NPM has 24 enabled proxy hosts.

I changed `Allow NPM to docker-main web UIs` (`6a60fd2c2d027bb05525a873`) to destination ports `2283,3000,3001,3002,3003,6060,9443`, replacing Dockge's 5001 with Dockhand's 3003. I added two IPv4 TCP 443 policies to NPM at `192.168.85.2`, each enabled with logging and an allow-response companion:

| Policy | Source | ID | Index |
|---|---|---|---:|
| Allow alpha-prod-01 Hawser to NPM HTTPS | 192.168.80.118 | 6aa9df4e25574794b908ab6f | 10000 |
| Allow security-01 Hawser to NPM HTTPS | 192.168.72.2 | 6aa9df4e25574794b908ab72 | 10001 |

## Verification

I compared live Docker inspection with the pre-removal capture: all 62 original container IDs, running states, and start timestamps match. Every original Compose path recorded in their Docker labels still exists. The seven new manager containers bring the fleet to 69 running containers.

I logged in through HTTPS and read all seven environments, 69 containers, and 47 projects through Dockhand's API. All reported running. The six remote reads use Hawser Edge through NPM, exercising the WSS transport. Unauthenticated environment and container API requests return 401. HTTP redirects to HTTPS with 301; the HTTPS root redirects to login with 307. DNS resolves to NPM and TLS certificate verification passes.

All seven manager definitions pass `docker compose config --quiet`. Hawser token files are mode 0600; temporary bootstrap keys are absent. The old Dockge credential can no longer be retrieved. I retained only configuration references and [verification evidence](../../Evidence/Dockge%20Replacement%20-%202026-09-15/Verification.json), with no credential values. No snapshot or host-side configuration backup was created.

## Open work

Remote Compose definitions need a reviewed import before UI editing. I did not claim that visibility adopts those files. Portainer retirement remains in the [central TODO](../../../../TODO.md); its server and four Edge Agents still run. Existing lifecycle actions were not exercised because the applications stayed running throughout.
