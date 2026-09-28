# BookLore

**Created:** 2026-09-13  
**Last updated:** 2026-09-28

I retired BookLore on 2026-09-28 after replacing it with [BookOrbit](../BookOrbit/README.md). The BookLore and MariaDB containers and their Docker network are removed. The tables below describe the former deployment.

On 2026-09-28 I imported all 42 books into a separate [BookOrbit deployment](../BookOrbit/README.md). BookOrbit now serves the same HTTPS address and TCP 6060. I retained the original database and application data for unsupported settings and moved the old Compose project to `/opt/retired/booklore`. The [migration record](../BookOrbit/Documentation/Change%20Records/Migration%20from%20BookLore%20-%202026-09-28.md) records the import results and settings that did not transfer.

| Item | Value (read 2026-09-24) |
|---|---|
| BookLore | v2.4.0, container `booklore`, TCP 6060 |
| Database | MariaDB 11.4.8, container `mariadb` |
| Internal URL | `https://booklore.alphasecunited.com`, NPM proxy host 10 |
| Direct fallback | `http://192.168.40.35:6060` |

Its former MariaDB dependency stayed on `lscr.io/linuxserver/mariadb:11.4.8`, the application-supported pin recorded in the [dependency update](../../Operations/Maintenance/Container%20Image%20Updates%20-%202026-09-03.md).

The retained [Compose override](Configuration/docker-compose.override.yml) was deployed beside the former `docker-compose.yml`. Its WUD labels were added to restrict database update suggestions to the 11.4.8 tag. I retired WUD on 2026-09-27; those labels are now inert and I left the running database unchanged. A future dependency change must still review the image pin. The main Compose file and database credentials remain on the host; this override is not a complete deployment definition.

The [2026-09-13 maintenance record](../../Operations/Maintenance/Container%20Image%20Updates%20-%202026-09-13.md) contains the recreation and health checks.
