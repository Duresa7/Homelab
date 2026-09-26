# Splunk Enterprise Security

**Created:** 2026-09-25  
**Last updated:** 2026-09-25

I run Splunk Enterprise Security 8.5.1 as the premium SIEM app on the [Splunk Enterprise](../Enterprise/README.md) 10.4.0 instance on `splunk-siem` (`192.168.72.3`). I installed it through Splunk Web on 2026-07-02 under the nonprofit donation license; the version was read from `app.conf` on 2026-09-24.

| Item | Value |
|---|---|
| Data | UniFi CEF and flows mapped to CIM by `unifi_insights`; six data models carry UniFi data |
| Detection | Eight UniFi correlation searches write notables to Incident Review; two of them also post to Discord |
| Open work | Roles and capabilities, Risk-Based Alerting, and file-integrity alerts once more Wazuh agents have real watches ([TODO](Documentation/TODO.md)) |

Work that touches both products is recorded under Enterprise and cross-linked from the ES TODO.

## Records

- [Install Log](Documentation/Build%20Log.md)
- [TODO](Documentation/TODO.md)
- [Troubleshooting](Documentation/Troubleshooting/README.md)
