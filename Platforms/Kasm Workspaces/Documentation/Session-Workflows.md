# Kasm Lab Session Workflows

**Created:** 2026-07-28  
**Last updated:** 2026-07-28

How I actually use the lab, one workflow per job. The isolation is already built & tested; this is the operating side of it. The design & the proof live in [Kasm Session Isolation - 2026-07-28](Change%20Records/Kasm%20Session%20Isolation%20-%202026-07-28.md).

## Two things that break isolation without telling me

**A workspace with no override runs on the management lane.** Kasm's default is `kasm_default_network`, which NATs out `eth0` on VLAN 78 with ordinary Internet. The session works perfectly, looks healthy, & has none of the containment below. Every lab workspace needs both a network & a DNS value in its Docker Run Config Override, & I treat a workspace missing either as broken.

**Proton fails closed only while its VPN object is enabled.** An enabled tunnel that drops kill-switches VLAN 74 as intended. Administratively disabling the VPN object instead makes UniFi fall back to the normal WAN with no error & no warning, so a VLAN 74 session would browse from my home address. Before any VLAN 74 session I check that both the `KASM Lab Proton Egress` route & the Proton VPN object are enabled.

## Getting in

The UI is `https://192.168.78.10/`, & SSH uses the same address. Reachable from Jedi PC at `192.168.50.241`, the Mac on Trusted, anything on Personal-A, & any client on the Management Access VPN. Nothing else on the network can even see the login page.

The certificate is self-signed because there's no proxy entry for this host, so the browser warning is expected. Community Edition caps me at five concurrent sessions & one named user.

## Setting a workspace up once

I add workspaces myself from the registry, then edit each one & paste the matching override. Leave the persistent profile path empty so nothing survives the session.

| Lane | Override to paste | What it's for |
| --- | --- | --- |
| VLAN 74 | `{"network":"lab74","dns":["9.9.9.9","149.112.112.112"]}` | Browsers, phishing links, tooling |
| VLAN 77 | `{"network":"lab77","dns":["192.168.77.10"]}` | Samples & disposable targets |
| VLAN 79 | `{"network":"lab79","dns":["192.168.79.10"]}` | Artifact review |

Nothing listens at `192.168.77.10` or `192.168.79.10`, which is the point: lookups fail inside the lane instead of leaking. Dropping the `dns` member lets Docker's embedded resolver at `127.0.0.11` forward through the management host, which quietly defeats an offline lane.

The `Lab Sessions` group already enforces the rest: upload allowed, download blocked, clipboard off in both directions, a one-hour limit, & no persistent profile.

## Opening a phishing link

Lane 74. Check the Proton route & VPN object are both enabled, then launch a browser workspace.

Before clicking anything, confirm the egress is Proton's & not mine:

```bash
curl -s ifconfig.me
```

Then follow the link, read the fake page, & note what I need. Anything I want to keep, I type into my own notes rather than downloading, because download is blocked on these workspaces by design. End the session when done; the container is destroyed with it.

What this buys me: the page sees a Proton exit address, never my home IP, & if the tunnel drops mid-session the traffic stops instead of falling back. What it doesn't buy me: permission to run the payload. If I want to execute what the page served, that's the next workflow, in a different lane.

## Practising against a target

Tooling on lane 74, target on lane 77. Start the target session first, then read its address from inside it:

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

Run that on `purple-server`. Then launch a workspace on lane 77 & drag the sample into the session window; it lands in the session's `Uploads` directory. Upload works even though the lane has no Internet at all, because the transfer rides the HTTPS connection my browser already has to Kasm rather than the container's network.

Execute it & watch. Expect DNS to fail and outbound connections to time out. That's the design: the sample cannot reach its operator, cannot pull a second stage, and cannot attack anyone else from my address. What I get is the local behaviour, the filesystem changes, and the fact & shape of its attempts.

When finished, end the session, then roll the host back:

```bash
qm shutdown 122 --timeout 180
qm rollback 122 pre-malware-2026-07-28 --start
```

Rolling back reverts Kasm's own database along with everything else, so a workspace I added after the snapshot disappears too. I take a fresh snapshot whenever I finish changing workspaces or settings, & then a rollback only costs me the session I just ran.

Three things not to do here. A Windows `.exe` will not run at all, because a Linux container has nothing to execute it, and that work needs a VM. Never mount a share from another host into the session, since that hands a live sample a filesystem path into the lab. And don't run a sample on lane 74 for convenience; that lane has working Internet.

## Inspecting a file without running it

Lane 79 for anything I want kept away from live sessions, lane 77 if it's part of a detonation I'm already running. Strings, hashes, unpacking, reading a suspicious PDF or an Office macro, and triaging a disk image are all fine here, because nothing hostile executes.

Neither lane has Internet, so a reputation lookup means copying the hash out to a lane 74 session or to my own machine. Pasting a hash is the safer habit anyway; uploading the sample itself hands it to a third party.

## Reviewing artifacts afterwards

Lane 79. It cannot be reached from 74 or 77 and cannot initiate toward either, so findings can't be touched by something still running in another lane. I reach it through the Kasm UI, never from another session.

Download stays blocked on the malware workspaces. If I want to pull a written report back to my PC, I enable download on the review workspace only, and I keep it off everywhere else.

## Checks when something feels wrong

From a lane 74 session, the exit address should be Proton's, and stopping Proton should kill Internet access entirely rather than fall back. From a 77 or 79 session, both of these must fail:

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

Five concurrent sessions and one named user, which is the Community Edition cap.

Sessions are not serialised, so a sample can run beside another workspace. A container escape reaches every session on the host through the shared kernel no matter what the gateway does to their lanes. Closing that means running one session at a time.

The host itself is monitored on `192.168.78.10:9100` only, so `node_exporter` never answers on a lab lane.

## Related records

- [Kasm Session Isolation - 2026-07-28](Change%20Records/Kasm%20Session%20Isolation%20-%202026-07-28.md)
- [Kasm Session Isolation plan](Change%20Plans/Kasm%20Session%20Isolation.md)
- [Deployment](Deployment.md)
- [Isolated Security Lab](../../../Architecture/Isolated-Security-Lab.md)
