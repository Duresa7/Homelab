# Splunk

**Created:** 2026-08-03  
**Last updated:** 2026-08-03

Splunk runs on `splunk-siem` at `192.168.72.3`, a Rocky Linux VM on the Security-A VLAN. It is the only platform here that is split into two products, so this folder holds them side by side rather than flattening them into one record set.

| Folder | What it covers |
| --- | --- |
| [Splunk Enterprise](Splunk%20Enterprise/) | The indexing and search tier, its build log, VM specifications, the UniFi CEF reference, and its backlog |
| [Splunk ES](Splunk%20ES/) | Enterprise Security on top of that tier, its build log, and its backlog |

Both share one host and one set of indexes. A change to the Enterprise tier can move Enterprise Security under it, so a record that touches both belongs with Enterprise and is cross-linked from ES rather than written twice.

SC4S runs on the same host and receives syslog from the UniFi gateway. The field mapping it depends on is in the [UniFi CEF reference](Splunk%20Enterprise/Documentation/UniFi-CEF-Reference.md).
