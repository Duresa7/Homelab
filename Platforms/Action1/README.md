# Action1

**Created:** 2026-09-12  
**Last updated:** 2026-09-19

Action1 is the cloud endpoint management plane for `ObiPC`. It handles software deployment, patching, and remote access for that machine. Each managed endpoint runs a local agent that polls the cloud. Since 2026-09-12, `HQ-MGT01` also runs Action1 Deployer for automatic enrollment across `ad.alphasecunited.com`, including servers and domain controllers. The whole-domain scope is saved; domain-controller installation is blocked by access denied because the Deployer account lacks administrator access there.

I deployed it on 2026-09-12 so that application installation on `ObiPC` goes through a console I control rather than through the person using the machine. That is the deployment half of the restriction work on that workstation; the execution half is AppLocker, which is tracked with the [Active Directory](../Active%20Directory/README.md) records that own `ObiPC`.

## Current State

| Item | Current value |
|---|---|
| Service | Action1 cloud with Action1 Deployer on `HQ-MGT01` |
| Deployer | `A1Connector`, automatic startup, Running as `ALPHASEC\svc-action1-deploy`; version 6.0.664.1, verified 2026-09-12 |
| Deployer path | `C:\Program Files (x86)\Action1\Connector\action1_connector.exe` |
| Deployer scope | All computers in `ad.alphasecunited.com`; domain-controller, server, and workstation class exclusions disabled. `ObiPC.ad.alphasecunited.com` was on the named-computer exclusion list from 11:43 PM on 2026-09-12 until 6:58 PM on 2026-09-18, when I removed it so the Deployer would reinstall the agent after the rebuild, which it did in five seconds; whether the exclusion goes back on is open, see [Deployer Health Check Blocked to ObiPC](Documentation/Troubleshooting/Deployer%20Health%20Check%20Blocked%20to%20ObiPC%20-%202026-09-12.md) |
| Instance | `app.na-2.action1.com`, North America 2 |
| Organisation identifier | Withheld. It is embedded in the agent download URL and any holder of it can enrol an endpoint into this organisation |
| Managed endpoints | Four console records: `HQ-MGT01`, `HQ-WS001`, and `ObiPC` Connected; preexisting `win11-dev-hyper` Disconnected. Neither domain controller appeared in the 2026-09-12 readback |
| Agent version | 6.0.664.1 |
| Agent install path | `C:\Windows\Action1\` |
| Agent service | `A1Agent`, display name `Action1 Agent`, `LocalSystem`, Automatic, Running |
| Content delivery | `us-cdn.action1.com`, resolving through `us-cdn-action1-com.b-cdn.net` |

## Managed endpoints

| Endpoint | OS | Agent | Enrolled | Notes |
|---|---|---|---|---|
| `ObiPC` | Windows 11 Pro 25H2, build 26200 | 6.0.664.1 | 2026-09-12 | Physical workstation, Secure Client VLAN 60, domain member in `OU=Standard,OU=Workstations`. Lost in the 2026-09-18 operating system reinstall and pushed back by the Deployer at 6:58 PM the same day, same version, see [ObiPC Rebuild and Rejoin - 2026-09-18](../Active%20Directory/Documentation/Change%20Records/ObiPC%20Rebuild%20and%20Rejoin%20-%202026-09-18.md) |

The 2026-09-12 console readback also showed `HQ-MGT01` (Windows Server 2025) and `HQ-WS001` (Windows 11 25H2) Connected. Their agent versions were not captured in that readback. The preexisting `win11-dev-hyper` record was Disconnected.

## Why this and not Intune

The [ObiPC MDM options](../Microsoft%20Intune/Documentation/ObiPC%20MDM%20Options%20-%202026-09-12.md) assessment on 2026-09-12 put Intune first for this machine, on the strength of the existing tenant. Action1 is what I actually deployed, for a narrower reason: I needed a way to install software on `ObiPC` for a restricted user on the same day, without scoping an automatic-enrollment GPO or re-checking licence assignment first.

This does not retire that assessment and does not close the co-management decision in the [Intune TODO](../Microsoft%20Intune/Documentation/TODO.md). `ObiPC` is still Microsoft Entra hybrid joined and still reads `MDM: None`. If Intune enrollment happens later, the overlap to settle is software deployment, because both products can install applications and configuring the same thing in two places is how a machine ends up in a state neither console describes.

## Self-service portal

Action1 announced a Self-Service App Portal on 2025-10-30 and, as of 2026-09-19, still lists it on the "Upcoming release" tab of its roadmap; no service release through May 2026 mentions it. Until it ships I built my own, [App Portal](../App%20Portal/README.md), with its source in the separate public repository [Duresa7/app-portal](https://github.com/Duresa7/app-portal). Its server runs on `docker-main` and turns a device's request into a `deploy_package` automation on that one endpoint; a Windows client installed to Program Files shows the catalog, progress, and history. The client fits the `ObiPC` AppLocker allowlist because it lives in Program Files and never runs an installer itself: the Action1 agent does, as `LocalSystem`. The API credential it uses was created here under Configuration, API Credentials, on 2026-09-19 and lives in the vault with the organisation identifier; the server has talked to the tenant with it since that afternoon, and every catalog package resolves. Nothing is enrolled yet, so no install has run through it. One thing the first live call taught me about this API: a lookup for a package identifier it does not know answers HTTP 200 with an empty body, not 404.

## Agent behaviour worth knowing

The agent installs into `C:\Windows\Action1\` rather than `Program Files`, and runs as `LocalSystem`. Both matter for the AppLocker work on this machine:

- AppLocker's default rules allow everything under `%WINDIR%`, so the agent and anything it stages under `C:\Windows\Action1\` fall inside the allowlist without a rule written for them.
- AppLocker applies to code launched in a user's context by default, not to `SYSTEM`, so the agent is outside enforcement either way.

The consequence is that software Action1 deploys is trusted by the allowlist. That is the intended design here, and it is also the honest limit of it: the console is a way into this machine that AppLocker does not police, so its credentials deserve the same care as a domain administrator's.

## Records

- [Deployer Health Check Blocked to ObiPC - 2026-09-12](Documentation/Troubleshooting/Deployer%20Health%20Check%20Blocked%20to%20ObiPC%20-%202026-09-12.md): the Deployer's routine agent health check against `ObiPC` fails every cycle, because the call crosses the VLAN 65 to VLAN 60 boundary and UniFi intrusion prevention blocks it. Corrects the RPC alert investigation's finding of no demonstrated outage. Fix identified, not yet applied.
- [RPC alert investigation - 2026-09-12](../../Security/Incidents/UniFi/Action1%20Remote%20Service%20Control%20Alert%20-%202026-09-12.md): UniFi blocked RPC flows to ObiPC during successful Deployer checks. I correlated both timestamps with Action1 logs, verified the running agent, and left IPS enabled.
- [AD Deployer Preparation - 2026-09-12](Documentation/Change%20Records/AD%20Deployer%20Preparation%20-%202026-09-12.md): Deployer installed on `HQ-MGT01` after a direct HTTPS download. Dedicated account and workstation firewall policy are applied; whole-domain scope is saved, three endpoints show Connected, and domain-controller enrollment verification remains open.
- [ObiPC Agent Deployment - 2026-09-12](Documentation/Change%20Records/ObiPC%20Agent%20Deployment%20-%202026-09-12.md)
