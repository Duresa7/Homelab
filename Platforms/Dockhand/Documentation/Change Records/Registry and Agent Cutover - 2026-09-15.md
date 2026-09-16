# Registry and Agent Cutover

**Created:** 2026-09-15  
**Last updated:** 2026-09-15

**Status:** Complete.  
**Verification:** 2026-09-15, 11:27 PM Eastern.

I applied the approved cutover from [Registry and Stack Preparation](Registry%20and%20Stack%20Preparation%20-%202026-09-15.md). All six custom applications now run under their private Forgejo image names. Six Hawser agents use `ghcr.io/finsys/hawser:latest` with direct container updates excluded, and each remote host has a stopped `hawser-updater` container. The twelve recreated containers retain their previous image contents, environment, command, entrypoint, user, working directory, mounts, and published ports.

## Applied changes

| Host | Custom containers moved to the private registry | Hawser updater |
|---|---|---|
| docker-main | docusaurus | Local socket; no agent |
| docker-blue | mcp-ssh-manager, mcp-unifi-network | Created, stopped |
| docker-network | None | Created, stopped |
| monitor-01 | alert-bot | Created, stopped |
| media-01 | None | Created, stopped |
| alpha-prod-01 | teamspeak-monitor | Created, stopped |
| security-01 | wazuh-mcp-server | Created, stopped |

The custom image namespace is `forgejo.alphasecunited.com/homelab-images/<image>:stable`. The UniFi image is named `unifi-network-mcp`; the other image names match their containers. I retained the four existing build contexts and added the two existing MCP Dockerfiles to the MCP stack definition. I removed the TeamSpeak monitor's temporary `dockhand.update=false` exclusion.

I applied each host separately and disabled pulls and builds for the application and agent replacements. I retagged the existing Hawser image as `latest`, preserving 0.2.48. I pulled `docker:29-cli` for the updater helpers. I ran the docker-blue cutover as a detached process so recreating SSH Manager could not terminate its own maintenance command.

I reconciled eleven original host Compose definitions with the prepared candidates and copied those candidates into Dockhand's imported definitions. All 47 stack definitions remain readable through its authenticated API. The imported files remain authoritative for later UI edits; subsequent edits do not automatically update the original host files.

## Verification

[Host verification](../../Evidence/Registry%20and%20Agent%20Cutover%20-%202026-09-15/Exports/Host-Verification.json) records each replacement, image preservation, runtime comparison, Compose comparison, and health result. All 57 unrelated containers retain their IDs, start timestamps, and running states. Both TeamSpeak voice servers are in that unchanged set. The monitor's Prometheus textfile was nonempty and 52 seconds old when checked.

[Update checks](../../Evidence/Registry%20and%20Agent%20Cutover%20-%202026-09-15/Exports/Fleet-Update-Checks.json) returned zero registry errors across all seven environments. Each of the six custom applications is recognized as a registry image with checking enabled. I also verified a fresh HTTPS login with the previously aligned credential.

[Stack verification](../../Evidence/Registry%20and%20Agent%20Cutover%20-%202026-09-15/Exports/Stack-Verification.json) confirms 47 readable definitions, six custom registry image references, and six updater services. The fleet now holds 69 running containers and six stopped updaters, 75 total, across 47 projects. Every running container with a configured health check reports healthy.

For each updater I verified the Docker CLI's Compose plugin, socket access, script syntax, and Compose validation inside a disposable `docker:29-cli` container with the helper's mounts. I did not start the actual update scripts: they pull a newer upstream agent if one exists, outside this same-image cutover. Starting `hawser-updater` in Dockhand is the future agent update action. Its maintenance profile keeps it stopped during normal stack deployments, and updating Hawser briefly disconnects only that host's management connection.

The earlier preparation already tested registry pull/replacement and push for all six custom images, plus stack create, deploy, edit, and removal on all seven hosts. This cutover does not claim every Dockhand feature has been exercised. Custom source changes still require a build and publication before image checks can discover them. Existing upstream version and digest pins remain explicit release choices. I did not apply the nine upstream updates found during the earlier audit, update Dockhand itself, or retire Portainer.

## Interrupted attempt and corrections

The previous session stopped after its cutover script reported `Source drift before apply`, before replacing a container. The Docusaurus source still matched its original byte hash. The script's prepare step read bytes, while its apply step read text and normalized 28 CRLF line endings. I changed apply and rollback to preserve raw bytes and verified preparation on every host. [Cutover validation failures](../Troubleshooting/Cutover%20Validation%20Failures%20-%202026-09-15.md) records this and the subsequent helper creation failure.

The first docker-network attempt recreated Hawser successfully, then rejected `docker compose create --no-deps` because that subcommand does not support the flag. The script restored the original definition and successfully rolled Hawser back. I removed the unsupported flag and reran that host successfully; the helper has no dependencies. The final validation compares both definitions after Compose normalization, which accounts for the updater's generated default network and command fields.

## Cleanup

I retained structured verification results instead of full terminal transcripts. Individual command results and the two failed attempts were observed in the working sessions; no complete shell transcript is retained for those steps. The metrics freshness check and credential validation are recorded above without separate exports.

I removed `/opt/docker/.dockhand-cutover` from all seven hosts and the completed `/opt/docker/dockhand/cutover` tree from docker-main after verification. The protected imported definitions and six updater scripts remain active configuration. Disposable updater validation containers removed themselves. I created no snapshot or persistent backup.
