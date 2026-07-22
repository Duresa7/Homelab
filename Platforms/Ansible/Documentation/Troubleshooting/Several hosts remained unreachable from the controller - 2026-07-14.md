# Several hosts remained unreachable from the controller

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Investigated:** 2026-07-14

Final TCP probes and Ansible audits classified `supabase-01`, `ai-alpha-01`, `ai-bravo-02`, and `ws-dc-1-main` as unreachable. Direct SSH Manager checks also timed out. `ws-dc-2-secondary` and `obi-pc` timed out and remain deliberately unknown.

UniFi Traffic Flows recorded the controller's SSH attempts as allowed, including prior flows to `edge-01` and `ws-dc-1-main`, so no UniFi firewall change was warranted. `edge-01` became reachable after I enrolled its independently verified host key. The other failures are endpoint availability, host firewall, or SSH-service issues I will investigate when those machines are online.
