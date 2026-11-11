$ErrorActionPreference = 'Stop'
$RecType = '{de94bba4-06d1-4d40-a16a-bfd50179d6ac}'
$c = Get-Partition -DriveLetter C
if (@(Get-Partition -DiskNumber $c.DiskNumber | Where-Object GptType -eq $RecType).Count -ne 0) { throw 'Recovery partition already present' }
$offKB = ($c.Offset + $c.Size) / 1KB
"select disk $($c.DiskNumber)`r`ncreate partition primary size=1024 offset=$offKB id=$($RecType.Trim('{}'))`r`nformat quick fs=ntfs label=`"Windows RE tools`"`r`ngpt attributes=0x8000000000000001" | Set-Content -Encoding ASCII C:\Windows\Temp\dp2.txt
diskpart /s C:\Windows\Temp\dp2.txt
Remove-Item C:\Windows\Temp\dp2.txt
'--- reagentc /enable'; reagentc /enable
reagentc /info | Select-String 'status|location'
$parts = Get-Partition -DiskNumber $c.DiskNumber
$parts | Select-Object PartitionNumber, Offset, Size, GptType | Format-Table -AutoSize | Out-String
$maxEnd = ($parts | ForEach-Object { $_.Offset + $_.Size } | Measure-Object -Maximum).Maximum
"maxEnd=$maxEnd"
