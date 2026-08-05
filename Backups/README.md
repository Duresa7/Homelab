# Backups

**Created:** 2026-08-05  
**Last updated:** 2026-08-05

This folder holds config files I copied off a host before editing them. It exists so a host does not have to keep the copy.

## How a file gets here

1. I copy the file on the host before the edit, because an edit I cannot reverse is not one I want to make blind.
2. Once the new config works and I have verified it, I check the copy for withheld values and redact them.
3. I commit the redacted copy here.
4. **Then I delete the copy from the host.** The host keeps nothing.

The change record for that work says the copy was made, where it landed, and that the host copy was removed.

## What does not belong here

A tracked file under a platform's `Configuration/` is the configuration a service actually reads. That is a versioned reference, not a backup, and it is never moved or deleted by this process. If you are looking for what a service runs today, read its `Configuration/` folder, not this one.

This is also not a home for hypervisor snapshots or disk images. I keep none, other than on the Kasm hosts, where a rollback point is part of what that lab is for.

## Naming

`<hostname>-<original filename>-<YYYY-MM-DD>`, so `monitor-01-docker-compose-2026-08-05.yml`. The date is the day I took the copy.

## Redaction is not optional

**This folder is published.** A config file is the single most likely place for a token, a password, or a key to reach the public repository by accident, because the sensitive part is usually one line in a file that is otherwise dull. Read the whole file before committing it, not a diff of it.

Withheld: credentials, API tokens, keys, my WAN address, MAC addresses, drive serials and WWNs, and tunnel and relay identifiers. A scrub cannot unpublish what a push already sent, so the check happens before the commit or not at all.
