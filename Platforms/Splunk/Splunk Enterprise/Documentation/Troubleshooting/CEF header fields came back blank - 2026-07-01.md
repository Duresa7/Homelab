# CEF header fields came back blank

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Symptom:** `... | table device_vendor device_product signature name severity` produced rows with only `_time` filled; all CEF columns blank. It raised a false worry that the CEF add-on wasn't working.

**Cause:** two things: (a) I had guessed the field names and they didn't match, and (b) **SC4S already parses the CEF at ingest**. The header vendor/product land as `sc4s_vendor` / `sc4s_product`, and the extension keys as `UNIFI*` fields. The `cefutils` (CEF Extraction Add-on) was installed and enabled but doesn't need to add anything.

**Fix:** I listed the real fields and used them:
```spl
index=netops sourcetype=cef | head 1 | fieldsummary | table field
index=netops sourcetype=cef | table _time sc4s_vendor sc4s_product UNIFIhost UNIFIadmin msg
```

SC4S performs the CEF parsing in this deployment. The search-head add-on remains useful for future CIM normalization, but it isn't required to expose `sc4s_*` or `UNIFI*` fields.
