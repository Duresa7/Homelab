# Syncthing TODO

**Created:** 2026-07-22  
**Last updated:** 2026-07-27

The [2026-07-27 sync comparison](Obsidian%20Sync%20Alternatives%20-%202026-07-27.md) recommends keeping Syncthing for a desktop-first vault. Every free or self-hosted alternative still needs a client or Obsidian plug-in on each device. Self-hosted LiveSync with CouchDB becomes the first alternative to test if iPhone or iPad editing becomes a normal requirement.

## Open Items

- [ ] Pair the laptop with folder ID `obsidian-the-vault` by following the [device-addition runbook](Adding%20a%20Device.md), preserve a local vault copy, apply the two workspace-file exclusions, & compare hashes after the first synchronization.
- [ ] Add a recurring independent backup for `D:\Documents\Vault-DK\The Vault`; staggered Syncthing versions don't protect against loss of `docker-main` or its `/data` filesystem.
