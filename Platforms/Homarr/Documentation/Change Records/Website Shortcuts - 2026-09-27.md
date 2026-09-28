# Website Shortcuts

**Created:** 2026-09-27  
**Last updated:** 2026-09-27

I expanded the existing private [Dashboard](https://dashboard.alphasecunited.com/boards/dashboard) from nine to 47 website shortcuts. I created 38 apps in Homarr's Apps catalog, reused the nine existing service apps, and enabled status checks on all 47 dashboard shortcuts. I also enabled status checks by default for future widgets. There is still exactly one board, with all ten existing integration widgets and their options and integration references preserved.

The shortcuts cover the 25 internal proxy names, Nginx Proxy Manager administration, UniFi, Coolify, Windows Admin Center, all five Proxmox nodes, five additional WUD instances and eight cAdvisor interfaces. CLI Proxy API opens `/management.html`; App Portal opens `/admin/login`. Coolify opens its public dashboard but checks its local `/api/health` endpoint, so the status does not merely measure its access-login page. The [configuration reference](../../Configuration/App-Shortcuts.json) lists every name, destination, icon and alternate ping URL.

I placed the shortcuts in four columns above the existing integration widgets on the same board. Every shortcut opens in a new tab. I checked the icons and replaced three missing upstream assets before verifying the rendered page.

I compared the service and proxy inventories with running containers through SSH Manager on docker-main, docker-blue, docker-network, monitor-01, app-01, security-01, alpha-prod-01 and media-01. I excluded retired services and HTTP backends without a browser interface, such as Ollama, Gluetun, exporters and the PXE provisioning endpoint. The existing Gluetun integration widget remains on the dashboard.

## Verification and remaining reachability

Homarr's own HTTP checks returned 200 for 42 of the 47 destinations. Five timed out: Windows Admin Center and Proxmox Purple, Blue, Red and Green. The existing network policy permits Homarr to reach Grey on TCP 8006; WAC and the other nodes have separate management access restrictions. Their shortcuts and checks remain enabled. I did not change firewall policy during this task. These failures establish that Homarr could not reach those pages, not that the services were down.

Configuration readback showed one board, 47 app widgets with status enabled, ten unchanged integration widgets and no overlapping grid positions. A fresh authenticated browser session rendered all 57 items without page errors or the tested integration-error indicators. The T3 browser displayed the same 57 items, including Forgejo, Open WebUI and CLI Proxy API, with no broken images.

Homarr's status feature sends HTTP requests from the server; it is not ICMP ping or an authenticated functional test. In this release, responses below HTTP 500 are not marked as errors. A reachable login page therefore shows availability without proving that sign-in works.

The [filtered verification export](../../Evidence/Apps%20-%202026-09-27/Exports/App-Status-Verification.json) retains response codes, timings and resulting counts. I retained no full terminal transcript or screenshot. No service restart or credential change was needed.
