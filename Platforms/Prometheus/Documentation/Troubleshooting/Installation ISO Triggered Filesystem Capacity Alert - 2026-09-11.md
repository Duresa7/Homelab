# Installation ISO Triggered Filesystem Capacity Alert

**Created:** 2026-09-11  
**Last updated:** 2026-09-11

## Symptom and cause

I received `WARNING: Filesystem is almost full` for `grey-server`, instance `192.168.70.10:9100`, mountpoint `/mnt/win11`, device `/dev/loop1`, at 100 percent for the 15-minute alert window.

I checked `df`, `findmnt`, `losetup`, and node_exporter through SSH Manager. The mount was the read-only UDF filesystem from `/var/lib/vz/template/iso/Win11_25H2_English_x64.iso`. It reported 7.3 GiB used and zero available bytes. The exporter reported `node_filesystem_readonly=1` and `node_filesystem_device_error=0`. Grey's root filesystem was 53 percent used with 43 GiB available.

The capacity expression included UDF, so the image's expected zero free space triggered the warning. I found no growth problem in this mount.

## Correction

I added `udf|iso9660` to both filesystem-type exclusion selectors in `homelab-filesystem-filling`, in the [versioned rule file](../../Configuration/grafana/provisioning/alerting/alphasec-united-alerts.yaml) and `/home/dkadi/monitoring/grafana/provisioning/alerting/alphasec-united-alerts.yaml` on `monitor-01`. I retained the 85 percent threshold, 15-minute delay, and rule UID. I left the ISO mounted.

I compared the old and new expressions through the live Prometheus query API before deploying. The old expression returned 32 series; the new expression returned 31. The only removed series was Grey's UDF mount at `/mnt/win11`, valued at 100 percent. All 18 root-filesystem series remained.

I checked the deployed file's original SHA-256 before editing and asserted the resulting hash before writing. I did not create a backup or snapshot. The available credential inventory contained the alert-bot shared secret but no Grafana administrator credential. I restarted only Grafana to load file provisioning. Prometheus was not restarted.

## Verification and limits

Grafana restarted at 2:32:36 PM Eastern and logged `finished to provision alerting` at 2:32:42 PM Eastern, followed by scheduler startup. Its health endpoint returned database `ok`, version `13.2.1`. The repository, deployed file, and file read inside the container shared SHA-256 `0ed04ee12cc28c29242c5a1833d0379ea59bf74ac2e38d88a7e15b10b1556af4`.

An attempted read-only SQLite verification could not open the database because of host permissions. A subsequent `sudo -n` attempt required a password. I used successful provisioning logs, the container-visible hash, and the live Prometheus query comparison to verify the change instead. I did not verify the resolved notification or authenticated alert-instance state.

I retained the observed results here; no separate raw terminal transcript was retained. The rule correction is deployed, and no further configuration work remains for this false capacity alert.
