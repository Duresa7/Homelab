# Obsolete Pool Import on grey-server

**Created:** 2026-10-07  
**Last updated:** 2026-10-07

**Status:** Resolved 2026-10-07; no reboot performed

Grey retained an enabled `zfs-import@hddpool.service` that failed with `cannot import 'hddpool': no such pool available`. The live pool is `hddpool-1`, and its separate import unit was already active and enabled. The obsolete instance made systemd report a failure without indicating a fault in the working pool.

My first read-only probe used the unescaped `zfs-import@hddpool-1.service` and reported inactive/disabled. I resolved the actual unit from `zfs-import.target`: `zfs-import@hddpool\x2d1.service`. That instance was active/exited with `Result=success`. I verified the real pool ONLINE before changing the obsolete instance.

On October 7 I disabled only `zfs-import@hddpool.service` and reset its failed state. I did not stop or disable `zfs-import@hddpool\x2d1.service`, export the pool, or restart CT 110.

At 9:25 PM EDT, the obsolete instance was disabled and inactive. The real pool was ONLINE, its import unit active and enabled, and CT 110 was running. Grey reported `running` with no failed units after its separate unused UPS-monitor cleanup. Boot behavior has not been retested because Grey remains excluded from rebooting. The [repair record](../../../../../Operations/Maintenance/Service%20Failure%20Repairs%20-%202026-10-07.md) contains the evidence links.
