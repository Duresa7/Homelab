# Media Storage Alert Threshold

**Created:** 2026-10-12  
**Last updated:** 2026-10-12

I changed the capacity alert for `media-01:/data` from above 85% to **90% or higher**. The new file-provisioned rule, `homelab-media-storage-filling` (Media storage is almost full), uses `$A >= 90`, retains the 15-minute pending period, and runs in the Capacity group's five-minute evaluation interval. Query A still reports actual percent used from filesystem available and total bytes.

I excluded only `host="media-01",mountpoint="/data"` from `homelab-filesystem-filling` using `unless on(host, mountpoint)`. The media host's root filesystem and every other filesystem keep the existing above-85% threshold. Proxmox storage thresholds are unchanged. The [versioned configuration](../../Configuration/grafana/provisioning/alerting/alphasec-united-alerts.yaml) now contains 24 rules.

At 6:10 PM Eastern I checked that the deployed file on `monitor-01` matched the repository SHA-256 `dae5d8351e3c296bf6a53776bde5166635a036f5a15333344ee18c1c6824c583`, wrote the updated file, and read back SHA-256 `f2d8a9785930b1e07e9755ab7e4060573d9e3c2b05133689be3ba3abcadbcf41`. I loaded it through `POST /api/admin/provisioning/alerting/reload`, which answered `Alerting config reloaded`. I did not restart Grafana or create a snapshot or backup.

I verified the loaded rules through Grafana's provisioning API: the media rule has the inclusive condition and 15-minute delay, the shared rule has the exclusion, and all 22 unrelated rules match their previous definitions. Grafana 13.2.3 reported database `ok`.

I executed the new rule's queries through Grafana's data-source query API. Both returned HTTP status 200 without an evaluation error: `/data` was 81.07299143081325% used and condition B was zero. Using the same Grafana math evaluator, 89.99% produced zero, exactly 90% produced one, and 90.01% produced one. These checks exercised the query and inclusive boundary without filling the disk or sending a test notification. I did not wait for the new rule's next scheduled five-minute evaluation or verify Discord delivery. No separate command transcript was retained.
