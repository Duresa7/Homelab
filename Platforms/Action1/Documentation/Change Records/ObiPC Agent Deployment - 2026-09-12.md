# ObiPC Agent Deployment

**Created:** 2026-09-12  
**Last updated:** 2026-09-12

I installed the Action1 agent on `ObiPC` on 2026-09-12 so that applications for the restricted user on that machine are deployed from a console I control. The agent installed, registered, and pulled its configuration from the cloud in the same session. `IK-user` was signed in at the console throughout and the install did not interrupt that session.

## Starting state

Read from the machine over SSH Manager before the install:

| Check | Observed result |
|---|---|
| OS | `Microsoft Windows 11 Business`, version 10.0.26200, `EditionID` `Professional` |
| Existing management agent | None. No Action1 service, no OMA-DM enrollment, no Intune Management Extension |
| Interactive session | `ALPHASEC\IK-user`, console session 1, Active, signed in 9:58 AM |

## The agent download URL is a credential

The download URL carries the organisation identifier as a path segment, in the form `https://app.na-2.action1.com/agent/<REDACTED_ACTION1_ORG_ID>/Windows/agent(My_Organization).msi`. Action1's own dialog says no login is required to use it, which is the point: anyone holding that URL can enrol a machine into this organisation. I treat it as withheld under my publication policy for the same reason a tunnel identifier is withheld, and it does not appear in this repository.

## Sequence, all 2026-09-12 Eastern

| Time | Step | Result |
|---|---|---|
| 10:07 AM | First download attempt | 0 bytes. `curl.exe -sSIL` returned `HTTP/1.1 200 OK` with `Content-Type: text/html` and an empty body, because I had mistyped one character of the organisation identifier. A wrong identifier returns 200 and an empty HTML response rather than a 404, so the failure looks like a network problem and is not one |
| 10:08 AM | Download, corrected identifier | 7,139,328 bytes. First 8 bytes `208,207,17,224,161,177,26,225`, which is the OLE2 compound document signature, so the file is a real MSI and not another HTML error body |
| 10:09 AM | `msiexec /i action1.msi /quiet /qn /norestart` | Verbose log to `C:\Windows\Temp\provision\action1-install.log` |
| 10:09 AM | Service check, 20 s after launch | `A1Agent`, `Action1 Agent`, Running, Automatic |
| 10:10 AM | Registration check | Agent had already written `rules.json` at 79,685 bytes and `advanced_settings.json` at 55,813 bytes |
| 10:11 AM | Cleanup | Removed the staged `.msi` and `.exe` installers from `C:\Windows\Temp\provision` |

## Verification

| Check | Result |
|---|---|
| Service | `A1Agent`, `LocalSystem`, Automatic, Running |
| Service binary | `C:\Windows\Action1\action1_agent.exe service` |
| Installed product | `Action1 Agent`, version 6.0.664.1, present in both the WMI product list and the machine uninstall key |
| Cloud registration | `rules.json` 79,685 bytes and `advanced_settings.json` 55,813 bytes present on disk. The agent does not author these locally, so their presence is the evidence that it reached the service and received its configuration |
| Name resolution | DNS client cache held `us-cdn.action1.com` to `us-cdn-action1-com.b-cdn.net` and `169.150.236.107` |
| User session | `ALPHASEC\IK-user` still signed in at the console after the install, uninterrupted |

I did not capture an established TCP connection owned by the agent process. I sampled `Get-NetTCPConnection` once per second for five seconds and saw none, which is expected for a polling agent between cycles and is not evidence against registration. The configuration files it had already written are the stronger check, so I did not extend the sample.

I have not confirmed the endpoint from the Action1 console. Everything above is read from the endpoint.

## Applications installed the same day

Chrome and Visual Studio Code went on before the agent did, from vendor installers rather than through Action1:

| Application | Version | Path |
|---|---|---|
| Google Chrome | 153.0.8010.37 | `C:\Program Files\Google\Chrome\Application\chrome.exe` |
| Visual Studio Code | 1.137.0 | `C:\Program Files\Microsoft VS Code\Code.exe` |

Both are machine-wide installs in `Program Files`, which is what the planned AppLocker allowlist trusts. A per-user install into the profile would have sat outside it.

Git, Node.js, and Python were in the same batch and did not install. Now that the agent is in place they belong in Action1 rather than in another hand-run script, so I stopped rather than finishing that way.

## winget is not usable on this machine over SSH

`winget` fails on `ObiPC` in an SSH session and I did not fix it. Recorded because the next person to reach for it will hit the same wall:

- Symptom: `winget install` and `winget search` both return `0x8a15000f : Data required by the source is missing`, and `No packages were found among the working sources`.
- Tried: `winget source reset --force`, then `winget source update`, which reported Done for all three sources; then removing and re-adding the `winget` source as `Microsoft.PreIndexed.Package`, which also reported Done. The following search failed identically.
- State: `winget` v1.29.290, App Installer 1.29.290.0. `msstore`, `winget`, and `winget-font` all listed.
- Root cause: not established. The pre-indexed source is delivered as an MSIX and the likely explanation is that it cannot deploy in a non-interactive session, but I did not prove that.
- Workaround: vendor installers fetched with `curl.exe` or `Invoke-WebRequest` and run with their silent switches.

## Two things about running installs over this SSH gateway

Both cost me time and both are properties of the gateway rather than of `ObiPC`:

- Commands against `obipc` are cut off at 30 seconds whatever `timeout` I pass, against a documented default of 120,000 ms and a cap of 300,000 ms. Anything longer has to be launched detached and polled.
- The gateway wraps the command in `powershell -EncodedCommand`, so a long script exceeds the 8,191 character command line limit and fails with `The command line is too long`. Writing a script to the host has to be chunked.

The first one bit twice over: a call that returned `Command timeout after 30000ms` to me kept running on the host and finished its work. I then launched a second copy, and the two overlapped on the Windows Installer mutex. Chrome and Visual Studio Code were installed by the first run. Nothing was damaged, but a timeout from this gateway means the client stopped waiting, not that the remote work stopped.

## Console path confirmed, later the same morning

The console confirmation resolved itself: a Chrome deployment started in the Action1 console reached the agent and ran. The agent's `package_downloads` folder held a `CLOUD_*_builtin` package for `ChromeSetup_153.0.8010.37_x64.exe` written at 10:14:34 AM, with a `.result` file containing `OK` at 10:14:54 AM. The `builtin` marker means it came from Action1's own Software Repository rather than a custom package. Chrome was already installed at that same version from earlier in the morning, so nothing on disk changed, but the job is the proof that console, cloud, and agent are connected end to end.

## Open

- Deploy Git, Node.js, and Python from the Action1 Software Repository. Tracked in the root [TODO](../../../../TODO.md) as part of the `ObiPC` restriction project.
- Decide where Action1 and Intune divide, before `ObiPC` is ever Intune enrolled. Both deploy software.
- `winget` on `ObiPC` is unexplained.
