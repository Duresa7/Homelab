# Splunk SIEM Home Lab: Build Log

**Created:** 2026-06-28  
**Last updated:** 2026-07-18

My build log for standing up a Splunk Enterprise SIEM in my home lab, from bare VM to a working log-ingestion pipeline. I recorded what I built, the exact commands, the alternatives I weighed at each fork, and my reasoning for every non-default choice. I wrote it for other IT and security practitioners: the goal is to show not just the steps but the decision-making behind them.

### Project documents

| Document | Purpose |
|---|---|
| **Build-Log.md** (this file) | Chronological build log with decisions and reasoning |
| **[VM-Specs.md](VM-Specs.md)** | Full Proxmox VM configuration reference |
| **[UniFi-CEF-Reference.md](UniFi-CEF-Reference.md)** | UniFi CEF format, keys, and SC4S index routing |
| **[Troubleshooting-Log.md](Troubleshooting-Log.md)** | Every problem hit, its cause, and the fix |
| **[TODO.md](TODO.md)** | Planned follow-up work |

| Field | Value |
|---|---|
| Project | Splunk Enterprise SIEM (home lab) |
| VM name | `splunk-siem` (VMID 109) |
| Proxmox host | `grey-server` |
| Guest OS | Rocky Linux 10.2 (x86_64) |
| Splunk version | Enterprise 10.4.0 (build `f798d4d49089`) |
| Network | VLAN 72 (Security-A), static `192.168.72.3/24` |
| License | Splunk nonprofit license, 10 GB/day ingest |
| Started | 2026-06-28 |

---

## Design goals

Four principles drove every decision in this build.

**Isolation.** A SIEM ingests logs from the whole environment, which makes it both a high-value target and a heavy consumer of disk and I/O. I gave it its own dedicated VM on Security-A, not a shared host, so a compromise or a runaway index is contained to one blast radius.

**Least privilege.** Nothing runs as root that does not have to. Splunk runs under a dedicated service account; SSH accepts keys only; the box sits behind the Proxmox firewall on a segmented VLAN.

**Best-practice ingestion.** Getting data in is where most SIEM builds cut corners. Splunk's own guidance is explicit that syslog should not be sent directly into the indexer [2][3]. I followed the recommended pattern (a dedicated syslog collector in front of Splunk) even though the shortcut would have been faster.

**Documentation as a deliverable.** I wrote down every step, command, and dead end as it happened, with reasoning, so the work is reproducible and reviewable.

## Architecture

```
                       VLAN 72 (Security-A)
  ┌──────────────────────────────────────────────────────────────┐
  │  splunk-siem  (Rocky Linux 10.2 VM on Proxmox host grey-server) │
  │                                                                │
  │   UniFi console ──CEF/syslog:1514──► SC4S (Podman container)   │
  │   (192.168.72.3:1514 verified)             │                    │
  │                                           └─HEC:8088─► Splunk   │
  │                                                        Enterprise│
  │                                        web UI :8000 / mgmt :8089 │
  └──────────────────────────────────────────────────────────────┘
```

## Step index

| # | Step | Status | Summary |
|:-:|---|:-:|---|
| 1 | Proxmox VM creation | Done | Dedicated, isolated VM on `grey-server` |
| 2 | Rocky Linux 10.2 install | Done | Minimal install, no desktop environment |
| 3 | System update | Done | Full `dnf upgrade` before configuration |
| 4 | SSH access and hardening | Done | ed25519 key-only auth, root login disabled |
| 5 | Splunk Enterprise install | Done | 10.4.0 as a dedicated user under systemd |
| 6 | UniFi log ingestion (CEF via SC4S) | Done | UniFi to SC4S to Splunk, parsed as CEF |

---

## Step 1: Proxmox VM creation

I created the VM `splunk-siem` (VMID 109) on the Proxmox host `grey-server`.

### Decision: dedicated VM, not LXC or Docker

The first fork was how to host Splunk at all: a full VM, a Proxmox LXC container, or Docker.

I went with a full VM for three concrete reasons. First, Splunk is supported and tested on full operating systems, and its own tuning requirements assume one; it needs Transparent Huge Pages disabled and raised `ulimits` (open files and max user processes), which are awkward to control from inside an unprivileged LXC [1]. Second, Splunk is a long-lived, stateful Java application whose indexes grow without bound, which is the opposite of the ephemeral, stateless workload containers are designed for. Third, a VM gives me clean snapshots and hard resource limits, and keeps the blast radius to one guest.

### Sizing and rationale

| Component | Setting | Rationale |
|---|---|---|
| vCPU | 4 cores, type `host` | Splunk's reference hardware is heavier, but at this ingest volume 4 cores is comfortable; `host` passes through CPU features for best performance [4] |
| Memory | 12288 MiB (12 GiB) | Matches Splunk's reference RAM; below ~8 GiB, search performance degrades [4] |
| Disk | Single 150 GiB, SSD-backed | Splunk is I/O bound; SSD is required for acceptable search speed. One disk for simplicity, sized well above the retention need |
| Firmware | UEFI / OVMF, q35 | Modern chipset and boot path |
| Guest agent | Enabled | Clean shutdown, IP reporting to Proxmox |

I chose the disk options deliberately: `virtio-scsi-single` controller with **SSD emulation** (so the guest treats it as an SSD and TRIM works), **discard** on (so deleted index space is reclaimed), **iothread** on (a dedicated I/O thread for the disk), and **cache = none** (writes go straight to disk, which is the safe choice for a database-like workload that must not lose data on a power cut). Full disk and controller detail is in [VM-Specs.md](VM-Specs.md).

### Network placement

At initial build I bridged the VM on `vmbr0` and tagged it to **VLAN 70 (MGMT-A)**, the security/management tier that already hosted Wazuh and Prometheus. My reasoning: a SIEM is monitoring tooling and belongs with the rest of the observability stack, not in the application/server tier it watches. Keeping it out of the server VLAN means that if that tier is compromised, the log collector is not sitting in the same segment. I enabled the Proxmox firewall on the VM. This original placement was superseded by the 2026-07-12 Security-A migration recorded later in this log.

<details>
<summary>Screenshots: Proxmox VM creation settings (2)</summary>

![Proxmox Create VM confirmation tab: 4 cores, host CPU type, 12288 MiB memory, 150 GiB scsi0 disk on ssd-lvm1 with discard, ssd, and iothread on, net0 on vmbr0 with VLAN tag 70 and firewall enabled, VMID 109 on grey-server](../Evidence/Screenshots/vm-config-1%20%281%29.png)

![Proxmox Create VM confirmation tab scrolled to the top: guest agent enabled, OVMF BIOS, q35 machine, and the Rocky 10.2 boot ISO mounted on ide2](../Evidence/Screenshots/vm-config-1%20%282%29.png)

</details>

---

## Step 2: Rocky Linux 10.2 installation

I booted the VM from `Rocky-10.2-x86_64-boot.iso`.

### Decision: Rocky Linux, minimal, headless

I chose Rocky Linux over Ubuntu or Debian because I wanted **RHEL-family parity**: most enterprise Splunk runs on RHEL and its derivatives, so the package manager, paths, and documentation all line up with what production environments use. That parity is worth more to me than familiarity, because the point of a home lab is to practise on what employers actually run.

I did a **Minimal Install with no desktop environment** to keep the footprint small so RAM and disk go to Splunk. Splunk's web UI is reached over the network, so the server itself never needs a GUI.

| Setting | Value |
|---|---|
| Keyboard / language | US |
| Base environment | Minimal Install |
| Add-ons | Standard, Headless Management |
| Desktop environment | None |
| User account | REDACTED_NAME_001 / `REDACTED_USER_001` (wheel/sudo, password required) |
| Interface | `ens18` |
| IP address | `192.168.70.109/24` (DHCP) |
| Gateway / DNS | `192.168.70.1` |
| MAC | `REDACTED_MAC_016` |
| Hostname | `splunk-siem` |

I set the hostname from the terminal (it can also be set on the installer's Network and Host Name screen):

```bash
sudo hostnamectl set-hostname splunk-siem
```

<details>
<summary>Screenshots: Rocky Linux installer (2)</summary>

![Installer Network and Host Name screen: ens18 connected with DHCP address 192.168.70.109/24, default route and DNS 192.168.70.1](../Evidence/Screenshots/Screenshot%202026-06-28%20175948.png)

![Installer Create User screen: admin account with wheel-group membership checked and a required password rated Strong](../Evidence/Screenshots/Screenshot%202026-06-28%20180042.png)

</details>

---

## Step 3: System update

I brought the system fully up to date before installing anything, so the build starts from a known-patched baseline:

```bash
sudo dnf upgrade --refresh -y
sudo reboot            # only if the kernel or systemd were updated
cat /etc/rocky-release # confirm: Rocky Linux 10.2
```

<details>
<summary>Screenshots: system update (2)</summary>

![sudo dnf upgrade --refresh -y finishing with Dependencies resolved, Nothing to do, Complete](../Evidence/Screenshots/Screenshot%202026-06-28%20182636.png)

![cat /etc/rocky-release returning Rocky Linux release 10.2 (Red Quartz), followed by sudo dnf check-update](../Evidence/Screenshots/Screenshot%202026-06-28%20182935.png)

</details>

---

## Step 4: SSH access and hardening

`openssh-server` ships with the Minimal install and `sshd` was already running. My goal here was to move from password authentication to key-only access and to remove the obvious remote attack paths.

### Threat model and decisions

Password authentication over SSH is the single most-attacked surface on any internet-adjacent host; even on an internal VLAN it invites credential-guessing from anything that lands on the segment. I made two changes to close that path: I disabled password authentication entirely so only known public keys are accepted, and I disabled direct root login so an attacker cannot target the highest-value account by name.

I chose `ed25519` as the key type. It is the modern best-practice algorithm: smaller keys and faster verification than RSA, with strong security margins.

```bash
mkdir -p ~/.ssh && chmod 700 ~/.ssh
nano ~/.ssh/authorized_keys       # one public key per line
chmod 600 ~/.ssh/authorized_keys
```

I installed three `ed25519` public keys, one per client, each identified by its comment:

| Key comment | Client | Passphrase |
|---|---|:-:|
| `mac-air3-REDACTED_USER_001` | MacBook Air | Yes |
| `ansible-control` | Ansible control node | No (automation needs unattended login) |
| `REDACTED_SSH_KEY_LABEL_001-nopass` | jedi-pc workstation | No |

I hardened `/etc/ssh/sshd_config`:

```ini
PermitRootLogin no
PubkeyAuthentication yes
PasswordAuthentication no
```

Applied and validated:

```bash
sudo systemctl restart sshd
sudo sshd -t                                                   # config syntax check
sudo sshd -T | grep -Ei 'permitrootlogin|passwordauth|pubkeyauth'
```

> **Safety note:** I confirmed key login from a second session before closing the first. Because password authentication was already off, a broken key setup would have locked the account out; the Proxmox console was my fallback.

<details>
<summary>Screenshots: SSH hardening and service checks (3)</summary>

![systemctl status sshd showing active (running) and firewall-cmd --list-services listing cockpit, dhcpv6-client, and ssh](../Evidence/Screenshots/Screenshot%202026-06-28%20183036.png)

![sshd_config open in nano with PermitRootLogin no, PubkeyAuthentication yes, and PasswordAuthentication no set](../Evidence/Screenshots/Screenshot%202026-06-28%20183418.png)

![Console session showing the Rocky 10.2 release check, sshd active, firewall services, and ip a with ens18 at 192.168.70.109/24](../Evidence/Screenshots/Screenshot%202026-06-28%20183653.png)

</details>

---

## Step 5: Splunk Enterprise install

I installed **Splunk Enterprise 10.4.0** (build `f798d4d49089`) from the official RPM [1].

### Decision: dedicated service account and systemd management

Two choices here matter for security and for correctness.

I run Splunk as a **dedicated `splunk` service account**, never as root or as my login user. This is least privilege in practice: if Splunk is compromised, the attacker lands as an unprivileged service account, not root.

```bash
sudo useradd -m -d /opt/splunk splunk
```

I downloaded the RPM to `/tmp` using the signed link from splunk.com and installed it to the default `/opt/splunk`:

```bash
cd /tmp
wget -O splunk-10.4.0-f798d4d49089.x86_64.rpm \
  "https://download.splunk.com/products/splunk/releases/10.4.0/linux/splunk-10.4.0-f798d4d49089.x86_64.rpm"
sudo rpm -i /tmp/splunk-10.4.0-f798d4d49089.x86_64.rpm
sudo chown -R splunk:splunk /opt/splunk
```

> **Gotcha:** I ran the first `rpm -i` without `sudo` and it failed with `can't create transaction lock ... Permission denied`, so nothing installed. The `Header V4 RSA/SHA256 ... NOKEY` warning is benign; it only means Splunk's GPG key is not imported, so the signature is not verified. Full write-up in [Troubleshooting-Log.md](Troubleshooting-Log.md) (#1 and #2).

I enabled boot-start as a **systemd-managed** service, running as the `splunk` user:

```bash
sudo /opt/splunk/bin/splunk enable boot-start -user splunk -systemd-managed 1 --accept-license
```

I used `-systemd-managed 1` rather than the legacy init approach because it generates `/etc/systemd/system/Splunkd.service`, and that unit applies the `ulimits` and Transparent Huge Pages settings Splunk needs automatically [1]. This is the tuning Splunk requires (THP disabled, high open-file and process limits) done the supported way instead of by hand-editing the OS. The same command prompted for and created the admin account.

Started and verified:

```bash
sudo systemctl start Splunkd
sudo systemctl status Splunkd        # active (running), enabled
sudo firewall-cmd --permanent --add-port=8000/tcp   # Splunk Web
sudo firewall-cmd --reload
```

| Item | Value |
|---|---|
| Web UI | `http://192.168.70.109:8000` |
| Admin user | `admin` |
| Management port | 8089 (splunkd) |
| Bundled services | KV store (MongoDB), Postgres |
| License | Splunk nonprofit license, 10 GB/day ingest |
| TLS | Plain HTTP for now; HTTPS is a planned follow-up |

<details>
<summary>Screenshots: Splunk Enterprise install (4)</summary>

![Install session: splunk service account created, RPM downloaded (1.5 GB at 263 MB/s), the unprivileged rpm -i failing with a transaction lock error, then the sudo install and boot-start enablement ending with Configured as systemd managed service](../Evidence/Screenshots/Screenshot%202026-06-29%20211322.png)

![Splunkd.service active (running) under systemd, with the startup log ending in splunkd started (build f798d4d49089)](../Evidence/Screenshots/Screenshot%202026-06-29%20212649.png)

![systemctl status Splunkd showing the full process tree (splunkd, supervisor, postgres, pgbouncer, traefik) and firewall-cmd opening port 8000/tcp](../Evidence/Screenshots/Screenshot%202026-06-29%20212728.png)

![Splunk Web login page served at http://192.168.70.109:8000 with the first-time sign-in notice](../Evidence/Screenshots/Screenshot%202026-06-29%20212751.png)

</details>

---

## Step 6: UniFi log ingestion (CEF via SC4S)

The first real data source is my UniFi network. This step is the core of the build, because getting data in correctly is where a SIEM is made or broken.

### Background: what UniFi sends

UniFi's **System Logging / SIEM** integration (Integration → System Logging / SIEM → SIEM Server) exports activity logs over syslog in **Common Event Format (CEF)** [9]. CEF is an industry-standard structured log format: a fixed header followed by `key=value` pairs, which lets any SIEM parse events from any vendor consistently.

```
CEF:Version|Device Vendor|Device Product|Device Version|Event Class ID|Name|Severity|[Extension]
```

I enabled all export categories (Network, UniFi OS, and Protect), which matters later. Full format and key reference is in [UniFi-CEF-Reference.md](UniFi-CEF-Reference.md).

### Decision: SC4S, not direct syslog, and not a Universal Forwarder

I had three ingestion approaches on the table.

I ruled out a **Universal Forwarder** first because it cannot apply here. A UF is an agent installed on a host to read its local files; UniFi is a closed appliance, so there is nothing to install it on. UniFi's only export mechanism is the push-based SIEM integration.

I ruled out **pointing UniFi's syslog straight at splunkd** on Splunk's own guidance. Splunk explicitly discourages direct TCP/UDP syslog input into the indexer, because a UDP listener drops events whenever Splunk restarts and a single stream is hard to scale [2][3]. There was also a practical blocker: the `splunk` service account cannot bind privileged ports.

I chose **Splunk Connect for Syslog (SC4S)** because it is Splunk's current recommended pattern for syslog collection [2][4]. SC4S is a containerized syslog-ng that receives syslog, parses it (including CEF natively), sets Splunk metadata, and forwards over HTTP Event Collector (HEC). It decouples ingestion from the indexer, so a Splunk restart does not lose events.

I picked **Podman over Docker** to run the SC4S container. Podman is native to Rocky/RHEL (in the base repos), is daemonless and can run rootless (a smaller attack surface, which suits a security-tier host), and integrates cleanly with systemd. SC4S supports both equally [5].

### Splunk-side preparation

I enabled HEC (SSL, port 8088) and created a token named `sc4s`. I left the token's allowed indexes blank on purpose: SC4S sets the destination index per event, so restricting the token to a list would cause events aimed at other indexes to drop. A default (lastChance) index of `main` catches anything unrouted.

I created the network-category indexes SC4S routes into, each capped at 5 GB to protect the disk: `netauth`, `netdns`, `netfw`, `netids`, `netops`.

<details>
<summary>Screenshots: HEC and index setup (5)</summary>

![HEC Edit Global Settings dialog: all tokens enabled, Enable SSL checked, HTTP port 8088](../Evidence/Screenshots/Screenshot%202026-06-30%20000305.png)

![Add Data wizard creating the HEC token named sc4s](../Evidence/Screenshots/Screenshot%202026-06-30%20000349.png)

![Token input settings: allowed indexes left empty, default index main](../Evidence/Screenshots/Screenshot%202026-06-30%20000525.png)

![Indexes page listing the new netauth, netdns, netfw, netids, and netops indexes, each with a 5 GB max size](../Evidence/Screenshots/Screenshot%202026-06-30%20130841.png)

![Edit Index dialog for netauth showing the 5 GB maximum index size](../Evidence/Screenshots/Screenshot%202026-06-30%20130849.png)

</details>

### SC4S deployment (Podman)

```bash
# kernel receive buffers (16 MB), per SC4S guidance [4]
echo 'net.core.rmem_default = 17039360
net.core.rmem_max = 17039360' | sudo tee -a /etc/sysctl.conf && sudo sysctl -p

sudo dnf install -y podman
sudo podman volume create splunk-sc4s-var
sudo mkdir -p /opt/sc4s/local /opt/sc4s/archive /opt/sc4s/tls
```

`/opt/sc4s/env_file` (HEC target plus the CEF listener on port 1514) [5][6]:

```ini
SC4S_DEST_SPLUNK_HEC_DEFAULT_URL=https://127.0.0.1:8088
SC4S_DEST_SPLUNK_HEC_DEFAULT_TOKEN=${SPLUNK_HEC_TOKEN}
SC4S_DEST_SPLUNK_HEC_DEFAULT_TLS_VERIFY=no
SC4S_LISTEN_CEF_UDP_PORT=1514
SC4S_LISTEN_CEF_TCP_PORT=1514
```

I copied the systemd unit `/lib/systemd/system/sc4s.service` verbatim from the SC4S Podman documentation (image `ghcr.io/splunk/splunk-connect-for-syslog/container3:latest`, `--network host`) [5]. Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now sc4s
sudo firewall-cmd --permanent --add-port=1514/udp
sudo firewall-cmd --permanent --add-port=1514/tcp
sudo firewall-cmd --reload
```

> **Gotcha: port 1514 already in use.** SC4S crash-looped with `Error binding socket; 0.0.0.0:1514, Address in use (98)`. `sudo ss -lntup | grep 1514` showed `splunkd` holding 1514, a leftover TCP data input from my earlier direct-ingest attempt (exactly the anti-pattern SC4S replaces). I deleted that input, the port came free, and SC4S bound cleanly. Full write-up in [Troubleshooting-Log.md](Troubleshooting-Log.md) (#4).

Finally, I pointed UniFi's SIEM Server at `192.168.70.109:1514`.

<details>
<summary>Screenshots: SC4S deployment and first events (9)</summary>

![Kernel receive-buffer settings (net.core.rmem 17039360) appended to /etc/sysctl.conf and applied with sysctl -p](../Evidence/Screenshots/Screenshot%202026-06-30%20131038.png)

![Podman already present via dnf, the splunk-sc4s-var volume created, and the /opt/sc4s directories made](../Evidence/Screenshots/Screenshot%202026-06-30%20131052.png)

![env_file contents: HEC URL https://127.0.0.1:8088, TLS verify off, CEF UDP and TCP listeners on 1514, token line redacted](../Evidence/Screenshots/Screenshot%202026-06-30%20131209.png)

![sc4s.service unit open in nano showing the podman run configuration from the SC4S documentation](../Evidence/Screenshots/Screenshot%202026-06-30%20131323.png)

![systemctl enable --now sc4s failing with Unit sc4s.service does not exist, then the unit written in nano and daemon-reload rerun](../Evidence/Screenshots/Screenshot%202026-06-30%20131353.png)

![SC4S container logs: Splunk HEC connection test successful, sc4s version 3.45.0, and firewall ports 1514/udp and 1514/tcp opened](../Evidence/Screenshots/Screenshot%202026-06-30%20133108.png)

![UniFi System Logging / SIEM panel pointed at 192.168.70.109 port 1514 with an Event Sent confirmation after Send Test Event](../Evidence/Screenshots/Screenshot%202026-06-30%20133152.png)

![stats count by index, sourcetype, host: CEF events from 192.168.70.1 arriving (still in main at this point) alongside SC4S startup events](../Evidence/Screenshots/Screenshot%202026-06-30%20134005.png)

![UniFi CEF events in Splunk search: the test syslog and an admin-access event with UNIFI extension fields parsed](../Evidence/Screenshots/Screenshot%202026-06-30%20134033.png)

</details>

### Index routing and the multi-product discovery

By default SC4S sends CEF to `main`. To route UniFi into `netops`, I added a metadata override at `/opt/sc4s/local/context/splunk_metadata.csv`. The key for CEF sources is `device_vendor`_`device_product`, taken from the CEF header [6].

My first attempt used a single key and only a fraction of events routed. Enumerating the live data explained why:

```spl
index=* sourcetype=cef Ubiquiti | stats count by sc4s_vendor sc4s_product
# UniFi Network = 200, UniFi OS = 59, UniFi Protect = 83
```

With all categories enabled, UniFi emits **three** distinct `device_product` values, so I needed three routing keys [8]:

```csv
Ubiquiti_UniFi OS,index,netops
Ubiquiti_UniFi Network,index,netops
Ubiquiti_UniFi Protect,index,netops
```

Restart with `sudo systemctl restart sc4s`. Routing changes are forward-only; events already in `main` stay there.

<details>
<summary>Screenshots: index routing and product discovery (6)</summary>

![splunk_metadata.csv with the initial single routing key Ubiquiti_UniFi OS,index,netops](../Evidence/Screenshots/Screenshot%202026-06-30%20134524.png)

![SC4S restarted after the metadata edit, container logs showing the HEC connection tests passing again](../Evidence/Screenshots/Screenshot%202026-06-30%20134549.png)

![index=netops sourcetype=cef Ubiquiti returning the first UniFi OS event routed into netops](../Evidence/Screenshots/Screenshot%202026-06-30%20134703.png)

![netops over 24 hours: 57 events, all of them UniFi OS admin config-change events, while other products were still missing](../Evidence/Screenshots/Screenshot%202026-07-01%20182042.png)

![stats count by sc4s_vendor and sc4s_product across all indexes: UniFi Network 200, UniFi OS 59, UniFi Protect 83](../Evidence/Screenshots/Screenshot%202026-07-01%20193859.png)

![index=netops stats by sc4s_product returning only UniFi OS (59 events) before the extra routing keys were added](../Evidence/Screenshots/Screenshot%202026-07-01%20195057.png)

</details>

### Verification

```spl
index=* sourcetype=sc4s:events "starting up"          # SC4S pipeline is alive
index=netops sourcetype=cef | stats count by sc4s_product   # all three products routing
index=main   sourcetype=cef earliest=-30m | stats count by sc4s_product   # empty = nothing leaking
```

The empty `main` result is the definitive proof: if any product string still lacked a routing key, new CEF events would be piling up in `main`. Zero there means every key matches and all UniFi data lands in `netops`, parsed as `sourcetype=cef` with fields extracted (vendor and product as `sc4s_vendor`/`sc4s_product`, and the extension keys as `UNIFI*`).

<details>
<summary>Screenshots: pipeline verification (3)</summary>

![Search for sourcetype=sc4s:events "starting up" returning two SC4S startup events](../Evidence/Screenshots/Screenshot%202026-06-30%20133401.png)

![index=netops over the last 30 minutes: UniFi Protect events counted by sc4s_product after the routing fix](../Evidence/Screenshots/Screenshot%202026-07-01%20201953.png)

![index=main sourcetype=cef over the last 30 minutes returning no results: nothing leaking to main](../Evidence/Screenshots/Screenshot%202026-07-01%20202008.png)

</details>

### Note on the CEF add-on

I installed the `cefutils` (CEF Extraction Add-on) [10] on the search head. Because SC4S already parses CEF at ingest, this add-on is largely redundant for search here; its remaining value is CIM normalization for future dashboards and correlation. See [Troubleshooting-Log.md](Troubleshooting-Log.md) (#7) for the field-name investigation.

<details>
<summary>Screenshots: CEF field-name investigation (4)</summary>

![Table of guessed CEF field names (device_vendor, device_product, signature) returning rows with only _time filled](../Evidence/Screenshots/Screenshot%202026-07-01%20182959.png)

![REST query against /services/apps/local confirming cefutils 1.5.6 installed and enabled](../Evidence/Screenshots/Screenshot%202026-07-01%20183115.png)

![fieldsummary limited to the guessed field prefixes returning no results](../Evidence/Screenshots/Screenshot%202026-07-01%20183141.png)

![fieldsummary listing the real fields on the events: UNIFI* extension keys and sc4s_* metadata fields](../Evidence/Screenshots/Screenshot%202026-07-01%20183450.png)

</details>

---

## 2026-07-12: Security-A network migration

I moved the established SIEM VM from MGMT-A/VLAN 70 (`192.168.70.109`) to the dedicated Security-A/VLAN 72 network with static address `192.168.72.3/24`, gateway and DNS `192.168.72.1`. The Proxmox NIC kept its VirtIO model, MAC, bridge, and guest-firewall setting; only the VLAN tag changed from 70 to 72. I backed up the in-guest NetworkManager profile before the address change.

After reboot, `Splunkd`, `sc4s`, `sshd`, and `qemu-guest-agent` were active. SC4S listened on TCP and UDP 1514, Splunk Web returned HTTP 303 over HTTPS 8000, HEC health returned HTTP 200 over HTTPS 8088, and management port 8089 listened. Internal reachability to `https://192.168.72.3:8000` returned HTTP 303. HTTPS egress worked while an unapproved external TCP/53 test timed out under the ordered Security-A egress policy.

I changed the UniFi console's SIEM export destination to `192.168.72.3:1514`. A fresh 317-byte CEF event reached SC4S at 22:40:27 EDT, forwarded through HEC with zero drops/queue, and appeared as one new `netops` event in Splunk's throughput metrics at 22:40:43. Full migration detail and evidence are in the UniFi [Security-A change record](../../../../Infrastructure/Network/UniFi/Documentation/Change%20Records/Security-A%20Migration%20-%202026-07-12.md).

---

## Current state

The SIEM is an isolated Security-A VM running Splunk Enterprise 10.4.0 with a healthy, end-to-end-verified UniFi-to-SC4S-to-HEC ingestion pipeline at `192.168.72.3:1514`. Planned follow-ups are tracked in [TODO.md](TODO.md).

---

## References

1. Splunk Enterprise, *Install on Linux* (v10.2). https://help.splunk.com/en/splunk-enterprise/get-started/install-and-upgrade/10.2/install-splunk-enterprise-on-linux-or-macos/install-on-linux
2. Splunk, *Syslog data collection* (Splunk Validated Architectures). https://help.splunk.com/en/data-management/splunk-validated-architectures/getting-data-in-forwarding-and-preprocessing/syslog-data-collection
3. Splunk, *How the Splunk platform handles syslog data over the UDP network protocol*. https://docs.splunk.com/Documentation/SplunkCloud/latest/Data/HowSplunkEnterprisehandlessyslogdata
4. Splunk Connect for Syslog, *Quickstart Guide*. https://splunk.github.io/splunk-connect-for-syslog/main/gettingstarted/quickstart_guide/
5. Splunk Connect for Syslog, *Podman + systemd*. https://splunk.github.io/splunk-connect-for-syslog/main/gettingstarted/podman-systemd-general/
6. Splunk Connect for Syslog, *Common Event Format (CEF)* source. https://splunk.github.io/splunk-connect-for-syslog/main/sources/base/cef/
7. Splunk Connect for Syslog, *Sources: Read First* (listening ports, vendor-product-by-source). https://splunk.github.io/splunk-connect-for-syslog/main/sources/
8. Splunk Connect for Syslog, *Ubiquiti UniFi* source. https://splunk.github.io/splunk-connect-for-syslog/main/sources/vendor/Ubiquiti/unifi/
9. Ubiquiti Help, *UniFi System Logs & SIEM Integration*. https://help.ui.com/hc/en-us/articles/33349041044119-UniFi-System-Logs-SIEM-Integration
10. *CEF Extraction Add-on for Splunk* (Splunkbase app 487; source: github.com/splunk/splunk-add-on-for-cef). https://splunkbase.splunk.com/app/487
