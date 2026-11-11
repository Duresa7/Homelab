$ErrorActionPreference = 'Stop'
$T = [int64]__TARGET__
$RecType = '{de94bba4-06d1-4d40-a16a-bfd50179d6ac}'
$R = 1GB; $tail = 1MB
$c = Get-Partition -DriveLetter C
$rec = @(Get-Partition -DiskNumber $c.DiskNumber | Where-Object GptType -eq $RecType)
$newC = $T - $c.Offset - $R - $tail
$min = (Get-PartitionSupportedSize -DriveLetter C).SizeMin
"C offset=$($c.Offset) size=$($c.Size) newC=$newC min=$min recoveryParts=$($rec.Count)"
if ($newC -lt ($min + 8GB)) { throw "Target too small: newC=$newC min=$min" }
if ($rec.Count -ne 1) { throw "Expected one recovery partition, found $($rec.Count)" }
if ($rec[0].Offset -lt $c.Offset) { throw 'Recovery partition is not after C:' }
$recNum = $rec[0].PartitionNumber
'--- reagentc /disable'; reagentc /disable
if (-not (Test-Path 'C:\Windows\System32\Recovery\Winre.wim')) { throw 'Winre.wim was not staged to C:' }
"--- delete recovery partition $recNum"
"select disk $($c.DiskNumber)`r`nselect partition $recNum`r`ndelete partition override" | Set-Content -Encoding ASCII C:\Windows\Temp\dp1.txt
diskpart /s C:\Windows\Temp\dp1.txt
if (@(Get-Partition -DiskNumber $c.DiskNumber | Where-Object GptType -eq $RecType).Count -ne 0) { throw 'Recovery partition still present' }
'--- shrink C:'
Resize-Partition -DriveLetter C -Size $newC
$c = Get-Partition -DriveLetter C
if ($c.Size -ne $newC) { throw "C: size is $($c.Size), expected $newC" }
$offKB = ($c.Offset + $c.Size) / 1KB
'--- create recovery partition'
"select disk $($c.DiskNumber)`r`ncreate partition primary size=1024 offset=$offKB id=$($RecType.Trim("{}"))`r`nformat quick fs=ntfs label=`"Windows RE tools`"`r`ngpt attributes=0x8000000000000001" | Set-Content -Encoding ASCII C:\Windows\Temp\dp2.txt
diskpart /s C:\Windows\Temp\dp2.txt
'--- reagentc /enable'; reagentc /enable
reagentc /info | Select-String 'status|location'
Remove-Item C:\Windows\Temp\dp1.txt, C:\Windows\Temp\dp2.txt -ErrorAction SilentlyContinue
$parts = Get-Partition -DiskNumber $c.DiskNumber
$parts | Select-Object PartitionNumber, Offset, Size, GptType | Format-Table -AutoSize | Out-String
$maxEnd = ($parts | ForEach-Object { $_.Offset + $_.Size } | Measure-Object -Maximum).Maximum
"maxEnd=$maxEnd target=$T fits=$($maxEnd -le ($T - $tail))"
