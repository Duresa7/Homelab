# Initial audit reported false missing keys and unknown host fingerprints

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Investigated:** 2026-07-14

My first full Mac audit connected to six targets, rejected seven targets whose host fingerprints were not yet trusted by `ansible-01`, and timed out against `edge-01` and `ws-dc-1-main`. The original parser also treated valid key lines as missing because its regular expression was too strict.

I changed the parser to compare the first two whitespace-separated fields, algorithm and encoded key material. For the untrusted targets, I read each host fingerprint through an authenticated SSH Manager session, scanned the same host independently from the controller, and enrolled it only where the SHA256 values matched. My first known-host update attempt failed on incorrect `awk` escaping and made no change; the corrected update was then verified by fingerprint.
