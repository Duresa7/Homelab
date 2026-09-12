# Read-only TCP probes. Open ports do not prove credentials, ADMIN$, or deployment work.
# Dynamic RPC must also be verified during the actual workstation pilot.
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
if ($env:COMPUTERNAME -ne 'HQ-MGT01') {
    throw 'Run these probes on HQ-MGT01 so the source matches the Deployer host.'
}

$checks = @(
    @{ Target = 'HQ-DC01.ad.alphasecunited.com'; Port = 389 }
    @{ Target = 'HQ-DC02.ad.alphasecunited.com'; Port = 389 }
    @{ Target = 'HQ-WS001.ad.alphasecunited.com'; Port = 135 }
    @{ Target = 'HQ-WS001.ad.alphasecunited.com'; Port = 445 }
    @{ Target = 'ObiPC.ad.alphasecunited.com'; Port = 135 }
    @{ Target = 'ObiPC.ad.alphasecunited.com'; Port = 445 }
    @{ Target = 'app.na-2.action1.com'; Port = 443 }
)

foreach ($check in $checks) {
    $client = New-Object System.Net.Sockets.TcpClient
    $connected = $false
    $pending = $null
    try {
        $pending = $client.BeginConnect($check.Target, $check.Port, $null, $null)
        if ($pending.AsyncWaitHandle.WaitOne(3000)) {
            $client.EndConnect($pending)
            $connected = $client.Connected
        }
    }
    catch {
        $connected = $false
    }
    finally {
        $client.Dispose()
        if ($null -ne $pending) { $pending.AsyncWaitHandle.Close() }
    }
    [pscustomobject]@{
        Source = $env:COMPUTERNAME
        Target = $check.Target
        Port = $check.Port
        Connected = $connected
    }
}
