# ES install/setup slow, initially looked disk I/O bound

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Symptom:** during the ES install/post-install setup (index and data model rebuild), the VM couldn't keep up. It was CPU-starved on only 4 allocated cores, and disk I/O looked like the bottleneck, with Splunk generating write/search load faster than the backing SSD storage appeared to service it.

**Cause:** I had sized `splunk-siem` for base Splunk Enterprise plus a single log source (UniFi via SC4S), at 4 cores / 12 GiB RAM. Splunk's own documentation lists 16 physical cores / 32 GB RAM as the minimum for a *production* ES search head [1]. The VM is well under that, and the post-install setup step (which rebuilds indexes and accelerates the CIM data models ES depends on) is exactly the CPU- and I/O-heavy operation that exposes an undersized host, even for a home lab at much smaller scale.

**Fix:** I increased `splunk-siem`'s vCPU allocation from 4 to 6 cores on the Proxmox host `grey-server`. I left storage unchanged (still the single SSD-backed `ssd-lvm1` disk); I suspected disk I/O initially but ruled it out, because the bottleneck was CPU. Confirmed resolved: Splunk Web now loads Enterprise Security fully, including Mission Control → Configure → All configurations.

The 6-vCPU VM remains below Splunk's stated 16-core production minimum. That minimum describes production deployment, while this instance ingests one source.

## References

1. Splunk, *Minimum specifications for a production deployment* (Enterprise Security 8.3). https://help.splunk.com/en/splunk-enterprise-security-8/install/8.3/planning/minimum-specifications-for-a-production-deployment
