# Semaphore CLI export/import limitations

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Investigated:** 2026-07-14

My first export attempt omitted the required project ID or name and exited without creating a backup. I couldn't inspect the JSON with `jq` because `jq` isn't installed on the controller, so I used Python for the structural inspection.

The CLI export couldn't reproduce the working execution configuration in a new project, so I kept the existing project and used the export only as a rollback reference.
