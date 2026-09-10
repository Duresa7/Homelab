# Active Directory

**Created:** 2026-09-09  
**Last updated:** 2026-09-10

This is the path I took to stand up the `ad.alphasecunited.com` forest on two Windows Server 2025 domain controllers, from three cloned virtual machines to a member server that Group Policy and Windows LAPS actually reach. It is written to be followed start to finish.

The lab it runs in is a five-node Proxmox cluster called Galaxy and a UniFi gateway with a zone-based firewall. Substitute your own addressing where the values are mine.

## What you end up with

A forest at the Windows Server 2016 functional level with two domain controllers, both global catalogs, in one site. A tiered organisational unit tree with computer and user redirection pointed somewhere policy reaches. Group Policy that sets local administrators per tier. Windows LAPS managing local administrator passwords in the directory. A member server proving all of it works.

| Host | Address | Role |
|---|---|---|
| `HQ-DC01` | `192.168.65.10` | First domain controller, all five operations master roles |
| `HQ-DC02` | `192.168.65.11` | Second domain controller |
| `HQ-MGT01` | `192.168.65.12` | Member server |

## Before you start

You need a Windows Server 2025 template with the QEMU guest agent installed, OpenSSH Server enabled, and sysprep already run. Mine is VM 300 on `grey-server`, built with OVMF firmware, a TPM 2.0 device, and a `virtio-scsi-single` controller.

You need a VLAN for the identity plane. Mine is VLAN 65, `192.168.65.0/24`, gateway `192.168.65.1`, and it sits in its own firewall zone so I can write policy against it. Put the domain controllers on static addresses before promoting anything. A domain controller that changes address after promotion leaves stale service records behind.

Decide the names now. Changing a forest name later means rebuilding it.

- Forest and domain: `ad.alphasecunited.com`
- NetBIOS: `ALPHASEC`
- Functional level: `WinThreshold`, which is the 2016 level

I use `ad.` as a subdomain of a domain I own. Do not use a domain you do not control, and do not use a made-up top-level domain like `.local`.

## Step 1: Clone the template three times

```bash
qm clone 300 301 --name HQ-DC01 --full 1 --storage ssd-lvm1
qm clone 300 302 --name HQ-DC02 --full 1 --storage ssd-lvm1
qm clone 300 303 --name HQ-MGT01 --full 1 --storage ssd-lvm1
```

Give the management server more room than the controllers. Mine runs 2 vCPU and 6 GiB against a 100G disk, where each controller has 4 vCPU and 4 GiB against 80G.

<!-- ![HQ-DC01 hardware in Proxmox](../Platforms/Active%20Directory/Evidence/Forest%20Build%20-%202026-09-09/Screenshots/S01-Proxmox-HQ-DC01-Hardware-2026-09-09.png) -->

## Step 2: Fix what cloning breaks

Three things are wrong on every clone and none of them announce themselves.

**The SSH host keys are identical.** Sysprep does not regenerate them, so all three machines present the same fingerprint and your client silently treats them as the same host. Delete the keys and let the service rebuild them.

```powershell
Remove-Item C:\ProgramData\ssh\ssh_host_* -Force
Restart-Service sshd
```

Then re-enroll each fingerprint wherever you pinned the old one.

**The network profile comes up Public.** That blocks SSH and ping and makes the machine look dead. Set it to Private, open the SSH rule on every profile, and allow echo requests.

```powershell
Set-NetConnectionProfile -InterfaceAlias Ethernet -NetworkCategory Private
Set-NetFirewallRule -Name 'OpenSSH-Server-In-TCP' -Profile Any
Enable-NetFirewallRule -Name 'FPS-ICMP4-ERQ-In'
```

**The local Administrator password may be blank.** Check it before you promote anything. This one matters more than it looks, and Step 4 explains why.

## Step 3: A grey console is not a hung machine

If the Proxmox console shows a grey screen with no sign-in prompt, the automatic first-logon session is stuck part-way through building the profile. There is no `explorer.exe` and no `LogonUI`. The machine is running and answers on the network.

```bash
qm guest exec 301 -- cmd /c "logoff 1"
```

That ends the broken session and the sign-in screen returns.

## Step 4: Set a real Administrator password before promoting

`Install-ADDSForest` turns the local `Administrator` into the domain `Administrator`. If that account has a blank password and the "password not required" flag, you get a forest whose built-in administrator has no password, and you will not notice until something else fails.

```powershell
$p = [Console]::In.ReadLine()
$s = ConvertTo-SecureString $p -AsPlainText -Force
Set-LocalUser -Name Administrator -Password $s -PasswordNeverExpires $true
net user Administrator /passwordreq:yes | Out-Null
```

Read the value from standard input rather than passing it as a parameter. Anything you pass as an argument to `qm guest exec` is written to the Proxmox task log in clear text.

## Step 5: Promote the first controller

Run this as a scheduled task under `NT AUTHORITY\SYSTEM`, not over an SSH session. The promotion restarts services your session depends on.

```powershell
$sec = ConvertTo-SecureString $pw -AsPlainText -Force
Install-ADDSForest -DomainName 'ad.alphasecunited.com' -DomainNetbiosName 'ALPHASEC' `
  -SafeModeAdministratorPassword $sec -ForestMode 'WinThreshold' -DomainMode 'WinThreshold' `
  -InstallDns:$true -CreateDnsDelegation:$false `
  -DatabasePath 'C:\Windows\NTDS' -LogPath 'C:\Windows\NTDS' -SysvolPath 'C:\Windows\SYSVOL' `
  -NoRebootOnCompletion:$true -Force:$true
```

The DSRM password is a separate credential from the domain administrator password. Store it before you need it, because the moment you need it is the moment the directory will not start.

<!-- ![Forest promotion result](../Platforms/Active%20Directory/Evidence/Forest%20Build%20-%202026-09-09/Screenshots/S02-Forest-Promotion-Result-2026-09-09.png) -->

Reboot, then promote the second controller with `Install-ADDSDomainController` against the same domain. Make it a global catalog. Two controllers is the point: one is a single point of failure holding every operations master role.

## Step 6: Name the site and map the subnets

A new forest gives you `Default-First-Site-Name` and no subnets, which means every client guesses which controller to use.

```powershell
Rename-ADObject -Identity (Get-ADReplicationSite -Identity 'Default-First-Site-Name').DistinguishedName -NewName 'HQ'
New-ADReplicationSubnet -Name '192.168.65.0/24' -Site 'HQ'
New-ADReplicationSubnet -Name '192.168.50.0/24' -Site 'HQ'
New-ADReplicationSubnet -Name '192.168.60.0/24' -Site 'HQ'
```

Map the client subnets now, before any workstation joins, so the first lookup a client makes is already correct.

<!-- ![Site HQ with mapped subnets](../Platforms/Active%20Directory/Evidence/Forest%20Build%20-%202026-09-09/Screenshots/S04-Sites-And-Subnets-2026-09-09.png) -->

## Step 7: DNS

Promotion creates the forward zone and `_msdcs`. Add the reverse zone, point the forwarder at your gateway, and turn on scavenging so dead records leave on their own.

```powershell
Add-DnsServerPrimaryZone -NetworkId '192.168.65.0/24' -ReplicationScope 'Forest'
Set-DnsServerForwarder -IPAddress '192.168.65.1'
Set-DnsServerScavenging -ScavengingState $true -RefreshInterval 7.00:00:00 -NoRefreshInterval 7.00:00:00 -ApplyOnAllZones
```

All three zones should be primary, AD-integrated, and set to secure dynamic update only. Confirm the controllers resolve an external name before moving on, because everything after this depends on name resolution working.

<!-- ![DNS zones on HQ-DC01](../Platforms/Active%20Directory/Evidence/Forest%20Build%20-%202026-09-09/Screenshots/S05-DNS-Zones-2026-09-09.png) -->

## Step 8: Build the organisational unit tree

The shape matters more than the names. Separate administrative accounts by tier, keep servers apart from workstations, and give yourself somewhere to put objects that are not ready yet.

```
Admin/{Tier 0,Tier 1,Tier 2}/{Accounts,Groups,Service Accounts}
Servers/{Management,Application}
Workstations/Standard
Users/Staff
Groups/{Roles,Permissions,Applications,Distribution}
Staging/{Computers,Users}
Disabled/{Users,Computers}
```

Then redirect the default containers. This is the step people skip, and skipping it means a machine that joins the domain lands in `CN=Computers`, where no organisational-unit-linked policy reaches it.

```cmd
redircmp "OU=Computers,OU=Staging,DC=ad,DC=alphasecunited,DC=com"
redirusr "OU=Users,OU=Staging,DC=ad,DC=alphasecunited,DC=com"
```

<!-- ![Tiered organisational unit tree](../Platforms/Active%20Directory/Evidence/Forest%20Build%20-%202026-09-09/Screenshots/S03-OU-Tree-2026-09-09.png) -->

## Step 9: Groups and administrative accounts

Nest a group into `Domain Admins` rather than putting people in it directly. Membership then becomes something you can see and audit in one place.

| Group | Purpose |
|---|---|
| `ADM-T0-DomainAdmins` | Nested into `Domain Admins` |
| `ADM-T1-ServerAdmins` | Local administrator on member servers |
| `ADM-T2-WorkstationAdmins` | Local administrator on workstations |

Build a separate account per tier. Mine are `DK-t0` and `DK-t2`. Put the Tier 0 account in `Protected Users` and flag it as sensitive and not delegated.

```powershell
Add-ADGroupMember -Identity 'Protected Users' -Members 'DK-t0'
Set-ADUser -Identity 'DK-t0' -AccountNotDelegated $true
```

Leave the built-in `Administrator` as break-glass and stop using it. `Protected Users` blocks NTLM and unconstrained delegation for its members, which is the point, and also means you cannot use those accounts for everything.

## Step 10: Password policy

The default domain policy applies to everyone, so set it for ordinary people: 14 characters, complexity on, history 24, and no expiry. Forced rotation drives predictable passwords.

Then add a fine-grained policy for the administrative groups, which is the only way to hold administrators to a higher bar than everyone else.

```powershell
New-ADFineGrainedPasswordPolicy -Name 'PSO-Admins' -Precedence 10 `
  -MinPasswordLength 20 -MaxPasswordAge 365.00:00:00 `
  -LockoutThreshold 5 -LockoutDuration 00:30:00 -LockoutObservationWindow 00:30:00 `
  -ComplexityEnabled $true
Add-ADFineGrainedPasswordPolicySubject -Identity 'PSO-Admins' -Subjects 'ADM-T0-DomainAdmins','ADM-T1-ServerAdmins','ADM-T2-WorkstationAdmins'
```

<!-- ![Default policy and PSO-Admins](../Platforms/Active%20Directory/Evidence/Forest%20Build%20-%202026-09-09/Screenshots/S09-Password-Policies-2026-09-09.png) -->

## Step 11: Local administrators by policy

Two policies, one for servers and one for workstations, each using Group Policy Preferences local users and groups. Each replaces the local `Administrators` membership with its tier group, so a Tier 2 account never gains rights on a server.

Link `C-SRV-LocalAdmins` to `Servers` and `C-WKS-LocalAdmins` to `Workstations`.

If you build the preference item by writing `Groups.xml` directly rather than through the editor, you also have to register the client-side extension on the policy object. A preference the client does not know to process is a policy that silently does nothing. Set `gPCMachineExtensionNames` to include the local users and groups extension `{17D89FEC-5C44-4972-B12D-241CAEF74509}` with tool extension `{79F92669-4224-476C-9C5C-6EFB4D87DF4A}`, and bump both `versionNumber` on the object and the version in `gpt.ini` so they stay in step.

<!-- ![Group Policy objects and links](../Platforms/Active%20Directory/Evidence/Forest%20Build%20-%202026-09-09/Screenshots/S06-Group-Policy-Objects-2026-09-09.png) -->

## Step 12: Windows LAPS

Windows LAPS is built into Windows Server 2025. Extend the schema, grant computers the right to write their own password, and link a policy.

```powershell
Update-LapsADSchema -Force
Set-LapsADComputerSelfPermission -Identity 'OU=Servers,DC=ad,DC=alphasecunited,DC=com'
Set-LapsADComputerSelfPermission -Identity 'OU=Workstations,DC=ad,DC=alphasecunited,DC=com'
Set-LapsADComputerSelfPermission -Identity 'OU=Computers,OU=Staging,DC=ad,DC=alphasecunited,DC=com'
```

Configure `C-CMP-LAPS` to back up to Active Directory with 20 characters, a 30-day rotation, encryption on, and a post-authentication reset, then link it to `Servers` and `Workstations`. The policy key is `HKLM\Software\Microsoft\Policies\LAPS`.

To verify the schema extension, look for the attribute. `Get-LapsADSchema` does not exist, and reaching for it wastes an afternoon.

```powershell
Get-ADObject -SearchBase (Get-ADRootDSE).schemaNamingContext -LDAPFilter '(lDAPDisplayName=msLAPS-EncryptedPassword)'
```

Force a client to act, then read the password back:

```powershell
Invoke-LapsPolicyProcessing
Get-LapsADPassword -Identity HQ-MGT01 -AsPlainText
```

<!-- ![LAPS password retrieved for HQ-MGT01](../Platforms/Active%20Directory/Evidence/Forest%20Build%20-%202026-09-09/Screenshots/S07-LAPS-Password-Retrieved-2026-09-09.png) -->

Once a machine is LAPS-managed, the directory holds the authoritative local administrator password and whatever you stored in a password manager for that machine is stale.

## Step 13: Join the member server, then reboot properly

Join `HQ-MGT01`, then reboot cleanly and let it sync time before you judge whether policy works.

Mine applied zero policies after joining, including the Default Domain Policy, and its Group Policy log still called the computer `WORKGROUP\HQ-MGT01`. The controller side was perfect. The machine was simply still running under its pre-join identity. A clean reboot fixed it.

If Windows Time never synchronises on a member, point it at the domain hierarchy:

```powershell
w32tm /config /syncfromflags:domhier /update
Restart-Service w32time
w32tm /resync
```

<!-- ![Tier 1 group in the local Administrators group](../Platforms/Active%20Directory/Evidence/Forest%20Build%20-%202026-09-09/Screenshots/S08-MGT01-Local-Administrators-2026-09-09.png) -->

## Step 14: Join a workstation without a domain administrator password

A normal `Add-Computer` needs a credential, and on Proxmox anything you pass to `qm guest exec` is written to the task log. An offline domain join avoids the problem completely: the domain controller creates the account and hands out a single-use package, and the workstation consumes it with no administrator password anywhere.

Provision on the controller, running as `NT AUTHORITY\SYSTEM` through the guest agent, which is the machine account and already has the rights:

```powershell
djoin.exe /provision /domain 'ad.alphasecunited.com' /machine 'HQ-WS001' `
  /machineou 'OU=Standard,OU=Workstations,DC=ad,DC=alphasecunited,DC=com' `
  /savefile 'C:\Windows\Temp\ws001odj.txt' /reuse
```

Pass those arguments from PowerShell variables. Sending the same command through `cmd /c` mangles the quoting around the organisational unit path, whose commas `cmd` treats as delimiters, and it fails with `0x57`, the parameter is incorrect.

Move the package to the workstation on a virtual disc rather than through a command line, so the machine password never lands in an argument or a log. Read it off the controller and decode it straight to a file without printing it:

```bash
pvesh get /nodes/grey-server/qemu/301/agent/file-read --file 'C:\Windows\Temp\ws001odj.b64' --output-format json \
  | python3 -c 'import sys,json,base64; d=json.load(sys.stdin); open("odj.txt","wb").write(base64.b64decode(d["content"].strip()))'
genisoimage -J -R -o /var/lib/vz/template/iso/ws001-odj.iso odj.txt
```

Attach that disc, then apply it on the workstation and reboot:

```powershell
djoin.exe /requestODJ /loadfile D:\ws001odj.txt /windowspath C:\Windows /localos
```

Two things will catch you here.

**The disc will not appear until the virtual machine is power-cycled.** Attaching a CD-ROM to a running guest and then restarting from inside Windows is not enough, because a guest-initiated reboot does not rebuild the emulated device model. The guest keeps showing the previous disc. Stop and start the virtual machine.

**Never hard-stop the guest between applying the join and its completing reboot.** I used a power cut rather than a shutdown to detach the disc, and Windows came up in Automatic Repair. A restart recovered it, but the repair had rolled back the pending transaction and the machine was back in a workgroup with the join undone. The computer object in the directory survived, so re-provisioning with `/reuse` and repeating the join worked. Use a graceful shutdown, and reboot from inside the guest.

Shred every copy of the package afterwards: the file on the controller, the decoded copy on the hypervisor, and the disc image. It is single use and invalid after the join, but it is still a machine password.

## Step 15: The network has to cooperate

Two gateway settings decide whether this forest behaves, and both are easy to miss because nothing fails loudly.

**Time.** The domain hierarchy only works if the top of it has real time. The controller holding the PDC emulator role is that top. If your firewall blocks its outbound NTP, it falls back to its own CMOS clock and every machine in the domain inherits the drift. Allow UDP 123 outbound from the identity zone, and check that the allow rule sits *above* any catch-all block for the same zone pair. Order decides the outcome; a rule below the block never runs.

```powershell
w32tm /config /manualpeerlist:"time.cloudflare.com,0x8 time.windows.com,0x8" /syncfromflags:manual /reliable:yes /update
w32tm /query /source
```

`w32tm /query /source` should name an external server. If it says `Local CMOS Clock`, the traffic is not getting out.

**DNS.** Domain members must resolve through the domain controllers, not the gateway. Set the DHCP name servers on each client VLAN to the two controllers. Then confirm the firewall actually permits that path, because on a zone-based firewall the client VLANs and the identity VLAN are usually in different zones and the default between zones is a block. The port set a domain member needs is 53, 88, 123, 135, 389, 445, 464, 636, 3268, 3269, and the dynamic range 49152 to 65535.

## Step 16: Verify, and do it from the right context

Here is the trap that will cost you the most time.

Over SSH, `dcdiag /test:replications` returns `DsBindWithSpnEx() failed with error 5, Access is denied`, and `repadmin /syncall` returns `SyncAll exited with fatal Win32 error: 8440`. It reads as a broken forest.

It is not. An OpenSSH network logon gets no delegatable Kerberos ticket, so any check that binds to the *other* controller fails as you. This is the double-hop problem. Anything touching only the controller you are logged into works fine, which is why promotion and object creation succeed while the replication tests fail.

Run those checks in machine-account context instead. Through Proxmox, `qm guest exec` runs as `NT AUTHORITY\SYSTEM`, which is the computer account and has real rights to the peer.

```bash
qm guest exec 301 --timeout 120 -- cmd /c "repadmin /replsummary"
```

Better still, prove replication with an object rather than a test. Create something on one controller and poll for it on the other. Mine crossed in 4 seconds.

```powershell
New-ADObject -Type contact -Name "canary-$(Get-Date -f yyyyMMddHHmmss)" -Path "OU=Staging,DC=ad,DC=alphasecunited,DC=com"
```

A healthy result is 0 failures out of 5 in both directions, both controllers listed as global catalogs in the site, and all five operations master roles accounted for.

## What good looks like

| Check | Expected |
|---|---|
| `repadmin /replsummary` | 0 of 5 failures each direction, no error column |
| `Get-ADForest` | Both controllers as global catalogs, one site |
| `w32tm /query /source` on the PDC | An external time server, not `Local CMOS Clock` |
| `Get-LapsADPassword` | Returns a password and an expiry for a managed machine |
| Local `Administrators` on a member | Contains the tier group, placed there by policy |

## Things that will bite you

- A clone keeps the template's SSH host keys. All of them present the same fingerprint.
- A clone comes up on the Public network profile with SSH and ping blocked.
- A blank local `Administrator` password becomes a blank domain `Administrator` password at promotion.
- `Get-LapsADSchema` is not a command.
- A firewall allow rule underneath a catch-all block never runs.
- A freshly joined machine can report its old workgroup identity until it is rebooted, and applies no policy until then.
- Replication tests fail over SSH for authentication reasons that have nothing to do with replication.
- On Windows 11 25H2, an answer file that drives partitioning with a scripted DiskPart through `RunSynchronous` fails with `0x80070103` after partitioning and before the image is applied. Use the documented `DiskConfiguration` element instead.
- `Press any key to boot from CD or DVD` expires in seconds and then falls through to no bootable device, so an unattended build stalls at a dead firmware prompt. Send keystrokes right after starting the guest.
- Install the QEMU guest agent as the first first-logon command, through the virtio guest tools. It also brings the network and balloon drivers, and it is the management channel that survives when SSH does not install.

## Source Records

- [Active Directory platform](../Platforms/Active%20Directory/README.md) for current state
- [Forest Build - 2026-09-09](../Platforms/Active%20Directory/Documentation/Change%20Records/Forest%20Build%20-%202026-09-09.md) for the build and its verification
- [HQ-WS001 Workstation Join - 2026-09-10](../Platforms/Active%20Directory/Documentation/Change%20Records/HQ-WS001%20Workstation%20Join%20-%202026-09-10.md) for the workstation and the offline join
- [Identity NTP and Client DNS - 2026-09-09](../Infrastructure/Network/UniFi/Documentation/Change%20Records/Identity%20NTP%20and%20Client%20DNS%20-%202026-09-09.md) for the gateway side
- [UniFi Network](UniFi-Network.md) for zones and policy order
- [Galaxy Proxmox Cluster](Galaxy-Proxmox-Cluster.md) for the cluster the guests run on
