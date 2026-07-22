# SSH Deploy Required sudo on red-server

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

## Symptom

The SSH Manager file-deploy operation copied all three NUT files to Grey but stopped before replacing the stock files on Red.

## Exact Error

`Deployment failed: copy failed: sh: 1: sudo: not found`

## Failed Attempts

I made one `ssh_deploy` attempt for Red's `nut.conf`, `ups.conf`, and `upsd.conf`. I didn't repeat the same method after the common error identified its dependency.

## Hypotheses

The deploy wrapper called `sudo` even though the configured SSH identity already logs in as root. Proxmox didn't have a `sudo` binary because it wasn't needed for that root-only path.

## Tests

I confirmed the Red SSH target used root and that the original NUT files remained in place. The same source files uploaded successfully to explicit paths under `/root`.

## Root Cause

The helper's privileged-copy path required `sudo`; Red didn't provide it.

## Corrective Action

I uploaded each file to an explicit `/root/peanut-*.new` path, then ran `install -o root -g root -m 0644` for `nut.conf` and `install -o root -g nut -m 0640` for `ups.conf` and `upsd.conf`. I removed only the three staging paths after `readlink -f` matched each expected `/root/peanut-*.new` path. The [configuration correction transcript](../../Evidence/PeaNUT%20UPS%20Dashboard%20Deployment%20-%202026-07-22/Logs/S03-NUT-Configuration-Corrections.txt) retains the structured error, exact correction command, output, and exit status.

## Verification

`/etc/nut/nut.conf` was `root:root 0644`; `ups.conf` and `upsd.conf` were `root:nut 0640`. The `ups01` driver and NUT server later reached `active`, and `upsc ups01@localhost` returned live data in the [Red verification transcript](../../Evidence/PeaNUT%20UPS%20Dashboard%20Deployment%20-%202026-07-22/Logs/S06-NUT-Verification-red-server.txt).
