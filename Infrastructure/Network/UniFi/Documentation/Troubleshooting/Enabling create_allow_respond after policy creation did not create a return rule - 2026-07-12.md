# Enabling `create_allow_respond` after policy creation did not create a return rule

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Investigated:** 2026-07-12

**Context:** Security-A migration cross-zone Wazuh and monitoring policies.

**Symptom:** New forward policies existed and showed `create_allow_respond=true` after an update, but traffic from `security-01` to Proxmox and DMZ endpoints still timed out. The controller had not created the expected hidden `(Return)` companion.

**Failed attempt:** I updated an already-created policy from `create_allow_respond=false` to `true`. That changed the visible policy data but did not materialize the controller-maintained reverse policy.

**Root cause:** On this controller, the return companion is created only when the policy is initially created with automatic response enabled. Toggling the flag later is not equivalent.

**Corrective action:** I re-created the four required cross-zone policies with automatic response enabled at creation, validated the return path, and removed the superseded forward-only policies. I used a single-port Proxmox test policy to isolate the behavior and removed it after the final combined policy worked.

**Verification:** From `security-01`, `192.168.90.10:9100`, `192.168.70.10:9100`, and `192.168.70.10:8006` each returned HTTP 200. The live controller showed the intended four custom policies with automatic response enabled and no superseded/test policies.
