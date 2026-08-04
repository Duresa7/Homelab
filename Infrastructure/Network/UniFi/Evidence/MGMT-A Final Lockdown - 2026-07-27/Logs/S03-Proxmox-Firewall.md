# S03 Proxmox Firewall

**Created:** 2026-07-27  
**Last updated:** 2026-07-27

I removed two related pieces from the live cluster firewall:

- the `pve_termix` IPSet containing `docker-main`
- the TCP 22 accept sourced from that IPSet

The before and after diff contained no other change. The live after-file SHA256 is `e26a6380cdd19f742dfdb5ec9ddd3c03f5202a894acdf751118dec22d5983735`.

`pve-firewall compile` passed. `pve-firewall status` reported `enabled/running` on Grey, Purple, Blue, and Red. I removed the temporary candidate, remote rollback copy, and compile log after the retained local exports and final tests were complete.
