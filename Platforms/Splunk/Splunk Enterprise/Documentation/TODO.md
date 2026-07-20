# Splunk SIEM: To-Do

**Created:** 2026-07-02  
**Last updated:** 2026-07-20

I track unfinished Splunk Enterprise work here. Completed deployment steps are in [Build-Log.md](Build-Log.md).

## TLS and Naming

- [x] Assigned a static SIEM address: `192.168.72.3/24` on Security-A, gateway/DNS `192.168.72.1`.
- [x] Enabled HTTPS on the Splunk web UI (`enableSplunkWebSSL`, Splunk's default self-signed cert). Reachable at `https://192.168.72.3:8000`.
- [ ] Next I want to assign a proper domain name (FQDN) for the SIEM instead of the bare IP.
- [ ] Stand up a reverse proxy in front of Splunk for TLS termination with a real (CA-signed) certificate, and route the stack through it. Replaces the self-signed cert once a domain exists.

## Data sources

- [x] Repointed the UniFi console SIEM/syslog export to `192.168.72.3:1514` and verified a fresh CEF event reaches SC4S/HEC and the `netops` index; no additional Gateway-to-Security rule was required.
- [ ] Add the Rocky host's own OS logs (route to `osnix`).
- [ ] Add Proxmox host logs.

## Analytics

- [ ] Build UniFi dashboards over the `netops` index.
- [ ] If I need correlation, wire in CIM normalization via the CEF add-on (`cefutils`) on the search head.
