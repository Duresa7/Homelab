# AD Deployer Preparation

**Created:** 2026-09-12  
**Last updated:** 2026-09-25

I installed Action1 Deployer on `HQ-MGT01`, initially for workstation enrollment. I subsequently expanded the scope to every computer in `ad.alphasecunited.com`, including servers and domain controllers. The whole-domain scope is saved and verified in the console. `HQ-MGT01`, `HQ-WS001`, and `ObiPC` show Connected; domain-controller enrollment remains open.

## Preparation and observed results

I verified the five AD computer objects and their OU placement through SSH Manager. `HQ-WS001` and `OBIPC` are in `OU=Standard,OU=Workstations`; the controllers are in `Domain Controllers`, and `HQ-MGT01` is in `OU=Management,OU=Servers`. `HQ-MGT01` had no Action1 Deployer service during the check.

I initially prepared a GPO because Action1's documentation recommends GPO or Intune before Deployer. After choosing Deployer, I removed the unlinked `C-WKS-Action1-Agent` policy and `APP-Action1-Workstations` group. Readback confirmed both were absent. No package was assigned, the policy was never linked, and no endpoint received it.

I downloaded the organization-specific Deployer EXE from the organisation's Action1 HTTPS link into a private local staging directory. It was 8,703,672 bytes and had a Windows executable header. Authenticode verification on the destination host remains pending. I stored a new 40-character random password for the planned `ALPHASEC\svc-action1-deploy` service account in my credential vault. The AD account has not been created. I removed the local plaintext credential staging file after storage.

I created administrator/SYSTEM-only `C:\Windows\Temp\Action1-Setup` staging directories on `HQ-DC01` and `HQ-MGT01`. The installer transfer through SSH Manager's `ssh_upload` operation was refused with the message `a secret is being passed to tool ssh_upload`. The installer contains organization authentication material. I did not retry the transfer through another route, run the installer, grant account permissions, or change firewall rules.

The temporary MSI used while investigating GPO deployment was removed from `ObiPC`. Readback confirmed removal and that its existing `A1Agent` service remained running. There is no separately retained terminal transcript for these preparation steps.

## Remaining work

- Verify enrollment of `HQ-DC01` and `HQ-DC02`. Neither appeared in the latest endpoint readback. The Deployer log reports access denied for both controllers. The account lacks controller administrator membership; TCP 135, 139, and 445 connect to both controllers.
- Remove any remaining local installation staging when the enrollment work is complete.

## Resumed verification on 2026-09-12

I decided to complete the deployment, including the organization-specific installer transfer. The next SSH Manager `ssh_upload` attempt still returned the error `a secret is being passed to tool ssh_upload`. I verified afterward that `C:\Windows\Temp\Action1-Setup\deployer.exe` was absent on `HQ-MGT01` and no Action1 service existed there. The private local installer remains staged for this unfinished deployment. Retrying the same upload does not get past this refusal; the installer has to reach the host another way.

The directory readback still showed no `svc-action1-deploy` account, no Action1 group, and no Action1 GPO. Both workstations remain in `OU=Standard,OU=Workstations,DC=ad,DC=alphasecunited,DC=com`. `ObiPC`'s existing `A1Agent` service is running. I made no host configuration, account, policy, or firewall changes during these resumed checks.

I tested these TCP connections from `HQ-MGT01` through SSH Manager:

| Destination | TCP port | Result |
|---|---|---|
| `HQ-DC01.ad.alphasecunited.com` | 389 | Connected |
| `HQ-DC02.ad.alphasecunited.com` | 389 | Connected |
| `HQ-WS001.ad.alphasecunited.com` | 135 | Connected |
| `HQ-WS001.ad.alphasecunited.com` | 445 | Failed |
| `ObiPC.ad.alphasecunited.com` | 135 | Failed |
| `ObiPC.ad.alphasecunited.com` | 445 | Failed |
| `app.na-2.action1.com` | 443 | Connected |

These are connection probes, not authenticated LDAP, SMB, or deployment tests. Dynamic RPC, TCP 139, and the Deployer's actual backend connection remain unverified. On `ObiPC`, Windows Firewall is enabled and the built-in inbound SMB and remote-service-administration rules are disabled. That is one prerequisite to address; these results do not identify every filter along the routed path. Any deployment allow rules should be limited to `HQ-MGT01` at `192.168.65.12` and the intended workstations, with live UniFi inspection before changing routed policy.

My attempt to inspect `HQ-WS001` through `Invoke-Command` from the SSH session on `HQ-DC01` failed with Kerberos error `0x8009030e`: `A specified logon session does not exist. It may already have been terminated.` I did not alter WinRM authentication or TrustedHosts. The workstation firewall and agent state are therefore not verified by that attempt.

I added two read-only checks: [Test-DeployerInstaller.ps1](../../Scripts/Test-DeployerInstaller.ps1) verifies the transferred file's Authenticode status and publisher; [Test-DeployerNetwork.ps1](../../Scripts/Test-DeployerNetwork.ps1) repeats the connection probes from the intended host. Both parsed successfully in Windows PowerShell on `HQ-MGT01`. The network script ran with exit code 0 and reproduced the table above; its per-port results determine readiness, not its exit code. The installer check was syntax-checked only because the file has not reached the host. Neither script installs software or changes permissions. There is no separately retained terminal transcript for these resumed checks.

## Direct download, account, and network configuration

After the transfer refusal, I used the download link directly on `HQ-MGT01`. The HTTPS download succeeded there. The file is 8,703,672 bytes, version `6.0.664.1`, with a valid Action1 Corporation Authenticode signature and SHA-256 `4A202260C457CFEF51F52288A204C5CB0825E5BB011D19E2D7AC42BFDEAC2295`. The installer-transfer block is therefore resolved for this deployment; the earlier failed transfer remains part of the history.

I created `svc-action1-deploy` in `OU=Service Accounts,OU=Tier 2,OU=Admin`, enabled it, marked it not delegatable, and set its password not to expire automatically. I subsequently replaced the initially generated password with a generated 16-character password by my choice, updated AD and the credential vault, verified vault readback, and overwrote and removed the local plaintext rotation file. Credential transport used recipient-specific CMS encryption with temporary, nonexportable Windows certificate keys; secret values were not printed. The first CMS decryption attempt used a certificate-provider path where a certificate object was required; passing the certificate object corrected it before account creation.

`APP-Action1-LocalAdmins` contains only the service account. I nested that group in `ADM-T2-WorkstationAdmins`, reusing `C-WKS-LocalAdmins`, and added it separately to the local Administrators group on `HQ-MGT01`. This replaces the planned additional local-administrator GPO. Readback confirms the account has neither Domain Admin nor `ADM-T1-ServerAdmins` membership. Authenticated WinRM HTTPS sessions from `HQ-MGT01` to both workstations returned elevated administrator tokens for this account.

I created `C-WKS-Action1-Deployer-Network`, linked only to `OU=Standard,OU=Workstations`. It carries three inbound Windows Firewall rules, all restricted to the Domain profile and remote address `192.168.65.12`: SMB TCP 445/139 for System, RPC endpoint mapping for `svchost.exe`/`RpcSs`, and dynamic service RPC for `services.exe`. Both workstations applied the GPO with `gpupdate` exit code 0 and showed all three rules enabled with the intended source and profile. `HQ-WS001` was checked through the QEMU guest agent on VM 310 because its SSH session is not configured.

I added UniFi policy `Allow Action1 Deployer to Secure Client`, index 10001, for IPv4 TCP from `192.168.65.12` in `AlphaSec-Identity` to the Secure Client network on `135,139,445,49152-65535`. Logging and the response companion are enabled. The network selector covers future workstation addresses in VLAN 60; Windows Firewall and the workstation OU limit which domain computers accept the deployment connection. Other routed workstation networks would need their own approved path. The [living firewall inventory](../../../../Infrastructure/Network/UniFi/Configuration/firewall.md) records the rule.

After those changes, TCP 135, 139, and 445 connected from `HQ-MGT01` to both `HQ-WS001` and `ObiPC`. The initial failed probes above describe the pre-change state. Windows Firewall on `HQ-MGT01` already allows outbound traffic on all three profiles and has no enabled outbound block rules, so I added no outbound host rule. The running Deployer later showed an established TCP 443 connection; I did not open alternate cloud port 22543 in UniFi. The vendor requires 443 or 22543.

The authenticated Action1 Automations page showed `No entries`. I created no patching or reboot automation. The Windows installer needed an interactive console: launching it from short SSH commands did not complete installation, and an attempted persistent SSH session used incompatible shell wrappers. I closed that session. After signing in to the Windows desktop, I ran the installer with the dedicated service account and received a successful Action1 Cloud connection test. Live readback shows `A1Connector` (`Action1 Deployer`) Running, automatic startup, as `ALPHASEC\svc-action1-deploy`, from `C:\Program Files (x86)\Action1\Connector\action1_connector.exe`. Cloud wizard scope and agent enrollment still require verification. There is no separately retained transcript for these steps.

## Whole-domain scope and enrollment readback

I changed the scope from workstations to all domain computers, explicitly including both domain controllers. In the browser I selected `All computers in Active Directory domains or OUs`, entered `ad.alphasecunited.com`, disabled the existing named-computer exclusion, and saved both the form and its confirmation dialog. Reopening the editor confirmed domain mode selected, the full domain persisted, and every exclusion unchecked.

The discovery overview reports Action1 Deployer running on `HQ-MGT01.ad.alphasecunited.com`, AD domain `ad.alphasecunited.com`, and four agents. The endpoint table shows `HQ-MGT01`, `HQ-WS001`, and `ObiPC` Connected, plus the preexisting `win11-dev-hyper` record Disconnected. Neither domain controller appears yet; selecting the domain does not verify installation on those hosts. I changed no patching or reboot automation in this scope update. There is no separately retained browser capture for this step.

Before this scope update, I verified the Deployer service restarted successfully with its stored service credential, removed both temporary certificate private keys and remote staging directories, and removed the temporary setup tasks. Readback showed the service Running and no setup tasks remaining. There is no separately retained transcript for that cleanup.

## Controller deployment diagnosis

I checked why `HQ-DC01` and `HQ-DC02` remained absent after saving whole-domain discovery. Neither controller has an `A1Agent` service. From `HQ-MGT01`, TCP 135, 139, and 445 connect to both controllers. The latest Deployer log contains an access-denied entry for each controller, so discovery has reached them and installation is failing on authorization.

On `HQ-DC01`, recursive membership of the domain's built-in Administrators group does not include `svc-action1-deploy`. Its workstation-only permissions were sufficient for the initial targets but do not authorize installation on domain controllers. My first membership probe requested the computed `tokenGroups` property through a search that AD rejected with error 8480; the replacement recursive group-membership check succeeded. I changed no privileges during diagnosis. The console still shows the same four endpoint records, with neither controller present. Dynamic RPC connectivity was not tested. There is no separately retained terminal transcript for these diagnostic checks.

## Vendor reference

[Action1 Deployer documentation](https://www.action1.com/documentation/action1-deployer/) describes account permissions, connectivity requirements, installation, and the cloud deployment-scope wizard.
