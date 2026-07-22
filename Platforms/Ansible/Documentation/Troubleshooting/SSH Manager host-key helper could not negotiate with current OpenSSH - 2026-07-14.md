# SSH Manager host-key helper could not negotiate with current OpenSSH

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Investigated:** 2026-07-14

The helper returned a key-exchange compatibility error involving the newer `sntrup761` method, so I did not use it to accept keys automatically. Instead, authenticated SSH Manager commands read each target's existing ED25519 host-key fingerprint, and I required the controller-side `ssh-keyscan` result to match before enrollment.
