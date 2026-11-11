$v = Get-BitLockerVolume -MountPoint C:
"VolumeStatus=$($v.VolumeStatus) Protection=$($v.ProtectionStatus) Method=$($v.EncryptionMethod)"
$v.KeyProtector | ForEach-Object { "Protector: $($_.KeyProtectorType)" }
"Domain: $((Get-CimInstance Win32_ComputerSystem).Domain)"
