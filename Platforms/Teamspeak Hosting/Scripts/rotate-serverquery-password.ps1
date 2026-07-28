<#
.SYNOPSIS
    Rotate a TeamSpeak ServerQuery password and store the replacement.

.DESCRIPTION
    TeamSpeak prints the ServerQuery password to stdout the first time an
    instance starts, and that line stays in the container log. Rotating makes
    the logged value worthless.

    The server generates the replacement; there is no way to choose it. This
    script captures what the server issues, proves it authenticates before
    storing it, writes it into the credential store, reads it back to confirm
    the two match, then checks that the old password is rejected.

    The value is never printed, echoed, or written to disk. Nothing about which
    credential store is used belongs in this file; supply the reference at run
    time.

.PARAMETER Port
    ServerQuery TCP port of the instance to rotate. Each instance keeps its own
    serveradmin account, so rotating one does not affect the others.

.PARAMETER LoginRef
    Secret reference resolving to the ServerQuery login name.

.PARAMETER PasswordRef
    Secret reference resolving to the current password. The replacement is
    written back to this same reference on success.

.EXAMPLE
    ./rotate-serverquery-password.ps1 -Port 10013 `
        -LoginRef 'op://<vault>/<item>/<section>/serverquery login' `
        -PasswordRef 'op://<vault>/<item>/<section>/serverquery password'

.NOTES
    Requires the ServerQuery port to be reachable and the calling host to be in
    that instance's query_ip_allowlist.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][int]$Port,
    [Parameter(Mandatory)][string]$LoginRef,
    [Parameter(Mandatory)][string]$PasswordRef,
    [string]$TargetHost = '127.0.0.1'
)

$ErrorActionPreference = 'Stop'

function Read-Until {
    param([IO.StreamReader]$Reader, [int]$TimeoutMs = 8000)
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $buf = ''
    while ($sw.ElapsedMilliseconds -lt $TimeoutMs) {
        $line = $null
        try { $line = $Reader.ReadLine() } catch { break }
        if ($null -eq $line) { Start-Sleep -Milliseconds 50; continue }
        $buf += $line + "`n"
        if ($line -match 'error id=\d+') { return $buf }
    }
    return $buf
}

function Convert-FromTS3Escape {
    param([string]$Value)
    $map = @{ '\\' = '\'; '\/' = '/'; '\s' = ' '; '\p' = '|'; '\a' = "`a"; '\b' = "`b";
        '\f' = "`f"; '\n' = "`n"; '\r' = "`r"; '\t' = "`t"; '\v' = "`v" }
    $out = ''
    $i = 0
    while ($i -lt $Value.Length) {
        if ($Value[$i] -eq '\' -and $i + 1 -lt $Value.Length) {
            $pair = $Value.Substring($i, 2)
            if ($map.ContainsKey($pair)) { $out += $map[$pair]; $i += 2; continue }
        }
        $out += $Value[$i]; $i++
    }
    return $out
}

function Connect-Query {
    $c = [Net.Sockets.TcpClient]::new()
    $c.ReceiveTimeout = 9000; $c.SendTimeout = 9000
    $c.Connect($TargetHost, $Port)
    $s = $c.GetStream()
    $r = [IO.StreamReader]::new($s)
    $w = [IO.StreamWriter]::new($s); $w.NewLine = "`n"; $w.AutoFlush = $true
    $r.ReadLine() | Out-Null   # "TS3"
    $r.ReadLine() | Out-Null   # welcome banner
    return @{ Client = $c; Reader = $r; Writer = $w }
}

$user = op read $LoginRef
$oldPw = op read $PasswordRef

$q = Connect-Query
$q.Writer.WriteLine("login client_login_name=$user client_login_password=$oldPw")
if ((Read-Until $q.Reader) -notmatch 'error id=0') {
    $q.Client.Close()
    throw 'Login with the current password failed. Nothing was changed.'
}
Write-Output 'Logged in with the current password.'

$q.Writer.WriteLine("clientsetserverquerylogin client_login_name=$user")
$reply = Read-Until $q.Reader
$q.Writer.WriteLine('quit')
$q.Client.Close()

if ($reply -notmatch 'client_login_password=([^\s]+)') {
    $safe = $reply -replace 'client_login_password=\S+', 'client_login_password=<redacted>'
    throw "The server did not return a replacement password. Reply: $safe"
}
$newPw = Convert-FromTS3Escape $Matches[1]
Write-Output "Server issued a replacement, $($newPw.Length) characters."

$q2 = Connect-Query
$q2.Writer.WriteLine("login client_login_name=$user client_login_password=$newPw")
$ok = (Read-Until $q2.Reader) -match 'error id=0'
if ($ok) { $q2.Writer.WriteLine('quit') }
$q2.Client.Close()
if (-not $ok) { throw 'The replacement did not authenticate. It was NOT stored.' }
Write-Output 'Replacement authenticates.'

# Split the reference into an item and a field assignment for op item edit.
if ($PasswordRef -notmatch '^op://([^/]+)/([^/]+)/(.+)$') {
    throw "PasswordRef is not a usable secret reference: $PasswordRef"
}
$vault = $Matches[1]; $item = $Matches[2]; $field = $Matches[3] -replace '/', '.'
op item edit $item --vault $vault "$field[password]=$newPw" --format json | Out-Null
Write-Output 'Stored the replacement.'

if ((op read $PasswordRef) -ne $newPw) { throw 'Stored value does not match what the server issued.' }
Write-Output 'Readback matches the server value.'

$q3 = Connect-Query
$q3.Writer.WriteLine("login client_login_name=$user client_login_password=$oldPw")
$oldStillWorks = (Read-Until $q3.Reader) -match 'error id=0'
if ($oldStillWorks) { $q3.Writer.WriteLine('quit') }
$q3.Client.Close()

if ($oldStillWorks) { Write-Warning 'The OLD password still authenticates.' }
else { Write-Output 'Old password is rejected. Rotation complete.' }

$newPw = $null; $oldPw = $null
Remove-Variable newPw, oldPw -ErrorAction SilentlyContinue
