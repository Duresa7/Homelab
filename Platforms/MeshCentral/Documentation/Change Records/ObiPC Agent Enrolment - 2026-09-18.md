# ObiPC Agent Enrolment

**Created:** 2026-09-18  
**Last updated:** 2026-09-18

I enrolled `ObiPC` in MeshCentral on 2026-09-18, the same evening as its [rebuild and rejoin](../../../Active%20Directory/Documentation/Change%20Records/ObiPC%20Rebuild%20and%20Rejoin%20-%202026-09-18.md). It is the first agent on Secure Client, VLAN 60, and the first end-user machine in the pilot; the earlier three are a management server, my own gaming PC, and a development VM.

## Installation type

The console offers three installation types when it builds the agent. I chose **Background & Interactive**, which installs the agent as a Windows service running as SYSTEM with desktop interaction, so the machine is reachable at the sign-in screen, through Ctrl+Alt+Delete and UAC prompts, and after a reboot with nobody signed in. *Background only* gives the same service without remote desktop. *Interactive only* runs as a process inside the signed-in user's session with that user's rights and nothing at the sign-in screen, which on this machine would also mean running from a profile path the AppLocker allowlist blocks. For a machine I manage for someone else, the first is the only one that fits.

I installed it at the machine as `local-obipc` and let it restart. The install itself was not captured over SSH, so the record below is the readback.

## Readback

From `ObiPC`, over SSH, after the restart at 7:10 PM:

| Check | Result |
|---|---|
| Service | `Mesh Agent`, running, automatic, `LocalSystem`, `C:\Program Files\Mesh Agent\MeshAgent.exe` |
| Install event | Service Control Manager 7045 at 7:08:41 PM, *A service was installed*, followed by 7030, the standing note that Windows no longer allows interactive services; MeshCentral handles the desktop through its own session helper, so this is expected for this installation type |
| Process | one `MeshAgent` process, session 0, started 7:10:40 PM, twelve seconds after boot, and no service restart events since |
| Device group | `End User Devices`, from the `.msh` beside the binary |
| Binary | 3,489,744 bytes, agent build dated 2026-02-15, signed with the server's own agent certificate, which no public authority chains to and Windows reports as unknown; that is how MeshCentral signs every agent it serves |
| Server connection | one established TCP session from the agent process to `192.168.85.2:443`, which is what `mesh.alphasecunited.com` resolves to, Nginx Proxy Manager on `docker-network` |

Under `Program Files` is the right place for it: the AppLocker baseline on this machine allows `%PROGRAMFILES%` for everyone, so the agent runs for every account without a rule change.

From the server on `docker-blue`, read out of the NeDB files inside the container:

| Check | Result |
|---|---|
| Event | 7:08:49 PM, *Added device ObiPC to device group End User Devices*, then 7:08:50 PM an OS description update |
| Node record | name `ObiPC`, host `192.168.60.102`, `Microsoft Windows 11 Pro - 25H2/26200`, agent type 4, which is Windows 64-bit, running as root |
| Devices in the database | `DuresaGamingPC`, `HQ-MGT01`, `ObiPC`, `dkadi-mb-air3`, `dkadi-surface-pro`, `ubuntu-dev` |

Eight seconds from the service being installed to the server holding the device, across a VLAN boundary with no firewall change: Secure Client and Personal-A are both in the `Internal` zone, the same reasoning as for `DuresaGamingPC`, and now demonstrated on VLAN 60 rather than inferred. The root [TODO](../../../../TODO.md) had carried that path as untested since 2026-09-12.

I did not look for the session on the proxy host: `ss` on `docker-network` sees nothing, because the connection terminates inside the Nginx Proxy Manager container's own network namespace. The agent-side established session and the server-side event are the two ends that matter.

Two devices I had not recorded before appear in the database, `dkadi-mb-air3` and `dkadi-surface-pro`; they were enrolled outside any record and the README's device table now lists them as such.

## Open

Same four tests as the rest of the pilot: console access while signed out, Ctrl+Alt+Delete, UAC elevation, and reconnect after reboot. `ObiPC` is the machine those tests should run on, because it is the one with a restricted user whose session an administrator would need to reach. No snapshot and no backup were taken.
