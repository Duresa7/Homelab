# Login Alignment and Update Verification

**Created:** 2026-09-15  
**Last updated:** 2026-09-15

I changed Dockhand's existing administrator username and password to match the approved shared login credential. I retained the same account and administrator role, verified a fresh HTTPS login, and synchronized the saved Dockhand credential. The source credential was not changed. Password changes invalidate existing sessions; a new sign-in is required. No credential values are recorded here.

I triggered an authenticated update check on each of the seven environments. Across 69 containers, nine registry-backed applications reported an update: CLI Proxy API, both Immich application containers, Forgejo, NetBird server, Radarr, Gluetun, Jellyfin, and Grafana. I did not apply application updates.

## Update-path test

I tested the actual Dockhand container update endpoint on each environment using `dockhand-update-check-20260915` with `busybox:stable`, entrypoint `/bin/sleep`, argument `300`, restart policy `no`, and network mode `none`. The temporary containers had no ports or volume mounts. The create request used `startAfterCreate: true`; the update request used `repullImage: true` and `startAfterUpdate: true`.

Every host returned a new container ID and a running replacement. I deleted each test container and removed `busybox:stable` where the tag had not existed before the test. Existing container IDs and running states matched the pre-test inventory on every host. The [verification results](../../Evidence/Login%20Alignment%20and%20Update%20Verification%20-%202026-09-15/Update%20Paths.json) retain the per-host outcomes. No full HTTP transcript is retained because authenticated requests contain session credentials; the sanitized result is the evidence artifact.

This proves the account permissions, registry pull path, local socket or Hawser connection, and container replacement operation on all seven hosts. It does not prove that a particular application upgrade is compatible with its existing data or configuration. I did not test agent self-replacement or the Dockhand self-update flow.

## Exceptions

| Container | Host | Update method and current result |
|---|---|---|
| teamspeak-monitor | alpha-prod-01 | Local source rebuild; the approved `dockhand.update=false` label removes the registry error. [Fix](../Troubleshooting/Local%20TeamSpeak%20Monitor%20Registry%20Check%20-%202026-09-15.md) |
| docusaurus | docker-main | Local build; Dockhand classifies it as local |
| mcp-ssh-manager | docker-blue | Local patched image; registry check errors; [build procedure](../../../Docker%20MCP%20Gateway/README.md) |
| mcp-unifi-network | docker-blue | Local patched image; registry check errors; [build procedure](../../../Docker%20MCP%20Gateway/README.md) |
| alert-bot | monitor-01 | Local build in the monitoring Compose project; registry check errors |
| wazuh-mcp-server | security-01 | Local compatibility build; registry check errors |
| Hawser agents | Six remote hosts | Host-side or companion updater required to avoid disconnecting their own update operation |
| Dockhand | docker-main | Dedicated self-update flow; not included in the disposable-container test |

The four remaining registry warnings are not connectivity failures: their locally built images are not available at the implied registry references. I confirmed the image references and project files through live Docker inspection and the two MCP build procedures in the existing records. I have not restarted those services or replaced their patched images with upstream images.

Remote Compose editing and source builds still need reviewed imports and build contexts. The current deployment supports ordinary registry-backed container updates across all seven hosts, but not an all-component one-click update workflow. I recorded that remaining scope in the [central TODO](../../../../TODO.md).
