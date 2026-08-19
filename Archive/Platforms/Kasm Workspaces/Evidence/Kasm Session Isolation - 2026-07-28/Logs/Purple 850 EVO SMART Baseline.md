# Purple 850 EVO SMART Baseline

**Created:** 2026-07-28  
**Last updated:** 2026-07-28

**Node:** `purple-server`  
**Device:** `/dev/sda`  
**Model:** Samsung SSD 850 EVO 250GB  
**Use:** `ssd-lvm2` general VM and LXC thin storage

| Counter | Before | After |
| --- | ---: | ---: |
| SMART overall health | PASSED | PASSED |
| Power-on hours | 45,241 | 45,242 |
| `Wear_Leveling_Count` normalized | 15 | 15 |
| `Wear_Leveling_Count` raw | 1,800 | 1,801 |
| Reallocated sectors | 0 | 0 |
| CRC errors | 0 | 0 |
| Uncorrectable errors | 0 | 0 |

I will move workloads off this drive if the normalized wear counter falls below 10 or any of the three error counters becomes nonzero.
