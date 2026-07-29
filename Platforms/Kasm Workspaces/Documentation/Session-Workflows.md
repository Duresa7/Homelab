# Kasm Lab Session Workflows

**Created:** 2026-07-28  
**Last updated:** 2026-07-28

How I use the lab, one workflow per job. The isolation and lane-assigned tiles are built and tested. The design and proof live in [Kasm Session Isolation - 2026-07-28](Change%20Records/Kasm%20Session%20Isolation%20-%202026-07-28.md) and [Kasm Workspace Build-Out - 2026-07-28](Change%20Records/Kasm%20Workspace%20Build-Out%20-%202026-07-28.md).

## Two things that break isolation without telling me

**A workspace with no override runs on the management lane.** Kasm's default is `kasm_default_network`, which NATs out `eth0` on VLAN 78 with ordinary Internet. The session works perfectly, looks healthy, & has none of the containment below. Every lab workspace needs both a network & a DNS value in its Docker Run Config Override, & I treat a workspace missing either as broken.

**Proton fails closed only while its VPN object is enabled.** An enabled tunnel that drops kill-switches VLAN 74 as intended. Administratively disabling the VPN object instead makes UniFi fall back to the normal WAN with no error & no warning, so a VLAN 74 session would browse from my home address. Before any VLAN 74 session I check that both the `KASM Lab Proton Egress` route & the Proton VPN object are enabled.

## Getting in

The normal way in is `https://kasm.<YOUR_BASE_DOMAIN>/` through NPM, which presents the wildcard certificate and throws no warning. `https://192.168.78.10/` still works as a direct fallback and still shows a self-signed warning, because Kasm's own certificate is untouched. SSH uses the address, never the name.

The direct address answers only Jedi PC at `192.168.50.241`, the Mac on Trusted, anything on Personal-A, and any client on the Management Access VPN. The proxied name resolves on the internal resolver alone and NPM has no WAN ingress, so nothing off-network reaches either path. It does mean the login page is now reachable from wherever NPM is reachable, which is wider than those four, so the password is what stands in front of it rather than the network.

Community Edition caps me at five concurrent sessions and one named user.

## Setting a workspace up once

I use the 19 lane-assigned tiles instead of editing registry originals. Any new tile needs the matching override and an explicit decision about its profile path.

The tile name tells me which lane I am about to land in. That is the whole reason the names are shaped this way.

| Tile suffix | Means | Override to paste |
| --- | --- | --- |
| `- Normal` | Ordinary WAN, saves state, for coding tools | `{"network":"lab75","dns":["9.9.9.9","149.112.112.112"]}` |
| `- VPN` | Internet through Proton, disposable, for links & tooling | `{"network":"lab74","dns":["9.9.9.9","149.112.112.112"]}` |
| `- Malware` | No Internet, no DNS, for samples | `{"network":"lab77","dns":["192.168.77.10"]}` |
| `- Target` | No Internet, no DNS, disposable victim on the same lane as malware | `{"network":"lab77","dns":["192.168.77.10"]}` |
| `- Review` | No Internet, no DNS, for artifacts | `{"network":"lab79","dns":["192.168.79.10"]}` |
| `- Full` | No override at all: management VLAN 78 with ordinary Internet and no containment | none |

The `- Full` tiles are the 15 registry originals, kept on purpose for the rare job that needs a plain session with no lane. Their category reads `Full Access - VLAN 78`, and that category is the thing to check, because "Full" does not warn me the way the earlier "Unsafe" label did.

Nothing listens at `192.168.77.10` or `192.168.79.10`, which is the point: lookups fail inside the lane instead of leaking. Dropping the `dns` member lets Docker's embedded resolver at `127.0.0.11` forward through the management host, which quietly defeats an offline lane.

The `Lab Sessions` group enforces upload allowed, download blocked, clipboard off in both directions, printing off, sharing off, microphone off, user storage mappings off, a one-hour limit, and no more than three sessions. Persistent profiles are allowed only so six named tiles can use their dedicated paths. Every malware, target, and review tile keeps that path empty.

## Working in the trusted-tools lane

I use `Claude Code - Normal`, `Codex CLI - Normal`, or `Terminal - Normal` for coding that needs the ordinary WAN and a profile that survives session destruction. Each tile has its own directory under `/var/lib/kasm-profiles`, so credentials and tool state do not cross between tools.

Before relying on the lane, I confirm the exit matches the current ordinary WAN and does not match Proton:

```bash
curl -s ifconfig.me
```

Lane 75 cannot reach sessions on 74, 77, or 79 and cannot reach the nine protected addresses in the checks below. It is a trusted Internet lane, not a path into the rest of the lab or home network.

## Opening a phishing link

`Chrome - VPN`, or `Tor Browser - VPN` when I want the extra hop. Check the Proton route & VPN object are both enabled first.

Before clicking anything, confirm the egress is Proton's & not mine:

```bash
curl -s ifconfig.me
```

Then follow the link, read the fake page, & note what I need. Anything I want to keep, I type into my own notes rather than downloading, because download is blocked on these workspaces by design. End the session when done; the container is destroyed with it.

What this buys me: the page sees a Proton exit address, never my home IP, & if the tunnel drops mid-session the traffic stops instead of falling back. What it doesn't buy me: permission to run the payload. If I want to execute what the page served, that's the next workflow, in a different lane.

## Practising against a target

`Kali - VPN` against `Debian - Target` or `Fedora - Target`. Start the target session first, then read its address from inside it:

```bash
ip -4 addr show eth0
```

Expect something in `192.168.77.208` through `192.168.77.223`. From the tooling session on 74 I can then reach it, scan it, & SSH into it. The gateway allows 74 to start connections toward 77 & blocks 77 from starting anything back, so a target I've just owned can't turn around & attack my tools. Replies to connections I started still flow, because that reverse block matches `NEW` & `INVALID` only.

Two sessions in the same lane can always see each other directly, since that traffic never reaches the gateway. Only cross-lane traffic is the firewall's decision.

## Watching a Linux sample run

Snapshot the host first. This is what makes "the Kasm host is disposable" true rather than aspirational:

```bash
qm snapshot 122 pre-malware-2026-07-28
```

Run that on `purple-server`. Then launch `REMnux - Malware` & drag the sample into the session window; it lands in the session's `Uploads` directory. Upload works even though the lane has no Internet at all, because the transfer rides the HTTPS connection my browser already has to Kasm rather than the container's network.

Execute it & watch. Expect DNS to fail and outbound connections to time out. That's the design: the sample cannot reach its operator, cannot pull a second stage, and cannot attack anyone else from my address. What I get is the local behaviour, the filesystem changes, and the fact & shape of its attempts.

When finished, end the session, then roll the host back:

```bash
qm shutdown 122 --timeout 180
qm rollback 122 pre-malware-2026-07-28 --start
```

Rolling back reverts Kasm's own database along with everything else, so a workspace I added after the snapshot disappears too. I take a fresh snapshot whenever I finish changing workspaces or settings, & then a rollback only costs me the session I just ran.

Three things not to do here. A Windows `.exe` will not run at all, because a Linux container has nothing to execute it, and that work needs a VM. Never mount a share from another host into the session, since that hands a live sample a filesystem path into the lab. And never run a sample on a `- VPN` tile for convenience; those have working Internet.

## Inspecting a file without running it

`REMnux - Review` for anything I want kept away from live sessions, `REMnux - Malware` if it's part of a detonation I'm already running. Strings, hashes, unpacking, reading a suspicious PDF or an Office macro, and triaging a disk image are all fine here, because nothing hostile executes.

Neither lane has Internet, so a reputation lookup means copying the hash out to a `- VPN` session or to my own machine. Pasting a hash is the safer habit anyway; uploading the sample itself hands it to a third party.

## Reviewing artifacts afterwards

`REMnux - Review` or `Debian - Review`. Neither can be reached from a VPN, malware, or target tile, and neither can initiate toward one, so findings can't be touched by something still running elsewhere. I reach them through the Kasm UI, never from another session.

Download stays blocked on every Lab Sessions tile. I move a written report out through a reviewed Git workflow from a `- Normal` tile instead of enabling download on a malware or review workspace.

## Checks when something feels wrong

From a `- VPN` session, the exit address should be Proton's, and stopping Proton should kill Internet access entirely rather than fall back. From a malware, target, or review session, both of these must fail:

```bash
timeout 3 bash -c 'echo > /dev/tcp/1.1.1.1/443'
getent hosts example.com
```

From any lane, every one of these must fail:

```text
192.168.78.10:443   the Kasm control plane
192.168.80.10:22    app-01
192.168.70.10:8006  grey-server Proxmox
192.168.70.11:8006  purple-server Proxmox
192.168.71.10:22    cluster network
192.168.72.2:443    Wazuh
192.168.73.2:9090   Prometheus
192.168.1.1:443     gateway UI
192.168.10.1:443    Trusted gateway
```

Write the probe exactly as above. `/dev/tcp/HOST/PORT` needs that second slash; a space instead makes every probe fail regardless of the firewall, which reads as a clean pass and is nothing of the sort.

If a session starts and then won't display, that's host-to-container reachability rather than Kasm. Check `ip route get 192.168.74.208` resolves through `shim74`, and check `qm config 122` still shows `firewall=0` on the lab NICs. The Proxmox per-NIC firewall filters by MAC, and every macvlan container has its own.

## Limits worth remembering

Five concurrent sessions and one named user are the Community Edition caps. The `alpha` account is limited to three by the Lab Sessions group, which is what the VM's 12 GiB actually serves: Kasm's own containers hold about 2 GiB, leaving 9.7 GiB against a 2.77 GiB default workspace.

Sessions are not serialised, so a sample can run beside another workspace. A container escape reaches every session on the host through the shared kernel no matter what the gateway does to their lanes. Closing that means running one session at a time.

The host itself is monitored on `192.168.78.10:9100` only, so `node_exporter` never answers on a lab lane.

## Related records

- [Kasm Session Isolation - 2026-07-28](Change%20Records/Kasm%20Session%20Isolation%20-%202026-07-28.md)
- [Kasm Workspace Build-Out - 2026-07-28](Change%20Records/Kasm%20Workspace%20Build-Out%20-%202026-07-28.md)
- [Kasm Session Isolation plan](Change%20Plans/Kasm%20Session%20Isolation.md)
- [Deployment](Deployment.md)
- [Isolated Security Lab](../../../Architecture/Isolated-Security-Lab.md)
