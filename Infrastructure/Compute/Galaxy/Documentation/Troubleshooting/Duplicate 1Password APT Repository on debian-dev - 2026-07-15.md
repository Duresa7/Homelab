# Duplicate 1Password APT Repository on `debian-dev`

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Investigated:** 2026-07-15  
**Owner:** Galaxy VM 102 / `debian-dev`  
**Status:** Resolved

## Symptom

`sudo apt update` succeeded but emitted duplicate `Packages`, translations, DEP-11, and icon target warnings referencing both:

- `/etc/apt/sources.list.d/1password.list`
- `/etc/apt/sources.list.d/1password.sources`

My regression command captured the complete APT output and failed when it matched `configured multiple times.*1password`.

## Root cause and correction

Both entries defined the same AMD64 repository, stable suite, main component, and signing key. The deb822 `.sources` file stated that the 1Password package automatically adds and configures it. The legacy `.list` file was newer, unmanaged, and redundant.

I copied the legacy file to root-only rollback path `/root/apt-source-backups/1password.list.pre-dedup-20260715` and removed it from `sources.list.d`. I left the maintained `.sources` file and `/usr/share/keyrings/1password-archive-keyring.gpg` unchanged.

## Verification

- Two consecutive `apt-get update` executions returned `PASS_NO_DUPLICATE_1PASSWORD_SOURCE` with no warnings.
- The 1Password repository remained reachable.
- `apt-cache policy 1password` reported installed and candidate version `8.12.28` from the retained repository.
- `apt-get check` completed successfully.
