<#
.SYNOPSIS
    Gives members of a restricted group on ObiPC one pass of signed-in time,
    then signs them out and refuses their sign-in until an administrator resets
    the pass.

.DESCRIPTION
    RETIRED again 2026-09-28. It ran from 2026-09-12 with a daily budget and an
    8 AM to 10 PM window, and I retired it on 2026-09-18 after the rebuild. On
    2026-09-28 I rewrote it as a one-time 90-minute pass that does not reset on
    its own, ran it for about an hour while IK-user was enabled, and
    unregistered the task when I disabled the account again. Nothing runs this
    script now. It stays as the versioned reference, with the session-detection
    fix, in case the control comes back.

    Active Directory logon hours block a new sign-in but never end a session
    that is already running, and Windows has no native usage limit for a domain
    account. This script is that control.

    It runs as SYSTEM from a scheduled task, once a minute. On each tick it finds
    the interactive sessions, works out which of them belong to the restricted
    group, and adds the elapsed time to that account's pass. Time is counted only
    while a session is Active, so a signed-out account keeps what it has left.
    Warnings go to the session first. When the pass is spent the account gets
    the local Deny log on locally and Deny log on through Remote Desktop rights,
    and then its sessions are signed out. The deny comes first so there is no
    gap in which to sign straight back in.

    Nothing lifts the deny except -Reset, run by an administrator, which removes
    both rights and deletes the pass so the account starts a new one.

.NOTES
    State lives in $StateRoot, which must not be writable by the restricted user,
    or the pass is trivially reset. Inheritance is off on that folder and only
    SYSTEM and Administrators are granted.

    The deny rights are written to the local security database. No Group Policy
    object in the domain defines user rights for ObiPC, so a policy refresh does
    not overwrite them. If one ever does, the lockout stops holding.

    Group membership is read from Active Directory rather than from the session
    token, because a token only carries the groups the account held when it
    signed in. A newly added member is covered on the next tick, not after a
    sign-out.

    If Active Directory cannot be reached, an account that already has a pass
    file is still treated as restricted, so pulling the network cable does not
    stop the clock. An account with no pass file is left alone and the miss is
    logged.

.EXAMPLE
    Limit-ObiPCUserSession.ps1 -Reset -Account testuser

    Removes the deny rights from testuser and deletes its pass, so its next
    sign-in starts a fresh 90 minutes.
#>
[CmdletBinding(DefaultParameterSetName = 'Tick')]
param(
    [Parameter(ParameterSetName = 'Tick')]
    [string]   $RestrictedGroup      = 'ROL-ObiPC-Restricted',
    [Parameter(ParameterSetName = 'Tick')]
    [int]      $PassMinutes          = 90,
    [Parameter(ParameterSetName = 'Tick')]
    [int[]]    $WarnMinutesRemaining = @(15, 5, 1),
    [Parameter(ParameterSetName = 'Tick')]
    [switch]   $DryRun,

    [Parameter(ParameterSetName = 'Reset', Mandatory)]
    [switch]   $Reset,
    [Parameter(ParameterSetName = 'Reset', Mandatory)]
    [string]   $Account,

    [string]   $StateRoot            = 'C:\ProgramData\ObiPC-SessionLimit'
)

$ErrorActionPreference = 'Stop'
$logFile    = Join-Path $StateRoot 'enforcement.log'
$denyRights = @('SeDenyInteractiveLogonRight', 'SeDenyRemoteInteractiveLogonRight')

function Write-Line {
    param([string] $Message)
    $stamp = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    $line  = "$stamp $Message"
    try { Add-Content -Path $logFile -Value $line } catch { }
    Write-Verbose $line
}

function Initialize-LogonRight {
    # The LSA calls add or remove one right for one SID and leave every other
    # entry alone, which secedit's export-and-reimport does not promise.
    if ('ObiPcLogonRight' -as [type]) { return }
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Security.Principal;

public static class ObiPcLogonRight
{
    [StructLayout(LayoutKind.Sequential)]
    struct LsaUnicodeString { public ushort Length; public ushort MaximumLength; public IntPtr Buffer; }

    [StructLayout(LayoutKind.Sequential)]
    struct LsaObjectAttributes { public int Length; public IntPtr RootDirectory; public IntPtr ObjectName; public uint Attributes; public IntPtr SecurityDescriptor; public IntPtr SecurityQualityOfService; }

    [DllImport("advapi32.dll")] static extern uint LsaOpenPolicy(IntPtr systemName, ref LsaObjectAttributes attributes, uint access, out IntPtr handle);
    [DllImport("advapi32.dll")] static extern uint LsaAddAccountRights(IntPtr handle, byte[] sid, LsaUnicodeString[] rights, uint count);
    [DllImport("advapi32.dll")] static extern uint LsaRemoveAccountRights(IntPtr handle, byte[] sid, bool allRights, LsaUnicodeString[] rights, uint count);
    [DllImport("advapi32.dll")] static extern uint LsaEnumerateAccountRights(IntPtr handle, byte[] sid, out IntPtr rights, out uint count);
    [DllImport("advapi32.dll")] static extern uint LsaFreeMemory(IntPtr buffer);
    [DllImport("advapi32.dll")] static extern uint LsaClose(IntPtr handle);
    [DllImport("advapi32.dll")] static extern int LsaNtStatusToWinError(uint status);

    const uint PolicyAllAccess = 0x000F0FFF;
    const uint StatusObjectNameNotFound = 0xC0000034;

    static IntPtr Open()
    {
        LsaObjectAttributes attributes = new LsaObjectAttributes();
        IntPtr handle;
        Check(LsaOpenPolicy(IntPtr.Zero, ref attributes, PolicyAllAccess, out handle), "LsaOpenPolicy");
        return handle;
    }

    static void Check(uint status, string call)
    {
        if (status != 0) { throw new System.ComponentModel.Win32Exception(LsaNtStatusToWinError(status), call + " failed"); }
    }

    static byte[] SidBytes(string sid)
    {
        SecurityIdentifier identifier = new SecurityIdentifier(sid);
        byte[] bytes = new byte[identifier.BinaryLength];
        identifier.GetBinaryForm(bytes, 0);
        return bytes;
    }

    static LsaUnicodeString[] Strings(string[] rights)
    {
        LsaUnicodeString[] result = new LsaUnicodeString[rights.Length];
        for (int i = 0; i < rights.Length; i++)
        {
            result[i].Buffer = Marshal.StringToHGlobalUni(rights[i]);
            result[i].Length = (ushort)(rights[i].Length * 2);
            result[i].MaximumLength = (ushort)(rights[i].Length * 2 + 2);
        }
        return result;
    }

    static void Free(LsaUnicodeString[] strings)
    {
        foreach (LsaUnicodeString s in strings) { Marshal.FreeHGlobal(s.Buffer); }
    }

    public static void Add(string sid, string[] rights)
    {
        IntPtr handle = Open();
        LsaUnicodeString[] strings = Strings(rights);
        try { Check(LsaAddAccountRights(handle, SidBytes(sid), strings, (uint)strings.Length), "LsaAddAccountRights"); }
        finally { Free(strings); LsaClose(handle); }
    }

    public static void Remove(string sid, string[] rights)
    {
        IntPtr handle = Open();
        LsaUnicodeString[] strings = Strings(rights);
        try
        {
            uint status = LsaRemoveAccountRights(handle, SidBytes(sid), false, strings, (uint)strings.Length);
            if (status != StatusObjectNameNotFound) { Check(status, "LsaRemoveAccountRights"); }
        }
        finally { Free(strings); LsaClose(handle); }
    }

    public static string[] Get(string sid)
    {
        IntPtr handle = Open();
        try
        {
            IntPtr buffer;
            uint count;
            uint status = LsaEnumerateAccountRights(handle, SidBytes(sid), out buffer, out count);
            if (status == StatusObjectNameNotFound) { return new string[0]; }
            Check(status, "LsaEnumerateAccountRights");
            string[] result = new string[count];
            int size = Marshal.SizeOf(typeof(LsaUnicodeString));
            for (int i = 0; i < count; i++)
            {
                LsaUnicodeString s = (LsaUnicodeString)Marshal.PtrToStructure(new IntPtr(buffer.ToInt64() + i * size), typeof(LsaUnicodeString));
                result[i] = Marshal.PtrToStringUni(s.Buffer, s.Length / 2);
            }
            LsaFreeMemory(buffer);
            return result;
        }
        finally { LsaClose(handle); }
    }
}
'@
}

function Get-InteractiveSession {
    # query.exe is the only reliable way to see the state of a session, which
    # matters because a disconnected session should not spend the pass.
    # With $ErrorActionPreference = 'Stop', query.exe writing "No User exists for *"
    # to stderr (nobody signed in) becomes a terminating NativeCommandError and the
    # whole tick dies with exit code 1. Relax the preference around the call only.
    # Do not read the exit code: run as SYSTEM, query.exe exits 1 even when it
    # lists a signed-in session, so an exit-code check sees nobody, ever.
    $raw = $null
    $previous = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $raw = @(& query.exe user 2>$null)
    } finally { $ErrorActionPreference = $previous }
    if ($raw.Count -lt 2) { return @() }

    $sessions = @()
    foreach ($line in $raw[1..($raw.Count - 1)]) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        # Leading '>' marks the current session; strip it before splitting.
        $fields = ($line -replace '^\s*>', ' ').Trim() -split '\s{2,}'
        if ($fields.Count -lt 3) { continue }

        # A disconnected session has no SESSIONNAME, so the column count shifts.
        if ($fields.Count -ge 4 -and $fields[2] -match '^\d+$') {
            $sessions += [pscustomobject]@{ User = $fields[0]; Id = [int] $fields[2]; State = $fields[3] }
        }
        elseif ($fields[1] -match '^\d+$') {
            $sessions += [pscustomobject]@{ User = $fields[0]; Id = [int] $fields[1]; State = $fields[2] }
        }
    }
    return $sessions
}

function Resolve-UserSid {
    param([string] $SamAccountName)
    try {
        $account = New-Object System.Security.Principal.NTAccount($env:USERDOMAIN, $SamAccountName)
        return $account.Translate([System.Security.Principal.SecurityIdentifier]).Value
    } catch { return $null }
}

function Test-RestrictedMember {
    param([string] $Sid)
    # Returns $true, $false, or $null when the directory could not be reached.
    try {
        $groupSearch = [adsisearcher] "(&(objectClass=group)(sAMAccountName=$RestrictedGroup))"
        $group = $groupSearch.FindOne()
        if (-not $group) { return $false }
        $groupDn = $group.Properties['distinguishedname'][0]

        $userSearch = [adsisearcher] "(&(objectClass=user)(objectSid=$Sid))"
        $user = $userSearch.FindOne()
        if (-not $user) { return $false }

        foreach ($dn in $user.Properties['memberof']) {
            if ($dn -eq $groupDn) { return $true }
        }
        return $false
    } catch {
        Write-Line "WARN directory lookup failed for $Sid : $($_.Exception.Message)"
        return $null
    }
}

function Get-StatePath {
    param([string] $Sid)
    return Join-Path $StateRoot "$Sid-pass.json"
}

function Get-State {
    param([string] $Sid)
    $path = Get-StatePath -Sid $Sid
    if (Test-Path $path) {
        try { return (Get-Content $path -Raw | ConvertFrom-Json) } catch { }
    }
    return [pscustomobject]@{ Minutes = 0.0; LastTick = $null; Warned = @(); LockedAt = $null }
}

function Save-State {
    param([string] $Sid, $State)
    $State | ConvertTo-Json -Compress | Set-Content -Path (Get-StatePath -Sid $Sid) -Encoding UTF8
}

function Send-SessionMessage {
    param([int] $SessionId, [string] $Text)
    if ($DryRun) { Write-Line "DRYRUN would message session $SessionId : $Text"; return }
    try { & msg.exe $SessionId /TIME:60 $Text 2>$null } catch {
        Write-Line "WARN msg.exe failed for session $SessionId : $($_.Exception.Message)"
    }
}

function Stop-Session {
    param([int] $SessionId, [string] $Reason)
    if ($DryRun) { Write-Line "DRYRUN would sign out session $SessionId ($Reason)"; return }
    Write-Line "ACTION signing out session $SessionId ($Reason)"
    try { & logoff.exe $SessionId 2>$null } catch {
        Write-Line "ERROR logoff failed for session $SessionId : $($_.Exception.Message)"
    }
}

function Lock-Account {
    param([string] $Sid)
    if ($DryRun) { Write-Line "DRYRUN would deny sign-in to $Sid"; return }
    Initialize-LogonRight
    [ObiPcLogonRight]::Add($Sid, $denyRights)
    $held = [ObiPcLogonRight]::Get($Sid)
    Write-Line "ACTION denied sign-in to $Sid, rights now: $($held -join ',')"
}

if (-not (Test-Path $StateRoot)) {
    New-Item -ItemType Directory -Path $StateRoot -Force | Out-Null
}

if ($Reset) {
    $sid = Resolve-UserSid -SamAccountName $Account
    if (-not $sid) { throw "Could not resolve $Account to a SID." }
    Initialize-LogonRight
    [ObiPcLogonRight]::Remove($sid, $denyRights)
    Remove-Item -Path (Get-StatePath -Sid $sid) -Force -ErrorAction SilentlyContinue
    $held = [ObiPcLogonRight]::Get($sid)
    Write-Line "RESET pass cleared and sign-in allowed for $sid, rights now: $($held -join ',')"
    [pscustomobject]@{ Sid = $sid; Rights = $held; PassFile = (Test-Path (Get-StatePath -Sid $sid)) }
    return
}

$now = Get-Date

# One entry per account, so two sessions for the same person spend the pass once.
$accounts = @{}
foreach ($session in Get-InteractiveSession) {
    $sid = Resolve-UserSid -SamAccountName $session.User
    if (-not $sid) { continue }
    if (-not $accounts.ContainsKey($sid)) { $accounts[$sid] = @() }
    $accounts[$sid] += $session
}

foreach ($sid in $accounts.Keys) {
    $sessions = $accounts[$sid]

    $isRestricted = Test-RestrictedMember -Sid $sid
    if ($null -eq $isRestricted -and (Test-Path (Get-StatePath -Sid $sid))) {
        Write-Line "WARN directory unreachable, $sid has a pass file so it stays restricted"
        $isRestricted = $true
    }
    if ($isRestricted -ne $true) { continue }

    $state = Get-State -Sid $sid

    # Already spent: a session should not exist. Deny again and sign it out.
    if ($state.LockedAt) {
        Lock-Account -Sid $sid
        foreach ($session in $sessions) { Stop-Session -SessionId $session.Id -Reason 'pass already spent' }
        continue
    }

    $active = @($sessions | Where-Object State -eq 'Active')
    if ($active.Count -eq 0) {
        # Keep the pass but do not bridge the gap on return.
        $state.LastTick = $null
        Save-State -Sid $sid -State $state
        continue
    }

    # Accumulate. The cap stops a sleep or hibernate from charging the whole gap
    # to the pass: only time this task actually observed is counted.
    if ($state.LastTick) {
        $elapsed = ($now - [datetime] $state.LastTick).TotalMinutes
        if ($elapsed -gt 0 -and $elapsed -le 5) { $state.Minutes += $elapsed }
    }
    $state.LastTick = $now.ToString('o')

    $left = $PassMinutes - $state.Minutes
    Write-Line ("{0} sessions={1} used={2:N1}m left={3:N1}m" -f $sid, (($active | ForEach-Object Id) -join ','), $state.Minutes, $left)

    if ($left -le 0) {
        foreach ($session in $active) {
            Send-SessionMessage -SessionId $session.Id -Text "Your $PassMinutes minutes on this computer are used up. Signing out now."
        }
        Lock-Account -Sid $sid
        if (-not $DryRun) { $state.LockedAt = $now.ToString('o') }
        Save-State -Sid $sid -State $state
        foreach ($session in $sessions) { Stop-Session -SessionId $session.Id -Reason 'pass spent' }
        continue
    }

    # Warn once per threshold.
    foreach ($threshold in $WarnMinutesRemaining) {
        $key = "warn-$threshold"
        if ($left -le $threshold -and ($state.Warned -notcontains $key)) {
            foreach ($session in $active) {
                Send-SessionMessage -SessionId $session.Id -Text "$([Math]::Ceiling($left)) minutes left on this computer. After that you will be signed out and cannot sign back in. Please save your work."
            }
            $state.Warned = @($state.Warned) + $key
            Write-Line "warned $sid at $threshold minutes"
        }
    }

    Save-State -Sid $sid -State $state
}
