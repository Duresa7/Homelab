# DNS Publication

**Created:** 2026-10-09  
**Last updated:** 2026-10-09

**Status:** DNS restored; SRV status and login transport verified. The custom hostname's server-list ping is still rejected by Playit.  
**Change:** 2026-10-09, 5:01 PM Eastern.  
**Verification:** 2026-10-09, 5:10 PM Eastern.

I restored `minecraft.alphasecunited.com` in Cloudflare for the [Minecraft server on Alpha](../../README.md). I reused the existing Playit allocation and the shared agent on `alpha-prod-01`.

## Records

| Type | Name | Target | Port | TTL | Proxy |
|---|---|---|---|---:|---|
| CNAME | `minecraft.alphasecunited.com` | `<REDACTED_MINECRAFT_RELAY>` | | 300 seconds | DNS only |
| SRV | `_minecraft._tcp.minecraft.alphasecunited.com` | `<REDACTED_MINECRAFT_SRV_TARGET>` | `<REDACTED_RELAY_PORT>` | 300 seconds | DNS only |

The SRV priority and weight are both 0. Its target and port match the existing Playit endpoint's public SRV record, rather than the server's local port. The origin remains `127.0.0.1:25565/tcp`, with proxy protocol disabled.

## Cloudflare change

Both exact-name API queries returned zero records before creation. I obtained the assigned public domain and port from the running Playit agent's read-only API data, checked the public SRV record against that allocation, and created the CNAME and SRV through the Cloudflare Account MCP. Both creates returned HTTP 200. Readback found exactly one record at each name, with the intended target, port, TTL and proxy state. The [redacted API export](../../Evidence/DNS%20Publication%20-%202026-10-09/Exports/Cloudflare%20DNS%20Creation.json) retains the before, create and readback results. I created no new tunnel or router port forward.

The earlier browser login was no longer present. I used the running agent's existing credential in memory on Alpha to read its assigned tunnel metadata. The credential stayed on Alpha, and no credential file was created. I retained the redacted [metadata export](../../Evidence/DNS%20Publication%20-%202026-10-09/Exports/Playit%20Agent%20Metadata.json), but no full host transcript for that read.

## Connection verification

At 5:01 PM Eastern, both 1.1.1.1 and 8.8.8.8 resolved the CNAME and SRV. Resolving the friendly name's SRV and querying its target returned Minecraft 26.3, protocol 777, zero connected players, a 20-player maximum and `AlphaSec United Minecraft` in 232.2 ms. The [DNS and protocol export](../../Evidence/DNS%20Publication%20-%202026-10-09/Exports/DNS%20and%20Minecraft%20Verification.json) retains that check and the failure below.

Sending `minecraft.alphasecunited.com` itself in the Minecraft handshake returned `ConnectionResetError`. At 5:02 PM Eastern, I tested both protocol 767 and 777: handshakes naming the resolved SRV target succeeded; handshakes naming the custom domain failed. The Playit allocation remains active with `hostname_verify_level: NoRawIp`. The [handshake comparison](../../Evidence/DNS%20Publication%20-%202026-10-09/Exports/Hostname%20Handshake%20Checks.json) retains the results. This is a Playit hostname-handling limitation, rather than missing Cloudflare records.

I repeated the protocol-777 check with the entered hostname and default port at 5:10 PM Eastern, more than nine minutes after record creation. It still returned `ConnectionResetError`. The [final server-list check](../../Evidence/DNS%20Publication%20-%202026-10-09/Exports/Final%20Server%20List%20Ping%20Check.json) retains that result.

I inspected address handling in the [official Minecraft 26.3 client](https://piston-data.mojang.com/v1/objects/e877b6a07acd633fb3bb475002175cec036e7b87/client.jar), whose downloaded SHA-1 matched `e877b6a07acd633fb3bb475002175cec036e7b87`. `ServerStatusPinger` sends the entered hostname and port, while `ConnectScreen` uses the resolved socket hostname and port when joining. The [inspection export](../../Evidence/DNS%20Publication%20-%202026-10-09/Exports/Client%20Address%20Handling.json) records those observations. I did not retain a full inspection transcript, and removed the temporary extracted classes afterward.

At 5:08 PM Eastern, a protocol-777 login transport check using the resolved SRV target reached the server and received its encryption request with online authentication required. I used `testuser` for the unauthenticated probe and closed the connection before authentication. The [login transport export](../../Evidence/DNS%20Publication%20-%202026-10-09/Exports/SRV%20Login%20Transport%20Verification.json) records the result. I have not completed an authenticated player join.

Players can use `minecraft.alphasecunited.com` without specifying a port for the SRV join route. The saved server can still display a failed ping because that check uses the entered hostname. Playit's [supported external-domain setup](https://playit.gg/support/external-domain-cloudflare/) requires Premium and account-side domain registration. I did not purchase a subscription, register an external domain in Playit, or change its hostname-verification setting.
