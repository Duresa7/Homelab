<#
.SYNOPSIS
    Enforces a daily sign-in window and a daily usage budget for members of a
    restricted group on ObiPC.

.DESCRIPTION
    Active Directory logon hours block a new sign-in but never end a session that
    is already running, and Windows has no native daily-usage budget for a domain
    account. This script is both of those controls.

    It runs as SYSTEM from a scheduled task, once a minute. On each tick it finds
    the interactive sessions, works out which of them belong to the restricted
    group, adds the elapsed time to that account's total for the local calendar
    day, and signs the session out when either the window closes or the budget is
    spent. Warnings go to the session first.

    Local time is deliberate. The script reads the clock the user sees, so the
    window follows daylight saving without anyone re-setting it twice a year.
    That is why the window lives here rather than only in the directory. Logon
    hours stay in place as a wider backstop for the case where this task is
    broken or disabled.

.NOTES
    State lives in $StateRoot, which must not be writable by the restricted user,
    or the budget is trivially reset. The scheduled task installer sets that ACL.

    Group membership is read from Active Directory rather than from the session
    token, because a token only carries the groups the account held when it
    signed in. A newly added member is covered on the next tick, not after a
    sign-out.

    If Active Directory cannot be reached, the script does nothing and says so.
    Failing open is deliberate: the cost of being wrong is a person losing their
    work, which is worse than a missed hour of enforcement.
#>
[CmdletBinding()]
param(
    [string]   $RestrictedGroup     = 'ROL-ObiPC-Restricted',
    [int]      $WindowStartHour     = 8,
    [int]      $WindowEndHour       = 22,
    [int]      $DailyBudgetMinutes  = 240,
    [int[]]    $WarnMinutesRemaining = @(15, 5),
    [string]   $StateRoot           = 'C:\ProgramData\ObiPC-SessionLimit',
    [switch]   $DryRun
)

$ErrorActionPreference = 'Stop'
$logFile = Join-Path $StateRoot 'enforcement.log'

function Write-Line {
    param([string] $Message)
    $stamp = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    $line  = "$stamp $Message"
    try { Add-Content -Path $logFile -Value $line } catch { }
    Write-Verbose $line
}

function Get-InteractiveSession {
    # query.exe is the only reliable way to see the state of a session, which
    # matters because a disconnected or locked session should not spend budget.
    $raw = & query.exe user 2>$null
    if (-not $raw -or $raw.Count -lt 2) { return @() }

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

function Get-State {
    param([string] $Sid)
    $today = (Get-Date).ToString('yyyy-MM-dd')
    $path  = Join-Path $StateRoot "$Sid-$today.json"
    if (Test-Path $path) {
        try { return (Get-Content $path -Raw | ConvertFrom-Json) } catch { }
    }
    return [pscustomobject]@{ Minutes = 0.0; LastTick = $null; Warned = @() }
}

function Save-State {
    param([string] $Sid, $State)
    $today = (Get-Date).ToString('yyyy-MM-dd')
    $path  = Join-Path $StateRoot "$Sid-$today.json"
    $State | ConvertTo-Json -Compress | Set-Content -Path $path -Encoding UTF8
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

if (-not (Test-Path $StateRoot)) {
    New-Item -ItemType Directory -Path $StateRoot -Force | Out-Null
}

$now = Get-Date
foreach ($session in Get-InteractiveSession) {
    if ($session.State -ne 'Active') { continue }

    $sid = Resolve-UserSid -SamAccountName $session.User
    if (-not $sid) { continue }

    $isRestricted = Test-RestrictedMember -Sid $sid
    if ($isRestricted -ne $true) { continue }

    $state = Get-State -Sid $sid

    # Accumulate. The cap stops a sleep or hibernate from charging the whole gap
    # to the budget: only time this task actually observed is counted.
    if ($state.LastTick) {
        $elapsed = ($now - [datetime] $state.LastTick).TotalMinutes
        if ($elapsed -gt 0 -and $elapsed -le 5) { $state.Minutes += $elapsed }
    }
    $state.LastTick = $now.ToString('o')

    $budgetLeft = $DailyBudgetMinutes - $state.Minutes
    $windowEnd  = $now.Date.AddHours($WindowEndHour)
    $windowLeft = ($windowEnd - $now).TotalMinutes
    $outsideWindow = ($now.Hour -lt $WindowStartHour) -or ($now.Hour -ge $WindowEndHour)

    Write-Line ("session {0} used={1:N1}m budgetLeft={2:N1}m windowLeft={3:N1}m" -f $session.Id, $state.Minutes, $budgetLeft, $windowLeft)

    if ($outsideWindow) {
        Send-SessionMessage -SessionId $session.Id -Text "Outside your allowed hours ($WindowStartHour`:00 to $WindowEndHour`:00). Signing out now."
        Stop-Session -SessionId $session.Id -Reason 'outside window'
        Save-State -Sid $sid -State $state
        continue
    }

    if ($budgetLeft -le 0) {
        Send-SessionMessage -SessionId $session.Id -Text "Your $DailyBudgetMinutes minutes for today are used up. Signing out now."
        Stop-Session -SessionId $session.Id -Reason 'budget spent'
        Save-State -Sid $sid -State $state
        continue
    }

    # Warn once per threshold, on whichever limit arrives first.
    $remaining = [Math]::Min($budgetLeft, $windowLeft)
    foreach ($threshold in $WarnMinutesRemaining) {
        $key = "warn-$threshold"
        if ($remaining -le $threshold -and ($state.Warned -notcontains $key)) {
            Send-SessionMessage -SessionId $session.Id -Text "$threshold minutes left on this computer today. Please save your work."
            $state.Warned = @($state.Warned) + $key
            Write-Line "warned session $($session.Id) at $threshold minutes"
        }
    }

    Save-State -Sid $sid -State $state
}
