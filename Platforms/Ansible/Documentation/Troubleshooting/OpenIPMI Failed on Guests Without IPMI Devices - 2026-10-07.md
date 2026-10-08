# OpenIPMI Failed on Guests Without IPMI Devices

**Created:** 2026-10-07  
**Last updated:** 2026-10-07

**Status:** Resolved on six guests, 2026-10-07

I confirmed `openipmi.service` was enabled and failed on `alpha-prod-01`, `ansible-01`, `docker-blue`, `docker-network`, `media-01` and `monitor-01`. Each lacked `/dev/ipmi0`, `/dev/ipmi/0` and `/dev/ipmidev/0`. The hardware service had no device to manage on these guests and left systemd degraded. The fleet reboot play waits for `running`, so these failures could make a completed reboot fail its health gate. I retained the unit state and device checks; this repair has no fresh driver-error transcript.

I checked all three device paths immediately before disabling and stopping OpenIPMI on each host, then masked the service and cleared any retained failure. I left the package installed and made no change to the fleet play's system-health requirement.

At 9:25 PM EDT all six services were inactive and masked, all six failed-unit lists were empty, and all six hosts reported `running`. I did not reboot them as part of this repair. The [repair record](../../../../Operations/Maintenance/Service%20Failure%20Repairs%20-%202026-10-07.md) links the execution and final verification captures.
