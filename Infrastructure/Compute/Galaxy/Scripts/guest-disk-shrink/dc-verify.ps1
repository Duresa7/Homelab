Get-Service NTDS, DNS, Netlogon, KDC, W32Time, DFSR | ForEach-Object { "$($_.Name)=$($_.Status)" }
'--- dcdiag (failures only)'
dcdiag /q /test:Services /test:Advertising /test:FsmoCheck /test:NetLogons /test:SysVolCheck /test:Replications /test:KnowsOfRoleHolders
"dcdiag exit=$LASTEXITCODE"
'--- repadmin /showrepl /csv summary'
repadmin /showrepl $env:COMPUTERNAME /csv | ConvertFrom-Csv | Select-Object 'Naming Context','Source DSA','Number of Failures','Last Success Time' | Format-Table -AutoSize | Out-String -Width 200
