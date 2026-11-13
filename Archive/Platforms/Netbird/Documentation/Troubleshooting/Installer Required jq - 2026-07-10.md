# NetBird Installer Required `jq`

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Date:** 2026-07-10  
**Step:** S08

**Symptom and exact error:** The official installer exited `1` before generating configuration:

```text
jq is not installed or not in PATH, please install with your package manager. e.g. sudo apt install jq
installer_exit=1
```

**Investigation:** I checked for the generated `config.yaml` and `docker-compose.yml` and confirmed both absent, proving the failure occurred before partial initialization.

**Corrective action:** I installed Debian's `jq` 1.7 package and reran the official v0.74.3 installer with the Nginx Proxy Manager option.

**Verification:** The second run exited `0`, generated the expected files, and started both NetBird containers.
