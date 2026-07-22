# GNOME Wired Network Indicator Showed a Question Mark on `debian-dev`

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Investigated:** 2026-07-15  
**Owner:** Galaxy VM 102 / `debian-dev`  
**Status:** Resolved

## Reproduction

GNOME displayed a question mark for the wired connection while DNS, the default route, and internet access continued to work. My tight CLI reproduction was:

```sh
state=$(nmcli -t -f STATE general)
ethernet=$(nmcli -t -f DEVICE,TYPE,STATE,CONNECTION device status | grep ':ethernet:')
test "$state" = connected && echo "$ethernet" | grep -q ':connected:'
```

Before repair, `state=connected` but `ens18:ethernet:unmanaged:` caused the assertion to fail consistently.

## Root cause

The Debian server-style installation still declared `ens18` in `/etc/network/interfaces` and ran it through `networking.service` plus `dhcpcd`. NetworkManager was configured with the standard ifupdown plugin setting `managed=false`, so GNOME's network UI could not associate the working kernel interface with a managed wired connection.

I briefly tested the Debian connectivity-check package as a secondary hypothesis. Its official `network-test.debian.org` endpoint did not resolve from my network, so I removed the package; leaving it enabled would have risked a different limited-connectivity question mark. Connectivity status now comes from the managed connection and working global route without an external probe.

## Corrective action

- I created native NetworkManager profile `Wired connection 1` for `ens18` with autoconnect enabled.
- I preserved the established management address explicitly: `192.168.40.135/24`, gateway `192.168.40.1`, and DNS `192.168.40.1`.
- I removed only the `ens18` stanza from `/etc/network/interfaces`; loopback remains under ifupdown.
- I performed the network-ownership cutover through the Proxmox guest agent with an automatic rollback to `/etc/network/interfaces.pre-networkmanager-20260715` if address, gateway, DNS, or NetworkManager assertions failed.

My first two attempts rolled back safely. The first exposed incorrect `ifdown` ordering. The second proved NetworkManager worked but received DHCP address `.136` because the old dhcpcd identity was inherited from the source template rather than the VM's current MAC. The final profile used the already-established `.135` address and passed immediately.

## Verification

- The GNOME-facing loop passed three consecutive times with `state=connected` and `ens18:ethernet:connected:Wired connection 1`.
- Restarting NetworkManager through the guest agent reactivated the profile automatically on attempt 2.
- Address `.135`, the `.1` default gateway, DNS resolution, and an HTTPS request to `deb.debian.org` all passed.
- SSH, GDM, and QEMU Guest Agent remained active; no failed systemd units were present.
- NetworkManager consumed 0.5% CPU in the final sample. A separate elevated desktop CPU sample was attributable to GNOME Shell, GNOME Software/PackageKit, and Chrome, not a network loop; the follow-up system sample was 97.6% idle and the final SSH Manager health result was `healthy`.
