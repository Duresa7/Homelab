# Deployer Health Check Blocked to ObiPC

**Created:** 2026-09-12  
**Last updated:** 2026-09-12  
**Investigated:** 2026-09-12

Action1 Deployer's routine agent health check against `ObiPC` fails on every cycle because UniFi's intrusion prevention blocks the remote service control call that carries it. The failure is real and recurring, not alert noise. No fix is applied yet.

## Symptom

A Discord message roughly once an hour, from the `UniFi - Intrusion detection blocked` rule: `ET RPC DCERPC SVCCTL - Remote Service Control Manager Access`, destination TCP 135, action `blocked`, source zone `AlphaSec-Identity`, destination zone `Internal`.

## Exact error

From the Deployer log on `HQ-MGT01`, `C:\Program Files (x86)\Action1\Connector\logs\`:

```
Unable to perform a routine health check for the agent on
ObiPC.ad.alphasecunited.com. The computer is not powered on or inaccessible
due to network or firewall issues. To diagnose, use the Services app
(services.msc) to connect to this computer remotely from the Action1 Deployer
computer.
```

In the same cycle `HQ-WS001` and `HQ-MGT01` both return `AUS check result: 0. Status: ok`.

## Findings

The Deployer health-checks every managed computer on a timer. The log ends each cycle with `Waiting with timeout 2734 sec`, about 46 minutes, which with the check itself produces the observed cadence.

UniFi returned 13 intrusion-prevention blocks from `192.168.65.12` in 24 hours. Every one targets `192.168.60.102` and nothing else. They carry two signature groups, `Remote Procedure Calls` on `DCE_ENDPOINT` at high risk, and `Malicious User Agents` at medium risk. After an initial cluster the gaps settle at 53, 53, 57, 55, and 54 minutes.

The Deployer log records `LastAttemptTime=2026/ 9/13 0: 7: 2` for `ObiPC`. UniFi's blocked flow for that cycle starts at `00:07:02.373` UTC, which is 8:07:02 PM Eastern. The two are the same event.

**`ObiPC` fails and the other two do not because of where they sit.** `HQ-WS001` at `192.168.65.20` and `HQ-MGT01` at `192.168.65.12` are both on IDENTITY-A, VLAN 65, so their health check never leaves the VLAN and the gateway never inspects it. `ObiPC` is on Secure Client, VLAN 60, so its check crosses the gateway and is inspected. Same operation, different path, different outcome.

The retry is self-sustaining. The log shows `MarkedForInstall=true` for `ObiPC`, because the Deployer cannot confirm the agent over RPC, so it re-attempts every cycle and is blocked every cycle.

`ObiPC` remains managed. Its agent polls the Action1 cloud over TCP 443 independently of the Deployer, and the console shows it Connected. What is broken is the Deployer's LAN-side health check, which duplicates information the cloud connection already carries.

## Correction to the earlier record

The [RPC alert investigation](../../../../Security/Incidents/UniFi/Action1%20Remote%20Service%20Control%20Alert%20-%202026-09-12.md) concluded that the remote service operations "finished successfully despite the blocked flow records" and found "no demonstrated Action1 outage from these blocks." That holds for the two install-time flows it examined. It does not hold for the routine health check, which fails every cycle. That record closed the investigation of its own two events and said future events matching the signature would need their own evidence. This record is that evidence.

## Fix identified, not applied

Excluding `ObiPC` from the Deployer's scope stops the call being made, which removes the blocked flow, the failing health check, and the hourly alert without changing any detection. `ObiPC` keeps its agent and its cloud connection.

**This has to be done in the Action1 console, not in the local configuration file.** `a1config.json` on `HQ-MGT01` carries the scope fields `exclude_dc`, `exclude_srv`, `exclude_wks`, `exclude_computers_list`, and `exclude_computers_list_enabled`, all currently `0` or empty. The file was last written at 2:03:53 PM on 2026-09-12, after the connector process started at 1:50:15 PM, so something other than the local service writes it. Editing it directly risks the console overwriting the change and leaves the console describing a scope the host does not implement, which is the drift the [platform record](../../README.md) warns about for exactly this reason.

I considered and rejected opening the IPS path so the health check succeeds. Remote service control from a management server to a workstation is a standard lateral movement technique, and this is the one path where the inspection is worth keeping.

## Also observed

`ObiPC` stopped answering ICMP and TCP 22, 135, 445, and 3389 at about 9:51 PM, while UniFi still reported it wired with `last_seen` one second earlier. Link up with no host response is consistent with modern standby. It would also explain the `EHOSTUNREACH` on TCP 22 recorded during the [RDP enablement](../../../Active%20Directory/Documentation/Change%20Records/Domain%20Machine%20RDP%20Enablement%20-%202026-09-12.md), and it means the RDP access enabled that day is unavailable while the machine sleeps. I could not read its power configuration because it was unreachable. This is a hypothesis, not a verified finding.

Every cycle in the same log also records `Agent deployment failed on HQ-DC01.ad.alphasecunited.com. Access is denied.(5)` and the same for `HQ-DC02`. That is the open domain-controller enrollment item in the [deployment record](../Change%20Records/AD%20Deployer%20Preparation%20-%202026-09-12.md) and the root [TODO](../../../../TODO.md), not a new problem.

## Verification still owed

Nothing is fixed yet, so nothing is verified. Once the console exclusion is saved, the checks are: the Deployer log stops naming `ObiPC` in its health-check cycle, UniFi returns no new intrusion-prevention block from `192.168.65.12` to `192.168.60.102` over a period longer than one cycle, and the console still shows `ObiPC` Connected.
