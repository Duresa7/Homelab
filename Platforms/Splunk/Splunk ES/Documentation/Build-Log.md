# Splunk Enterprise Security: Configuration Log

**Created:** 2026-07-02  
**Last updated:** 2026-07-18

My log of installing and configuring **Splunk Enterprise Security (ES)** on top of the existing Splunk Enterprise SIEM build. Same audience and purpose as the base SIEM log: written for other IT/security practitioners, recording what I did, the exact steps and commands, the alternatives I considered, and the reasoning behind non-default choices. Companion to the [Splunk Enterprise build log](../../Splunk%20Enterprise/Documentation/Build-Log.md), which covers standing up the VM, OS, Splunk Enterprise itself, and UniFi log ingestion.

### Project documents

| Document | Purpose |
|---|---|
| **Build-Log.md** (this file) | Chronological log of ES install and configuration steps |
| **[Troubleshooting-Log.md](Troubleshooting-Log.md)** | Every problem hit, its cause, and the fix |
| **[TODO.md](TODO.md)** | Planned follow-up configuration work |

| Field | Value |
|---|---|
| Project | Splunk Enterprise Security (home lab) |
| Runs on | `splunk-siem` VM (VMID 109), same instance as the base build; see [Splunk Enterprise VM specifications](../../Splunk%20Enterprise/Documentation/VM-Specs.md) |
| Base Splunk | Enterprise 10.4.0 |
| License | Splunk nonprofit donation program, which explicitly includes an ES entitlement (plus SOAR Community Edition) alongside the 10 GB/day Enterprise license [1] |
| Started | 2026-07-02 |

---

## Step index

| # | Step | Status | Summary |
|:-:|---|:-:|---|
| 1 | ES app install (Splunk Web) | Done | Installed via Manage Apps → Install app from file; hit a CPU-bound setup issue, fixed by raising the VM to 6 vCPU |

---

## Step 1: Splunk Enterprise Security app install

### What I did

I installed the Splunk Enterprise Security app through **Splunk Web**, not the CLI: **Apps → Manage Apps → Install app from file**, uploading the ES `.spl` package. Done 2026-07-02, on the existing `splunk-siem` VM (the same instance already running Splunk Enterprise 10.4.0 and ingesting UniFi logs via SC4S).

### Decision: Splunk Web install, not CLI

Splunk supports installing ES either by uploading the `.spl` through Splunk Web or via `splunk install app <file>.spl` on the CLI. I took the Web UI path because it drives the same post-install setup/configuration workflow (index and data model rebuild) automatically after upload, which is convenient for a single-instance home lab. The CLI path is more common in scripted/production deployments (search head clusters, deployer-managed environments).

### Licensing

I confirmed before installing: the Splunk nonprofit donation program grant already in use for the base SIEM includes ES as part of the entitlement, so I needed no separate purchase or license file [1].

### Issue encountered: undersized VM (CPU-bound)

The install/post-install setup step (which rebuilds indexes and accelerates the CIM data models ES depends on) is far more CPU- and I/O-intensive than running base Splunk Enterprise. On the VM's original 4 vCPU, this step crawled. I suspected disk I/O at first, but I left the VM's SSD-backed storage unchanged and the fix was CPU alone, which points to the 4-core allocation as the actual constraint rather than the disk.

**Fix:** I raised `splunk-siem` from 4 to 6 vCPU on `grey-server`. I confirmed the fix by loading Enterprise Security fully in Splunk Web, including Mission Control → Configure → All configurations, on 2026-07-02. Full symptom/cause/fix writeup in [Troubleshooting-Log.md](Troubleshooting-Log.md) (#1). I updated the [Splunk Enterprise VM specifications](../../Splunk%20Enterprise/Documentation/VM-Specs.md) to reflect the new core count, since the VM is shared infrastructure documented there.

---

## Current state

Step 1 is done: Enterprise Security is installed and running on `splunk-siem` at 6 vCPU. Next up is Step 2, scoping the CIM data models to the indexes actually in use, followed by the rest of the configuration work tracked in [TODO.md](TODO.md) (indexes, roles/capabilities, correlation searches, asset/identity, risk-based alerting).

---

## References

1. Splunk, *Splunk Pledge: Nonprofit Organizations* (Global Impact donation program, includes Splunk Enterprise Security and SOAR Community Edition). https://www.splunk.com/en_us/about-us/splunk-pledge/nonprofit-license-application.html
2. Splunk, *Licensing for Splunk Enterprise Security*. https://help.splunk.com/en/splunk-enterprise-security-8/user-guide/8.5/introduction/licensing-for-splunk-enterprise-security
3. Splunk, *Minimum specifications for a production deployment* (Enterprise Security 8.3). https://help.splunk.com/en/splunk-enterprise-security-8/install/8.3/planning/minimum-specifications-for-a-production-deployment
