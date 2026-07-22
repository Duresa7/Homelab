# PeaNUT UPS Dashboard Deployment Plan

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Status:** Completed on 2026-07-22. See the [deployment record](../Change%20Records/PeaNUT%20UPS%20Dashboard%20Deployment%20-%202026-07-22.md).

## Outcome

I will expose live load, charge, runtime, voltage, & state from both BR1500MS2 units through one authenticated PeaNUT 6.0.0 dashboard. This project does not enable automated host or guest shutdown.

## Steps

### Step 1: Inspect the existing state

- Confirm each APC USB HID device on its physical Proxmox host.
- Record Proxmox, Debian, Docker, Compose, firewall, listener, & workload baselines.
- Confirm TCP/3493 & dashboard TCP/8090 are unused.

### Step 2: Prepare configuration & recovery points

- Pin PeaNUT 6.0.0 by the Linux AMD64 manifest digest.
- Store the dashboard login in 1Password and keep the value out of Git & evidence.
- Save the pre-change Galaxy firewall file before adding TCP/3493 access.

### Step 3: Deploy NUT telemetry

- Install Debian NUT 2.8.1-5 on Red & Grey.
- Bind each `usbhid-ups` driver to the local APC USB device.
- Publish telemetry on the matching MGMT-A address without configuring `upsmon` shutdown actions.

### Step 4: Deploy PeaNUT

- Deploy the pinned container on `docker-main` at TCP/8090.
- Configure `192.168.70.13:3493` & `192.168.70.10:3493` as read-only NUT endpoints.
- Restrict the cross-VLAN path to `docker-main` and the two NUT hosts.

### Step 5: Verify & document

- Confirm both UPS devices return identity, load, charge, runtime, voltage, & line state.
- Confirm the recreated PeaNUT container is healthy and enumerates both devices.
- Confirm existing containers & Proxmox guests remain running.
- Update the platform, power, firewall, service inventory, root TODO, Mission Control, & dated change record.

## Stop Conditions

- Stop if either USB device isn't identified as APC vendor `051d`, product `0002`.
- Stop if the NUT driver exposes no usable telemetry after one configuration correction.
- Stop before any UniFi mutation until its preview has been reviewed under the required preview-and-confirm flow.
- Stop if a package or container action interrupts an existing guest or Docker workload.

## Rollback

I can stop and remove the PeaNUT Compose project without touching NUT. I can restore the saved `/etc/pve/firewall/cluster.fw`, disable the two NUT server units, restore their backed-up configuration files, & remove the packages after confirming no shutdown client depends on them.
