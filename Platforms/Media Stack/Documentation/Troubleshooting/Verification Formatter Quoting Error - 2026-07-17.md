# Verification Formatter Quoting Error

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Investigated:** 2026-07-17

## Symptom

Two read-only Python formatters I invoked through nested SSH, `pct exec`, and shell quoting failed:

```text
NameError: name 'ip' is not defined. Did you mean: 'id'?
NameError: name 'source' is not defined
```

## Root Cause

Single-quoted Python dictionary keys were consumed by the enclosing shell quoting layer.

## Correction and Verification

My failed attempts used single-quoted dictionary keys inside an outer single-quoted shell command. I verified the hypothesis by observing that the enclosing shell removed those quotes before Python parsed the script. I rewrote the formatter to assign dictionary values to variables using double-quoted keys before interpolation.

The corrected VPN check returned a provider exit, matching provider-assigned and qBittorrent listening ports, `random_port=False`, `upnp=False`, and qBittorrent's Gluetun container network mode. The corrected Arr health formatter returned the exact messages recorded above. Both corrected commands exited `0`. No container or configuration mutation occurred during the failed formatting attempts.
