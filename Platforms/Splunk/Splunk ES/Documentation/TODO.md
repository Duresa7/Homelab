# Splunk ES: To-Do

**Created:** 2026-07-02  
**Last updated:** 2026-07-20

I track unfinished Splunk Enterprise Security work here. Completed setup is in [Build-Log.md](Build-Log.md).

## Completed Foundation

- [x] Resolved the app install/setup issue from 2026-07-02 (tracked in [Troubleshooting-Log.md](Troubleshooting-Log.md) #1): raising `splunk-siem` from 4 to 6 vCPU cleared the CPU-bound setup stall, and I verified the ES configuration UI.
- [x] Completed the ES post-install configuration step (index and data model rebuild): the Splunk Web install workflow finished after the CPU correction; follow-on CIM scoping remains separate below.

## Data Readiness

- [ ] Next I want to normalize the existing UniFi/CEF data in `netops` to the Common Information Model (CIM) so it populates ES data models (Network Traffic, Authentication, etc.), likely via the `cefutils` add-on already installed on the search head
- [ ] Confirm ES's required indexes exist (`notable`, `risk`, `threat_activity`, and related) and are sized appropriately

## Access

- [ ] Review ES roles and capabilities (`ess_admin`, `ess_analyst`, etc.) and assign to the `admin` user / any additional accounts

## Detection

- [ ] Enable a small first set of correlation searches relevant to UniFi data, rather than turning on everything at once
- [ ] Set up Risk-Based Alerting (RBA) so low-fidelity matches accumulate risk instead of firing individual notables
- [ ] Populate the Asset and Identity framework with known home lab devices (so notables resolve to real hosts/owners, not bare IPs)

## Later

- [ ] Evaluate threat intelligence feed integration
- [ ] Build glass tables / custom security dashboards once base detections are working
