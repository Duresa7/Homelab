# Internal HTTPS, ObiPC Enrollment and the First Self-Update

**Created:** 2026-09-19  
**Last updated:** 2026-09-19

Three pieces of work in one evening, all of them the parts that only a real machine can settle: the client updated itself while it was running, the portal moved behind the reverse proxy with a certificate, and `ObiPC` — the machine this project exists for — got the client.

## The updater replaced a running client

I cut **v0.2.1** for no reason other than to make an update exist. The version bump is the only change in it. Every part of the updater had been exercised on a build machine except the two that cannot be: renaming an executable that is currently running, and the *Restart to update* path in the client. `testuser` still had the client open on `HQ-WS001` from the afternoon's install, which is the exact condition I wanted.

The first run found the release, downloaded 101.8 MB, verified its SHA-256 against the published `SHA256SUMS`, unpacked it, and then did the right thing: it refused to swap under a running client, wrote `Staged` with the message *Close App Portal to finish updating*, and waited its twenty seconds before giving up gracefully. Download to staged took four seconds.

With the client closed, the next run swapped it. `AppPortal.exe` read 0.2.0.0 before and 0.2.1.0 after. The rename of the running updater into `.previous` behaved as designed and logged its own limitation plainly — *`.previous` stays for now: Access to the path 'AppPortal.Updater.exe' is denied* — because the updater cannot delete the copy of itself it is executing. The run after that deleted both `.previous` and `.update` and wrote `UpToDate` at 0.2.1.

One rough edge I looked at and decided was not one. `update.json` still described the staged state for the half-minute between the swap and the following run, so a client reopened inside that window would read a status file claiming an update was ready. It does not matter, because the banner is a version comparison rather than a status flag: *ready* requires the staged version to be newer than the running one, and 0.2.1 is not newer than 0.2.1. The banner stays hidden and the next run corrects the file.

`ObiPC` ran its own check unprompted seven minutes after installation and reported `UpToDate` at 0.2.1. Two machines now keep themselves current without me.

## The portal has a name and a certificate

`appportal.alphasecunited.com` resolves to `192.168.85.2` through the controller's local DNS and terminates on Nginx Proxy Manager as proxy host 32, forwarding to `http://192.168.40.35:3004` with the shared wildcard certificate, Force SSL, HTTP/2 and Block Common Exploits. That matches every other internal host; nothing here is special.

What actually blocked it was a firewall rule nobody would think to check. `Allow NPM to docker-main web UIs` lists destination ports explicitly — 2283, 3000, 3001, 3002, 3003 and 6060 — so the proxy could reach Dockhand on 3003 and timed out on the portal's 3004. From the proxy itself, `curl` to 3003 returned 307 and 3004 returned nothing at all. I added 3004 to that policy's port list rather than creating a new one, because the policy already means *the approved docker-main web interfaces* and the portal is one of them.

## The plain-HTTP allow is gone

`HQ-WS001` now points at `https://appportal.alphasecunited.com`. Its device token did not change; only `serverUrl` in `client.json` did.

The path it takes changed completely. `Allow HQ-WS001 to NPM HTTPS` admits `192.168.65.20` to `192.168.85.2:443` and nothing else, and `Allow Identity to App Portal` — the plain-HTTP allow to `192.168.40.35:3004` that carried the afternoon's test — is deleted. A bearer token no longer crosses the LAN in the clear.

Two things are worth writing down. **An interrupted create still creates.** I cancelled the policy-creation call mid-flight and the controller had already taken it twice, a millisecond apart, leaving two identical policies; I deleted the second. This is the same trap as a preview call that mutates, and the rule stands: check the live list before retrying anything that creates. **A deleted policy is not instantly enforced.** Immediately after the delete, `HQ-WS001` still connected to `192.168.40.35:3004`. About a minute later the same probe was refused, with TCP 3003 refused as a control and the TLS path still answering. If I had tested once and stopped, I would have recorded exactly the wrong conclusion.

## ObiPC carries the client

Action1 lists two `ObiPC` endpoints. One was last seen 2026-09-13 and is the machine as it existed before the rebuild; the live one has today's timestamp and `192.168.60.102`. I registered the live one with `device add`, and the token went into the vault item *<REDACTED_CREDENTIAL_ITEM_NAME>* without appearing on a terminal. Registering by name a second time simply rotates the token, which is what happened while I was getting the vault item's shape right; the value in the vault is the one the server's hash matches, and I proved that by calling the server's device endpoint with it before installing anything.

The client went on over SSH as an elevated session, from the release archive, after checking its SHA-256 against the release's `SHA256SUMS` on the machine itself. `ObiPC` runs 0.2.1 pointing at the TLS name, with the updater task registered and the Start menu shortcut in place for everyone.

**I chose not to push it through Action1, and that is a decision rather than an omission.** An Action1 deployment would have to carry the device token inside the automation's script text, where the console retains it; a bearer secret for a machine does not belong in an automation history. `ObiPC` has SSH, so it did not need that path. The fleet answer is an enrollment code the client can exchange for its own token, which belongs in the application rather than in a deployment script, and it is on the backlog.

AppLocker allows the client, though not by the test that looks like it should prove it. `Test-AppLockerPolicy` reported `DeniedByDefault` for the restricted group, which is the known false negative: that cmdlet only matches rules naming the principal you pass, and the rule covering the client is the `Everyone: Program Files` allow. Reading the effective policy instead shows one path rule over `%PROGRAMFILES%\*` for `S-1-1-0` with the Exe collection enforced, and no deny matching the install path. The honest statement is that the policy permits it and the last word belongs to the first launch by a restricted user.

## Verification

| Check | Result |
|---|---|
| Release v0.2.1 | CI run 35460013838 green; `AppPortal-client-win-x64.zip` and `SHA256SUMS` attached |
| Update with the client running | Downloaded 101.8 MB, SHA-256 verified, staged in four seconds, `Staged` / *Close App Portal to finish updating* |
| Swap of a running executable | `AppPortal.exe` 0.2.0.0 before, 0.2.1.0 after |
| Cleanup | `.previous` deferred on the applying run, then `.previous` and `.update` both absent; status `UpToDate` at 0.2.1 |
| Unattended check on `ObiPC` | Ran on its own at 14:15, `UpToDate`, task `Ready`, last result 0 |
| Proxy host | NPM host 32, certificate 1, Force SSL, HTTP/2; 24 enabled hosts |
| Local DNS | `appportal.alphasecunited.com` → `192.168.85.2`; controller returns 30 records, 24 of them to Nginx Proxy Manager |
| Proxy to portal before the port change | `curl` from `docker-network`: 3003 returned 307, 3004 returned nothing |
| Proxy to portal after the port change | `https://appportal.alphasecunited.com/healthz` returns `{"status":"ok"}` from both `ObiPC` and `HQ-WS001` |
| `HQ-WS001` after the cutover | `serverUrl` is the TLS name, token unchanged at 47 characters, device endpoint returns `HQ-WS001` / `Connected`, catalog returns five apps |
| Plain HTTP after the delete | Connected immediately after the delete; refused about a minute later, with TCP 3003 refused as a control |
| `ObiPC` registration | `device add` against the endpoint last seen today; vault item created; the vaulted token authenticates and the server resolves it to `ObiPC` / `Connected` |
| `ObiPC` install | Archive SHA-256 matched the release before extraction; `AppPortal.exe` 0.2.1.0, updater present, task `Ready`, shortcut present, `client.json` at the TLS name with a 47-character token, staging files removed |
| `ObiPC` client to server | Device endpoint returns `ObiPC` / `Connected`, catalog returns five apps, over TLS |
| AppLocker on `ObiPC` | Effective Exe collection enforced; one allow for `S-1-1-0` over `%PROGRAMFILES%\*`; no deny matches the install path |

## Open

- **No one has installed anything from `ObiPC` yet.** Every link in the chain is proven there except a person pressing Install, which is `IK-user`'s to do.
- **Enrollment codes.** The device token has to be typed at install time or embedded in a deployment script. A short-lived enrollment code the client exchanges for its own token would remove both, and would make an Action1 deployment safe.
- **Signed releases.** The updater still trusts the GitHub release; the checksums come from the same place as the archive.
- **`testuser` is still in `ROL-ObiPC-Restricted`** as the AppLocker fixture and belongs back in the unrestricted group when that walkthrough finishes.
