# BookLore

**Created:** 2026-09-13  
**Last updated:** 2026-09-13

I run BookLore on `docker-main` from `/opt/docker/booklore`. Its MariaDB dependency stays on `lscr.io/linuxserver/mariadb:11.4.8`, the application-supported pin recorded in the [dependency update](../../Operations/Maintenance/Container%20Image%20Updates%20-%202026-09-03.md).

The [Compose override](Configuration/docker-compose.override.yml) is deployed beside the existing `docker-compose.yml`. It limits WUD to rebuilds of that exact database tag. WUD 9 otherwise proposes the historic `110.4.21mariabionic-ls31` variant as a newer version. A future dependency change must update the image pin and this label together. The main Compose file and database credentials remain on the host; this override is not a complete deployment definition.

The [2026-09-13 maintenance record](../../Operations/Maintenance/Container%20Image%20Updates%20-%202026-09-13.md) contains the recreation and health checks.
