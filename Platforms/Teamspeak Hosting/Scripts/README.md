# TeamSpeak Scripts

**Created:** 2026-07-28  
**Last updated:** 2026-07-29

Operational helpers for the three TeamSpeak instances on `alpha-prod-01`. No script contains a credential, an address, or a domain: every value comes from an argument or the environment. The rotation script stays out of git because it invokes my credential store's CLI directly, so the table below names it without linking it.

| Script | Purpose |
|---|---|
| [ts3-probe.py](ts3-probe.py) | Send a real TS3 Init1 handshake to a public or local voice endpoint and report whether the service answered |
| `rotate-serverquery-password.ps1` | Rotate one instance's ServerQuery password and store the replacement without displaying it. Kept on local disk only, because it calls my credential store's CLI by name |
| [migration-scripts-job/](migration-scripts-job/) | Channel export and import used during the server migration |

## Probing

`ts3-probe.py` is the same check the [monitoring collector](../Source/teamspeak-monitor/) runs, in a form I can point at anything by hand. A pass requires a reply whose MAC is `TS3INIT1`, so it proves the voice service answered rather than a port being open. `blackbox_exporter` cannot do this at all, because it has no UDP prober.

Compare the two paths to place a fault:

```bash
./ts3-probe.py --public ts01 ts02 ts03 --domain <YOUR_BASE_DOMAIN>
./ts3-probe.py --local 9987 9988 9989
```

Public failing while local passes means the Playit tunnel or DNS broke. Both failing means the TeamSpeak server did. Exit status is 0 only when every probed endpoint answered.

The public probe needs outbound UDP to the Playit relays, which `monitor-01` deliberately doesn't have.

## Rotating a ServerQuery password

Each instance keeps its own `serveradmin` account, so rotating one leaves the others alone. The server generates the replacement; it can't be chosen. The script proves the new password authenticates before storing it, reads it back, and then confirms the old one is rejected.

```powershell
./rotate-serverquery-password.ps1 -Port 10013 -TargetHost 192.168.80.118 `
    -LoginRef '<login reference>' -PasswordRef '<password reference>'
```

Run it from a host in that instance's `query_ip_allowlist`.
