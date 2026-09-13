# Internal HTTPS Through Nginx Proxy Manager

**Created:** 2026-09-13  
**Last updated:** 2026-09-13  
**Implementation:** 2026-09-13  
**Verification:** 2026-09-13

I moved MeshCentral onto `https://mesh.alphasecunited.com` behind Nginx Proxy Manager so it presents the shared Let's Encrypt wildcard certificate instead of a self-signed certificate for a bare address. The work ran from 01:05 AM to 01:21 AM EDT.

The reason is the [Linux agent installer trap](../Troubleshooting/Linux%20agent%20installer%20cannot%20download%20the%20agent%20over%20a%20self-signed%20certificate%20-%202026-09-13.md): `meshinstall.sh` downloads the agent with bare `wget` and `curl`, so a server nothing trusts means editing the script on every Linux install. A certificate the machines already trust removes that permanently, and removes the browser warning with it.

## What I changed

| Layer | Change |
|---|---|
| UniFi local DNS | A record `mesh.alphasecunited.com` to `192.168.85.2`, TTL 300, record ID `6aa6313625574794b9fefb1b` |
| UniFi firewall | `Allow NPM to docker-blue MeshCentral`, policy ID `6aa6311c25574794b9fefad6` |
| Nginx Proxy Manager | Proxy host 29, `mesh.alphasecunited.com` to `https://192.168.40.39:443` |
| MeshCentral | `cert`, `certUrl`, and `trustedProxy` in `config.json` |

The firewall policy admits only `192.168.85.2` in `AlphaSec-Access` to `192.168.40.39:443` in Internal over IPv4 TCP, with logging and a response companion enabled at creation and the Always schedule. I asked for index 10001 and the controller assigned 10006. The user-defined total went from 84 to 85. The existing `Allow NPM to docker-blue Executor` covers port 4788 only, which is why a second policy was needed for the same pair of hosts.

The proxy host copies the settings of the Executor host on the same backend: certificate 1, the wildcard and apex certificate, Force SSL, HTTP/2, block common exploits, caching off, and the same advanced block turning off buffering and setting the three timeouts to 3,600 seconds. WebSocket upgrade is enabled, which MeshCentral needs for both the browser and the agents. It forwards over HTTPS rather than HTTP, so the traffic between Nginx Proxy Manager and `docker-blue` stays encrypted.

In `config.json` I set `cert` to `mesh.alphasecunited.com`, `certUrl` to `https://mesh.alphasecunited.com`, and `trustedProxy` to `192.168.85.2`. I left `tlsOffload` at `false` deliberately: MeshCentral keeps terminating TLS on its own 443, so the direct address still serves HTTPS and the agents installed against it keep a working transport. Turning offload on would have made MeshCentral serve plain HTTP and stranded them.

## Why this was safe to attempt

Before changing anything I compared what the server hands to agents through each path. `MeshServer` and `ServerID` were identical whether I requested the settings through the proxy name or the direct address:

```
ServerID=E44B4D5C61543BF9…(truncated)
MeshServer=wss://192.168.40.39:443/agent.ashx
```

`ServerID` is a hash of `agentserver-cert-public.crt`, which is the agent's trust anchor and is not the web certificate. Renaming the server and putting a proxy in front of it does not touch that file, so this was reversible rather than a one-way door. I took a copy of `config.json` first, and it is in [Backups](../../../../Backups/docker-blue-meshcentral-config-pre-proxy-2026-09-13.json); I removed it from the host once the new configuration worked.

## Verification

| Check | Result |
|---|---|
| `mesh.alphasecunited.com` resolves | `192.168.85.2` |
| `curl https://mesh.alphasecunited.com/` with validation on | `status=200 ssl_verify=0` |
| Certificate presented | `CN=*.alphasecunited.com`, issuer Let's Encrypt `YE1`, expires 2026-12-08 |
| Advertised agent URL after the change | `MeshServer=wss://mesh.alphasecunited.com:443/agent.ashx` |
| Agents after the restart | All three reconnected: `192.168.40.179`, `192.168.50.241`, `192.168.65.12` |
| Install command with no certificate flags | Downloaded and installed |
| `ubuntu-dev` agent after reinstall | Connects to `192.168.85.2:443`, service active |
| Live configuration tracked | `Configuration/config.json`, MD5 `44960c07b2bc865a9f0483b69aeeeebe` at 1,333 bytes, matching the container |

The install proof is the point of the exercise. I re-ran the generated command on `ubuntu-dev` with no `--no-check-certificate` anywhere, against the new name, and it downloaded the script, the agent, and the settings, then reported `Installing service [DONE]` and `Starting service... [OK]`. The agent now reaches the server through Nginx Proxy Manager.

## Open and unresolved

`DuresaGamingPC` was connected at 01:17:34 AM and 01:18:08 AM, after the configuration change and restart, and was absent from three connection samples taken 8 seconds apart from 01:21:05 AM. Its own firewall refuses TCP 135, 139, and 445 from `ubuntu-dev`, so I could not establish whether the machine is powered on. The change had already proven itself on that agent before the disconnection, and `Allow Internal to AlphaSec-Access` permits Secure VLAN 50 to reach Nginx Proxy Manager on any port, so no firewall work is outstanding for it. It needs a look at the machine.

MeshCentral logged one certificate name error at startup while it regenerated its own certificate for the new name:

```
Error: mesh.alphasecunited.com does not match name in TLS certificate: 192.168.40.39, localhost
```

It appeared once and has not repeated. The direct address now serves `CN=mesh.alphasecunited.com`.

The two agents still installed against `192.168.40.39` keep working, because MeshCentral still terminates TLS there. They will move to the proxy name when I reinstall them, which is not urgent.

I took no snapshot and no backup beyond the configuration copy described above.
