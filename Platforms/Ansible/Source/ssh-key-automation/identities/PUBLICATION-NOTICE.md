# SSH Identity Notice

**Created:** 2026-07-15  
**Last updated:** 2026-07-25

The public project uses `_new-device-template.yml.example` in place of environment-specific identity files. Each deployed file supplies a public key, fingerprint, identity label, & approved target list. An identity may also select a different POSIX account and authorized-keys path or attach OpenSSH key restrictions without changing the other identities.

Copy the template when adding an identity.
