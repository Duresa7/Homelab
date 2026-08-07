# Obsidian Sync Alternatives

**Created:** 2026-07-27  
**Last updated:** 2026-07-27

**Research date:** 2026-07-27  
**Scope:** Free or self-hosted synchronization for one normal Obsidian vault across computers and mobile devices

## Answer

I should keep Syncthing for this vault unless iPhone or iPad access becomes a normal part of my workflow. My current system already gives each computer a full local copy, uses `docker-main` as an always-on peer, encrypts transfers between peers, & keeps received file versions on the server for 90 days. Replacing it now would add a new server or plug-in without removing per-device setup.

Installing Syncthing on every computer isn't a special weakness of Syncthing. Every synchronization method needs code on each device so it can notice a changed file, send it, receive other changes, & write them into the local vault:

| Method | What I install on each device |
|---|---|
| Syncthing | Syncthing or an operating-system wrapper |
| Self-hosted LiveSync | The LiveSync Obsidian community plug-in |
| Remotely Save | The Remotely Save Obsidian community plug-in |
| Nextcloud file sync | The Nextcloud desktop client |
| Git | Git, an Obsidian plug-in, or another Git client |
| Seafile | The Seafile sync client |

The server can't watch a local folder on a computer unless a local program or Obsidian plug-in reports the changes. Another product can hide this step inside Obsidian, but it can't remove it.

## Current Fit

I already run Syncthing 2.1.2 on `docker-main` and Windows. The vault is stored as normal files at `D:\Documents\Vault-DK\The Vault`, while the server copy lives at `/data/syncthing/vaults/the-vault`. This is the right shape for a desktop-first Obsidian vault: every computer works offline, Obsidian reads ordinary local files, & synchronization continues even when Obsidian is closed.

The extra computer setup is one installation, one device-ID exchange, one folder share, & two ignore rules for `workspace.json` and `workspace-mobile.json`. I don't need to install a separate database, publish another HTTPS service, or put credentials into an Obsidian plug-in.

Syncthing preserves both versions when two devices edit the same file before they exchange changes. It renames the older version with a `sync-conflict` suffix and distributes that conflict file to the peers. It doesn't merge Markdown text. I must compare the two files myself.

The server's 90-day staggered versioning is useful, but it isn't a complete backup. Syncthing archives a file when a change from another peer replaces or deletes the server's copy. It can't archive a change made locally on the same peer before that change occurs. Loss of `docker-main` and its `/data` filesystem would also remove the server copy and its versions, so the planned independent vault backup still matters.

## Option Comparison

| Option | Conflicts | Version history | Desktop support | Mobile support | Setup & maintenance | Fit for this vault |
|---|---|---|---|---|---|---|
| Syncthing | Keeps a separate conflict file; manual merge | Per-folder versioning; current server keeps received versions for 90 days | Windows, macOS, & Linux | Android uses a community fork; iOS uses a community client | Low because it is already deployed | Best current choice |
| LiveSync with CouchDB | Automatically merges simple conflicts and prompts for harder ones | Database revisions help with conflicts, but aren't a durable backup | Runs anywhere Obsidian runs | Runs inside Obsidian on Android & iOS | Medium to high; CouchDB, HTTPS, plug-in settings, database backup, & upgrades | Best alternative when mobile matters |
| Remotely Save with WebDAV or S3 | Free version detects conflicts and asks which copy to keep; richer merge handling is paid | Depends on the storage backend; Nextcloud can provide file versions | Runs anywhere Obsidian runs | Supported inside Obsidian on Android & iOS | Medium; plug-in plus WebDAV, Nextcloud, MinIO, or another S3-compatible service | Good simpler mobile option |
| Nextcloud desktop sync | Keeps a local conflicted copy; manual merge | Built-in server file versions | Windows, macOS, & Linux | Official mobile apps provide file access, but direct Obsidian vault use depends on mobile filesystem access | High if deployed only for one vault | Useful only if I also want a general private cloud |
| Git | Three-way merges when possible; manual conflict resolution otherwise | Best history after each commit | Windows, macOS, & Linux | Mobile Obsidian Git support is documented as unstable | Medium user effort on every pull, commit, merge, & push | Better as backup/history than primary sync |
| Seafile | Keeps a separate conflict file | Server version control | Windows, macOS, & Linux | Android & iOS apps provide file access | High if deployed only for one vault | No advantage over the current Syncthing deployment |

## Self-hosted LiveSync with CouchDB

Self-hosted LiveSync is the strongest replacement if I want the same vault on Windows, macOS, Linux, Android, & iOS. I install one community plug-in inside Obsidian on each device, then point every copy at a CouchDB server. The plug-in supports continuous synchronization through CouchDB, end-to-end encryption, filename obfuscation, simple automatic conflict merging, & optional synchronization of `.obsidian` settings.

This removes the separate Syncthing process from each computer. It does not remove per-device configuration. I still install and configure the plug-in in every Obsidian installation, and synchronization depends on Obsidian running. Mobile operating systems can suspend Obsidian in the background, so I would open Obsidian and wait for the plug-in's progress indicators before closing it after a rename or deletion.

CouchDB adds work on the server. The upstream Docker image exposes TCP 5984 and stores data under `/opt/couchdb/data`, but the container is only the first step. I would also need HTTPS, authentication, database initialization, restricted network exposure, tested backups, upgrades, & monitoring. CouchDB automatically compacts old database content. Its own documentation says old non-leaf revision bodies are discarded during compaction, so I can't treat the database revision tree as vault version history or backup.

LiveSync's project documentation warns against running it beside another synchronization method. A migration would therefore require a vault backup, a clean cutover, & testing with a copied vault before I disable Syncthing.

## Remotely Save with Self-hosted WebDAV or S3

Remotely Save is easier to understand than CouchDB LiveSync. I install the plug-in in Obsidian on every device and use one central storage service as the meeting point. The free plug-in supports WebDAV, Amazon S3-compatible storage such as MinIO, Dropbox, & OneDrive Personal. It also supports mobile Obsidian, scheduled synchronization, sync on save, & optional end-to-end encryption using the `rclone crypt` format.

The free conflict handling is weaker than LiveSync. It detects a conflict and lets me choose the newer or larger copy. The paid Pro feature adds Markdown merging or duplicate-file handling. Automatic synchronization only runs while Obsidian is open, and its documentation says automatic errors fail silently. I would need to check the plug-in status instead of assuming a save reached the server.

For a self-hosted setup, I would pair Remotely Save with Nextcloud WebDAV if I already wanted Nextcloud for other files. Nextcloud then supplies web access and server-side file versions. A smaller WebDAV service or MinIO uses fewer application features, but file history would depend on that server's own versioning or an independent backup.

This is a reasonable middle choice for Android or iOS. It isn't a reason to replace a working desktop Syncthing deployment by itself.

## Nextcloud as Direct File Sync

Nextcloud is a general private cloud, not an Obsidian-specific sync engine. Its official desktop client synchronizes a chosen local directory on Windows, macOS, & Linux. When the local and server copies both change, the client downloads the server version and keeps the local work in a file named as a conflicted copy. By default, that conflict copy stays on the affected computer and isn't uploaded.

Nextcloud's file versions are more visible than Syncthing's version folder. The web interface can restore an earlier version, but the server thins versions as they age and caps version storage at 50 percent of the user's current free space. It saves a new version only when at least two minutes have passed since the previous saved version.

I wouldn't deploy Nextcloud only to synchronize this vault. It needs a server, database, HTTPS, storage, upgrades, backups, & a desktop client on every computer. It becomes sensible if I also want self-hosted file sharing, calendars, contacts, photo uploads, or browser access.

On mobile, the official Nextcloud apps provide access to files, but that doesn't guarantee that Obsidian can use the folder as a normal local vault on every operating system. If mobile Obsidian is the goal, using Remotely Save inside Obsidian against Nextcloud's WebDAV endpoint is the clearer route.

## Git-based Sync

Git gives me the clearest history. Each commit records a recoverable snapshot, and a self-hosted bare Git repository can be the remote. Git also performs a three-way merge when two histories change different lines. If both devices change the same lines, Git stops and requires me to resolve the conflict before synchronization continues.

That behavior is good for source code and poor for invisible note sync. A useful result depends on committing before I pull, pulling before I edit on another device, resolving conflicts correctly, & pushing afterward. The Obsidian Git plug-in can automate commit, pull, & push on desktop, but its own documentation calls mobile support experimental and unstable. It lists crashes, memory limits, no SSH authentication, & no rebase support on mobile.

I would use Git as an extra history or backup layer after excluding private material and testing restore, not as the main transport for this vault. It also shouldn't share the same live vault with another sync engine unless the interaction has been tested.

## Seafile

Seafile is a free, open-source, self-hosted file platform with Windows, macOS, Linux, Android, & iOS clients. Its desktop client keeps local files and renames the second edit as a conflict file when two devices change the same file. The Community Edition includes multi-platform file sync and version control.

I don't gain anything for this vault by replacing Syncthing with Seafile. I would still install a sync client on every computer and maintain a larger server application. The official mobile description covers browsing, previewing, uploading, & sharing files; it doesn't document opening a synchronized Seafile library as a local Obsidian vault. I would choose Seafile only if I wanted its broader file-sharing platform for other data.

## Recommendation

I should keep Syncthing as the primary sync method for the current desktop-first vault. It is already installed, verified, private, free, self-hosted, & independent of whether Obsidian is open. Adding a computer means installing one small sync program, which is the same category of per-device work every alternative requires.

I would reconsider this decision under two conditions:

1. If iPhone or iPad becomes a normal editing device, I will test Self-hosted LiveSync with CouchDB against a copy of the vault. It has the clearest Obsidian-native support across all Obsidian platforms.
2. If I deploy Nextcloud for general file storage anyway and want simpler mobile synchronization, I will test Remotely Save against Nextcloud WebDAV. I won't deploy Nextcloud only for this vault.

I will not run two synchronization engines against the live vault. Any trial starts with a separate vault copy and an independent backup. The existing open item for a recurring backup remains necessary regardless of which sync method I use.

## Sources

### Obsidian

- [Sync your notes across devices](https://obsidian.md/help/sync-notes)
- [Local and remote vaults](https://obsidian.md/help/sync/vault-types)

### Syncthing

- [Getting Started](https://docs.syncthing.net/intro/getting-started.html)
- [Understanding Synchronization](https://docs.syncthing.net/users/syncing.html)
- [File Versioning](https://docs.syncthing.net/users/versioning.html)
- [Security Principles](https://docs.syncthing.net/users/security.html)
- [Community Contributions](https://docs.syncthing.net/users/contrib.html)

### Self-hosted LiveSync & CouchDB

- [Self-hosted LiveSync repository and feature list](https://github.com/vrtmrz/obsidian-livesync)
- [Self-hosted LiveSync settings](https://github.com/vrtmrz/obsidian-livesync/blob/main/docs/settings.md)
- [Self-hosted LiveSync quick setup](https://github.com/vrtmrz/obsidian-livesync/blob/main/docs/quick_setup.md)
- [Apache CouchDB Docker installation](https://docs.couchdb.org/en/stable/install/docker.html)
- [Apache CouchDB replication and conflict model](https://docs.couchdb.org/en/stable/replication/conflicts.html)
- [Apache CouchDB compaction](https://docs.couchdb.org/en/stable/maintenance/compaction.html)

### Remotely Save

- [Remotely Save repository and feature list](https://github.com/remotely-save/remotely-save)
- [Remotely Save synchronization algorithm](https://github.com/remotely-save/remotely-save/blob/master/docs/sync_algorithm/v3/intro.md)
- [Remotely Save encryption formats](https://github.com/remotely-save/remotely-save/blob/master/docs/encryption/README.md)

### Nextcloud

- [Desktop clients](https://docs.nextcloud.com/server/latest/user_manual/en/desktop/index.html)
- [Desktop synchronization conflicts](https://docs.nextcloud.com/desktop/3.8/conflicts.html)
- [WebDAV access](https://docs.nextcloud.com/server/stable/user_manual/en/files/access_webdav.html)
- [File version control](https://docs.nextcloud.com/server/stable/user_manual/en/files/version_control.html)

### Git & Seafile

- [Git basic branching and merging](https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging.html)
- [Obsidian Git plug-in](https://github.com/Vinzent03/obsidian-git)
- [Seafile clients](https://www.seafile.com/en/download/)
- [Seafile file conflicts](https://help.seafile.com/syncing_client/file_conflicts/)
- [Seafile editions](https://www.seafile.com/en/pricing/)
