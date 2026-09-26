# Ansible failed when the locale was omitted

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Investigated:** 2026-07-14

One final audit attempt exited 1 with `unsupported locale setting` because `runuser` did not preserve the expected locale. Re-running with `LANG=C.utf8` and `LC_ALL=C.utf8` succeeded. The runbook and Semaphore environment both set these variables explicitly.
