# ObiPC Shutdown

**Created:** 2026-09-20  
**Last updated:** 2026-09-20

I shut down [ObiPC](../../ObiPC_Specs.md) at 6:00 PM Eastern on 2026-09-20. Before the shutdown, `hostname` through SSH Manager returned `ObiPC` with exit code 0. I sent `shutdown.exe /s /t 0` to server `obipc` at `192.168.60.102`; it returned exit code 0 with empty stdout and stderr.

After the shutdown request, I checked TCP port 22 from `ubuntu_dev` through SSH Manager, allowing 10 seconds before a connection attempt with a 3-second timeout. The check returned `reachable: false`. Windows accepted the shutdown and SSH became unreachable; I did not independently observe physical power state. No separate terminal capture was retained. No follow-up work is pending.
