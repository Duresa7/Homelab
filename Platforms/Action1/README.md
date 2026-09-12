# Action1

**Created:** 2026-09-12  
**Last updated:** 2026-09-12

Action1 is the cloud endpoint management plane for `ObiPC`. It handles software deployment, patching, and remote access for that machine. There is no self-hosted component: the service runs in Action1's cloud and each managed endpoint runs a local agent that polls it.

I deployed it on 2026-09-12 so that application installation on `ObiPC` goes through a console I control rather than through the person using the machine. That is the deployment half of the restriction work on that workstation; the execution half is AppLocker, which is tracked with the [Active Directory](../Active%20Directory/README.md) records that own `ObiPC`.

## Current State

| Item | Current value |
|---|---|
| Service | Action1 cloud, no on-premises component |
| Instance | `app.na-2.action1.com`, North America 2 |
| Organisation identifier | Withheld. It is embedded in the agent download URL and any holder of it can enrol an endpoint into this organisation |
| Managed endpoints | 1, `ObiPC`. Console-to-endpoint path proven 2026-09-12 by a console-initiated Chrome deployment the agent executed with result `OK` |
| Agent version | 6.0.664.1 |
| Agent install path | `C:\Windows\Action1\` |
| Agent service | `A1Agent`, display name `Action1 Agent`, `LocalSystem`, Automatic, Running |
| Content delivery | `us-cdn.action1.com`, resolving through `us-cdn-action1-com.b-cdn.net` |

## Managed endpoints

| Endpoint | OS | Agent | Enrolled | Notes |
|---|---|---|---|---|
| `ObiPC` | Windows 11 Pro 25H2, build 26200 | 6.0.664.1 | 2026-09-12 | Physical workstation, Secure Client VLAN 60, domain member in `OU=Standard,OU=Workstations` |

## Why this and not Intune

The [ObiPC MDM options](../Microsoft%20Intune/Documentation/ObiPC%20MDM%20Options%20-%202026-09-12.md) assessment on 2026-09-12 put Intune first for this machine, on the strength of the existing tenant. Action1 is what I actually deployed, for a narrower reason: I needed a way to install software on `ObiPC` for a restricted user on the same day, without scoping an automatic-enrollment GPO or re-checking licence assignment first.

This does not retire that assessment and does not close the co-management decision in the [Intune TODO](../Microsoft%20Intune/Documentation/TODO.md). `ObiPC` is still Microsoft Entra hybrid joined and still reads `MDM: None`. If Intune enrollment happens later, the overlap to settle is software deployment, because both products can install applications and configuring the same thing in two places is how a machine ends up in a state neither console describes.

## Agent behaviour worth knowing

The agent installs into `C:\Windows\Action1\` rather than `Program Files`, and runs as `LocalSystem`. Both matter for the AppLocker work on this machine:

- AppLocker's default rules allow everything under `%WINDIR%`, so the agent and anything it stages under `C:\Windows\Action1\` fall inside the allowlist without a rule written for them.
- AppLocker applies to code launched in a user's context by default, not to `SYSTEM`, so the agent is outside enforcement either way.

The consequence is that software Action1 deploys is trusted by the allowlist. That is the intended design here, and it is also the honest limit of it: the console is a way into this machine that AppLocker does not police, so its credentials deserve the same care as a domain administrator's.

## Records

- [ObiPC Agent Deployment - 2026-09-12](Documentation/Change%20Records/ObiPC%20Agent%20Deployment%20-%202026-09-12.md)
