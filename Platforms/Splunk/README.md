# Splunk

**Created:** 2026-08-03  
**Last updated:** 2026-09-25

I run Splunk Enterprise 10.4.0 with Splunk Enterprise Security 8.5.1 on `splunk-siem` at `192.168.72.3`, a Rocky Linux 10.2 VM on the Security-A VLAN (versions read 2026-09-24). Splunk Enterprise indexes and searches UniFi and Wazuh data. Enterprise Security is the premium app installed on top of it and supplies the SIEM features.

| Folder | What it covers |
| --- | --- |
| [Enterprise](Enterprise/README.md) | The indexing and search platform: inputs, the UniFi and Wazuh apps, Discord delivery, build log, VM specifications, UniFi CEF reference, backlog |
| [Enterprise Security](Enterprise%20Security/README.md) | The ES app, its install log, and its backlog |

Both products share one host and one set of indexes. A change to Splunk Enterprise can affect ES, so a record that touches both belongs with Enterprise and is cross-linked from Enterprise Security rather than written twice.

The step-by-step build is the [Splunk guide](../../Guides/Splunk.md); the Wazuh feed is the [Wazuh Alerts in Splunk guide](../../Guides/Wazuh-Alerts-in-Splunk.md).
