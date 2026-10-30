# Enable RDP with NLA on win11-dev, limited to Jedi PC in Windows Firewall. Run elevated.
Set-ItemProperty 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name fDenyTSConnections -Value 0
Set-ItemProperty 'HKLM:\System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp' -Name UserAuthentication -Value 1
Enable-NetFirewallRule -DisplayGroup 'Remote Desktop'
Get-NetFirewallRule -DisplayGroup 'Remote Desktop' | Where-Object Direction -eq Inbound | Set-NetFirewallRule -RemoteAddress 192.168.50.241
