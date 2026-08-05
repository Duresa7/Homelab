# Preview Server LAN-Exposed Repository Root Incident

**Created:** 2026-07-26  
**Last updated:** 2026-08-04

## Incident Metadata

| Field | Value |
|---|---|
| Incident ID | ASU-PREVIEW-20260725-001 |
| Occurred | 2026-07-25; start not retained |
| Detected | 2026-07-25, while rewriting the preview server; exact minute not retained |
| Mitigated | 2026-07-25 15:11:28 EDT, when the replacement `serve.js` was written |
| Status | Closed |
| Severity | SEV-3 |
| Impact type | Potential disclosure of unpublished repository content; no confirmed access |
| Affected service | Local preview static file server on `jedi-pc`, TCP 8123 |
| Affected asset | The whole `D:\Documents\Homelab` working tree, including `Sensitive/` |

## Summary

The first version of my preview server called `.listen(8123)` with no host argument. Node binds `0.0.0.0` and `[::]` when you leave the host out, so the server answered on every interface instead of just the loopback I assumed. It also resolved paths straight from the repository root with no allow list. Those two defects compound: the missing bind address decided who could ask, and the missing allow list decided how much they got.

While that server was running, `curl http://192.168.50.241:8123/Sensitive/Hardware/drive-serials.md` from elsewhere on the LAN returned HTTP 200 and 2,082 bytes of full drive serial numbers. `netstat` confirmed both wildcard bindings. I replaced the script the same day.

## Impact

Every file in the working tree was fetchable by path: 1,210 files and 94,738,393 bytes at the time of writing. `Sensitive/` accounts for 573 files and 58,758,859 bytes of that.

Two items there outrank the drive serials by a wide margin:

- `Sensitive/Scrub Operation/Git History/original-history-before-scrub-2026-07-15.bundle`, 12,486,978 bytes. That's the complete pre-scrub git history, which is the exact thing the 2026-07-15 public-repository scrub existed to keep out of public view.
- `Sensitive/Scrub Operation/Manifests/private-redaction-value-map-2026-07-15.csv`, 310 data rows with the columns `Category`, `OriginalValue`, `Placeholder`, `Occurrences`. It maps every placeholder in the public repository back to the real value. One file turns the scrubbed repository back into the unscrubbed one.

Also reachable: `Sensitive/Scrub Operation/Originals Before Redaction/` at 129 unredacted files, two more history bundles, and the local agent instruction files under `/.claude/`.

The runtime configs that would have been worst are not in the tree on this machine. `Platforms/Nginx Proxy Manager/Configuration/data`, its `letsencrypt` directory, `Platforms/Netbird/Configuration/config.yaml`, and `dashboard.env` are all absent locally, so no live service credential or private key was served.

## Who Could Reach It

I read the zone matrix from the controller on 2026-07-26. `jedi-pc` holds `192.168.50.241` on Secure/VLAN 50, which sits in the built-in Internal zone.

| Source zone | Toward Internal | Reachable |
|---|---|---|
| Internal | `Allow All Traffic`, ALLOW, ANY to ANY, index 2147483647 | Yes |
| Vpn | `Allow All Traffic`, ALLOW, ANY to ANY | Yes |
| Gateway | `Allow All Traffic`, ALLOW, ANY to ANY | Yes |
| External | `Block All Traffic`, BLOCK, plus `Block Invalid Traffic` | No |
| Untrusted | `Block All Traffic` plus the `Isolated Networks` BLOCK | No |
| Dmz | `Block All Traffic`; only return traffic allowed | No |
| The six custom zones | `Block All Traffic` on each; return-only | No |

So the exposure covered the six networks in Internal, which are Management, Trusted/VLAN 10, Personal-A/VLAN 40, Secure/VLAN 50, Secure Client/VLAN 60, and AD-SERVERS/VLAN 65, plus the five networks in Vpn, which include FamilyVPN. It did not cover the internet, IoT, the DMZ, or any lab or server VLAN. No port forward pointed at 8123.

The server never emitted a directory listing; it stats the path and 404s anything that isn't a file. That's weaker protection than it sounds. `.gitignore` is committed and public on GitHub, and it names `/Sensitive/` on its own line. Anyone who read the public repository already had the map.

## Timeline

| Time | Event |
|---|---|
| 2026-07-25 08:12:37 EDT | `Mission Control/index.pre-redesign-2026-07-25.html.bak` written; the preview work is underway |
| 2026-07-25, start not retained | The vulnerable server runs, bound to `0.0.0.0` and `[::]` |
| 2026-07-25, exact minute not retained | `netstat` shows both wildcard bindings |
| 2026-07-25, exact minute not retained | A LAN fetch of `/Sensitive/Hardware/drive-serials.md` against `192.168.50.241:8123` returns HTTP 200 and 2,082 bytes |
| 2026-07-25 15:11:28 EDT | The replacement `serve.js` is written with the loopback bind and the allow list |
| 2026-07-25 15:11:34 EDT | `.claude/launch.json` is written pointing at the new script |
| 2026-07-26 | I record the incident and rerun validation |

## Findings

- The defect was `.listen(PORT)` with no host, not a firewall misconfiguration. UniFi behaved exactly as configured; intra-zone Internal traffic is allowed by design.
- The old script wasn't retained, so its first-run time is unknown. I can bound the exposure to 2026-07-25 and no later than 15:11:28 EDT, and I can't narrow the start.
- There are no access logs. The old server wrote nothing to disk beyond its startup line, and no UniFi traffic-flow record for TCP 8123 to `192.168.50.241` survives. Nothing suggests anyone fetched anything, and I can't prove nobody did.
- Serving the repository root was a second, independent defect. Fixing only the bind would have left the whole tree readable from the workstation itself and from anything that later got a loopback path.

## Root Cause

I wrote a single-user tool and never named the interface it should listen on. Node's default filled in the most permissive option available. I then pointed it at the repository root because that was the shortest path to previewing a file, which put `Sensitive/` one URL away from a server I had already told to answer the whole LAN.

## Corrective Actions

1. The listener binds `127.0.0.1` explicitly. `serve.js` now passes `HOST` to `.listen(PORT, HOST, ...)`.
2. An `ALLOW` list restricts serving to `Guides` and `Mission Control`. Everything else returns 404.
3. Paths that are empty or start with a dot are rejected, so dotfiles and `.claude/` are unreachable.
4. The resolved absolute path is re-checked against the allow list after `path.resolve`, so `..` can't climb out of an allowed folder.
5. The reasoning is recorded in the [Preview Server README](../../../Engineering/Preview%20Server/README.md) beside the code, with an explicit instruction never to add `Sensitive` to `ALLOW`.

On 2026-08-04 I replaced the folder allow list with per-request `git ls-files` membership, which follows the repository's publication boundary while retaining the loopback bind, resolved-path re-check, dotfile rejection, and absence of a default page.

## Validation

I reran the checks on 2026-07-26 with the server up.

| Check | Observed result |
|---|---|
| Listener binding | `Get-NetTCPConnection -LocalPort 8123` returns `127.0.0.1` only |
| LAN address, sensitive path | `http://192.168.50.241:8123/Sensitive/Hardware/drive-serials.md` refuses the connection |
| LAN address, allowed path | `http://192.168.50.241:8123/Mission%20Control/index.html` refuses the connection |
| Loopback, allowed path | `Mission Control/index.html` returns 200 and 313,814 bytes |
| Loopback, drive serials | 404 |
| Loopback, redaction value map | 404 |
| Loopback, pre-scrub history bundle | 404 |
| Loopback, `CLAUDE.md` | 404 |
| Loopback, `.claude/settings.local.json` | 404 |
| Loopback, `Guides/../Sensitive/Hardware/drive-serials.md` | 404 |

Because there are no logs from the exposure window, I classify this as potential disclosure with no confirmed access, not as proof that nothing was read.

## Lessons

`.listen(port)` binds every interface. A tool meant for one machine has to say so in the code, because the default is the opposite of what a local tool wants.

The bind address and the allow list are separate controls doing separate jobs, and I needed both. Either one alone still fails: a loopback-only server rooted at the repository would have kept `Sensitive/` one path away, and an allow-listed server on `0.0.0.0` would have published `Mission Control/` to the LAN.

A public `.gitignore` is a directory of the private paths. It's the right way to exclude files from git and a poor secret, so any local server has to assume the attacker already knows where to look.

## Follow-Ups

| Action | Status |
|---|---|
| Bind the listener to `127.0.0.1` | Complete |
| Restrict serving to an explicit allow list | Complete |
| Reject dotfiles and paths that escape an allowed folder | Complete |
| Verify the LAN address refuses and sensitive paths 404 | Complete |
| Move the pre-scrub history bundles and the redaction value map outside the working tree | Complete |

I completed the durable fix on 2026-07-27. I moved the three history bundles and the private redaction value map to `D:\Documents\Redaction Map`, outside the Homelab working tree. The four files total 13,536,299 bytes. I compared SHA256 values before and after the move: all four matched, no source copy remained, and there were zero mismatches. I chose a normal local folder without encryption.

## Linked Records

- [Preview Server](../../../Engineering/Preview%20Server/README.md), the tool and the two limits it now enforces
- Mission Control, the local dashboard the server was originally built to preview. I deleted it on 2026-08-04, so there is nothing to link. After that deletion and before the tracked-file rule replaced the folder list, the server served `Guides/` and `Assets/` only.
