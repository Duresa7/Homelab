# Registry and Stack Preparation

**Created:** 2026-09-15  
**Last updated:** 2026-09-15

**Status:** Preparation verified; container cutover awaits approval.  
**Verification completed:** 2026-09-15, 10:30 PM Eastern.

I want Dockhand's existing update, image, and stack controls to work across the seven connected hosts. I kept this work within those controls. I did not add a fleet-wide update job or apply the nine upstream application updates found in the earlier audit.

## Applied and verified

I enabled private image publication in the existing Forgejo installation at `forgejo.alphasecunited.com`. I created the non-administrator `dockhand-images` service account and private `homelab-images` organization. I saved its credentials in my credential vault and configured [Dockhand's registry entry](../../Configuration/forgejo-registry.json) with package read/write permission. The temporary organization bootstrap token was revoked. Anonymous access to a published image manifest returned HTTP 401.

I tagged and published each running custom container's existing image ID as `forgejo.alphasecunited.com/homelab-images/<image>:stable`. This copied existing contents without rebuilding or replacing the applications.

| Host | Running container | Registry image |
|---|---|---|
| docker-main | docusaurus | docusaurus:stable |
| docker-blue | mcp-ssh-manager | mcp-ssh-manager:stable |
| docker-blue | mcp-unifi-network | unifi-network-mcp:stable |
| monitor-01 | alert-bot | alert-bot:stable |
| alpha-prod-01 | teamspeak-monitor | teamspeak-monitor:stable |
| security-01 | wazuh-mcp-server | wazuh-mcp-server:stable |

I used isolated disposable containers to exercise Dockhand's registry check and pull/replacement against every private image. All six passed. I also pushed each unchanged image through Dockhand's native Images > Push operation; all six passed. The [private-image results](../../Evidence/Registry%20and%20Stack%20Preparation%20-%202026-09-15/Exports/Private-Image-Verification.json) and [push results](../../Evidence/Registry%20and%20Stack%20Preparation%20-%202026-09-15/Exports/Image-Push-Verification.json) record each host and image.

I imported all 47 existing Compose projects using normalized definitions under `/opt/docker/dockhand/stacks/imported/<host>/<project>/compose.yaml`. Each file is mode 0600. I encrypted transfers containing resolved configuration, preserved project names and absolute host paths, merged BookLore's two Compose files, and removed the VPN profile gate only from the two already-running media services. A Compose round-trip comparison passed on each host before import. No application deployment was part of adoption.

All 47 definitions were readable through Dockhand's Compose API after adoption. I then created, deployed, read, saved, and removed a disposable stack on each host. All seven lifecycle tests passed. [Import results](../../Evidence/Registry%20and%20Stack%20Preparation%20-%202026-09-15/Exports/Stack-Imports.json) and [lifecycle results](../../Evidence/Registry%20and%20Stack%20Preparation%20-%202026-09-15/Exports/Stack-Lifecycle-Verification.json) retain those checks.

Dockhand's self-update check returned no error and no available update for the current image. I did not run its self-update operation.

## Prepared cutover

I staged eleven validated Compose definitions beneath `/opt/docker/dockhand/cutover` on `docker-main`: five application projects containing six custom services, and six Hawser projects. `manifest.json` lists the candidate paths and targeted services. These candidates are not active stack definitions.

The application candidates change the six services to the published registry names. They retain the four existing build contexts and add `/opt/docker/mcp-gateway/Dockerfile.ssh-manager` and `Dockerfile.unifi-network` to the two MCP services. The TeamSpeak monitor candidate removes its temporary `dockhand.update=false` exclusion. I verified that both additional Dockerfiles exist on `docker-blue`.

The Hawser candidates use `ghcr.io/finsys/hawser:latest`, set `dockhand.update=false` on the agent, and add a stopped `hawser-updater` service using `docker:29-cli` behind the `maintenance` profile. I installed the [updater script](../../Scripts/update-hawser.sh) on all six remote hosts and checked its shell syntax. The [overlay](../../Configuration/hawser-update-overlay.yaml) is the public reference for these changes. I have not created or started the updater containers.

At cutover I will retag the current Hawser image locally and recreate with pulling disabled, retaining the current 0.2.48 contents. Subsequent starts of `hawser-updater` will pull the latest agent image and recreate only Hawser. The helper reads the running agent's Compose-file labels so it follows the new path after a Dockhand deployment. This follows the [upstream companion-updater workflow](https://dockhand.pro/manual/#updating-hawser-agent).

Applying the prepared changes requires recreating the six named custom application containers and six Hawser agents, one host at a time. I will preserve existing image IDs for this migration, reconcile the original host definitions with the imported definitions, create the updater containers without starting them, and verify health and registry checks after each change. MCP service connections, the documentation site, the alert bot, and monitoring briefly pause while their containers are replaced. TeamSpeak voice servers and unrelated application containers are outside this cutover.

## Remaining limits and source ownership

The running custom containers still reference local image names. Until cutover, four still produce the original registry warning; Docusaurus is treated as local and the TeamSpeak monitor is excluded. Publication alone does not change a running container's image reference.

The imported definitions are authoritative for Dockhand UI edits. Original host files remain in place and do not automatically receive those edits. I must reconcile them before a later command-line deployment. Version and digest pins on upstream dependencies are unchanged; changing a pin remains an explicit release choice.

Check for updates compares published images. It cannot fetch custom application source changes or build them. I can build custom services from their prepared Compose definitions and publish the image with Dockhand's push control. Future source changes and compatibility checks still precede publication.

## Verification and cleanup

I corrected two test-harness assumptions during validation: the images API uses `repoTags` and `id`, and a successful push returns `status: complete`. The final image checks use those fields. I removed the disposable containers, test stacks, and `busybox:stable` test tags from all seven hosts. I also removed temporary transfer keys, encrypted bundles, and the host-side publishing credential directories after native push verification. Registry credentials remain in the vault and Dockhand's configured registry store.

All 69 pre-existing containers retained their IDs, start timestamps, and running states throughout this preparation. [Final verification](../../Evidence/Registry%20and%20Stack%20Preparation%20-%202026-09-15/Exports/Unchanged-Container-Verification.json) records the per-host totals. This baseline is after the earlier approved TeamSpeak monitor-only repair.

I created no snapshot or backup. I retained structured verification results rather than complete shell transcripts for this work; the commands and intermediate authentication or harness failures were observed in the working session. Publication uses Forgejo's documented [container registry](https://forgejo.org/docs/latest/user/packages/container/) interface.
