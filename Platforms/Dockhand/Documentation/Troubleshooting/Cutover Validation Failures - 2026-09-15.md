# Cutover Validation Failures

**Created:** 2026-09-15  
**Last updated:** 2026-09-15

The approved registry cutover stopped with `Source drift before apply` before replacing its first container. The source file `/opt/docker/docusaurus/Configuration/docker-compose.yml` had not changed: SHA-256 over its raw bytes matched the prepared value. SHA-256 over `read_text().encode()` did not match, and the source contained 28 CRLF line endings. Python's text read normalized those line endings. I changed apply to hash `read_bytes()` and rollback to use `write_bytes()`. All seven hosts then passed preparation; Docusaurus recreated with its original image contents and returned healthy.

The first Hawser cutover on docker-network then stopped at `create-stopped-updater`. Its agent had already recreated successfully. The script restored its original Compose file and successfully rolled the agent back. I inspected `docker compose create --help`: `--no-deps` is unsupported by `create`. I removed that flag from the helper creation command; the helper has no dependencies. The retry completed, leaving Hawser healthy and the updater in `created` state.

A final configuration comparison initially reported `Deployed config differs` on all six Hawser projects. Comparing field paths showed Compose had supplied `services.hawser-updater.networks` and `services.hawser-updater.command`. I corrected the verification to normalize both the approved candidate and deployed file through Compose before comparison. All eleven deployed project definitions matched their approved candidates.

These were defects in the temporary cutover and verification scripts. The [completed cutover](../Change%20Records/Registry%20and%20Agent%20Cutover%20-%202026-09-15.md) links the final host, stack, and registry results. No complete terminal transcript is retained for the failed attempts; the commands and results were observed during the working sessions. I removed the host-side temporary scripts after verification.
