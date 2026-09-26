# S01 Popup Automation and Fleet Verification

**Created:** 2026-07-31  
**Last updated:** 2026-07-31

**Capture time:** 2026-07-31 10:06 EDT  
**Targets:** Galaxy five-node cluster  
**Mechanism:** Windows PowerShell, WSL Bash, and SSH Manager

## Local Fixture Test

```powershell
wsl.exe -- bash -lc "cd '/mnt/d/Documents/Homelab' && bash 'Infrastructure/Compute/Galaxy/Tests/test-disable-proxmox-subscription-popup.sh'"
```

```text
proxmox-widget-toolkit fixture: popup patch applied
proxmox-widget-toolkit fixture: popup patch already present
subscription popup patch tests passed
proxmox-widget-toolkit fixture: unsupported subscription-check layout
Exit code: 0
```

## Fleet Read-Back

I ran this read-only command through SSH Manager on Grey, Purple, Blue, and Red. I sent the same command to Green through Grey's key-only SSH path.

```bash
f=/usr/share/javascript/proxmox-widget-toolkit/proxmoxlib.js
s=/usr/local/sbin/disable-proxmox-subscription-popup
host=$(hostname)
sha=$(sha256sum "$s" | cut -d' ' -f1)
stock=$(grep -Foc "res.data.status.toLowerCase() !== 'active'" "$f" || true)
patched=$(grep -Foc "res.data.status.toLowerCase() == 'NoMoreNagging'" "$f" || true)
proxy=$(systemctl is-active pveproxy)
http=$(curl -k -s -o /dev/null -w '%{http_code}' https://127.0.0.1:8006/api2/json/version)
printf 'host=%s script_sha256=%s stock=%s patched=%s pveproxy=%s api_http=%s\n' "$host" "$sha" "$stock" "$patched" "$proxy" "$http"
```

```text
host=grey-server script_sha256=78997493747df685c1851710e0e6a1b6eb5b672273921c37800c28c9ff3309d5 stock=0 patched=2 pveproxy=active api_http=401
host=purple-server script_sha256=78997493747df685c1851710e0e6a1b6eb5b672273921c37800c28c9ff3309d5 stock=0 patched=2 pveproxy=active api_http=401
host=blue-server script_sha256=78997493747df685c1851710e0e6a1b6eb5b672273921c37800c28c9ff3309d5 stock=0 patched=2 pveproxy=active api_http=401
host=red-server script_sha256=78997493747df685c1851710e0e6a1b6eb5b672273921c37800c28c9ff3309d5 stock=0 patched=2 pveproxy=active api_http=401
host=green-server script_sha256=78997493747df685c1851710e0e6a1b6eb5b672273921c37800c28c9ff3309d5 stock=0 patched=2 pveproxy=active api_http=401
Exit code: 0 on every host
```

