# Termix Walkthrough

**Created:** 2026-07-20  
**Last updated:** 2026-07-20

## What This Guide Covers

I upgraded Termix, created a dedicated reusable Ed25519 identity, onboarded every reachable SSH target, opened a narrow Proxmox firewall path, & organized the hosts into four folders. This guide follows the checks that kept unreachable machines out of the saved inventory.

## Current Status and Verified Versions

Termix 2.5.0 and guacd 1.6.0 run on `docker-main` at `192.168.40.35`; Termix returns HTTP 200 on TCP 8080. Nine hosts are verified through Termix under four folders. Ten SSH Manager targets were unreachable during implementation and weren't presented as onboarded.

## What You Need

- A Docker host running Termix and guacd.
- An approved administrative path to install one public key on each target.
- A complete target list with address and username.
- Firewall access from the Termix host to TCP 22 on intended targets.

## How the Pieces Fit Together

> Diagram placeholder

## Walkthrough

### Step 1: Upgrade and Verify Termix

I upgraded the existing Compose project from 2.2.1 to 2.5.0 with `pull`, `down`, & `up -d`. I kept the named volume and checked Termix, guacd, TCP 4822 between them, port 8080, logs, & restart counts.

### Step 2: Probe Every Candidate

I started with 19 SSH Manager targets and sent a live `echo TERMIX_SSH_OK` probe through the approved administrative connections. Nine succeeded. I kept the other ten out of Termix because a saved but unreachable host would give a false result.

### Step 3: Create the Reusable Identity

I used Termix's key generator to create `Termix Homelab SSH`. I recorded the Ed25519 public fingerprint as `<K05_FINGERPRINT>` and used that fingerprint for later audit and retirement.

### Step 4: Install the Public Key

I added the generated public key to the nine reachable accounts through their existing administration path, then verified the exact entry on each target before creating host records.

### Step 5: Create the Host Records

I created nine Termix hosts using the reusable credential and per-host username overrides. I enabled only the terminal, tunnel, file-manager, statistics, Docker, or Proxmox features that matched each host.

### Step 6: Fix the Proxmox SSH Path

Five hosts connected immediately; all four Proxmox nodes timed out. UniFi traffic records showed the flows were allowed, so I traced the block to the Proxmox Datacenter firewall. I created `pve_termix` for only `192.168.40.35` and placed a TCP 22 accept before the existing SSH drop.

### Step 7: Organize the Inventory

I placed the nine records under `Homelab/Docker`, `Homelab/Edge`, `Homelab/Servers`, & `Homelab/Proxmox`. I repeated the connection test after moving them because the folder change still touched application data.

### Step 8: Verify from Termix

I exercised Termix's own SSH metrics path for all nine records. Each returned HTTP 200 with `success: true`; the Termix container stayed healthy with zero restarts.

## What I Checked After Each Step

- Termix 2.5.0 and guacd 1.6.0 reported healthy.
- Termix returned HTTP 200 and connected to guacd on TCP 4822.
- The generated public key was present on nine approved accounts.
- Five non-Proxmox and four Proxmox sessions succeeded from Termix.
- `pve_termix` contained only `192.168.40.35` and only opened TCP 22.
- Exactly four folders remained after organization.

## Troubleshooting and Recovery

If Termix times out while another client works, test TCP 22 from `docker-main` and inspect both UniFi and host firewall decisions. If authentication fails, compare the target username and `<K05_FINGERPRINT>` before adding another key. Remove the narrow Proxmox IPSet rule if the Termix host is retired.

## Known Limits

The ten targets that failed the initial reachability test remain outside Termix. The 2.5.0 upgrade used the mutable `latest` image and didn't include a fresh application-data backup, so a downgrade may not be safe.

## Source Records

- [Termix upgrade](../Platforms/Termix/Documentation/Change%20Records/Termix%20Upgrade%202.2.1%20to%202.5.0%20-%202026-07-13.md)
- [SSH host onboarding](../Platforms/Termix/Documentation/Change%20Records/Termix%20SSH%20Host%20Onboarding%20-%202026-07-14.md)
- [Troubleshooting log](../Platforms/Termix/Documentation/Troubleshooting-Log.md)
