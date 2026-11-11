"Host: $env:COMPUTERNAME  Disk0: $([math]::Round((Get-Disk 0).Size/1GB,2)) GiB  Health: $((Get-Disk 0).HealthStatus)"
Get-Volume -DriveLetter C | ForEach-Object { "C: size=$([math]::Round($_.Size/1GB,2)) GiB free=$([math]::Round($_.SizeRemaining/1GB,2)) GiB health=$($_.HealthStatus)" }
"Repair-Volume scan: $(Repair-Volume -DriveLetter C -Scan)"
reagentc /info | Select-String 'status|location'
Get-Partition -DiskNumber 0 | Select-Object PartitionNumber, Offset, Size, GptType | Format-Table -AutoSize | Out-String
$cs = Get-CimInstance Win32_ComputerSystem
"Domain=$($cs.Domain) PartOfDomain=$($cs.PartOfDomain)"
"Errors (disk/ntfs/volmgr) since boot: " + @(Get-WinEvent -FilterHashtable @{LogName='System'; Level=1,2; StartTime=(Get-CimInstance Win32_OperatingSystem).LastBootUpTime} -ErrorAction SilentlyContinue | Where-Object { $_.ProviderName -match 'disk|Ntfs|volmgr|partmgr|stor' }).Count
