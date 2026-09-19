# Run elevated on the workstation. This reads configuration and tests the current
# secure channel; it does not simulate an offline password sign-in or unlock.
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$computer = Get-CimInstance Win32_ComputerSystem
$winlogon = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon'
$foreground = Get-ItemProperty 'HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\CurrentVersion\Winlogon' -ErrorAction SilentlyContinue
$netlogon = Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Services\Netlogon\Parameters'
$system = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System'
$hello = Get-ItemProperty 'HKLM:\SOFTWARE\Policies\Microsoft\PassportForWork' -ErrorAction SilentlyContinue
$logon = Get-ItemProperty 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\System' -ErrorAction SilentlyContinue
$applied = @(Get-CimInstance -Namespace root\rsop\computer -ClassName RSOP_GPO | Where-Object name -eq 'C-WKS-OnlineLogon').Count -eq 1
$providers = @($system.ExcludedCredentialProviders -split ',')
$expectedProviders = @(
    '{cb82ea12-9f71-446d-89e1-8d0924e1256e}', '{D6886603-9D2F-4EB2-B667-1971041FA96B}',
    '{8AF662BF-65A0-4D0A-A540-A338A999D36F}', '{BEC09223-B018-416D-A0AC-523971B639F5}',
    '{2135f72a-90b5-4ed3-a7f1-8bb705ac276a}', '{F8A1793B-7873-4046-B2A7-1F318747F427}'
)
$alternativeProvidersExcluded = @($expectedProviders | Where-Object { $_ -notin $providers }).Count -eq 0
$passwordProviderAvailable = '{60b78e88-ead8-445c-9cfd-0b87f74ea6cd}' -notin $providers
$channel = Test-ComputerSecureChannel
$result = [pscustomobject]@{
    ReadAt = (Get-Date).ToString('o')
    Computer = $env:COMPUTERNAME
    Domain = $computer.Domain
    PartOfDomain = $computer.PartOfDomain
    SecureChannel = $channel
    CachedLogonsCount = $winlogon.CachedLogonsCount
    ForceUnlockLogon = $winlogon.ForceUnlockLogon
    SyncForegroundPolicy = $foreground.SyncForegroundPolicy
    NetlogonAutomatic = (Get-Service Netlogon).StartType -eq 'Automatic'
    MachinePasswordChangesEnabled = $netlogon.DisablePasswordChange -ne 1
    AlternativeProvidersExcluded = $alternativeProvidersExcluded
    PasswordProviderAvailable = $passwordProviderAvailable
    HelloProvisioningDisabled = $hello.Enabled -eq 0
    ConveniencePinDisabled = $logon.AllowDomainPINLogon -eq 0
    PicturePasswordDisabled = $logon.BlockDomainPicturePassword -eq 1
    PolicyApplied = $applied
    Pass = $computer.PartOfDomain -and $channel -and
        $winlogon.CachedLogonsCount -eq '0' -and
        $winlogon.ForceUnlockLogon -eq 1 -and
        $foreground.SyncForegroundPolicy -eq 1 -and
        (Get-Service Netlogon).StartType -eq 'Automatic' -and
        $netlogon.DisablePasswordChange -ne 1 -and
        $alternativeProvidersExcluded -and $passwordProviderAvailable -and
        $hello.Enabled -eq 0 -and $logon.AllowDomainPINLogon -eq 0 -and
        $logon.BlockDomainPicturePassword -eq 1 -and $applied
}
$result | ConvertTo-Json -Compress
if (-not $result.Pass) { exit 1 }
