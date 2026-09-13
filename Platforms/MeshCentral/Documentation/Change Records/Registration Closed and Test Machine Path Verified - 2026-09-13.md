# Registration Closed and Test Machine Path Verified

**Created:** 2026-09-13  
**Last updated:** 2026-09-13  
**Implementation:** 2026-09-13  
**Verification:** 2026-09-13

I claimed the site administrator account, closed registration, and demonstrated that `HQ-WS001` reaches the server. The [deployment record](Deployment%20-%202026-09-12.md) covers the build this follows.

## Site administrator and registration

I created the site administrator account through the browser at `https://192.168.40.39` and stored its credential in my password manager. The server had been holding that account open since the 2026-09-12 deployment: `NewAccounts` was `true` and the startup log said the next new account would be site administrator, so anything that could reach TCP 443 could have claimed it.

With the account created I set `NewAccounts` to `false` in `config.json` and restarted the container at 12:05 AM EDT. Line 42 now reads `"NewAccounts": false`. The restarted server logged `Pre-existing config found, not recreating`, `Leaving config as-is. Dynamic Configuration is off.`, and `MeshCentral HTTPS server running on 192.168.40.39:443`, and no longer logs the line offering site administrator to the next account. `curl` against the server returned HTTP 200 afterwards and the container read `Up 3 minutes` at 12:08 AM EDT.

The window between deployment and this change was about 20 minutes, reachable only from Personal-A, Secure Client VLAN 60, and the two identity hosts the firewall policy names. Nothing else registered: the account I created is the site administrator.

## HQ-WS001 network path

The [deployment record](Deployment%20-%202026-09-12.md) verified the firewall policy from `HQ-MGT01` and left `HQ-WS001` covered by the same rule but untested. `HQ-WS001` is VM 310 on `grey-server`, Windows 11 Pro 25H2 at `192.168.65.20`, and it is not enrolled in SSH Manager, so I tested it through the QEMU guest agent from `grey-server`:

```
qm guest exec 310 --timeout 45 -- powershell.exe -NoProfile -Command "Write-Output (hostname); Test-NetConnection -ComputerName 192.168.40.39 -Port 443 -InformationLevel Quiet"
```

Exit code 0, `out-data`:

```
HQ-WS001
True
```

`qm agent 310 ping` returned exit code 0 first. An earlier attempt at the same command failed because the PowerShell variables in it were expanded by the shell on `grey-server` before `qm` saw them, leaving `=hostname` as a command; I removed the variables rather than escaping them.

Both identity hosts the policy names are now demonstrated rather than inferred. `ObiPC` on Secure Client VLAN 60 is still untested and still needs no policy, because Secure Client and Personal-A are both in the `Internal` zone.

I retained no separate transcript for this work. The commands and their complete output are quoted above.

## Scope

I installed no agent and made no change on `HQ-WS001`. I am installing the agent on the test machine myself, outside this record, so nothing here establishes that a device enrolled or that a remote desktop session works. RustDesk `hbbs` and `hbbr` keep running on `docker-blue`.
