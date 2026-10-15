# Purple Server NIC Transmit Hang Evidence

**Created:** 2026-10-15  
**Last updated:** 2026-10-15

This journal capture retains the commands and output for Purple's transmit hang, cluster membership loss and power-key recovery.

| Step | Evidence | What it proves |
|---|---|---|
| S01 | [Hang, membership and power-key recovery](Logs/S01%20Hang,%20Membership%20and%20Power-Key%20Recovery%20-%202026-10-15.md) | The first and last e1000e hang blocks retain the same stuck transmit-ring values across 50 minutes 36 seconds. Purple lost quorum while the other four nodes stayed quorate; the power key initiated a clean guest shutdown, and Purple booted the already-installed kernel and rejoined the five-node cluster. |

The [incident report](../../Purple%20Server%20NIC%20Transmit%20Hang%20-%202026-10-14.md) holds the timeline, impact, findings, corrective action and validation.
