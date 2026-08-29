# To-Do

**Created:** 2026-07-02  
**Last updated:** 2026-08-29

I track unfinished Splunk Enterprise Security work here. Completed setup is in [Build-Log.md](Build-Log.md).

## Completed Foundation

- [x] Resolved the [app install/setup issue from 2026-07-02](Troubleshooting/ES%20install-setup%20slow,%20initially%20looked%20disk%20I-O%20bound%20-%202026-07-02.md): raising `splunk-siem` from 4 to 6 vCPU cleared the CPU-bound setup stall, and I verified the ES configuration UI.
- [x] Completed the ES post-install configuration step (index and data model rebuild): the Splunk Web install workflow finished after the CPU correction; follow-on CIM scoping remains separate below.

## Data Readiness

- [x] 2026-08-28: Normalized both UniFi sources to CIM through the `unifi_insights` app rather than `cefutils`. Network_Traffic returns 6,875 allowed and 4 blocked, Intrusion_Detection returns 10,849 high and 635 medium, Authentication resolves console access to a username. See [UniFi Flow Collection and Insights App - 2026-08-28](../../Enterprise/Documentation/Change%20Records/UniFi%20Flow%20Collection%20and%20Insights%20App%20-%202026-08-28.md).
- [x] 2026-08-28: Confirmed the ES indexes exist. `notable` is present with a 500000 MB cap, alongside `risk`, `threat_activity`, `notable_summary` and the rest.
- [x] 2026-08-29: Extended CIM coverage to UniFi OS and UniFi Protect, and corrected two faults in the mapping. Network_Traffic no longer counts IDS detections as connections, and severity now falls back to the CEF header grading instead of reading informational on everything the gateway does not risk-band. Network_Sessions, Change and Alerts populate as well, so six data models carry UniFi data. See [UniFi Syslog Export Restored and CIM Coverage Completed - 2026-08-29](../../Enterprise/Documentation/Change%20Records/UniFi%20Syslog%20Export%20Restored%20and%20CIM%20Coverage%20Completed%20-%202026-08-29.md).

## Access

- [ ] Review ES roles and capabilities (`ess_admin`, `ess_analyst`, etc.) and assign to the `admin` user / any additional accounts

## Detection

- [x] 2026-08-28: Enabled eight correlation searches over the UniFi data, each verified to run clean and to match real history. Three are tuned against this network's own behaviour: P2P is excluded because 10,849 of 11,477 detections are this network's BitTorrent traffic, the controller's own service accounts are excluded from the configuration rule, and `ansible-01` is excluded from the scanning rule.
- [x] 2026-08-29: Confirmed the rules reach Incident Review rather than only running. 150 scheduled executions over 24 hours, all `success`, and seven notables in `index=notable` from three rules at the severities they declare.
- [ ] Set up Risk-Based Alerting (RBA) so low-fidelity matches accumulate risk instead of firing individual notables. The eight rules above write individual notables today.
- [ ] Populate the Asset and Identity framework with known home lab devices (so notables resolve to real hosts/owners, not bare IPs)

## Later

- [ ] Evaluate threat intelligence feed integration
- [x] 2026-08-28: Built custom security dashboards as the `unifi_insights` app. Glass tables are still untouched.
