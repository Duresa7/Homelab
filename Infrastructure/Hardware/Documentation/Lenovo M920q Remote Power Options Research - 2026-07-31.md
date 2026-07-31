# Lenovo M920q Remote Power Options Research

**Created:** 2026-07-31  
**Last updated:** 2026-07-31

## Question

I checked whether I can restart or power-cycle the rack-mounted Lenovo ThinkCentre M920q while its bare-metal installer is hung. I made no configuration or power changes during this research.

## Current Answer

I don't have a working remote reset path for Green in its current state. Its Intel AMT management ports don't answer, Bane port 4 has PoE disabled, & the rack has no managed PDU outlet assigned to this machine. Cycling the switch port would only interrupt Ethernet.

A physical power-button action is the available recovery now. For later incidents, I can provision Intel AMT before deployment if this M920q has the AMT-capable SKU, or place its AC adapter on a managed switched outlet.

## Intel AMT

The M920q product line was sold in two manageability configurations: Intel vPro with Intel AMT 12.0, or none. Lenovo also lists an Intel I219-LM onboard Ethernet controller & separate 65 W, 90 W, and 135 W power-adapter options. I can't infer AMT support from the M920q model name alone; I need the machine type, CPU/configuration, or a local firmware check. [Lenovo's M920 Tiny PSREF lists both manageability choices, the I219-LM, & the external adapters](https://psref.lenovo.com/syspool/Sys/PDF/ThinkCentre/ThinkCentre_M920_Tiny/ThinkCentre_M920_Tiny_Spec.html).

AMT can control power when the operating system is unavailable because the Intel Management Engine runs in firmware. It still needs line power, a supported Intel network connection, & prior configuration. Intel states that remote power commands require the managed device to be configured; its setup guide requires AMT to be enabled in Intel MEBx, network access activated, & network preferences entered. [Intel documents the power-management requirement](https://www.intel.com/content/www/us/en/docs/active-management-technology/developer-guide/2021/integrating-intel-amt-remote-power-management.html) and [the MEBx setup sequence](https://www.intel.com/content/www/us/en/docs/active-management-technology/developer-guide/2021/intel-active-management-technology-10.html).

The management path uses TCP 16992 for HTTP WS-Management or TCP 16993 for HTTPS WS-Management. Redirection features use TCP 16994 or TLS on 16995; RMCP uses 623 or TLS on 664. KVM can also involve TCP 5900. [Intel's port table defines each listener](https://software.intel.com/sites/manageability/AMT_Implementation_and_Reference_Guide/WordDocuments/manageabilityports.htm). A closed or unreachable 16992/16993 path means I can't issue an AMT power command from the network. It doesn't prove which prerequisite is missing; the SKU, MEBx provisioning, VLAN path, firewall path, & credentials remain separate checks.

KVM isn't automatic with AMT. Intel requires the KVM setting enabled in MEBx, the redirection service enabled, its listener enabled, & authentication before a viewer connects. [Intel documents those KVM prerequisites & ports](https://www.intel.com/content/www/us/en/docs/active-management-technology/developer-guide/2021/integrating-kvm-feature-into-a-management-console.html). If Green wasn't provisioned before the installer hung, I can't add this path without local firmware access.

## Wake-on-LAN

Wake-on-LAN can't restart this powered-on hung installer. Intel defines Wake on Magic Packet as a wake mechanism for standby, with an optional setting for a shutdown or powered-off state. It doesn't define a reset command for a machine already running in the S0 power state. [Intel's Wake-on-LAN guide describes standby & power-off behavior](https://edc.intel.com/content/www/us/en/design/products/ethernet/adapters-and-devices-user-guide/29.4/wake-on-lan-wol-options/https%3A%25252F%25252Fedc.intel.com%25252Fcontent%25252Fwww%25252Fcn%25252Fzh%25252Fdesign%25252Fproducts%25252Fethernet%25252Fadapters-and-devices-user-guide%25252F29.4%25252Fwake-on-lan-wol-options%25252F/). A magic packet is useful after shutdown only when firmware, adapter, & power-state settings preserve that wake path.

After I installed Proxmox, `ethtool nic0` reported `Supports Wake-on: pumbg` and `Wake-on: g`. That proves the running driver has Magic Packet wake enabled. It still does not prove the firmware will wake from soft-off, and it does not turn Wake-on-LAN into a reset mechanism for a running system.

## UniFi Port Control

UniFi treats port state & PoE as different controls. Port state governs whether Ethernet switching is active; the PoE setting governs whether the switch supplies power to a connected client. [Ubiquiti documents both controls separately](https://help.ui.com/hc/en-us/articles/33402927617047-UniFi-Switch-Settings).

Green receives power from its Lenovo AC adapter, not from Bane port 4. With PoE disabled, toggling or disabling that data port cannot interrupt the adapter's AC input. A real remote hard power cycle needs a switched AC outlet. Ubiquiti's Power Distribution Pro is one official example: it has 16 power-control outlets & is designed to manage each connection remotely. [Ubiquiti lists its outlet count & electrical ratings](https://techspecs.ui.com/unifi/integrations/usp-pdu-pro) and [describes per-connection remote management](https://store.ui.com/us/en/collections/unifi-power-tech-power-distribution/products/usp-pdu-pro?variant=USP-PDU-Pro).

## Recommendation

I should recover this install with the physical power button. Before relying on AMT later, I should confirm Green's exact M920q configuration, enter MEBx locally, provision AMT with a new credential, enable only the required power or KVM features, place its management address on the intended VLAN, & test a controlled reset while the machine is healthy.

If Green lacks the AMT-capable configuration, I should use a managed AC outlet. I should also set and test Lenovo's after-power-loss behavior before depending on an outlet cycle, because removing AC and restoring AC are separate from the machine's firmware decision to turn back on.
