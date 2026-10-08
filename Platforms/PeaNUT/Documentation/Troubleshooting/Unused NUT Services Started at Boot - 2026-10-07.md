# Unused NUT Services Started at Boot

**Created:** 2026-10-07  
**Last updated:** 2026-10-07

**Status:** Boot activation corrected; automatic shutdown remains unconfigured

After Red's October 6 reboot, `nut-server.service` and `nut-monitor.service` reported `ActiveState=failed`, each with five restarts. Neither unit was enabled, but `nut.target` was enabled and wanted both. Red had no active UPS stanza after the [August 31 driver repair](ups01%20NUT%20Driver%20Restart%20Loop%20After%20the%20UPS%20Swap%20-%202026-08-31.md), and the USB check still found no APC device. Grey also had an unused, failed `nut-monitor` pulled in by its working NUT target. I did not retain a fresh daemon-error trace in this repair; the unit state and activation dependencies are in the capture.

On October 7 I disabled and stopped Red's `nut.target`, `nut-driver.target`, and driver-enumerator service and path. I disabled and masked Red's `nut-server` and `nut-monitor`, masked Grey's `nut-monitor`, and cleared their failure states. I updated Red's live `ups.conf` restoration comment and its [versioned reference](../../Configuration/NUT/red-server/ups.conf) to include the target and enumerator setup and the server unmask step.

At 9:25 PM EDT, Red's targets and enumerator were disabled and inactive, its server and monitor were masked and inactive, and Grey's monitor was masked and inactive. Both hosts reported `running` with no failed units. Grey's `nut-server` remained active and enabled and `upsc ups02@localhost ups.status` returned `OL`. I did not restart Grey's UPS driver or server.

UPS-01 stays unmonitored by the September 7 decision. These changes prevent unused services from failing at startup; they do not configure battery-triggered shutdown. I must configure and validate that function before unmasking either monitor. The [repair record](../../../../Operations/Maintenance/Service%20Failure%20Repairs%20-%202026-10-07.md) links the exact commands and verification.
