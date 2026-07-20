# Splunk Enterprise Security: Configuration Log

**Created:** 2026-07-02  
**Last updated:** 2026-07-20

I installed Splunk Enterprise Security on the existing Splunk Enterprise 10.4.0 SIEM. The [Splunk Enterprise build log](../../Splunk%20Enterprise/Documentation/Build-Log.md) covers the VM, OS, base application, & UniFi ingestion path.

### Related Records

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

## Step index

| # | Step | Status | Summary |
|:-:|---|:-:|---|
| 1 | ES app install (Splunk Web) | Done | Installed via Manage Apps → Install app from file; hit a CPU-bound setup issue, fixed by raising the VM to 6 vCPU |

## Step 1: Splunk Enterprise Security app install

### What I did

On 2026-07-02, I uploaded the ES `.spl` package through **Apps → Manage Apps → Install app from file** on `splunk-siem`. The same VM already ran Splunk Enterprise 10.4.0 and ingested UniFi logs through SC4S.

### Decision: Splunk Web install, not CLI

Splunk supports either a Web upload or `splunk install app <file>.spl`. I used the Web path because this is one search head and the upload starts the post-install index and data-model work.

### Licensing

I confirmed before installing: the Splunk nonprofit donation program grant already in use for the base SIEM includes ES as part of the entitlement, so I needed no separate purchase or license file [1].

### Issue encountered: undersized VM (CPU-bound)

The index rebuild and CIM data-model acceleration stalled on the VM's original 4 vCPU. I left the SSD-backed storage unchanged and raised the VM to 6 vCPU; setup then completed.

**Fix:** I raised `splunk-siem` from 4 to 6 vCPU on `grey-server`. Enterprise Security then loaded **Mission Control → Configure → All configurations** on 2026-07-02. The [troubleshooting log](Troubleshooting-Log.md#1-es-installsetup-slow-initially-looked-disk-io-bound-2026-07-02) records the failure, & [VM specifications](../../Splunk%20Enterprise/Documentation/VM-Specs.md) records the 6-vCPU state. Remaining CIM, index, role, correlation-search, asset, identity, & risk work is in [TODO.md](TODO.md).

## References

1. Splunk, *Splunk Pledge: Nonprofit Organizations* (Global Impact donation program, includes Splunk Enterprise Security and SOAR Community Edition). https://www.splunk.com/en_us/about-us/splunk-pledge/nonprofit-license-application.html
2. Splunk, *Licensing for Splunk Enterprise Security*. https://help.splunk.com/en/splunk-enterprise-security-8/user-guide/8.5/introduction/licensing-for-splunk-enterprise-security
3. Splunk, *Minimum specifications for a production deployment* (Enterprise Security 8.3). https://help.splunk.com/en/splunk-enterprise-security-8/install/8.3/planning/minimum-specifications-for-a-production-deployment
