# Read-only check. Run on HQ-MGT01 after the installer transfer succeeds.
[CmdletBinding()]
param(
    [string]$Path = 'C:\Windows\Temp\Action1-Setup\deployer.exe'
)

$ErrorActionPreference = 'Stop'
if ($env:COMPUTERNAME -ne 'HQ-MGT01') {
    throw 'Run this check on HQ-MGT01.'
}
if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
    throw 'The Deployer installer has not reached the staging path.'
}

$file = Get-Item -LiteralPath $Path
$signature = Get-AuthenticodeSignature -LiteralPath $Path
if ($signature.Status -ne 'Valid') {
    throw "Installer signature is not valid: $($signature.Status)."
}
if ($signature.SignerCertificate.Subject -notmatch '(?i)(?:^|,\s*)(?:CN|O)="?Action1(?: Corporation| Corp\.?| Inc\.?)?"?(?:,|$)') {
    throw 'The valid signature does not identify the expected Action1 publisher. Review before execution.'
}

[pscustomobject]@{
    Computer = $env:COMPUTERNAME
    Bytes = $file.Length
    SHA256 = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
    Signature = $signature.Status.ToString()
    Publisher = $signature.SignerCertificate.Subject
}
