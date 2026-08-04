# RPM install failed: transaction lock permission denied

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Symptom**
```
warning: splunk-...x86_64.rpm: Header V4 RSA/SHA256 Signature, key ID b3cd4420: NOKEY
error: can't create transaction lock on /usr/lib/sysimage/rpm/.rpm.lock (Permission denied)
```

**Cause:** I ran `rpm -i` as my normal user. Installing an RPM writes to the system package database, which requires root.

**Fix:** I re-ran it with root:
```bash
sudo rpm -i /tmp/splunk-10.4.0-f798d4d49089.x86_64.rpm
```

The `NOKEY` warning was separate from the permission failure. It reported that the Splunk signing key wasn't imported; the transaction lock failed because the command lacked root permission.
