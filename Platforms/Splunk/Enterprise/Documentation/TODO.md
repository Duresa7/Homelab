# To-Do

**Created:** 2026-07-02  
**Last updated:** 2026-09-03

I track unfinished Splunk Enterprise work here. Completed deployment steps are in [Build-Log.md](Build-Log.md).

## TLS and Naming

- [x] Assigned a static SIEM address: `192.168.72.3/24` on Security-A, gateway/DNS `192.168.72.1`.
- [x] Enabled HTTPS on the Splunk web UI (`enableSplunkWebSSL`, Splunk's default self-signed cert). Reachable at `https://192.168.72.3:8000`.
- [x] 2026-07-22: Assigned `splunk.alphasecunited.com` as the internal FQDN through UniFi local DNS.
- [x] 2026-07-22: Published Splunk Web through NPM with the existing Let's Encrypt wildcard certificate, Force SSL, HTTP/2, Block Common Exploits, & WebSocket support. NPM connects to the existing HTTPS 8000 listener; HEC and syslog remain direct backend ports. See [Internal HTTPS Service Onboarding - 2026-07-22](../../../Nginx%20Proxy%20Manager/Documentation/Change%20Records/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22.md).

## Data sources

- [x] Repointed the UniFi console SIEM/syslog export to `192.168.72.3:1514` and verified a fresh CEF event reaches SC4S/HEC and the `netops` index; no additional Gateway-to-Security rule was required.
- [x] 2026-08-28: Added UniFi Traffic Flows. The syslog export carries events only, so the per-connection records behind Insights come from the controller's v2 API through `unifi-flow-collector.service` into `netfw` at sourcetype `unifi:flow`. See [UniFi Flow Collection and Insights App - 2026-08-28](Change%20Records/UniFi%20Flow%20Collection%20and%20Insights%20App%20-%202026-08-28.md).
- [x] 2026-08-29: Restored the UniFi OS and UniFi Protect exports. The categories were never deselected; the SIEM Server address had been cleared and the port read 514, where SC4S listens for CEF on 1514. All three products are current again. See [UniFi Syslog Export Restored and CIM Coverage Completed - 2026-08-29](Change%20Records/UniFi%20Syslog%20Export%20Restored%20and%20CIM%20Coverage%20Completed%20-%202026-08-29.md).
- [x] 2026-08-30: Added Wazuh. A Universal Forwarder on `wazuh-01` ships `/var/ossec/logs/alerts/alerts.json` to `192.168.72.3:9997` into the `wazuh` index at sourcetype `wazuh:alerts`, everything forwarded, 30 days retained, no backfill. See [Alert Forwarding to Splunk - 2026-08-29](../../../Wazuh/Documentation/Change%20Records/Alert%20Forwarding%20to%20Splunk%20-%202026-08-29.md).
- [ ] Add the Rocky host's own OS logs (route to `osnix`).
- [ ] Add Proxmox host logs.
- [x] 2026-08-29: Put the UniFi Protect detections and the network health events on the client activity dashboard, under Network health and camera detections.
- [ ] Decide whether UniFi Protect deserves its own index. `splunk_metadata.csv` routes all three products to `netops` today and the CEF reference notes the split as an option.

## Analytics

- [x] 2026-08-28: Built the `unifi_insights` app: three Dashboard Studio views over `netfw` and `netops`, plus the field mapping they rest on.
- [x] 2026-08-28: Repaired the CEF space-truncation fault that reduced every signature to `ET` or `GPL`. The extractions are in the app's `props.conf` and the detail is in the [CEF reference](UniFi-CEF-Reference.md#parsing-fault-values-containing-spaces).
- [x] 2026-08-29: Added [Tests/verify_unifi_insights.py](../Tests/verify_unifi_insights.py), which runs every deployed panel query, every correlation search and a probe of each CIM data model. It reads the views off disk rather than holding a copy of the queries, so it does not drift when a panel changes.
- [x] 2026-08-30: Built the `wazuh_insights` app: one Dashboard Studio view over the `wazuh` index, seven glance tiles and six panels, plus the CIM mapping under it. See [Wazuh Insights App - 2026-08-29](Change%20Records/Wazuh%20Insights%20App%20-%202026-08-29.md).
- [x] 2026-09-03: Nine saved searches across `unifi_insights` and `wazuh_insights` post to Discord through the alert bot's `/splunk` endpoint: five UniFi and four Wazuh, each tuned against 30 days of history, one message per source or machine, with suppression per pair. Splunk is the only thing that notifies on security events. See [Discord Delivery for UniFi and Wazuh Alerts - 2026-09-03](Change%20Records/Discord%20Delivery%20for%20UniFi%20and%20Wazuh%20Alerts%20-%202026-09-03.md).
- [ ] Remove the `wazuh-01` exclusion from `Wazuh - Machines gone quiet, listed` after 2026-09-08, when the renamed manager's old name has aged out of the seven-day window. Harmless if left.
- [ ] Add a machine and severity filter to the Wazuh Insights dashboard. The first attempt at a multiselect input broke the whole definition and I rebuilt without it.
- [ ] Give `wazuh_insights` the equivalent of [Tests/verify_unifi_insights.py](../Tests/verify_unifi_insights.py), which would have caught the malware macro counting VirusTotal's rate-limit errors as findings.
- [ ] Break high-risk flows down by `ips_category`. The collector captures it and no panel uses it yet.
- [x] 2026-08-28: CIM normalization done in `unifi_insights` rather than through `cefutils`. Network_Traffic, Intrusion_Detection and Authentication all return UniFi data.
- [x] 2026-08-29: Extended the CIM mapping to all three products and corrected two faults in it. `unifi_cef_firewall` was matching `UNIFIcategory=Security`, which put 11,819 IDS detections into Network_Traffic as if they were connections; it is now class 203 only. Severity now falls back to the CEF header grading, so a health event is no longer always informational. Network_Sessions, Change and Alerts populate as well, and 40 of 41 event classes carry an event type.
