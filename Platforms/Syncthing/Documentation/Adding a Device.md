# Adding a Device to the Obsidian Vault

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

I use this runbook to add a Windows, macOS, or Linux computer to folder ID `obsidian-the-vault`. Each computer keeps its own local vault directory; `docker-main` remains the always-on peer at `192.168.40.35:22000`. A mobile client gets its own device ID and joins the same folder ID, but Android and iOS impose different storage and background-execution limits described under [Mobile Devices](#mobile-devices).

## How Pairing Works

Syncthing identifies a computer by its device ID, not its hostname or IP address. Both devices must add each other's ID before they connect. Device IDs are public certificate fingerprints; I don't copy `config.xml`, TLS keys, or an existing Syncthing data directory between computers.

The folder ID must remain `obsidian-the-vault` on every peer. The path doesn't have to match:

| Operating system | Example local path |
|---|---|
| Windows | `C:\Users\<YOUR_WINDOWS_USERNAME>\Documents\The Vault` |
| macOS | `/Users/<YOUR_MAC_USERNAME>/Documents/The Vault` |
| Linux | `/home/<YOUR_LINUX_USERNAME>/Documents/The Vault` |

I don't place this vault inside iCloud Drive, OneDrive, Dropbox, or another synchronized directory. Two file synchronization engines can race on the same deletion, rename, or temporary file.

## Step 1: Install and Start Syncthing

### Windows

I install the current package from WinGet:

```powershell
winget install --exact --id Syncthing.Syncthing
syncthing --no-browser --no-restart
```

If the second command isn't found, I close & reopen PowerShell so it reloads the WinGet command aliases. For sign-in startup, I open `shell:startup` from the Run dialog and create a shortcut with this target:

```text
C:\Users\<YOUR_WINDOWS_USERNAME>\AppData\Local\Microsoft\WinGet\Links\syncthing.exe --no-console --no-browser --no-restart
```

### macOS

The official macOS wrapper includes the Syncthing daemon, a menu-bar status icon, & a Start at Login option. It can't run beside the Homebrew `syncthing` formula or another wrapper. I check for the formula and remove it before installing the application:

```bash
if brew list --formula syncthing >/dev/null 2>&1; then
  brew services stop syncthing
  brew uninstall syncthing
fi
brew install --cask syncthing-app
open -a Syncthing
```

I enable **Start at Login** from the Syncthing menu-bar application. If Homebrew isn't installed, I use the signed DMG from the [official Syncthing macOS releases](https://github.com/syncthing/syncthing-macos/releases).

### Linux

I install Syncthing from the distribution or [official Syncthing package repository](https://apt.syncthing.net/), then enable its per-user systemd service:

```bash
systemctl --user enable --now syncthing.service
```

Package commands differ between Debian, Ubuntu, Fedora, Arch, & other distributions. The check that matters is the same: `http://127.0.0.1:8384` opens on the new computer and reports a running Syncthing version.

## Step 2: Back Up and Prepare the Local Path

I make a separate backup if the new computer already contains an Obsidian vault. Syncthing merges existing content; an empty destination downloads the server copy, while a populated destination can upload existing or conflicting files.

I create the destination directory before accepting the share. The operating-system examples are:

```powershell
New-Item -ItemType Directory -Force 'C:\Users\<YOUR_WINDOWS_USERNAME>\Documents\The Vault'
```

```bash
mkdir -p "$HOME/Documents/The Vault"
```

I don't open this empty directory in Obsidian yet.

## Step 3: Record Both Device IDs

On the new computer, I open `http://127.0.0.1:8384`, then select **Actions > Show ID**. I copy the new device ID.

I perform the initial pairing while the new computer is on the home network or connected through the homelab VPN. It must reach `192.168.40.35` on TCP 22 for the management tunnel and TCP 22000 for the direct Syncthing connection. An off-site computer without that VPN route can't complete the following steps.

The `docker-main` GUI listens only on its own loopback address. From PowerShell, macOS Terminal, or a Linux shell, I open an SSH tunnel and leave that terminal running:

```bash
ssh -N -L 8385:127.0.0.1:8384 root@192.168.40.35
```

The configured SSH account is `root` with key authentication. I use an existing approved private key on the new computer or add that computer's public key through an already authorized admin session; I don't copy a private key from `docker-main`. I then open `http://127.0.0.1:8385`, select **Actions > Show ID**, & copy the `docker-main` device ID. Closing the SSH session removes the TCP 8385 tunnel; it doesn't stop Syncthing.

If SSH authentication fails, I fix the account or authorized key first. I don't expose the server GUI on `0.0.0.0:8384` to work around missing SSH access.

## Step 4: Add the Devices to Each Other

In the tunneled `docker-main` GUI, I select **Add Remote Device** and enter:

| Field | Value |
|---|---|
| Device ID | The new computer's device ID |
| Device Name | A recognizable name such as `MacBook`, `Laptop`, or `Desktop` |
| Addresses | `dynamic` |

In the new computer's GUI, I select **Add Remote Device** and enter:

| Field | Value |
|---|---|
| Device ID | The `docker-main` device ID |
| Device Name | `docker-main` |
| **Advanced > Addresses** | `tcp://192.168.40.35:22000, dynamic` |

I save both device records and wait for **Connected**. Adding a device on one side only leaves it disconnected because Syncthing requires mutual approval.

## Step 5: Share and Accept the Vault

In the `docker-main` GUI, I expand **The Vault**, select **Edit > Sharing**, check the new computer, & save. The new computer then offers folder ID `obsidian-the-vault`.

I accept the offer with these settings:

| Field | Value |
|---|---|
| Folder Label | `The Vault` |
| Folder ID | `obsidian-the-vault` |
| Folder Path | The local path prepared in Step 2 |
| Folder Type | `Send & Receive` |

Before saving, I open the folder's **Ignore Patterns** tab and enter:

```text
.obsidian/workspace.json
.obsidian/workspace-mobile.json
```

The GUI writes those two lines to the new device's `.stignore`. Syncthing never synchronizes `.stignore`, so I repeat this step on every new computer. Themes, plugins, hotkeys, & other `.obsidian` settings remain synchronized.

## Step 6: Verify Before Opening Obsidian

I wait until the new computer reports both conditions:

- `docker-main` shows **Connected**.
- `The Vault` shows **Up to Date**, with matching Local State & Global State counts.

The initial 2026-07-22 deployment contained 14 synchronized files totaling 6,425,692 bytes. That number changes as I add notes; **Up to Date** & matching state counts are the reusable checks.

I open the local folder as a vault in Obsidian only after synchronization finishes. I then create `Syncthing Setup Test.md`, confirm it reaches another peer, delete it, & confirm the deletion reaches `docker-main`. Server-side staggered versioning retains replaced or deleted files for up to 90 days.

## Optional Direct Peer

The new computer only needs a relationship with `docker-main`; Windows & the new device still exchange changes through the always-on server. I can also pair the new computer directly with Windows by repeating the mutual device-ID exchange and sharing `obsidian-the-vault` between them. That extra path keeps local synchronization working while `docker-main` is offline.

## Mobile Devices

The numbered desktop steps don't map one-for-one to mobile operating systems. I still exchange device IDs, use folder ID `obsidian-the-vault`, add the two workspace ignore patterns, & verify **Up to Date** before opening the vault.

On Android, the Syncthing project's original Android wrapper was archived on 2024-12-03. The current [Syncthing community contributions](https://docs.syncthing.net/users/contrib.html) list Syncthing-Fork & BasicSync; each app must receive Android storage and background-execution permissions before it can synchronize an Obsidian-accessible directory.

Syncthing doesn't publish an official iOS or iPadOS client. The same community list names Synctrain for iOS, iPadOS, & macOS. Apple background-execution and file-provider rules mean I test foreground synchronization and Obsidian folder access on the specific client before trusting it with the live vault.

## Removing a Device

If I retire or lose a computer, I remove its device entry from `docker-main` and every direct peer. Removing the device stops future synchronization but doesn't delete the remaining peers' vault directories.

## References

- [Syncthing getting started](https://docs.syncthing.net/intro/getting-started.html)
- [Syncthing GUI folder and device states](https://docs.syncthing.net/intro/gui.html)
- [Ignoring files](https://docs.syncthing.net/users/ignoring.html)
- [Starting Syncthing automatically](https://docs.syncthing.net/users/autostart.html)
- [Official Syncthing macOS application](https://github.com/syncthing/syncthing-macos)
