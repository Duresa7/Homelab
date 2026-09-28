# Migration from BookLore

**Created:** 2026-09-28  
**Last updated:** 2026-09-28

**Status:** Complete; BookOrbit active at the original HTTPS address.  
**Initial import completed:** 2026-09-28 at 2:15 PM Eastern.  
**Cutover and retirement:** 2026-09-28 at 2:18–2:22 PM Eastern.

I followed the [official migration workflow](https://bookorbit.app/migration): install BookOrbit separately, scan the existing files, validate the BookLore source, map the account and paths, run a dry run, and import. The guide lists BookLore v2.2.2 as tested; my source is v2.4.0. Live schema validation passed with no missing required tables.

## Deployment and source

I deployed BookOrbit v3.1.0 and PostgreSQL 18.6 with pgvector under `/opt/docker/bookorbit` on `docker-main` (`192.168.40.35`). Before deployment, its root filesystem had 41 GB available. BookLore held 42 book files, 1.4 GB, one library, and one account. BookLore remained healthy on TCP 6060 throughout staging.

During staging, BookOrbit published TCP 6061. It mounted the original books and cover directory read-only and connected to MariaDB over the existing `booklore_default` Docker network. I created a separate PostgreSQL database and application data directory. I did not create a snapshot or a backup or alter the source book files.

The first startup failed because UID/GID 1000 could not write the new application data directory and its subdirectories. I corrected ownership only under `/opt/docker/bookorbit/data/app`; the application then started and its setup endpoint returned HTTP 200. I completed initial setup with my standard application account and verified a fresh login.

## Import verification

The initial scan completed at 2:14 PM Eastern with 42 books added, zero missing, and no scan error. `/books` mapped to `/books`, with all 42 source paths present. The dry run matched 42 books with zero unresolved books and zero duplicate matches, and mapped the one source account.

The first live-run request returned HTTP 400 because I had validated paths before saving the profile. I validated them again against saved profile 1, regenerated the dry run, and started run 1. It completed at 2:15 PM Eastern with zero failed entities.

| Entity | Imported |
|---|---:|
| Book metadata | 42 |
| Author links | 42 |
| Genre links | 131 |
| Covers | 41 |
| Reading progress | 4 |
| Reading sessions | 4 |
| Reading statuses | 4 |
| Annotations | 1 |

The [aggregate migration report](../../Evidence/Migration%20-%202026-09-28/migration-summary.json) records 269 imported entities, 91 skipped, one unresolved cover, and zero failures. Its entity counters are not book counts. All 42 books matched. Source book 35, matched to target book 2, had no `/data/booklore/data/images/35` directory, explaining the missing cover. No bookmark, audiobook-progress, or collection-membership rows were imported; the source had no rows for those categories.

PDF annotation, book note, Kobo reading-state, and comic metadata tables were empty. Two ebook viewer preferences and one Kobo user-settings record remain in BookLore because the importer defers those settings. The source had two shelves but no shelf memberships; no collection entries transferred.

An authenticated request for the first book's file returned HTTP 206 and 1,024 bytes for the requested range. Both application roots returned HTTP 200 after migration. PostgreSQL reported 18.6. I verified Compose configuration parsing and pinned the application image reference to the digest in the [platform README](../../README.md).

I retained the aggregate report and deployed Compose reference. I did not retain complete SSH transcripts for discovery, startup repair, account setup, scan, import, or verification; the observations above are the results returned during those steps. Temporary account and session files were shredded and removed locally and on `docker-main`.

## Cutover and retirement

I confirmed the requested cutover and removal of the old application. I stopped BookLore, regenerated the dry run, and completed import run 2 against the still-running MariaDB source. It again matched all 42 books with zero failed imports. The retained aggregate report is from this final run.

I moved BookOrbit from TCP 6061 to TCP 6060, set `APP_URL=https://booklore.alphasecunited.com`, and made the existing `/books` mount writable. I removed the source-media mount and the temporary MariaDB network attachment, then recreated BookOrbit with its pinned image. NPM host 10, the DNS record, certificate, and firewall destination stayed unchanged. An immediate HTTPS request during startup returned 502; the post-start request returned 200.

A fresh login through HTTPS passed. Authenticated range requests through NPM read 32 bytes from each of the 42 book files successfully. A temporary file creation and removal as UID/GID 1000 verified library write access. Both BookOrbit containers reported healthy. The old BookDrop directory contained no pending files. I left library watching, automatic file metadata writes, and file renaming disabled; the BookOrbit Book Dock uses its default application-data directory.

Final PostgreSQL readback confirmed 42 books, four reading-progress rows, four reading-session rows, and one annotation. Repeating the import did not duplicate these records. The HTTPS setup-status endpoint confirmed that initial setup was complete.

After those checks, I removed the `booklore` and `mariadb` containers and the `booklore_default` network using the old project's Compose teardown without deleting data. I removed the retired imported stack definition from Dockhand and adopted `/opt/docker/bookorbit/docker-compose.yml` with its host `.env`; Compose API readback passed. I moved the original project to `/opt/retired/booklore` so it is no longer an active project under `/opt/docker`.

I renamed the existing Homarr shortcut to BookOrbit, preserved its destination, and changed the icon to the new application's favicon. The icon returned an image content type, and Homarr's status check returned HTTP 200.

The books remain at `/data/booklore/books` as the active BookOrbit library. The original MariaDB data remains at `/data/booklore/mariadb/config` and application data at `/data/booklore/data`; these are retained original data, not new backups. They preserve settings the importer did not transfer. The old application is no longer running. Deleting that retained data would discard those unsupported settings and is outside this completed cutover.

I removed temporary credential and migration-session files again after final verification. I created no snapshot or backup. I updated the platform index, service inventory, NPM backend description, DNS description, and Homarr shortcut reference in place. I did not retain complete command transcripts for cutover, retirement, or the follow-up UI configuration; the results above and the final aggregate report are the retained observations.
