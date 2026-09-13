# WebRTC Enabled

**Created:** 2026-09-13  
**Last updated:** 2026-09-13  
**Implementation:** 2026-09-13  
**Verification:** 2026-09-13

I set `"WebRTC": true` in `config.json` and restarted the container at 12:53 PM EDT. It had been `false`, which is the generated default. With it on, the browser and the agent attempt a direct peer-to-peer channel for desktop and file traffic instead of relaying everything through the server on `docker-blue`.

The server returned HTTP 200 through `https://mesh.alphasecunited.com` after the restart, logged no errors, and the tracked [`Configuration/config.json`](../../Configuration/config.json) matches the container at MD5 `0ee1daf9faba9dd25fe87e5dcded4633`.

## What this needs from the network, and what I did not open

Signalling is unaffected: the candidate exchange rides the existing TCP 443 WebSocket, which already works through Nginx Proxy Manager. What peer-to-peer needs is a direct path between the machine running the browser and the machine running the agent, on ephemeral high UDP ports, which never touches the server or the proxy.

| Pair | Zones | Peer-to-peer today |
|---|---|---|
| `ubuntu-dev` and `DuresaGamingPC` | Personal-A 40 and Secure 50, both `Internal` | Permitted. Intra-zone traffic is allowed and no block policy covers that pair |
| Either of those and `HQ-MGT01` | `Internal` and `AlphaSec-Identity` | Blocked. The identity boundary permits only named services |

Across the identity boundary the enabled policies are RDP 3389, WAC HTTPS 443, the Action1 service ports, WinRM, and the MeshCentral 443 rule. Ephemeral UDP is not among them in either direction, so a session between a browser in `Internal` and the agent on `HQ-MGT01` will fail its connectivity checks and fall back to relaying through the server.

I left that boundary closed on purpose and added no firewall policy for this change. Making peer-to-peer work there means allowing a high ephemeral UDP range between `Internal` hosts and `192.168.65.12` in both directions, which is a far wider hole than the single-port rules that boundary carries today. The thing it buys is lower latency on a local network where the relay already crosses two switch hops, and the fallback costs nothing but some traffic through a container that is not under load. That trade does not favour opening it, so it stays a decision rather than an action.

## How to tell which path a session used

MeshCentral records a relay session in its event log when traffic goes through the server. A desktop session that negotiates peer-to-peer successfully does not produce that event, and the session's own connection indicator in the browser reports the connection type. The next desktop session between `ubuntu-dev` and `DuresaGamingPC` is the one to watch, since that pair is the only one currently able to connect directly.

I have not yet observed a session under this setting, so nothing here establishes that peer-to-peer actually negotiates on this network. It establishes that the setting is live and that the network permits one of the three pairs to try.

## Related

Session recording is off in practice, so nothing is lost by traffic bypassing the server. If server-side recording is ever configured, peer-to-peer traffic would not be captured by it, because the server never sees it.
