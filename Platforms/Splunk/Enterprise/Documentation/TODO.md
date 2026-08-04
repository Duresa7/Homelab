# To-Do

**Created:** 2026-07-02  
**Last updated:** 2026-08-04

I track unfinished Splunk Enterprise work here. Completed deployment steps are in [Build-Log.md](Build-Log.md).

## TLS and Naming

- [x] Assigned a static SIEM address: `192.168.72.3/24` on Security-A, gateway/DNS `192.168.72.1`.
- [x] Enabled HTTPS on the Splunk web UI (`enableSplunkWebSSL`, Splunk's default self-signed cert). Reachable at `https://192.168.72.3:8000`.
- [x] 2026-07-22: Assigned `splunk.alphasecunited.com` as the internal FQDN through UniFi local DNS.
- [x] 2026-07-22: Published Splunk Web through NPM with the existing Let's Encrypt wildcard certificate, Force SSL, HTTP/2, Block Common Exploits, & WebSocket support. NPM connects to the existing HTTPS 8000 listener; HEC and syslog remain direct backend ports. See [Internal HTTPS Service Onboarding - 2026-07-22](../../../Nginx%20Proxy%20Manager/Documentation/Change%20Records/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22.md).

## Data sources

- [x] Repointed the UniFi console SIEM/syslog export to `192.168.72.3:1514` and verified a fresh CEF event reaches SC4S/HEC and the `netops` index; no additional Gateway-to-Security rule was required.
- [ ] Add the Rocky host's own OS logs (route to `osnix`).
- [ ] Add Proxmox host logs.

## Analytics

- [ ] Build UniFi dashboards over the `netops` index.
- [ ] If I need correlation, wire in CIM normalization via the CEF add-on (`cefutils`) on the search head.
