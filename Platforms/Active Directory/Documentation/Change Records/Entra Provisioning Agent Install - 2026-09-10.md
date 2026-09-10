# Entra Provisioning Agent Install

**Created:** 2026-09-10  
**Last updated:** 2026-09-10

I installed the Microsoft Entra provisioning agent, version 1.1.2334.0, on `HQ-MGT01` on 2026-09-10 and registered it to the tenant. The agent is the on-premises half of Entra Cloud Sync. The interactive parts, the download and the configuration wizard, happened on the machine's Proxmox console under my Microsoft 365 account, because they need a Global Admin sign-in that no automation channel holds. Everything else, the prerequisite checks, the cleanup, and the verification, was done from the server side through the QEMU guest agent and SSH to the domain controllers.

## Prerequisites as found

Read on `HQ-MGT01` before the download: domain member of `ad.alphasecunited.com`, .NET Framework 4.8 (`Release` 533509), TLS 1.2 enabled for .NET clients, outbound 443 open to `login.microsoftonline.com`, `graph.microsoft.com` and `aadcdn.msftauth.net`, 78.7 GB free on `C:`, Edge present, no agent installed. On `HQ-DC01` the KDS root key existed, effective 2026-09-09 4:43 PM, which is what lets the wizard create a group managed service account. Nothing needed fixing.

## Licensing, corrected

Before the install I checked the licensing position against Microsoft Learn, because an earlier plan of mine said to turn off security defaults and move to Conditional Access. That was wrong for this tenant. Every user other than my own account is on Microsoft 365 Business Basic, which does not include Entra ID P1. Conditional Access and password writeback both require P1 per user. Security defaults are free and apply to every tenant.

So security defaults stay on. Microsoft also enforces multifactor authentication on every sign-in to the Entra admin center, the Microsoft 365 admin center and the Azure portal regardless of tenant settings, so the two administrative accounts registered it: `BG-admin` with the Authenticator app and a phone number, `DK-user` with the Authenticator app and a passkey. Microsoft's documentation states the Cloud Sync service account is exempt from that enforcement. A password reset made in Microsoft 365 will not write back to the directory for a Basic user; it flows only from the directory upward. That is the position until a user holds P1.

## The install

Downloaded from the Entra admin center under Entra ID, Entra Connect, Cloud sync, Agents. The installer ran cleanly and registered two products, `Microsoft Azure AD Connect Provisioning Agent` and `Microsoft Entra Provisioning Agent Package`, both 1.1.2334.0.

It created one Start menu shortcut, and it was the wrong one: `Microsoft ECMA2Host Configuration Wizard`, which configures on-premises application connectors and has nothing to do with Cloud Sync. No shortcut was created for `AADConnectProvisioningAgentWizard.exe`, which sits beside it in `C:\Program Files\Microsoft Azure AD Connect Provisioning Agent\`. I created a shortcut to it in the Start menu and on the public desktop, both named `Microsoft Entra Provisioning Agent Configuration Wizard`, so the right wizard can be found without a path.

## Two detours

**Certificates from the wrong wizard.** Opening the ECMA2Host wizard offers to generate a certificate, and four were generated between 12:33 PM and 12:35 PM: self-signed, subject and issuer `CN=HQ-MGT01`, valid to 2031-09-10, each placed in both the machine's Personal store and its Trusted Root store. A self-signed certificate in Trusted Root is not something this server should carry. I deleted all four private keys through the CNG key handle and removed the certificates from both stores through `X509Store.Remove`. `Remove-Item -DeleteKey` is not available in Windows PowerShell 5.1's certificate provider, which is why the first attempt removed nothing. Read back afterwards: no `CN=HQ-MGT01` self-signed certificate in Personal, Trusted Root or Intermediate, and the Personal store empty. An attempted uninstall from Programs and Features produced a fatal-error dialog; the install was intact and the uninstall was not needed.

**The wizard rejects a Protected Users member.** The Configure Service Account page asks for a domain administrator once, to create the gMSA. It rejected `DK-t0` with *The user name or password is incorrect*. The password was correct. That account is in `Protected Users`, which blocks NTLM and plain LDAP binds, and the wizard's credential check depends on one of those. Five attempts tripped `PSO-Admins`, whose lockout threshold is 5 with a 30 minute duration, so the account was also locked.

I unlocked it, then proved the password with a method Protected Users allows: an interactive logon on `HQ-DC01` through `Start-Process -Credential`, which uses Kerberos. The stored password logged on; the same password with one character appended was refused. The value came from the password manager through standard input and never appeared in a command, a log, or this record. I then confirmed the two vault entries, the shared template and the account's own item, hold the same value, comparing in memory.

The wizard step was completed with the built-in domain `Administrator`, which is not in `Protected Users`. Afterwards `Administrator` showed zero bad password attempts and `DK-t0` showed zero and unlocked. The credential is used once and the wizard does not keep it.

A related observation: neither controller audits credential-validation failures. `auditpol` shows `Credential Validation` set to `Success` only, so the failed attempts produced no 4776 events and the lockout had to be read from the account itself. Turning on failure auditing there is worth doing.

## Result

Read from `HQ-MGT01` through the guest agent and from `HQ-DC01` after the wizard finished:

| Check | Result |
|---|---|
| Service `AADConnectProvisioningAgent` | Running, Automatic |
| Runs as | `ad.alphasecunited.com\pGMSA_e6620264$` |
| gMSA object | `CN=provAgentgMSA,CN=Managed Service Accounts`, created 1:35:16 PM, enabled |
| Allowed to retrieve its password | `HQ-MGT01` only |
| Rights on the domain partition | `Replicating Directory Changes`, `Replicating Directory Changes All`, `Reset Password`, plus create, delete and write on user and group objects |
| Agent certificate | subject `CN=58cab82a-29ec-4085-b2b8-bccb6b00d5af`, issued by `HISConnectorRegistrationCA.his.msappproxy.net`, expires 2027-01-17 |
| Agent log | `Agent successfully registered with AAD`, 1:35:38 PM, `CredentialType: UseGMSA` |
| Connections | four established sessions to Microsoft on 443, one to `HQ-DC02` on 389 |

The certificate subject is the tenant identifier, which this platform already publishes as the service connection point's `azureADId`. The agent's connector identifier is a relay identifier and is withheld.

The two replication rights are what password hash sync requires, and the reset right is what password writeback would use if a user were licensed for it.

## Open

1. ~~Create the AD to Microsoft Entra ID configuration in Cloud sync.~~ Done 2026-09-10, first cycle at 2:20 PM; see [Cloud Sync Configuration and First Cycle](Cloud%20Sync%20Configuration%20and%20First%20Cycle%20-%202026-09-10.md).
2. Enable device sync in that configuration, provision `HQ-WS001` on demand, and confirm it reports as hybrid joined.
3. Assign Business Basic to `IK-user`, `AH-user` and `testuser` once they appear in the tenant.
4. Set `Credential Validation` auditing to include failures on both controllers.

Password writeback is not configured and will not be until a user in scope holds P1. Nothing in this record changes the temporary shared-password arrangement described in [Shared Test Password and Admin Policy Relaxation](Shared%20Test%20Password%20and%20Admin%20Policy%20Relaxation%20-%202026-09-10.md).
