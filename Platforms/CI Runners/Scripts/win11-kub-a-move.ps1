# One-shot readdress of win11-dev onto KUB-A. Register as a SYSTEM scheduled task,
# start it, then retag the VM's net0 from 40 to 82 within 15 seconds (see the runbook).
Start-Sleep 15
$if = 'Ethernet'
Set-NetIPInterface -InterfaceAlias $if -AddressFamily IPv4 -Dhcp Disabled
Get-NetIPAddress -InterfaceAlias $if -AddressFamily IPv4 -ErrorAction SilentlyContinue | Remove-NetIPAddress -Confirm:$false
Get-NetRoute -InterfaceAlias $if -AddressFamily IPv4 -DestinationPrefix 0.0.0.0/0 -ErrorAction SilentlyContinue | Remove-NetRoute -Confirm:$false
New-NetIPAddress -InterfaceAlias $if -IPAddress 192.168.82.11 -PrefixLength 24 -DefaultGateway 192.168.82.1 | Out-Null
Set-DnsClientServerAddress -InterfaceAlias $if -ServerAddresses 192.168.82.1
Start-Sleep 10
Set-NetConnectionProfile -InterfaceAlias $if -NetworkCategory Private -ErrorAction SilentlyContinue
"done $(Get-Date -Format o)" | Out-File C:\ProgramData\netmove.log
