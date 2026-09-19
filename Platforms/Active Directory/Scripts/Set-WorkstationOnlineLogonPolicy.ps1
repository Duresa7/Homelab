#Requires -Modules GroupPolicy
[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$Domain = 'ad.alphasecunited.com',
    [string]$Server = 'HQ-DC01.ad.alphasecunited.com',
    [string]$TargetOU = 'OU=Workstations,DC=ad,DC=alphasecunited,DC=com'
)

$ErrorActionPreference = 'Stop'
$name = 'C-WKS-OnlineLogon'
$gpoArgs = @{ Domain = $Domain; Server = $Server }

if (-not $PSCmdlet.ShouldProcess($TargetOU, "Apply ${name}: require online domain-password sign-in and exclude alternative sign-in providers")) {
    return
}

$gpo = Get-GPO -All @gpoArgs | Where-Object DisplayName -eq $name
if (-not $gpo) {
    $gpo = New-GPO -Name $name -Comment 'Domain workstation sign-in requires a reachable domain controller. Local recovery accounts remain available.' @gpoArgs
}
$gpo.GpoStatus = 'UserSettingsDisabled'

$winlogon = 'HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon'
Set-GPRegistryValue -Guid $gpo.Id -Key $winlogon -ValueName CachedLogonsCount -Type String -Value '0' @gpoArgs | Out-Null
Set-GPRegistryValue -Guid $gpo.Id -Key $winlogon -ValueName ForceUnlockLogon -Type DWord -Value 1 @gpoArgs | Out-Null

# Wait for the network during foreground computer/user policy processing.
Set-GPRegistryValue -Guid $gpo.Id -Key 'HKLM\SOFTWARE\Policies\Microsoft\Windows NT\CurrentVersion\Winlogon' -ValueName SyncForegroundPolicy -Type DWord -Value 1 @gpoArgs | Out-Null

# Existing Hello credentials can still work when new provisioning is disabled.
# Exclude their sign-in providers as well; retain the Windows password provider.
$excludedProviders = @(
    '{cb82ea12-9f71-446d-89e1-8d0924e1256e}' # Convenience PIN
    '{D6886603-9D2F-4EB2-B667-1971041FA96B}' # Windows Hello PIN
    '{8AF662BF-65A0-4D0A-A540-A338A999D36F}' # Face
    '{BEC09223-B018-416D-A0AC-523971B639F5}' # Fingerprint
    '{2135f72a-90b5-4ed3-a7f1-8bb705ac276a}' # Picture password
    '{F8A1793B-7873-4046-B2A7-1F318747F427}' # FIDO security key
) -join ','
Set-GPRegistryValue -Guid $gpo.Id -Key 'HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System' -ValueName ExcludedCredentialProviders -Type String -Value $excludedProviders @gpoArgs | Out-Null
Set-GPRegistryValue -Guid $gpo.Id -Key 'HKLM\SOFTWARE\Policies\Microsoft\PassportForWork' -ValueName Enabled -Type DWord -Value 0 @gpoArgs | Out-Null
Set-GPRegistryValue -Guid $gpo.Id -Key 'HKLM\SOFTWARE\Policies\Microsoft\Windows\System' -ValueName AllowDomainPINLogon -Type DWord -Value 0 @gpoArgs | Out-Null
Set-GPRegistryValue -Guid $gpo.Id -Key 'HKLM\SOFTWARE\Policies\Microsoft\Windows\System' -ValueName BlockDomainPicturePassword -Type DWord -Value 1 @gpoArgs | Out-Null

$link = (Get-GPInheritance -Target $TargetOU @gpoArgs).GpoLinks | Where-Object GpoId -eq $gpo.Id
if ($link) {
    Set-GPLink -Guid $gpo.Id -Target $TargetOU -LinkEnabled Yes @gpoArgs | Out-Null
} else {
    New-GPLink -Guid $gpo.Id -Target $TargetOU -LinkEnabled Yes @gpoArgs | Out-Null
}

[pscustomobject]@{
    Policy = $name
    TargetOU = $TargetOU
    Registry = @(Get-GPRegistryValue -Guid $gpo.Id -Key $winlogon @gpoArgs | Select-Object ValueName, Value, Type)
    WaitForNetwork = (Get-GPRegistryValue -Guid $gpo.Id -Key 'HKLM\SOFTWARE\Policies\Microsoft\Windows NT\CurrentVersion\Winlogon' -ValueName SyncForegroundPolicy @gpoArgs).Value
    ExcludedCredentialProviders = $excludedProviders
}
