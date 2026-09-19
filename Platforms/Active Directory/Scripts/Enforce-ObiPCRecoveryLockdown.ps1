<#
.SYNOPSIS
    Keeps the Windows Recovery Environment disabled on ObiPC and requires
    administrator credentials for every recovery tool should it ever come back.

.DESCRIPTION
    On 2026-09-18 a standard user wiped ObiPC from the recovery menu, which on
    Windows 11 offers "Reset this PC, Remove everything" with no credentials at
    all. Two controls close that, and both live on the disk rather than in the
    directory, so this script re-applies them at every boot and once a day:

      1. reagentc /disable. Unmaps the recovery image from the boot
         configuration. Reset this PC, Startup Settings (Safe Mode), Startup
         Repair after failed boots, and the recovery command prompt all stop
         working, for everyone. A feature update re-enables WinRE during its
         specialize pass, which is why this runs on a schedule and not once.

      2. The Security/RecoveryEnvironmentAuthentication policy set to 1
         (RequireAuthentication) through the local MDM bridge. It has no Group
         Policy template, but the PolicyManager default on this build redirects
         it to HKLM\SOFTWARE\Policies\Microsoft\WinRE\WinREAuthenticationRequirement,
         which the C-WKS-ObiPC-Lockdown GPO also sets. Belt and braces: if WinRE
         is ever enabled again, both "Keep my files" and "Remove everything"
         then prompt for an administrator account.

    Recovery for the owner is a rebuild from the baseline, which is this
    workspace's standing recovery path anyway. To use WinRE deliberately, run
    reagentc /enable from an elevated prompt, do the work, and let the next tick
    disable it again.

.NOTES
    Must run as SYSTEM: the MDM bridge (root\cimv2\mdm\dmmap) refuses any other
    caller. -Install copies this file to C:\ProgramData\ObiPC-Lockdown, locks the
    folder to SYSTEM and Administrators, registers the scheduled task
    "ObiPC Recovery Lockdown" (at startup and daily at 3:00 AM), and runs it once.

    Ran 2026-09-18 on ObiPC after the reinstall. Bootstrap-ObiPC.ps1 does not
    include this step; run it after the machine is joined.
#>
[CmdletBinding()]
param(
    [switch] $Install,
    [string] $InstallRoot = 'C:\ProgramData\ObiPC-Lockdown',
    [string] $TaskName    = 'ObiPC Recovery Lockdown'
)

$ErrorActionPreference = 'Continue'
$logFile = Join-Path $InstallRoot 'recovery.log'

function Write-Line {
    param([string] $Message)
    $line = "{0} {1}" -f (Get-Date).ToString('yyyy-MM-dd HH:mm:ss'), $Message
    try { Add-Content -Path $logFile -Value $line } catch { }
    Write-Output $line
}

if ($Install) {
    New-Item -ItemType Directory -Path $InstallRoot -Force | Out-Null
    $target = Join-Path $InstallRoot 'Enforce-ObiPCRecoveryLockdown.ps1'
    Copy-Item -Path $PSCommandPath -Destination $target -Force
    & icacls.exe $InstallRoot /inheritance:r /grant:r 'SYSTEM:(OI)(CI)F' 'BUILTIN\Administrators:(OI)(CI)F' | Out-Null
    & schtasks.exe /create /f /tn $TaskName /ru SYSTEM /sc onstart /delay 0001:00 `
        /tr "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$target`"" | Out-Null
    # A second trigger on the same task: daily at 3:00 AM.
    $svc = New-Object -ComObject Schedule.Service; $svc.Connect()
    $task = $svc.GetFolder('\').GetTask($TaskName)
    $def  = $task.Definition
    $daily = $def.Triggers.Create(2)           # TASK_TRIGGER_DAILY
    $daily.StartBoundary = (Get-Date).Date.AddHours(3).ToString('yyyy-MM-dd\THH:mm:ss')
    $daily.DaysInterval  = 1
    $def.Settings.StartWhenAvailable = $true
    $svc.GetFolder('\').RegisterTaskDefinition($TaskName, $def, 6, 'SYSTEM', $null, 5) | Out-Null   # 6 = create or update, 5 = service account
    "Installed $target and task '$TaskName'. Running it once now."
    & schtasks.exe /run /tn $TaskName | Out-Null
    return
}

if (-not (Test-Path $InstallRoot)) { New-Item -ItemType Directory -Path $InstallRoot -Force | Out-Null }
Write-Line "tick as $([Security.Principal.WindowsIdentity]::GetCurrent().Name)"

# 1. Recovery environment off.
$status = (& reagentc.exe /info 2>&1 | Select-String 'Windows RE status').Line -replace '.*:\s*', ''
Write-Line "WinRE status before: $status"
if ($status -eq 'Enabled') {
    $out = & reagentc.exe /disable 2>&1
    Write-Line ("reagentc /disable: " + (($out | Select-String 'REAGENTC.EXE').Line))
    $status = (& reagentc.exe /info 2>&1 | Select-String 'Windows RE status').Line -replace '.*:\s*', ''
    Write-Line "WinRE status after: $status"
}

# 2. Recovery tools require administrator credentials, through the MDM bridge.
$ns = 'root\cimv2\mdm\dmmap'; $cls = 'MDM_Policy_Config01_Security02'
try {
    $inst = Get-CimInstance -Namespace $ns -ClassName $cls -ErrorAction Stop | Where-Object InstanceID -eq 'Security'
    if (-not $inst) {
        New-CimInstance -Namespace $ns -ClassName $cls -Property @{
            ParentID = './Vendor/MSFT/Policy/Config'; InstanceID = 'Security'; RecoveryEnvironmentAuthentication = [int] 1
        } -ErrorAction Stop | Out-Null
        Write-Line 'RecoveryEnvironmentAuthentication: instance created with value 1'
    } elseif ($inst.RecoveryEnvironmentAuthentication -ne 1) {
        $inst.RecoveryEnvironmentAuthentication = [int] 1
        Set-CimInstance -CimInstance $inst -ErrorAction Stop
        Write-Line 'RecoveryEnvironmentAuthentication: instance updated to 1'
    } else {
        Write-Line 'RecoveryEnvironmentAuthentication: already 1'
    }
} catch {
    Write-Line "WARN MDM bridge failed: $($_.Exception.Message)"
}

# 3. Read back what WinRE will actually consult.
# PolicyManager records only that a provider set the value; the value itself lands
# in the WinRE policy key through the redirect described above.
$pm  = (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\PolicyManager\current\device\Security' -ErrorAction SilentlyContinue).RecoveryEnvironmentAuthentication_ProviderSet
$reg = (Get-ItemProperty 'HKLM:\SOFTWARE\Policies\Microsoft\WinRE' -ErrorAction SilentlyContinue).WinREAuthenticationRequirement
Write-Line "readback: WinRE=$status PolicyManager.RecoveryEnvironmentAuthentication_ProviderSet=$pm Policies\WinRE\WinREAuthenticationRequirement=$reg"
