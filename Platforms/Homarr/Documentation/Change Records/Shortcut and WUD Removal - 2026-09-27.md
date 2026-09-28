# Shortcut and WUD Removal

**Created:** 2026-09-27  
**Last updated:** 2026-09-27

I removed all eight cAdvisor apps, all six WUD apps and the Homarr administration shortcut from the Apps catalog and the single Dashboard board. I removed the WUD integration and its data widget, then compacted the remaining shortcuts into eight rows of four above the other widgets.

Readback confirmed one private board with 32 shortcuts, nine data widgets and nine integrations. No cAdvisor, WUD or Homarr shortcut remains in the catalog, no WUD widget remains, and all remaining shortcuts retain enabled status checks. The other widgets retain their options and integration references. The [shortcut configuration](../../Configuration/App-Shortcuts.json) reflects the remaining apps.

The first WUD app deletion encountered a foreign-key constraint because its integration still referenced it. I deleted the integration first, then completed the app deletions and verified the catalog again. A fresh authenticated browser session rendered all 41 items without page errors or the tested error indicators. I retained no separate transcript or screenshot for this cleanup.

This change removes entries from Homarr only; it does not uninstall services or remove proxy configuration. WUD service retirement is recorded separately in the [retirement record](../../../Prometheus/Documentation/Change%20Records/WUD%20Retirement%20-%202026-09-27.md). The five previously recorded shortcut reachability failures remain outside this change.
