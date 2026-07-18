# 🔧 Splunk SIEM: Troubleshooting Log

**Created:** 2026-07-01  
**Last updated:** 2026-07-17

Every problem hit during the build, what caused it, and how it was fixed. Companion to [Build-Log.md](Build-Log.md). The build log records *what was done*; this records *what went wrong and the fix*.

## Quick index

| # | Where | Symptom | Root cause | Fix |
|:-:|---|---|---|---|
| 1 | Step 5 | `rpm -i` → transaction lock permission denied | Ran without `sudo` | Re-ran with `sudo` |
| 2 | Step 5 | `splunk: command not found` | Install (#1) had actually failed; `/opt/splunk` was empty | Fixed once #1 succeeded |
| 3 | Step 6 | `Failed to enable unit: sc4s.service does not exist` | Unit file never created | Created `/lib/systemd/system/sc4s.service` |
| 4 | Step 6 | SC4S crash-loop, `0.0.0.0:1514 Address in use` | `splunkd` already listening on 1514 (leftover TCP input) | Deleted the Splunk TCP input |
| 5 | Step 6 | Search returned 0 results | Time range was real-time | Switched to a historical range |
| 6 | Step 6 | UniFi test event "missing" | Searched the wrong sourcetype | Searched `sourcetype=cef` instead |
| 7 | Step 6 | CEF header fields blank | Guessed field names; SC4S already parses CEF | Used real field names |
| 8 | Step 6 | Only `UniFi OS` routed to `netops` | UniFi sends 3 product strings; only 1 key defined | Added all 3 routing keys |

---

## 1. RPM install failed: transaction lock permission denied

**Symptom**
```
warning: splunk-...x86_64.rpm: Header V4 RSA/SHA256 Signature, key ID b3cd4420: NOKEY
error: can't create transaction lock on /usr/lib/sysimage/rpm/.rpm.lock (Permission denied)
```

**Cause:** `rpm -i` was run as the normal user. Installing an RPM writes to the system package database, which requires root.

**Fix:** re-ran with root:
```bash
sudo rpm -i /tmp/splunk-10.4.0-f798d4d49089.x86_64.rpm
```

**Takeaway:** the `NOKEY` warning above the error is unrelated and **benign**: it only means Splunk's GPG signing key isn't imported, so the signature isn't verified. Package installs need root.

---

## 2. `splunk: command not found` after "installing"

**Symptom**
```
sudo /opt/splunk/bin/splunk enable boot-start ...
sudo: /opt/splunk/bin/splunk: command not found
```

**Cause:** a red herring caused by #1. Because the `rpm -i` had failed, Splunk was never unpacked. `/opt/splunk` existed only because `useradd -m -d /opt/splunk splunk` had created it as the service account's (empty) home directory, so it *looked* installed but had no binaries.

**Fix:** resolved automatically once the `sudo rpm -i` in #1 succeeded and populated `/opt/splunk`.

**Takeaway:** "directory exists but binary missing" usually means an earlier install step silently failed. Scroll back and check.

---

## 3. SC4S unit does not exist

**Symptom**
```
sudo systemctl enable --now sc4s
Failed to enable unit: Unit sc4s.service does not exist
```

**Cause:** the env file and directories were created, but the systemd unit file itself was never written, so systemd had nothing to enable.

**Fix:** created `/lib/systemd/system/sc4s.service` from the official SC4S Podman template, then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now sc4s
```

**Takeaway:** SC4S has several moving parts (volume, dirs, `env_file`, **unit file**). Missing the unit file is an easy step to skip.

---

## 4. SC4S crash-loop: port 1514 already in use

**Symptom:** container up but syslog-ng restarting endlessly:
```
Error binding socket; addr='AF_INET(0.0.0.0:1514)', error='Address in use (98)'
syslog-ng failed to start; exiting...
```

**Diagnosis:** found who held the port:
```bash
sudo ss -lntup | grep -w 1514
# tcp LISTEN 0 128 0.0.0.0:1514 ... users:(("splunkd",pid=...))
```
`splunkd` itself was listening on 1514, a leftover **Splunk TCP data input** from an earlier attempt to receive UniFi directly (the exact "syslog straight into splunkd" anti-pattern that SC4S replaces).

**Fix:** deleted that input (**Settings → Data Inputs → TCP → port 1514 → Delete**), then `sudo systemctl restart sc4s`. SC4S bound 1514 cleanly and the HEC connection test succeeded.

**Takeaway:** for "address in use," `ss -lntup | grep <port>` names the culprit process immediately. Also: don't leave splunkd listening on syslog ports when using a dedicated collector.

---

## 5. Search returned 0 results (real-time trap)

**Symptom:** `index=* sourcetype=sc4s:events "starting up"` showed **0 of 0 events**, even though SC4S had clearly started.

**Cause:** the time picker was set to **"All time (real-time)"**. A real-time search only shows events arriving from the moment you run it; the startup event had happened minutes earlier.

**Fix:** switched the time range to a historical window (**Last 24 hours** / **All time**). The events appeared.

**Takeaway:** if you *know* data exists but a search is empty, check for real-time mode first.

---

## 6. UniFi test event "missing": wrong sourcetype

**Symptom:** after sending a UniFi test event, `sourcetype=sc4s:events "starting up"` still didn't show it.

**Cause:** `sc4s:events` is SC4S's **own internal** log (its startup/health messages), not the data it forwards. UniFi data arrives as `sourcetype=cef`.

**Fix:** searched the right place:
```spl
index=* sourcetype!=sc4s:events earliest=-60m | stats count by index sourcetype host sc4s_vendor sc4s_fromhostip
index=* sourcetype=cef Ubiquiti
```
The UniFi events showed up immediately (`sourcetype=cef`, `sc4s_fromhostip=192.168.70.1`).

**Takeaway:** `sc4s:events` = SC4S talking about itself; your device data is under its own sourcetype (`cef` here).

---

## 7. CEF header fields came back blank

**Symptom:** `... | table device_vendor device_product signature name severity` produced rows with only `_time` filled; all CEF columns blank. Raised a false worry that the CEF add-on wasn't working.

**Cause:** two things: (a) the field names were guessed and didn't match, and (b) **SC4S already parses the CEF at ingest**. The header vendor/product land as `sc4s_vendor` / `sc4s_product`, and the extension keys as `UNIFI*` fields. The `cefutils` (CEF Extraction Add-on) was installed and enabled but doesn't need to add anything.

**Fix:** listed the real fields and used them:
```spl
index=netops sourcetype=cef | head 1 | fieldsummary | table field
index=netops sourcetype=cef | table _time sc4s_vendor sc4s_product UNIFIhost UNIFIadmin msg
```

**Takeaway:** because SC4S does index-time parsing, the search-head CEF add-on is largely **redundant** here; its only real value is CIM normalization for dashboards/correlation later. Blank columns usually mean wrong field names, not missing data. Confirm with `fieldsummary`.

---

## 8. Only one UniFi product routed to `netops`

**Symptom:** after adding `Ubiquiti_UniFi OS,index,netops` and restarting, `index=netops sourcetype=cef | stats count by sc4s_product` showed **only `UniFi OS`**; ~283 Network + Protect events were still in `main`.

**Diagnosis:** enumerated the actual products arriving:
```spl
index=* sourcetype=cef Ubiquiti | stats count by sc4s_vendor sc4s_product
# UniFi Network = 200, UniFi OS = 59, UniFi Protect = 83
```
With all export categories enabled, UniFi emits **three** `device_product` values. SC4S routes by `device_vendor`_`device_product`, so the single `Ubiquiti_UniFi OS` key matched only 59 events; the rest fell back to `main`.

**Fix:** added a routing line per product to `/opt/sc4s/local/context/splunk_metadata.csv`:
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

**Takeaways**
- SC4S metadata routing keys are **per `device_vendor`_`device_product`:** enumerate real values with `stats count by sc4s_product` rather than assuming.
- Routing changes are **forward-only:** events already indexed in `main` stay there; only new events follow the new rule.
- An **empty `main`** for new CEF is the definitive proof that every product key matches.
