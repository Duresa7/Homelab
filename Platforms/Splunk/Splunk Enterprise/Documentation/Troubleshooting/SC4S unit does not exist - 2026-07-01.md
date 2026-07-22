# SC4S unit does not exist

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Symptom**
```
sudo systemctl enable --now sc4s
Failed to enable unit: Unit sc4s.service does not exist
```

**Cause:** I had created the env file and directories but never written the systemd unit file itself, so systemd had nothing to enable.

**Fix:** I created `/lib/systemd/system/sc4s.service` from the official SC4S Podman template, then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now sc4s
```
