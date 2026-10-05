# Explicit Encryption Keys

**Created:** 2026-10-05  
**Last updated:** 2026-10-05

**Status:** Complete  
**Date:** 2026-10-05

Sure's provider settings showed "Encryption keys missing" and told me to configure explicit Active Record encryption keys before saving provider credentials. I set them explicitly, found that nothing had been encrypted until then, and encrypted the existing rows with Sure's own backfill task. No provider credentials had been saved at any point.

## What I found

Sure 0.7.5-hotfix.1 has two separate checks. `ActiveRecordEncryptionConfig.ready?` is true whenever Rails holds keys, including the keys the self-hosted initializer derives from `SECRET_KEY_BASE`. The models' `encrypts` declarations are gated by `Encryptable.encryption_ready?`, which calls `explicitly_configured?`, and that is true only when the three environment variables or Rails credentials are set. With derived keys alone, Rails had keys but no model used them. The [deployment record](Deployment%20-%202026-10-05.md) had read `ready?` as proof of encryption, and that conclusion was wrong.

## Change

| Step | Action and observed result |
|---|---|
| Fingerprint | I hashed each runtime key inside `sure-web` and kept the first 12 hex characters: primary `6613f776f769`, deterministic `8c002eb9e4fc`, salt `f148fea15fca`. |
| Keys | On the host I derived the same three values from `SECRET_KEY_BASE`, exactly as the initializer does, and appended them to `.env` as `ACTIVE_RECORD_ENCRYPTION_PRIMARY_KEY`, `..._DETERMINISTIC_KEY` and `..._KEY_DERIVATION_SALT`. Their fingerprints matched the runtime keys. `.env` stayed mode `0600` and no value was printed. |
| Compose | I added the three variables to the Rails environment block with `:?` guards. The host and repository copies matched at SHA-256 prefix `3beb3b712d167a6b`. `docker compose up -d` recreated `web` and `worker`. The startup warning stopped, and `explicitly_configured?` returned true with the same fingerprints. |
| Failure | A fresh HTTPS login then returned 422. In PostgreSQL the email column still held plaintext. Now that `User` encrypts `email` deterministically, Sure looked the address up by its encrypted form and found no match. |
| Recovery | I used Sure's documented path. A temporary `docker-compose.override.yml` set `ACTIVE_RECORD_ENCRYPTION_SUPPORT_UNENCRYPTED_DATA=true` for `web` and `worker`. A dry run of `security:backfill_encryption` processed 1 user and 4 sessions with 0 failures, and the real run updated 1 user and 4 sessions with 0 failures. |
| Cleanup | I deleted the override and recreated `web` and `worker`. The compatibility variable was unset inside `sure-web`. |

## Verification

In PostgreSQL the user's email column now holds ciphertext rather than plaintext, and the first and last name columns are ciphertext as well. Rails decrypted the email and found the user by it. A fresh HTTPS login with the standard application account returned 302 to `/`, and the authenticated root returned 200. Reading every encrypted attribute on every record checked 10 fields, and none were unreadable. The startup log showed no encryption warning.

The commands ran over SSH from `ubuntu-dev`, and their output is summarized above. No transcript was retained.

## Open

The three keys must never change. Keeping them as explicit values means a future change to `SECRET_KEY_BASE` no longer alters them.
