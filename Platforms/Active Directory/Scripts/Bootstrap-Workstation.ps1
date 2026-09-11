<#
Bootstrap-Workstation.ps1
Created: 2026-09-10

Run once, as Administrator, on a freshly installed Windows 11 Pro machine that is plugged into
Secure Client (VLAN 60). It gives the machine its name and a key-only OpenSSH server so that the
rest of the build (domain join, verification, Entra hybrid join) is done remotely from SSH Manager.
It does not join the domain and it needs no domain credential.

Usage, in an elevated PowerShell:
    Set-ExecutionPolicy -Scope Process Bypass -Force
    .\Bootstrap-Workstation.ps1 -ComputerName <name>

This is the template. Each physical machine gets its own copy in this folder, Bootstrap-<Name>.ps1,
with the name filled in, so the exact script run on every machine is kept.

The SSH Manager public key comes from `authorized_key.pub`, a sidecar file kept beside this script
and not published. Copy `authorized_key.pub.example`, rename it, and paste in your own key.
#>
[CmdletBinding()]
param(
    # Any valid Windows computer name: 1 to 15 letters, digits or hyphens, not all digits.
    [Parameter(Mandatory)][ValidatePattern('^(?!\d+$)[A-Za-z0-9-]{1,15}$')][string]$ComputerName
)
$ErrorActionPreference = 'Stop'
$KeyPath = Join-Path $PSScriptRoot 'authorized_key.pub'
if (-not (Test-Path $KeyPath)) { throw "Public key file not found: $KeyPath. Copy authorized_key.pub.example, rename it, and paste in your own key." }
$PublicKey = (Get-Content $KeyPath -Raw).Trim()
if ([string]::IsNullOrWhiteSpace($PublicKey)) { throw "Public key file is empty: $KeyPath." }

function Step($m) { Write-Host "`n== $m" -ForegroundColor Cyan }

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole('Administrators')) {
    throw 'Run this from an elevated PowerShell.'
}

Step 'Hardware prerequisites'
$tpm = Get-Tpm
"TPM present: $($tpm.TpmPresent)  ready: $($tpm.TpmReady)"
"Secure Boot: $(try { Confirm-SecureBootUEFI } catch { 'not UEFI' })"
$os = Get-CimInstance Win32_OperatingSystem
"Windows: $($os.Caption) build $($os.BuildNumber)"

Step 'Network profile to Private (OpenSSH inbound rule does not cover Public)'
Get-NetConnectionProfile | Where-Object NetworkCategory -ne 'DomainAuthenticated' |
    ForEach-Object { Set-NetConnectionProfile -InterfaceIndex $_.InterfaceIndex -NetworkCategory Private; "  $($_.InterfaceAlias): Private" }

Step 'OpenSSH Server'
$cap = Get-WindowsCapability -Online -Name 'OpenSSH.Server~~~~0.0.1.0'
if ($cap.State -ne 'Installed') {
    'Installing the Windows capability...'
    try { Add-WindowsCapability -Online -Name 'OpenSSH.Server~~~~0.0.1.0' | Out-Null } catch { Write-Warning "Capability install failed: $($_.Exception.Message)" }
    $cap = Get-WindowsCapability -Online -Name 'OpenSSH.Server~~~~0.0.1.0'
}
if ($cap.State -ne 'Installed') {
    'Capability route failed (HQ-WS001 had the same problem). Trying winget...'
    winget install --id Microsoft.OpenSSH.Preview --exact --accept-source-agreements --accept-package-agreements --silent
}
if (-not (Get-Service sshd -ErrorAction SilentlyContinue)) { throw 'sshd service is not present after both install routes. Stop here and report.' }
Set-Service sshd -StartupType Automatic
Start-Service sshd
"sshd: $((Get-Service sshd).Status), startup $((Get-Service sshd).StartType)"

Step 'Firewall: OpenSSH inbound on every profile, ICMP echo on'
if (Get-NetFirewallRule -Name 'OpenSSH-Server-In-TCP' -ErrorAction SilentlyContinue) {
    Set-NetFirewallRule -Name 'OpenSSH-Server-In-TCP' -Profile Any -Enabled True
} else {
    New-NetFirewallRule -Name 'OpenSSH-Server-In-TCP' -DisplayName 'OpenSSH Server (sshd)' -Direction Inbound -Protocol TCP -LocalPort 22 -Action Allow -Profile Any | Out-Null
}
Enable-NetFirewallRule -Name 'FPS-ICMP4-ERQ-In' -ErrorAction SilentlyContinue
'done'

Step 'Key-only access for administrators'
$authKeys = 'C:\ProgramData\ssh\administrators_authorized_keys'
Set-Content -Path $authKeys -Value $PublicKey -Encoding ascii
icacls $authKeys /inheritance:r /grant 'Administrators:F' /grant 'SYSTEM:F' | Out-Null
$cfg = 'C:\ProgramData\ssh\sshd_config'
$text = Get-Content $cfg -Raw
$text = $text -replace '(?m)^#?\s*PasswordAuthentication\s+\w+', 'PasswordAuthentication no'
$text = $text -replace '(?m)^#?\s*PubkeyAuthentication\s+\w+', 'PubkeyAuthentication yes'
if ($text -notmatch '(?m)^PasswordAuthentication no') { $text += "`nPasswordAuthentication no" }
if ($text -notmatch '(?m)^PubkeyAuthentication yes')   { $text += "`nPubkeyAuthentication yes" }
Set-Content -Path $cfg -Value $text -Encoding ascii
Restart-Service sshd
'password authentication off, public key on, key installed'

Step 'Computer name'
if ($env:COMPUTERNAME -ne $ComputerName) { Rename-Computer -NewName $ComputerName -Force; "renamed to $ComputerName, takes effect at reboot" } else { 'already correct' }

Step 'Report this back'
Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway } | ForEach-Object {
    "  Interface : $($_.InterfaceAlias)"
    "  Address   : $($_.IPv4Address.IPAddress)"
    "  Gateway   : $($_.IPv4DefaultGateway.NextHop)   (expect 192.168.60.1 on Secure Client)"
    "  DNS       : $($_.DNSServer.ServerAddresses -join ', ')   (expect 192.168.65.10, 192.168.65.11)"
}
"  Domain DNS : $(try { (Resolve-DnsName ad.alphasecunited.com -Type A -ErrorAction Stop | Select-Object -First 1).IPAddress } catch { 'FAILED: ' + $_.Exception.Message })"
"  Host key   : $((ssh-keygen -lf C:\ProgramData\ssh\ssh_host_ed25519_key.pub) -replace '\s+\S+$','')"
Write-Host "`nSend the block above, then reboot: Restart-Computer" -ForegroundColor Yellow
