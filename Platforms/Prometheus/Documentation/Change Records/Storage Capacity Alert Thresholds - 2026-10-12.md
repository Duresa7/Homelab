# Storage Capacity Alert Thresholds

**Created:** 2026-10-12  
**Last updated:** 2026-10-12

I extended the [media storage threshold change](Media%20Storage%20Alert%20Threshold%20-%202026-10-12.md) to the remaining storage-capacity alerts. `homelab-filesystem-filling` and `homelab-pve-storage-filling` now use Grafana math condition `$A >= 90` instead of an above-85% threshold. All three storage rules retain their 15-minute pending period and five-minute evaluation interval. I updated their descriptions to match. Disk activity, drive health, memory, and other alert conditions are unchanged.

I kept the existing rule UIDs and selectors. The dedicated media rule still owns `media-01:/data`, and the shared filesystem rule excludes it. The Proxmox rule continues to cover ZFS pools and LVM thin pools. The [versioned configuration](../../Configuration/grafana/provisioning/alerting/alphasec-united-alerts.yaml) still holds 24 rules.

I checked the deployed file on `monitor-01` against SHA-256 `f2d8a9785930b1e07e9755ab7e4060573d9e3c2b05133689be3ba3abcadbcf41` before writing. The updated file read back as `4e8d49085b02e3e6f5b134816e66212d259c9bc7fff4ceff269571a3a4118193`, matching the repository. Grafana's authenticated alerting reload answered `Alerting config reloaded`; no restart, snapshot, or backup was needed. No separate command transcript was retained.

I read back all 24 provisioned rules and verified that only the two intended rules changed. All three storage rules have the inclusive 90% condition and 15-minute delay. Grafana 13.2.3 reported database `ok`.

I executed both updated rules through Grafana's data-source query API. Each query and condition returned status 200 without an evaluation error. The filesystem query returned 27 series and the Proxmox storage query returned 13; every condition was zero. The highest values were about 68.16% and 76.82%, respectively. For each rule's math condition, synthetic 89.99%, 90%, and 90.01% inputs produced zero, one, and one. I did not fill a disk, send a test notification, or wait for the next scheduled evaluation. No implementation work remains open.
