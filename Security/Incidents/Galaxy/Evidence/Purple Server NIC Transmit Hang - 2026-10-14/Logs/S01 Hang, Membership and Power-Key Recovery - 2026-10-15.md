# S01 Hang, Membership and Power-Key Recovery

**Created:** 2026-10-15  
**Last updated:** 2026-10-15

**Captured:** 2026-10-15 00:54 EDT, from the retained journal of the boot that ended at 00:35:29 EDT  
**Targets:** `purple-server`, 192.168.70.11, and `grey-server`, 192.168.70.10  
**Mechanism:** SSH Manager `ssh_execute`, root shell  
**Working directory:** SSH Manager default

Output is verbatim. Nothing in it needed redaction; the boot-time NIC line that carries Purple's MAC address is outside these windows and is not included.

## purple-server: first hang, Corosync and pmxcfs

### Command

```sh
journalctl -b -1 --no-pager -o short-iso --since '2026-10-14 23:44:45' --until '2026-10-14 23:44:52' | awk '/Detected Hardware Unit Hang/{f=1} f&&/^2026/&&!/Detected Hardware Unit Hang/{exit} f' | head -20
journalctl -b -1 --no-pager -o short-iso --since '2026-10-14 23:44:45' --until '2026-10-14 23:45:02' -u corosync -u pve-cluster
```

### Standard output

```text
2026-10-14T23:44:51-04:00 purple-server kernel: e1000e 0000:00:1f.6 nic0: Detected Hardware Unit Hang:
                                                  TDH                  <50>
                                                  TDT                  <82>
                                                  next_to_use          <82>
                                                  next_to_clean        <50>
                                                buffer_info[next_to_clean]:
                                                  time_stamp           <12e2a3af4>
                                                  next_to_watch        <51>
                                                  jiffies              <12e2a3f80>
                                                  next_to_watch.status <0>
                                                MAC Status             <80083>
                                                PHY Status             <796d>
                                                PHY 1000BASE-T Status  <3800>
                                                PHY Extended Status    <3000>
                                                PCI Status             <10>
2026-10-14T23:44:51-04:00 purple-server corosync[1866]:   [KNET  ] link: host: 4 link: 0 is down
2026-10-14T23:44:51-04:00 purple-server corosync[1866]:   [KNET  ] link: host: 4 link: 1 is down
2026-10-14T23:44:51-04:00 purple-server corosync[1866]:   [KNET  ] link: host: 1 link: 0 is down
2026-10-14T23:44:51-04:00 purple-server corosync[1866]:   [KNET  ] link: host: 1 link: 1 is down
2026-10-14T23:44:51-04:00 purple-server corosync[1866]:   [KNET  ] link: host: 5 link: 0 is down
2026-10-14T23:44:51-04:00 purple-server corosync[1866]:   [KNET  ] link: host: 5 link: 1 is down
2026-10-14T23:44:51-04:00 purple-server corosync[1866]:   [KNET  ] link: host: 3 link: 0 is down
2026-10-14T23:44:51-04:00 purple-server corosync[1866]:   [KNET  ] link: host: 3 link: 1 is down
2026-10-14T23:44:51-04:00 purple-server corosync[1866]:   [KNET  ] host: host: 4 (passive) best link: 0 (pri: 1)
2026-10-14T23:44:51-04:00 purple-server corosync[1866]:   [KNET  ] host: host: 4 has no active links
2026-10-14T23:44:51-04:00 purple-server corosync[1866]:   [KNET  ] host: host: 4 (passive) best link: 0 (pri: 1)
2026-10-14T23:44:51-04:00 purple-server corosync[1866]:   [KNET  ] host: host: 4 has no active links
2026-10-14T23:44:51-04:00 purple-server corosync[1866]:   [KNET  ] host: host: 1 (passive) best link: 0 (pri: 1)
2026-10-14T23:44:51-04:00 purple-server corosync[1866]:   [KNET  ] host: host: 1 has no active links
2026-10-14T23:44:51-04:00 purple-server corosync[1866]:   [KNET  ] host: host: 1 (passive) best link: 0 (pri: 1)
2026-10-14T23:44:51-04:00 purple-server corosync[1866]:   [KNET  ] host: host: 1 has no active links
2026-10-14T23:44:51-04:00 purple-server corosync[1866]:   [KNET  ] host: host: 5 (passive) best link: 0 (pri: 1)
2026-10-14T23:44:51-04:00 purple-server corosync[1866]:   [KNET  ] host: host: 5 has no active links
2026-10-14T23:44:51-04:00 purple-server corosync[1866]:   [KNET  ] host: host: 5 (passive) best link: 0 (pri: 1)
2026-10-14T23:44:51-04:00 purple-server corosync[1866]:   [KNET  ] host: host: 5 has no active links
2026-10-14T23:44:51-04:00 purple-server corosync[1866]:   [KNET  ] host: host: 3 (passive) best link: 0 (pri: 1)
2026-10-14T23:44:51-04:00 purple-server corosync[1866]:   [KNET  ] host: host: 3 has no active links
2026-10-14T23:44:51-04:00 purple-server corosync[1866]:   [KNET  ] host: host: 3 (passive) best link: 0 (pri: 1)
2026-10-14T23:44:51-04:00 purple-server corosync[1866]:   [KNET  ] host: host: 3 has no active links
2026-10-14T23:44:53-04:00 purple-server corosync[1866]:   [TOTEM ] Token has not been received in 3712 ms
2026-10-14T23:44:55-04:00 purple-server corosync[1866]:   [TOTEM ] A processor failed, forming new configuration: token timed out (4950ms), waiting 5940ms for consensus.
2026-10-14T23:45:01-04:00 purple-server corosync[1866]:   [QUORUM] Sync members[1]: 2
2026-10-14T23:45:01-04:00 purple-server corosync[1866]:   [QUORUM] Sync left[4]: 1 3 4 5
2026-10-14T23:45:01-04:00 purple-server corosync[1866]:   [TOTEM ] A new membership (2.2ca) was formed. Members left: 1 3 4 5
2026-10-14T23:45:01-04:00 purple-server corosync[1866]:   [TOTEM ] Failed to receive the leave message. failed: 1 3 4 5
2026-10-14T23:45:01-04:00 purple-server pmxcfs[1697]: [dcdb] notice: members: 2/1697
2026-10-14T23:45:01-04:00 purple-server pmxcfs[1697]: [status] notice: members: 2/1697
2026-10-14T23:45:01-04:00 purple-server pmxcfs[1697]: [status] notice: node lost quorum
2026-10-14T23:45:01-04:00 purple-server corosync[1866]:   [QUORUM] This node is within the non-primary component and will NOT provide any services.
2026-10-14T23:45:01-04:00 purple-server corosync[1866]:   [QUORUM] Members[1]: 2
2026-10-14T23:45:01-04:00 purple-server corosync[1866]:   [MAIN  ] Completed service synchronization, ready to provide service.
2026-10-14T23:45:01-04:00 purple-server pmxcfs[1697]: [dcdb] crit: received write while not quorate - trigger resync
2026-10-14T23:45:01-04:00 purple-server pmxcfs[1697]: [dcdb] crit: leaving CPG group
2026-10-14T23:45:01-04:00 purple-server pmxcfs[1697]: [dcdb] notice: start cluster connection
2026-10-14T23:45:01-04:00 purple-server pmxcfs[1697]: [dcdb] crit: cpg_join failed: CS_ERR_EXIST
2026-10-14T23:45:01-04:00 purple-server pmxcfs[1697]: [dcdb] crit: can't initialize service
```

## purple-server: hang count, last hang and power-key shutdown

### Command

```sh
journalctl -b -1 -k --no-pager -o short-iso | grep -c 'Detected Hardware Unit Hang'
journalctl -b -1 -k --no-pager -o short-iso --since '2026-10-15 00:35:26' | awk '/Detected Hardware Unit Hang/{f=1} f' | head -16
journalctl -b -1 --no-pager -o short-iso --since '2026-10-15 00:35:00' --until '2026-10-15 00:35:21' | grep -E 'Power key|Powering off|System is powering down|Stopping VM|end task.*qmshutdown|all VMs and CTs stopped|Stopped [0-9]+\.scope'
last -x -F | head -3
```

### Standard output

```text
1519
2026-10-15T00:35:27-04:00 purple-server kernel: e1000e 0000:00:1f.6 nic0: Detected Hardware Unit Hang:
                                                  TDH                  <50>
                                                  TDT                  <82>
                                                  next_to_use          <82>
                                                  next_to_clean        <50>
                                                buffer_info[next_to_clean]:
                                                  time_stamp           <12e2a3af4>
                                                  next_to_watch        <51>
                                                  jiffies              <12e589301>
                                                  next_to_watch.status <0>
                                                MAC Status             <80083>
                                                PHY Status             <796d>
                                                PHY 1000BASE-T Status  <3800>
                                                PHY Extended Status    <3000>
                                                PCI Status             <10>
2026-10-15T00:35:29-04:00 purple-server systemd-shutdown[1]: Syncing filesystems and block devices.
2026-10-15T00:35:03-04:00 purple-server systemd-logind[792]: Power key pressed short.
2026-10-15T00:35:03-04:00 purple-server systemd-logind[792]: Powering off...
2026-10-15T00:35:03-04:00 purple-server systemd-logind[792]: System is powering down.
2026-10-15T00:35:07-04:00 purple-server pvesh[2490780]: Stopping VM 401 (timeout = 180 seconds)
2026-10-15T00:35:07-04:00 purple-server pvesh[2490780]: Stopping VM 121 (timeout = 180 seconds)
2026-10-15T00:35:14-04:00 purple-server systemd[1]: Stopped 121.scope.
2026-10-15T00:35:15-04:00 purple-server pve-guests[2490783]: end task UPID:purple-server:002601A1:04A2E267:6AD057FB:qmshutdown:121:root@pam:
2026-10-15T00:35:18-04:00 purple-server systemd[1]: Stopped 401.scope.
2026-10-15T00:35:19-04:00 purple-server pve-guests[2490783]: end task UPID:purple-server:002601A0:04A2E266:6AD057FB:qmshutdown:401:root@pam:
2026-10-15T00:35:20-04:00 purple-server pve-guests[2490783]: all VMs and CTs stopped
reboot   system boot  7.0.14-22-pve    Thu Oct 15 00:36:09 2026 - still running            
reboot   system boot  7.0.14-20-pve    Tue Oct  6 00:31:10 2026 - Thu Oct 15 00:35:03 2026 (9+00:03)
shutdown system down  7.0.14-20-pve    Thu Oct 15 00:35:03 2026 - Thu Oct 15 00:36:09 2026  (00:01)
```

The TX ring registers in the last hang block, 50 minutes 36 seconds after the first, are unchanged: TDH `<50>`, TDT `<82>`, next_to_watch `<51>` and the stuck descriptor's time_stamp `<12e2a3af4>`. Only `jiffies` advanced.

## grey-server: Purple leaves and rejoins

### Command

```sh
journalctl --no-pager -o short-iso -u corosync --since '2026-10-14 23:44:50' --until '2026-10-14 23:45:02'
journalctl --no-pager -o short-iso -u corosync --since '2026-10-15 00:36:40' --until '2026-10-15 00:36:50'
```

### Standard output

```text
2026-10-14T23:44:52-04:00 grey-server corosync[1783]:   [KNET  ] link: host: 2 link: 0 is down
2026-10-14T23:44:52-04:00 grey-server corosync[1783]:   [KNET  ] link: host: 2 link: 1 is down
2026-10-14T23:44:52-04:00 grey-server corosync[1783]:   [KNET  ] host: host: 2 (passive) best link: 0 (pri: 1)
2026-10-14T23:44:52-04:00 grey-server corosync[1783]:   [KNET  ] host: host: 2 has no active links
2026-10-14T23:44:52-04:00 grey-server corosync[1783]:   [KNET  ] host: host: 2 (passive) best link: 0 (pri: 1)
2026-10-14T23:44:52-04:00 grey-server corosync[1783]:   [KNET  ] host: host: 2 has no active links
2026-10-14T23:44:53-04:00 grey-server corosync[1783]:   [TOTEM ] Token has not been received in 3712 ms
2026-10-14T23:45:01-04:00 grey-server corosync[1783]:   [QUORUM] Sync members[4]: 1 3 4 5
2026-10-14T23:45:01-04:00 grey-server corosync[1783]:   [QUORUM] Sync left[1]: 2
2026-10-14T23:45:01-04:00 grey-server corosync[1783]:   [TOTEM ] A new membership (1.2ca) was formed. Members left: 2
2026-10-14T23:45:01-04:00 grey-server corosync[1783]:   [TOTEM ] Failed to receive the leave message. failed: 2
2026-10-14T23:45:01-04:00 grey-server corosync[1783]:   [QUORUM] Members[4]: 1 3 4 5
2026-10-14T23:45:01-04:00 grey-server corosync[1783]:   [MAIN  ] Completed service synchronization, ready to provide service.
2026-10-15T00:36:43-04:00 grey-server corosync[1783]:   [KNET  ] link: Resetting MTU for link 0 because host 2 joined
2026-10-15T00:36:43-04:00 grey-server corosync[1783]:   [KNET  ] host: host: 2 (passive) best link: 0 (pri: 1)
2026-10-15T00:36:43-04:00 grey-server corosync[1783]:   [QUORUM] Sync members[5]: 1 2 3 4 5
2026-10-15T00:36:43-04:00 grey-server corosync[1783]:   [QUORUM] Sync joined[1]: 2
2026-10-15T00:36:43-04:00 grey-server corosync[1783]:   [TOTEM ] A new membership (1.2d3) was formed. Members joined: 2
2026-10-15T00:36:43-04:00 grey-server corosync[1783]:   [QUORUM] Members[5]: 1 2 3 4 5
2026-10-15T00:36:43-04:00 grey-server corosync[1783]:   [MAIN  ] Completed service synchronization, ready to provide service.
2026-10-15T00:36:43-04:00 grey-server corosync[1783]:   [KNET  ] pmtud: Global data MTU changed to: 1397
2026-10-15T00:36:45-04:00 grey-server corosync[1783]:   [KNET  ] rx: host: 2 link: 1 is up
2026-10-15T00:36:45-04:00 grey-server corosync[1783]:   [KNET  ] link: Resetting MTU for link 1 because host 2 joined
2026-10-15T00:36:45-04:00 grey-server corosync[1783]:   [KNET  ] host: host: 2 (passive) best link: 0 (pri: 1)
2026-10-15T00:36:45-04:00 grey-server corosync[1783]:   [KNET  ] pmtud: Global data MTU changed to: 1397
```
