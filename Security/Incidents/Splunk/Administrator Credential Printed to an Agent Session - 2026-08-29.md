# Splunk Administrator Credential Printed to an Agent Session

**Created:** 2026-08-29  
**Last updated:** 2026-08-29

## Incident Metadata

| Field | Value |
|---|---|
| Incident ID | ASU-SPLUNK-20260829-001 |
| Detected | 2026-08-29, immediately, in the output of the command that caused it; exact minute not retained |
| Mitigated | 2026-08-29 3:05 AM EDT, when the staged credential file was shredded off `splunk-siem` |
| Status | Closed |
| Severity | SEV-5 |
| Impact type | Credential disclosure into an agent session context; no persisted copy, no confirmed unauthorized use |
| Affected service | Splunk Enterprise 10.4.0 on `splunk-siem` |
| Affected asset | The Splunk administrator credential |

## Summary

While building the `unifi_insights` app I staged the Splunk administrator credential into `/home/dkadi/.splunk_netrc` on `splunk-siem`, using `op inject` so the value went from the password manager to a mode-600 file without passing through a command line. That part worked as intended.

REST calls against that file then started returning `Unauthorized`, so I went to check which host the file was scoped to. I ran:

```bash
awk '{print $1, $2, $3, $4, "password <redacted>"}' /home/dkadi/.splunk_netrc
```

The intent was to print the keys and suppress the values. A curl netrc is three lines, `machine`, `login` and `password`, one key-value pair per line, so on the third line `$2` **is** the password. The literal `"password <redacted>"` I appended did nothing except make the output look redacted. The command printed the credential.

The real fault was 214 bytes further up: the file said `machine 127.0.0.1` and I was calling `https://localhost:8089`, so curl never offered the credentials at all. I did not need to look inside the file to learn that.

## Impact

The value entered the agent session's working context and was therefore included in the model request for that turn. That path cannot be recalled and is the exposure this record exists for.

It did not reach disk. The session transcript persists the tool result with `<REDACTED_PASSWORD>` in the position the value occupied, so the file on disk never carried it.

Splunk Web is not published to the internet and has no WAN port forward. The management port 8089 the credential authenticates against is bound to the host and reachable only from the internal networks.

## Affected Assets

- Splunk Enterprise 10.4.0 on `splunk-siem` at `192.168.72.3`, and its administrator account.
- `/home/dkadi/.splunk_netrc`, staged 2026-08-28 1:57 PM EDT and shredded 2026-08-29 3:05 AM EDT.
- The agent session transcript at `~/.claude_alt/projects/-home-ai-agent-Documents-Homelab/`.

No Splunk data, index, app or search was affected. The `unifi_insights` work continued and completed on the same instance.

## Symptoms

None observable on the service. Splunk stayed healthy throughout and authenticated normally. This was a disclosure event in the tooling around the work, not a fault in the work.

## Timeline

| Time | Event |
|---|---|
| 2026-08-28 1:57 PM EDT | I staged the credential to `/home/dkadi/.splunk_netrc` through `op inject`, mode 600, owner `dkadi`. |
| 2026-08-29, exact minute not retained | REST calls returned `Unauthorized` because the netrc named `127.0.0.1` and the requests targeted `localhost`. |
| 2026-08-29, exact minute not retained | I ran the `awk` above to inspect the file's structure, and it printed the credential. |
| 2026-08-29, exact minute not retained | I repointed the requests at `127.0.0.1`, which resolved the original `Unauthorized`. |
| 2026-08-29 3:05 AM EDT | I shredded `/home/dkadi/.splunk_netrc` and removed every scratch script staged alongside it. |
| 2026-08-29 3:20 AM EDT | I swept every file under `$HOME` for the value, reading the comparison value from the password manager through a pipe so it never reached a command line or a file. Zero matches. |
| 2026-08-29 3:35 AM EDT | I streamed all 3,371 blobs in the repository's full history through the same comparison. Zero matches. |
| 2026-08-29 3:46 AM EDT | I confirmed the persisted transcript carries `<REDACTED_PASSWORD>` in both places the value would otherwise appear. |

## Findings

- The persisted transcript contains the marker `<REDACTED_PASSWORD>` in the two positions the value occupied. It never held the plaintext.
- A sweep of every readable text file under `$HOME`, excluding only `.git`, `node_modules` and cache directories, returned zero matches.
- A sweep of all 3,371 blobs across every reachable commit in this repository returned zero matches. Nothing was ever committed.
- `/home/dkadi/.splunk_netrc` no longer exists. The eleven scratch scripts staged beside it during the work are also gone.
- The staging itself followed the rule it was supposed to: `op inject` wrote the file directly, so the value was never a command-line argument or a shell variable. The failure was reading the file back, not writing it.
- The `"password <redacted>"` literal in the command made the output *look* sanitised. That is worse than no attempt, because it invites a reader to skim past the line.

## Root Cause

I inspected a credential file's contents to answer a question about the file's scope. There was no reason to read any value: the question was which host the file named, and that is the first field of the first line.

The compounding error was assuming `awk '{print $1, $2}'` prints only keys. It prints keys and values whenever the file's format is one key-value pair per line, which is what a netrc is.

## Corrective Actions

1. I shredded `/home/dkadi/.splunk_netrc` with `shred -u` and removed the scratch scripts staged with it.
2. I verified the persisted transcript carries `<REDACTED_PASSWORD>` where the value would have been, so nothing on disk retains it.
3. I swept `$HOME` and the repository's entire commit history against the live value pulled from the password manager through a pipe, and confirmed zero copies exist.
4. I recorded the read pattern below so the same command is not reached for again.
5. The Splunk administrator credential was not rotated.

## Validation

The evidence for closure is negative and it is complete for every path that persists:

| Check | Result |
|---|---|
| Value present in the persisted session transcript | No; the marker occupies both positions |
| Value present anywhere under `$HOME` | No; zero matches across every readable text file |
| Value present in repository history | No; zero matches across 3,371 blobs |
| Staged credential file still on `splunk-siem` | No; shredded 3:05 AM EDT |

What this does not prove is the model-request path, which is the one channel that carried the value off the host and cannot be swept. That is why the record exists at all rather than being a note in a change record.

## Lessons

**Never read a credential file to learn something about it.** Read its metadata. `ls -l` gives the mode and owner, `wc -l` gives the shape, and `cut -d' ' -f1` gives the keys without ever touching a value. If the answer needs a value, the question is wrong.

**A netrc is one key-value pair per line, so field two is the secret on the line that matters.** Any `print $2` over a credential file is a disclosure by construction, whatever else is on the line.

**Do not decorate output with the word redacted.** Appending `"password <redacted>"` produced a line that reads as sanitised and is not. Either the command cannot emit the value or it should not be run.

**`Unauthorized` from a netrc is almost always the machine line, not the credential.** curl matches the netrc entry against the hostname in the URL, so `machine 127.0.0.1` does not serve a request to `localhost`. Check that before looking anywhere else.

## Follow-Ups

| Action | Status |
|---|---|
| Shred the staged credential file and its scratch scripts | Complete |
| Confirm the persisted transcript retains no plaintext value | Complete |
| Sweep `$HOME` and repository history for surviving copies | Complete |
| Rotate the Splunk administrator credential | Not performed |
| Fold the read pattern into the credential-handling guidance | Open, see [TODO.md](../../../TODO.md) |

## Linked Records

- [UniFi Syslog Export Restored and CIM Coverage Completed - 2026-08-29](../../../Platforms/Splunk/Enterprise/Documentation/Change%20Records/UniFi%20Syslog%20Export%20Restored%20and%20CIM%20Coverage%20Completed%20-%202026-08-29.md), the work in progress when this happened
- [Grafana Plaintext Administrator Credential - 2026-07-22](../Grafana/Plaintext%20Administrator%20Credential%20-%202026-07-22.md), the precedent for a plaintext credential getting an incident record
- [SSH Manager Sudo Password on Ten Guests - 2026-08-20](../../../Operations/Maintenance/SSH%20Manager%20Sudo%20Password%20on%20Ten%20Guests%20-%202026-08-20.md), the earlier transcript exposure and the scan-from-`$HOME` lesson this record reused
