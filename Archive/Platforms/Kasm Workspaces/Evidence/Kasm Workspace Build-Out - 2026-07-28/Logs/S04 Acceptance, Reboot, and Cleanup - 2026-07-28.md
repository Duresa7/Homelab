# S04 Acceptance, Reboot, and Cleanup

**Created:** 2026-07-28  
**Last updated:** 2026-07-28

**Capture time:** 2026-07-28 EDT  
**Target:** `kasm-01`, four live Kasm sessions, and UniFi gateway enforcement  
**Mechanism:** Kasm API, SSH Manager MCP, Docker inspection, and in-session shell probes

## Real-session acceptance

I launched one real workspace in each lane as `alpha`:

| Workspace | Lane and address | Egress result | Persistent profile |
| --- | --- | --- | --- |
| Terminal - Trusted 75 | `lab75`, `.208` | Ordinary WAN matched the Kasm host | `/var/lib/kasm-profiles/terminal-trusted` mounted |
| Terminal - Browser 74 | `lab74`, `.208` | Proton exit `185.98.168.20` | None |
| REMnux - Target 77 | `lab77`, `.208` | DNS and direct TCP egress blocked | None |
| Debian - Review 79 | `lab79`, `.208` | DNS and direct TCP egress blocked | None |

I did not retain the ordinary WAN address. The lane 75 test compared it in memory with the host result and recorded only that they matched.

Every lane failed TCP probes to all nine protected destinations:

```text
192.168.78.10:443
192.168.80.10:22
192.168.70.10:8006
192.168.70.11:8006
192.168.71.10:22
192.168.72.2:443
192.168.73.2:9090
192.168.1.1:443
192.168.10.1:443
```

While the lane 75 session ran, I kept live TCP 6901 listeners in lane 74, 77, and 79 sessions. Lane 75 could not connect to any of them. This proved the cross-lane policies against active endpoints, not closed ports.

The self-signed Kasm certificate prevented a retained automated browser capture of the toolbar, and browser safety policy did not permit bypassing the warning. I verified the authoritative group settings directly from Kasm's database and used those settings during real `alpha` session launches. I retained no visual toolbar artifact.

## Reboot and recovery

`qm reboot 122` timed out while VM 122 completed shutdown instead of restarting. I verified the VM was stopped, then ran `qm start 122`. The guest boot ID changed from `f43c...` to `b74d...`.

After startup, all four shims returned at `.201/32`, all four Docker macvlan networks returned with their original subnets and ranges, and the Kasm API health endpoint returned `{"ok":true}` after about 42 seconds of container startup. I launched a fresh `Debian - Target 77` session after reboot, verified `lab77` at `.208`, and destroyed it.

## Snapshots and residue

I created final snapshot `baseline-tiles-2026-07-28`. A later review found that Kasm had widened the exercised `terminal-trusted` directory to 0777. I restored all six approved profile directories to 0750, deleted only that final snapshot, and recreated it from the corrected current state. The snapshot list contained both the pre-change and replacement final snapshots. `ssd-lvm2` then reported 52.22 percent data use and 2.39 percent metadata use.

I destroyed every acceptance session. Kasm reported zero `alpha` sessions, `/tmp` held no `kasm-*` file, and the temporary health response file was removed.
