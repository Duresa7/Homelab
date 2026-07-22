# SC4S crash-loop: port 1514 already in use

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Symptom:** container up but syslog-ng restarting endlessly:
```
Error binding socket; addr='AF_INET(0.0.0.0:1514)', error='Address in use (98)'
syslog-ng failed to start; exiting...
```

**Diagnosis:** I found who held the port:
```bash
sudo ss -lntup | grep -w 1514
# tcp LISTEN 0 128 0.0.0.0:1514 ... users:(("splunkd",pid=...))
```
`splunkd` itself was listening on 1514, a leftover **Splunk TCP data input** from my earlier attempt to receive UniFi directly (the exact "syslog straight into splunkd" anti-pattern that SC4S replaces).

**Fix:** I deleted that input (**Settings → Data Inputs → TCP → port 1514 → Delete**), then ran `sudo systemctl restart sc4s`. SC4S bound 1514 cleanly and the HEC connection test succeeded.
