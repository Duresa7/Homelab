# Splunk

**Created:** 2026-08-03  
**Last updated:** 2026-08-04

I run Splunk Enterprise 10.4.0 on `splunk-siem` at `192.168.72.3`, a Rocky Linux VM on the Security-A VLAN. Splunk Enterprise indexes and searches the data. Splunk Enterprise Security is the premium app installed on top of it and supplies the SIEM features.

| Folder | What it covers |
| --- | --- |
| [Enterprise](Enterprise/) | The indexing and search platform, its build log, VM specifications, the UniFi CEF reference, and its backlog |
| [Enterprise Security](Enterprise%20Security/) | The ES app, its configuration log, and its backlog |

Both products share one host and one set of indexes. A change to Splunk Enterprise can affect ES, so a record that touches both belongs with Enterprise and is cross-linked from Enterprise Security rather than written twice.

SC4S runs on the same host and receives syslog from the UniFi gateway. The field mapping it depends on is in the [UniFi CEF reference](Enterprise/Documentation/UniFi-CEF-Reference.md).
