# `splunk: command not found` after "installing"

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Symptom**
```
sudo /opt/splunk/bin/splunk enable boot-start ...
sudo: /opt/splunk/bin/splunk: command not found
```

**Cause:** a red herring caused by #1. Because the `rpm -i` had failed, Splunk was never unpacked. `/opt/splunk` existed only because my `useradd -m -d /opt/splunk splunk` had created it as the service account's (empty) home directory, so it *looked* installed but had no binaries.

**Fix:** resolved itself once the `sudo rpm -i` in #1 succeeded and populated `/opt/splunk`.
