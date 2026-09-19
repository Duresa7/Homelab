# Credential, Catalog Verification and Self-Update - 2026-09-19

**Created:** 2026-09-19  
**Last updated:** 2026-09-19

The [first deployment](Server%20Deployment%20on%20docker-main%20-%202026-09-19.md) left App Portal running with nothing to talk to: the Action1 API credential did not exist, so every install request answered HTTP 502. This record covers the afternoon that changed that, and what the first live call against the tenant turned up.

## The credential goes live

You created the API credential in the Action1 console and stored it in the vault under the title *<REDACTED_CREDENTIAL_ITEM_NAME>*, in the vault my automation account can read. The item carried the client id and the secret; the organisation identifier that every API path needs was not in it, so I resolved it from the API itself, listing organisations with the fresh token (there is one, *AlphaSec United*), and added it to the item as a third field. The client id turns out to embed the organisation identifier, so that field is a convenience rather than a second secret.

`server.env` on `docker-main` is rendered from vault references only. The template names the three fields; the manager's CLI resolves them into a local file that never appears on a terminal, `scp` carries it to the host as `server.env.new` with mode 600, and a rename puts it in place. The container is then recreated, because Compose reads `env_file` at creation and not on restart. The local copy is shredded afterwards. Neither value was printed at any point; each field was checked by length only (36, 92 and 32 characters).

The public repository's README and templates named the manager and its CLI; as of this evening they say "secrets manager" and carry placeholders, so the two repositories follow the same rule.

One exposure to record, at your decision: the item stores the client id in the `username` field, which the API Credential template treats as plain text, so a metadata read of the item printed it into my session. The secret was masked and never shown. You judged that no rotation was warranted. The client id is not in this repository and stays out of it.

## The first live call found a crash

`catalog verify` inside the container resolved Google Chrome to 153.0.8010.53 and then died with an unhandled `JsonException` on Mozilla Firefox. Action1 answers a lookup for a package identifier it does not know with **HTTP 200 and an empty body**, not a 404, and the server's JSON reader threw on the empty input. The same code path sits behind `POST /api/v1/installs`, where the exception would have surfaced to a device as a 500 with no useful message.

The Firefox identifier in the catalog was a guess, as were VLC and Visual Studio Code; Chrome and 7-Zip had been checked. `packages search` against the tenant found the real ones. The Firefox entry that matched the name I had used was the macOS build; the Windows en-US package has a different suffix entirely.

Both problems are fixed in the repository rather than on the host:

- Every body read in the Action1 client goes through one helper. An empty body is null, which `ResolvePackageVersionAsync` already reports as "no published version" and the API as 422. A body that is not JSON becomes the `Action1Exception` every caller handles. Three tests cover the empty body, a maintenance-page HTML body, and a normal version list.
- Error text that reaches device clients has the organisation identifier replaced with `{org}`, and the server's startup line says `organization (set)` rather than the value. HttpClient request logging is at Warning, so request paths carrying package and organisation identifiers stay out of the container log.
- Firefox, VLC and Visual Studio Code carry the identifiers the tenant reports.

## The client updates itself

You asked for a way to stop re-downloading the client for every release. The constraint is the same one that shaped the whole design: the person at the keyboard cannot write to Program Files, and on `ObiPC` cannot run anything outside it, so the client cannot update itself and a per-user updater would be blocked by AppLocker.

`AppPortal.Updater.exe`, a single self-contained executable beside the client, runs from a scheduled task named **App Portal Updater** as `SYSTEM`: five minutes after boot, a minute after any logon, daily at a random time between noon and one, and whenever a user presses the button in the client. A run asks GitHub for the latest release, compares the tag with the installed file version, downloads the archive while hashing it, checks the hash against the `SHA256SUMS` the release publishes, unpacks the client folder into `.staged` inside Program Files, and swaps it in by renaming: current files into `.previous`, staged files into place. Windows permits renaming a running executable, which is how the updater replaces itself and why a client that is open does not have to be killed; the swap simply waits for the next run, or for twenty seconds after the client asks and exits. A move that fails half-way restores the old files. `.previous` is deleted on the following run.

The client never touches the release feed. It reads `%ProgramData%\AppPortal\update.json`, which the updater writes, and shows a banner: *App Portal x is available* with **Update now**, or once staged *App Portal x is ready* with **Restart to update**, which starts the task and exits. The task's security descriptor grants Authenticated Users read and execute, so a standard user can start it and nothing else. Scratch space is under Program Files, so nothing a user controls can put a build on the machine.

What the checksum proves and does not prove: a truncated or corrupted download, and a mismatch between the archive and what CI published, are caught. A compromised GitHub account is not, because the checksums come from the same release. The releases are unsigned. Signing is the next hardening step and is on the TODO.

Versioning moved to one place, `Directory.Build.props`, and a release build takes its version from the tag, because the updater compares the tag with the installed file version and the two must agree. The previous release, v0.1.1, shipped binaries stamped 0.1.0 for that reason; it did not matter then and would have mattered now.

## The test machine is enrolled and can now reach the server

You want to try the client on `HQ-WS001` as `testuser` before anything touches `ObiPC`. Action1 lists that VM as a managed endpoint, connected, Windows 11 25H2, so it qualifies. I registered it on the server with `device add`, which printed the device token once; the token went from that output into a vault item, *<REDACTED_CREDENTIAL_ITEM_NAME>*, without appearing on a terminal, alongside the server address and the install command that takes it. The server keeps only the token's SHA-256, and its device store re-reads `devices.json` by timestamp, so the new record was live without a restart.

The identity plane could not reach the portal at all, which is the network doing what it was built to do: `HQ-WS001` is `192.168.65.20` on VLAN 65, and nothing in that zone routes to `docker-main` on VLAN 40 without a policy. I added one, scoped to that single address and that single port, and proved it both ways: the machine now answers `{"status":"ok"}` from the portal's health endpoint, while `HQ-MGT01` in the same zone stays refused. `ObiPC` will need nothing equivalent, since Secure Client and Personal-A are both inside the Internal zone.

Two things worth knowing for the next enrollment. Action1 carries **two** `ObiPC` endpoints, one last seen 2026-09-13 and therefore the machine before the rebuild; the current one is the entry seen today. And `testuser`'s membership of `ROL-ObiPC-Restricted`, put in place this morning for the AppLocker test, changes nothing on `HQ-WS001`: the AppLocker policy is filtered to `OBIPC$`, and the restricted user policy reaches a session only through loopback processing that exists on `ObiPC`'s computer policy alone. On the test VM `testuser` is an ordinary standard user, which is the right seat for this test.

## Verification

| Check | Result |
|---|---|
| Rendered environment file | 0 unresolved references; three credential fields present, checked by length only |
| Container after recreate | `Up`, `(healthy)`; startup log `Action1 mode: Live; ... organization (set)` |
| Token request from the container | HTTP 200 in 942 ms |
| `catalog verify` before the fix | Chrome OK, then an unhandled `JsonException` on Firefox |
| `catalog verify` after the fix and the corrected identifiers | Chrome 153.0.8010.53, Firefox 156.0, 7-Zip 26.03.00.0, VLC 3.0.23, Visual Studio Code 1.138.0; *All catalog packages resolve* |
| Test suite | 31 passing: 20 server, 11 updater |
| Updater publish, win-x64 | one file, `AppPortal.Updater.exe`, 37.6 MB |
| Update banners | Rendered under Xvfb in both themes from a fabricated status file; images are in the repository's `docs/images/` |
| `device list` on the server | `HQ-WS001`, enabled, registered 2026-09-19 15:12 UTC |
| Vault item for the token | *<REDACTED_CREDENTIAL_ITEM_NAME>*, credential field concealed, server address in the hostname field |
| Network path before the firewall change | **Dropped.** From `HQ-WS001` itself, through its guest agent, TCP to `192.168.40.35:3004` timed out at five seconds while LDAP to `HQ-DC01` answered at once. Nginx Proxy Manager was equally unreachable from the zone |
| Network path after the firewall change | TCP 3004 connects and `http://192.168.40.35:3004/healthz` returns `{"status":"ok"}` from `HQ-WS001` |
| Firewall control | `HQ-MGT01` at `192.168.65.12`, same zone, outside the policy, refused on 3004 both before and after |
| Release `v0.2.0` | CI run 35450364737: *Build and test*, *Publish Windows client* and *Build server image* all `success`; assets `AppPortal-client-win-x64.zip` (106.7 MB) and `SHA256SUMS`; the archive verifies against the checksum file and contains `client/AppPortal.Updater.exe` and `client/Uninstall-AppPortalClient.ps1` |

## Open

- **`HQ-WS001` is enrolled for the test; `ObiPC` is not.** Registering `ObiPC` with `device add` against its current Action1 endpoint, vaulting the token, and deploying the client through Action1 is the next piece of work once the test passes.
- **The path to the server is a test fixture, not the end state.** `HQ-WS001` sits on VLAN 65, which by design reaches neither `docker-main` nor Nginx Proxy Manager. On 2026-09-19 I opened `Allow Identity to App Portal`, a narrow IPv4 TCP allow from that one address to `192.168.40.35:3004`, recorded in the [firewall configuration](../../../../Infrastructure/Network/UniFi/Configuration/firewall.md). It carries a bearer token over plain HTTP on the LAN, which is acceptable for a test on a machine I control and not acceptable as a standing arrangement. The durable answer is an Nginx Proxy Manager host with the wildcard certificate and a name the controllers resolve, after which this policy is removed.
- **Signed releases.** The updater trusts the GitHub release; a signature checked against a key embedded in the updater would remove that dependency.
- **TLS.** The listener is plain HTTP on the LAN. Putting it behind Nginx Proxy Manager is unchanged from the first record.
- **The client has not run on a real machine.** The Windows-specific paths in the updater, the scheduled task registration and the swap on a running executable are all tested only in their cross-platform parts.
