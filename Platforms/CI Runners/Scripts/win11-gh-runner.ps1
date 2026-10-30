# Create the gh-runner local admin on win11-dev and move every runner service to it.
# Run elevated as dkadi. The password arrives as %USERPROFILE%\ghr.txt (copied with scp
# from the password manager) and is deleted on read.
$ErrorActionPreference = 'Stop'
$pwFile = "$env:USERPROFILE\ghr.txt"
$sec = ConvertTo-SecureString ((Get-Content -Raw $pwFile).Trim()) -AsPlainText -Force
Remove-Item -Force $pwFile
if (-not (Get-LocalUser -Name gh-runner -ErrorAction SilentlyContinue)) {
  New-LocalUser -Name gh-runner -Password $sec -FullName 'GitHub Actions runner' -Description 'Runs the GitHub Actions runner services' -PasswordNeverExpires -UserMayNotChangePassword | Out-Null
}
Add-LocalGroupMember -Group Administrators -Member gh-runner -ErrorAction SilentlyContinue
$sid = (Get-LocalUser gh-runner).SID.Value
# User rights: allow service logon, deny console and RDP logon.
$cfg = "$env:TEMP\ur.inf"; $db = "$env:TEMP\ur.sdb"
secedit /export /cfg $cfg /areas USER_RIGHTS | Out-Null
$c = Get-Content $cfg
function Add-Right($lines, $name, $sid) {
  $i = [array]::FindIndex([string[]]$lines, [Predicate[string]]{ param($l) $l -like "$name *" })
  if ($i -ge 0) { if ($lines[$i] -notmatch [regex]::Escape($sid)) { $lines[$i] = $lines[$i] + ",*$sid" }; return ,$lines }
  $j = [array]::IndexOf([string[]]$lines, '[Privilege Rights]')
  $l = [System.Collections.Generic.List[string]]$lines; $l.Insert($j + 1, "$name = *$sid"); return ,$l.ToArray()
}
foreach ($r in 'SeServiceLogonRight','SeDenyInteractiveLogonRight','SeDenyRemoteInteractiveLogonRight') { $c = Add-Right $c $r $sid }
Set-Content -Path $cfg -Value $c -Encoding Unicode
secedit /configure /db $db /cfg $cfg /areas USER_RIGHTS /quiet | Out-Null
Remove-Item -Force $cfg, $db -ErrorAction SilentlyContinue
$plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec))
foreach ($svc in Get-CimInstance Win32_Service -Filter "Name like 'actions.runner.%'") {
  $res = Invoke-CimMethod -InputObject $svc -MethodName Change -Arguments @{ StartName = '.\gh-runner'; StartPassword = $plain }
  "$($svc.Name): Change returned $($res.ReturnValue)"
  Restart-Service -Name $svc.Name
}
$plain = $null
Start-Sleep 8
Get-CimInstance Win32_Service -Filter "Name like 'actions.runner.%'" | Select-Object Name,StartName,State | Format-List
