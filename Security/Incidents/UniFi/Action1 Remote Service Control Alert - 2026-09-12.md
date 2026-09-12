# Action1 Remote Service Control Alert

**Created:** 2026-09-12  
**Last updated:** 2026-09-12

## Disposition

I investigated the 2:47 PM Discord notification for blocked RPC traffic from `HQ-MGT01`. I classified the two observed flow records as authorized Action1 Deployer activity based on matching timestamps, target, deployment logs, and the target's service-install event. I found no demonstrated Action1 outage from these blocks. I left IPS and alert delivery unchanged. This closes the investigation of these events, not future events matching the same signature.

## Alert and affected assets

The supplied Splunk / UniFi `unifi_insights` notification reported `ET RPC DCERPC SVCCTL - Remote Service Control Manager Access`, destination TCP 135, action `blocked`, count 2, source zone `AlphaSec-Identity`, and destination zone `Internal`. It did not identify the destination host. The live UniFi flow query resolved it to `ObiPC`, `192.168.60.102`, in Secure Client VLAN 60. The source is `HQ-MGT01`, `192.168.65.12`, in IDENTITY-A VLAN 65.

The full signature text and destination port above come from the supplied notification. The MCP's flow response independently confirms `DCE_ENDPOINT`, high risk, `EMERGING_RPC`, and an `INTRUSION_PREVENTION` policy named `Remote Procedure Calls`; it does not expose the numeric signature ID or full signature text.

## Timeline and findings

All times are Eastern on 2026-09-12.

| Time | Observation |
|---|---|
| 2:03:53 PM | Action1 Deployer logged `ManagedAgent::Install - ObiPC.ad.alphasecunited.com` and `CreateAgentUpdateService`. UniFi's first blocked flow began at 2:03:53.853 PM. |
| 2:03:54 PM | ObiPC System event 7045 recorded `Action1 Agent Update Service`, image `C:\Windows\Action1\action1_update.exe`. The Deployer logged `AUS check result: 0. Status: ok`. |
| 2:36:07 PM | Action1 checked ObiPC again and logged `AUS check result: 0. Status: ok`. UniFi's second blocked flow began at 2:36:07.535 PM. |
| 2:47 PM | The supplied Discord message reported the blocked RPC activity. Notification time is later than the underlying flow start. |
| 2:50–2:54 PM | I queried UniFi and both Windows hosts, checked the Deployer executable signature, and verified Arc and controller enrollment state. |

Each of the two UniFi flow records carries count 2. They are two aggregated records, not proof of two compromised hosts or a complete packet count. Their end times were 2:08:53.978 PM and 2:41:08.075 PM. I did not capture a packet trace or process-to-socket history; attribution rests on the matching application and endpoint evidence.

`A1Connector` was Running on HQ-MGT01 as process 8024, `action1_connector.exe`. Authenticode returned Valid (numeric status 0) with publisher Action1 Corporation. ObiPC's `A1Agent` was Running with Automatic startup during the final check. The remote service operations finished successfully despite the blocked flow records. The transport or retry that allowed completion was not captured, so I did not claim a specific fallback mechanism.

The existing `Allow Action1 Deployer to Secure Client` firewall policy remains enabled, IPv4 TCP, source `192.168.65.12`, destination Secure Client network, ports `135,139,445,49152-65535`, with logging and response handling. An ordinary firewall allow does not prevent IPS from inspecting and blocking matching traffic.

## Relationship to Azure Arc and controller enrollment

Arc on HQ-MGT01 independently reported Connected, agent `1.67.03504.3207`, resource group `rg-homelab-arc`, region `eastus`, and cloud `AzureCloud`. The observed RPC traffic is associated with Action1's workstation operations, not evidence of Arc enrolling the domain.

HQ-DC01 and HQ-DC02 have neither `A1Agent` nor `himds`. Action1's Deployer log separately records `Access is denied.(5)` for both controllers. That unfinished enrollment is tracked in the [Action1 deployment record](../../../Platforms/Action1/Documentation/Change%20Records/AD%20Deployer%20Preparation%20-%202026-09-12.md). I did not grant the deployment account additional privileges during this investigation.

## Action and validation

I made no runtime changes. I did not suppress the signature, exempt HQ-MGT01 from IPS, change the firewall, stop the Deployer, or silence Splunk notifications. The observed Action1 operations already returned success, so reproducing them by creating another remote service would add a mutation without establishing a repair need. I used the existing flow and application logs as a retrospective correlation check instead of an active failure reproduction or regression test.

The [retained readback](Evidence/Action1%20RPC%20Alert%20-%202026-09-12/Readback.json) contains the scoped UniFi query and results, the firewall readback, exact SSH commands, complete returned stdout/stderr, and exit codes. All retained SSH checks returned exit code 0. Initial discovery and service-list probes have no separately retained transcript. The final ObiPC readback reports service status 4 (Running), startup type 2 (Automatic), and the service-install event that corroborates the Deployer log.

These alerts can recur while Action1 performs the same operation. A future failed deployment needs its own timestamp and endpoint evidence before any narrowly scoped IPS exception is considered. This investigation is not a repository-wide or host-wide compromise assessment.

[Action1's documentation](https://www.action1.com/documentation/action1-deployer/) lists RPC 135, SMB 139/445, and dynamic RPC as Deployer requirements. [Ubiquiti's IDS/IPS documentation](https://help.ui.com/hc/en-us/articles/360006893234-UniFi-Gateway-Intrusion-Detection-and-Prevention-IDS-IPS) describes signature-triggered blocking and suppression.
