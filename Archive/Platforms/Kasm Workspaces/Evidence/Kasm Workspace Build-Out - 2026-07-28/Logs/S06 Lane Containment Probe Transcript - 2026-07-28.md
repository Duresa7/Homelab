# S06 Lane Containment Probe Transcript

**Created:** 2026-07-28  
**Last updated:** 2026-07-28  
**Captured:** 2026-07-28

The build-out's 36-probe containment matrix was recorded as a summary table because the sessions that produced it were destroyed before the transcript was kept. I re-ran the matrix afterward and kept the output this time. This file is that transcript.

## Method

Four throwaway containers, one per lane, each on the lane's macvlan network with the lane's resolver, using the same image the lane tiles clone from. The entrypoint is overridden so the probes run instead of the desktop, which is the only reason this fits in a single container run.

```bash
docker run --rm --name probe74 -e LANE=74 --network lab74 --dns 9.9.9.9 \
  --entrypoint /bin/bash kasmweb/debian-trixie-desktop:1.19.0-rolling-daily -c "<probe block>"
```

The other three ran with `lab75` and `9.9.9.9`, `lab77` and `192.168.77.10`, `lab79` and `192.168.79.10`. All four ran concurrently. Return codes read: 0 is a successful connection, 2 is a failed name lookup, 124 is `timeout` killing the attempt at three seconds.

The probe writes `/dev/tcp/HOST/PORT` with both slashes. Writing a space in place of the second slash makes every probe fail no matter what the firewall does, which looks identical to a clean pass.

## Transcript

```text
##### lane 74 #####
lane=74
address: 192.168.74.208/24
--- resolver ---
nameserver 127.0.0.11
# Overrides: [nameservers]
getent example.com rc=0
--- protected targets (want every rc non-zero) ---
192.168.78.10:443 rc=124
192.168.80.10:22 rc=124
192.168.70.10:8006 rc=124
192.168.70.11:8006 rc=124
192.168.71.10:22 rc=124
192.168.72.2:443 rc=124
192.168.73.2:9090 rc=124
192.168.1.1:443 rc=124
192.168.10.1:443 rc=124
--- direct internet ---
1.1.1.1:443 rc=0
--- egress address ---
185.98.168.20
##### lane 75 #####
lane=75
address: 192.168.75.208/24
--- resolver ---
nameserver 127.0.0.11
# Overrides: [nameservers]
getent example.com rc=0
--- protected targets (want every rc non-zero) ---
192.168.78.10:443 rc=124
192.168.80.10:22 rc=124
192.168.70.10:8006 rc=124
192.168.70.11:8006 rc=124
192.168.71.10:22 rc=124
192.168.72.2:443 rc=124
192.168.73.2:9090 rc=124
192.168.1.1:443 rc=124
192.168.10.1:443 rc=124
--- direct internet ---
1.1.1.1:443 rc=0
--- egress address ---
<REDACTED: ordinary WAN address>
##### lane 77 #####
lane=77
address: 192.168.77.208/24
--- resolver ---
nameserver 127.0.0.11
# Overrides: [nameservers]
getent example.com rc=2
--- protected targets (want every rc non-zero) ---
192.168.78.10:443 rc=124
192.168.80.10:22 rc=124
192.168.70.10:8006 rc=124
192.168.70.11:8006 rc=124
192.168.71.10:22 rc=124
192.168.72.2:443 rc=124
192.168.73.2:9090 rc=124
192.168.1.1:443 rc=124
192.168.10.1:443 rc=124
--- direct internet ---
1.1.1.1:443 rc=124
--- egress address ---
(none)
##### lane 79 #####
lane=79
address: 192.168.79.208/24
--- resolver ---
nameserver 127.0.0.11
# Overrides: [nameservers]
getent example.com rc=2
--- protected targets (want every rc non-zero) ---
192.168.78.10:443 rc=124
192.168.80.10:22 rc=124
192.168.70.10:8006 rc=124
192.168.70.11:8006 rc=124
192.168.71.10:22 rc=124
192.168.72.2:443 rc=124
192.168.73.2:9090 rc=124
192.168.1.1:443 rc=124
192.168.10.1:443 rc=124
--- direct internet ---
1.1.1.1:443 rc=124
--- egress address ---
(none)
```

One line is redacted. Lane 75's egress printed my ordinary WAN address, and that address does not belong in this repository. Its value is the comparison, not the number: lane 75 returned something other than `185.98.168.20`, which is what proves VLAN 75 is absent from the `KASM Lab Proton Egress` route and reaches the Internet through the normal WAN. Lane 74 returned the Proton exit.

## Results

36 of 36 lane-to-target probes timed out. Every lane failed to reach the Kasm control plane at `192.168.78.10:443`, `app-01`, both Proxmox nodes, the cluster network, Wazuh, Prometheus, and both gateway addresses.

| Lane | Address | DNS | Direct Internet | Egress |
| --- | --- | --- | --- | --- |
| 74 | 192.168.74.208 | Resolves | Reachable | Proton exit `185.98.168.20` |
| 75 | 192.168.75.208 | Resolves | Reachable | Ordinary WAN, redacted above |
| 77 | 192.168.77.208 | Fails, rc=2 | Timed out | None |
| 79 | 192.168.79.208 | Fails, rc=2 | Timed out | None |

Every container took the lane's `.208` address, so Docker honoured the `network` key from the run config in all four lanes.

## On the resolver file

All four lanes show `nameserver 127.0.0.11`, Docker's embedded resolver, with an `# Overrides: [nameservers]` marker. The plan's Phase 3 gate expected the file to name `192.168.77.10` literally and would have halted the build. That expectation was wrong, and the file text is not the thing worth checking.

The embedded resolver forwards only to the upstream Docker was given. On lanes 77 and 79 that upstream is an address where nothing listens, so `getent` returns rc=2 and no query reaches any other resolver. On lanes 74 and 75 the upstream is `9.9.9.9` and lookups succeed. The behaviour is the proof; the file is an implementation detail of how Docker wires it up.

## Cleanup

All four containers ran with `--rm` and removed themselves. I deleted the probe script and its four output files from `/tmp` and confirmed the guest was back to the eight Kasm control-plane containers with nothing matching `probe` or `laneprobe` left in `/tmp`.
