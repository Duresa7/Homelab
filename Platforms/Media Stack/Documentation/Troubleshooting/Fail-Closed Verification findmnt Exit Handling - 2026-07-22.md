# Fail-Closed Verification `findmnt` Exit Handling

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

## Symptom

The first missing-disk verification wrapper exited `1` after it stopped CT 842 & unmounted `/mnt/bindmounts/media-01-hdd`. It stopped before the planned `pct start 842` assertion.

## Exact Error

SSH Manager returned exit `1` with only the capture timestamp on standard output. The container-stop messages were complete on standard error; no destructive command ran after the unmount.

## Hypothesis and Test

I inspected `pct status 842`, both systemd unit states, `findmnt`, the bind-source path, & `pct config 842`. CT 842 was stopped, the mount and automount units were inactive, `/mnt/bindmounts/media-01-hdd/data` was absent, & `mp0` still named that path.

## Root Cause

This assertion used `findmnt` inside a command substitution while the wrapper had `set -e` enabled:

```sh
test -z "$(findmnt -rn -T "$MEDIA_MOUNT" -o SOURCE)"
```

`findmnt` returns exit `1` when no filesystem matches. That was the state the test wanted, but `set -e` terminated the wrapper before `test -z` could evaluate the empty output.

## Correction

I resumed from the inspected stopped state and checked the missing `data` child directly with `test ! -e`. I captured `pct start 842` exit `255`, started the systemd automount, triggered the ext4 mount, & restarted CT 842.

## Verification

The LXC pre-start hook refused the missing bind source. After remount, `/data` resolved to `/dev/sda1`, eight containers ran, & Jellyfin and Gluetun reported healthy. The [S05 evidence transcript](../../Evidence/Media%20Stack%20HDD%20Data%20Migration%20-%202026-07-22/Logs/S05-Fail-Closed-Cleanup-and-Final-Audit-2026-07-22.md) records both the failed wrapper & corrected test.
