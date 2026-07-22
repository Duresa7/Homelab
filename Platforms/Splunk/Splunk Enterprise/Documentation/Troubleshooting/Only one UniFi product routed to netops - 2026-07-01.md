# Only one UniFi product routed to `netops`

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Symptom:** after adding `Ubiquiti_UniFi OS,index,netops` and restarting, `index=netops sourcetype=cef | stats count by sc4s_product` showed **only `UniFi OS`**; ~283 Network + Protect events were still in `main`.

**Diagnosis:** I enumerated the actual products arriving:
```spl
index=* sourcetype=cef Ubiquiti | stats count by sc4s_vendor sc4s_product
# UniFi Network = 200, UniFi OS = 59, UniFi Protect = 83
```
With all export categories enabled, UniFi emits **three** `device_product` values. SC4S routes by `device_vendor`_`device_product`, so my single `Ubiquiti_UniFi OS` key matched only 59 events; the rest fell back to `main`.

**Fix:** I added a routing line per product to `/opt/sc4s/local/context/splunk_metadata.csv`:
```csv
Ubiquiti_UniFi OS,index,netops
Ubiquiti_UniFi Network,index,netops
Ubiquiti_UniFi Protect,index,netops
```
then `sudo systemctl restart sc4s`.

**Verification:** the clincher was the `main` check coming back empty:
```spl
index=netops sourcetype=cef earliest=-30m | stats count by sc4s_product   # products routing
index=main   sourcetype=cef earliest=-30m | stats count by sc4s_product   # 0 = nothing leaking
```

SC4S routes on each `device_vendor`_`device_product` pair, and the change affects only new events. The empty `main` result for the final 30-minute window showed that all three observed product keys matched.
