# ObiPC MDM Options

**Created:** 2026-09-12  
**Last updated:** 2026-09-12

I checked ObiPC and both domain controllers through SSH Manager and compared Windows MDM options against vendor documentation on 2026-09-12. Intune is my recommended next step because the existing tenant already manages my Apple devices and the recorded Business Premium assignment covers DK-user. This is an assessment, not an enrollment decision. I changed no host, Group Policy, or tenant configuration.

## Live checks

| Check | Observed result |
|---|---|
| Domain | `ad.alphasecunited.com`, NetBIOS `ALPHASEC`; HQ-DC01 is the PDC |
| Controllers | HQ-DC01, `192.168.65.10`, and HQ-DC02, `192.168.65.11`; both Windows Server 2025 Standard and global catalogs |
| Services | NTDS, DNS, and Netlogon running on both controllers |
| Replication | Direct `Get-ADReplicationPartnerMetadata` queries on each controller returned last result 0 and zero consecutive failures for the partner |
| ObiPC OS | `Win32_OperatingSystem` reports Microsoft Windows 11 Business, build 26200; the installation record calls the original edition Pro |
| Domain connection | `PartOfDomain: true`, `Test-ComputerSecureChannel: true` |
| Hybrid join | `AzureAdJoined: YES`, `DomainJoined: YES`, `DeviceAuthStatus: SUCCESS`, `TpmProtected: YES` |
| Placement | `CN=OBIPC,OU=Standard,OU=Workstations,DC=ad,DC=alphasecunited,DC=com` |
| Applied policies | Local Group Policy, Default Domain Policy, C-WKS-LocalAdmins, C-CMP-LAPS |
| LAPS | Encrypted password attribute populated, expiry 10/11/2026 at 4:06:31 AM Eastern; no password retrieved |
| MDM | No OMA-DM account registry entries; no Intune Management Extension service; automatic enrollment policy values absent |

The first `repadmin /replsummary` from HQ-DC01 reported 0 failures across its five inbound naming contexts but operational error 110 when retrieving HQ-DC02's summary. I followed up directly on each controller; both local partner queries succeeded. This establishes the returned partner state, not the cause of the cross-controller query error or a complete AD health audit.

`MdmUrl` was blank in the local SSH account's `dsregcmd` output. That account is not the licensed interactive domain user, so I do not infer the tenant's MDM user scope or the domain user's PRT state from it. The missing enrollment registry entries and policy values are separate checks.

I retain summarized observations here, not a terminal transcript. Commands completed with exit code 0 and empty stderr, including the first replication command whose stdout contained the operational error. Tenant licences, Apple enrollments, and restrictions are from the [2026-09-11 tenant readback](../Evidence/MacBook%20Air%20M3%20Enrollment%20-%202026-09-11/Logs/S01%20Tenant%20Readiness%20Readback%20-%202026-09-11.md) and [platform record](../README.md); I did not re-query the tenant today.

## Options

| Option | Fit for ObiPC | Cost and deployment |
|---|---|---|
| Microsoft Intune | My first choice for the existing AD and Entra setup. Adds application deployment, Windows update configuration, and device settings while retaining domain sign-in. | Cloud service; Business Premium includes Intune Plan 1. The recorded assignment to DK-user means no additional Intune subscription for that user's enrollment, subject to licence readback before deployment. [Microsoft](https://learn.microsoft.com/en-us/microsoft-365/admin/security-and-compliance/m365bp-devices-enrollment?view=o365-worldwide) |
| ManageEngine Endpoint Central | Alternative for desktop administration, patching, software deployment, remote control, and MDM in one console. I would evaluate this if running the management server in the lab is the priority. | On-premises and cloud options. The on-premises Free edition is listed for 25 endpoints; individual capabilities and add-ons follow the edition matrix. [Vendor comparison](https://www.manageengine.com/products/desktop-central/edition-comparison-matrix.html) |
| Fleet | Alternative for self-hosted device inventory, Windows MDM settings, scripts, and configuration maintained in Git. Adds a service to operate alongside AD. | Free and Premium can be self-hosted. Free includes MDM and OS settings; built-in application deployment, encryption enforcement, and OS-update enforcement are Premium features. [Pricing](https://fleetdm.com/pricing) |

Fleet's [Windows enrollment instructions](https://fleetdm.com/guides/windows-mdm-setup) support enrollment by installing fleetd, but also state that Windows tamper protection is disabled when MDM is turned on. I would validate that behavior and its security implications on HQ-WS001 before considering Fleet for ObiPC.

ManageEngine also offers [MDM Plus](https://www.manageengine.com/mobile-device-management/free-mobile-device-management-software.html), free for up to 25 devices. For this desktop, I would compare Endpoint Central first: the vendor's [MDM Plus FAQ](https://www.manageengine.com/mobile-device-management/faq.html) recommends its desktop management offering for comprehensive Windows and macOS management.

## Proposed Intune scope

I would retain the AD join, user profile, and existing LAPS and local-administrator policies. Microsoft's [Group Policy enrollment path](https://learn.microsoft.com/en-us/windows/client-management/enroll-a-windows-10-device-automatically-using-group-policy) supports existing domain-joined devices; reimaging and Autopilot are not prerequisites for this path.

Before enrollment, I would verify DK-user's Intune and Entra licensing, MDM user scope, Windows enrollment restrictions, and interactive domain-user sign-in state. I would scope the automatic enrollment GPO to ObiPC, using User Credential, and verify enrollment on the endpoint and in Intune. I would choose application, update, and device configuration assignments separately to avoid configuring the same settings through GPO and MDM.

I keep the [standing compliance and Conditional Access decision](../README.md#decisions). Enrollment does not authorize changing that decision, disk encryption, or Windows Hello policy. Other staff accounts have Business Basic in the existing record; I would verify their licensing before extending user-based Intune management to them.

The existing TODO calls this co-management. Microsoft's [definition](https://learn.microsoft.com/en-us/intune/configmgr/comanage/overview) requires Configuration Manager plus Intune. The proposal here is AD Group Policy alongside Intune, without deploying Configuration Manager. Windows Admin Center remains an administration console and does not replace MDM enrollment.
