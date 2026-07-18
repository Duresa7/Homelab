# 🔧 Splunk ES: Troubleshooting Log

**Created:** 2026-07-02  
**Last updated:** 2026-07-09

Every problem hit while installing and configuring Splunk Enterprise Security, its cause, and the fix. Companion to [Build-Log.md](Build-Log.md). The build log records *what was done*; this records *what went wrong and the fix*.

## Quick index

| # | Where | Symptom | Root cause | Fix |
|:-:|---|---|---|---|
| 1 | Step 1 | ES setup slow/stalled under load | VM undersized for ES (CPU-bound, not disk) | Increased vCPU 4 → 6 |

---

## 1. ES install/setup slow, disk I/O bound (2026-07-02)

**Symptom:** during the ES install/post-install setup (index and data model rebuild), the VM couldn't keep up — CPU-starved on only 4 allocated cores, and disk I/O became the bottleneck, with Splunk generating write/search load faster than the backing SSD storage could service it.

**Cause:** `splunk-siem` was sized for base Splunk Enterprise plus a single log source (UniFi via SC4S), at 4 cores / 12 GiB RAM. Splunk's own documentation lists 16 physical cores / 32 GB RAM as the minimum for a *production* ES search head [1] — the VM is well under that, and the post-install setup step (which rebuilds indexes and accelerates the CIM data models ES depends on) is exactly the CPU- and I/O-heavy operation that exposes an undersized host, even for a home lab at much smaller scale.

**Fix:** increased `splunk-siem`'s vCPU allocation from 4 to 6 cores on the Proxmox host `grey-server`. Storage was left unchanged (still the single SSD-backed `ssd-lvm1` disk) — disk I/O was suspected initially but ruled out; the bottleneck was CPU. Confirmed resolved: Splunk Web now loads Enterprise Security fully, including Mission Control → Configure → All configurations.

**Takeaway:** ES's setup step is far heavier than running base Splunk Enterprise; a VM comfortable for the SIEM build was not comfortable for ES. Two extra cores was enough to get past the setup step at this small scale, well short of Splunk's stated 16-core production minimum — a reminder that vendor minimums target production scale, not a single-source home lab.

---

## References

1. Splunk, *Minimum specifications for a production deployment* (Enterprise Security 8.3). https://help.splunk.com/en/splunk-enterprise-security-8/install/8.3/planning/minimum-specifications-for-a-production-deployment
