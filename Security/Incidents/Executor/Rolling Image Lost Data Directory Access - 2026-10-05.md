# Rolling Image Lost Data Directory Access

**Created:** 2026-10-07  
**Last updated:** 2026-10-07

**Incident date:** 2026-10-05, approximately 11:49 PM to 11:56 PM EDT  
**Status:** Closed; service restored and subsequently verified through SSH Manager

## Summary and impact

During the fleet Compose update, Executor on `docker-blue` entered a restart loop and all MCP integrations reached through it timed out. The interruption lasted approximately eight minutes. SSH Manager was inaccessible through Executor during that period, so I used the existing direct SSH path through `ansible-01` to repair the container's data-directory ownership.

## Findings and correction

The new image ran as UID/GID 65532 while `/opt/docker/executor/data` remained owned by root with mode 700. Executor reported `EACCES: permission denied, open '/data/secret.key'`. The Compose health gate failed and stopped that project's update.

At approximately 11:56 PM I changed the data directory and its existing contents to UID/GID 65532 and restarted Executor. I changed no stored key or database content. The container reached healthy within 20 seconds. The [implementation record](../../../Platforms/Executor/Documentation/Change%20Records/Rolling%20Image%20Recreation%20-%202026-10-05.md) records the image comparison, commands and ownership readback.

## Validation and closure

The container health check passed, the MCP endpoint answered, the saved-connection inventory returned, and an SSH Manager call through Executor succeeded. The first post-restart call required session re-establishment; its retry worked. The October 7 service-repair verification again used Executor and SSH Manager successfully.

I retained the fleet Compose failure output under [fleet evidence](../../../Operations/Evidence/Fleet%20Update%20-%202026-10-05/Logs/blue-hawser.log). There is no standalone exact-command transcript for the ownership repair; its observed result is recorded in the implementation record. Future recreations depend on preserving UID/GID 65532 ownership of the bind-mounted data directory. No further corrective action remains for this outage.
