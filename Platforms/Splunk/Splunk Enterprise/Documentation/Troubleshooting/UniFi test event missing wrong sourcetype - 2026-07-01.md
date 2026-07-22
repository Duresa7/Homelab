# UniFi test event "missing": wrong sourcetype

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Symptom:** after sending a UniFi test event, `sourcetype=sc4s:events "starting up"` still didn't show it.

**Cause:** `sc4s:events` is SC4S's **own internal** log (its startup/health messages), not the data it forwards. UniFi data arrives as `sourcetype=cef`.

**Fix:** I searched the right place:
```spl
index=* sourcetype!=sc4s:events earliest=-60m | stats count by index sourcetype host sc4s_vendor sc4s_fromhostip
index=* sourcetype=cef Ubiquiti
```
The UniFi events showed up immediately (`sourcetype=cef`, `sc4s_fromhostip=192.168.70.1`).
