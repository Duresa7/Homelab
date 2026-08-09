# TNIO AI Bot

**Created:** 2026-07-09  
**Last updated:** 2026-08-09

I preserved the TNIO lore-retrieval source snapshots, OpenClaw-backed inference records, evaluation tests, runtime configuration, product description, & dated accuracy work formerly operated on `ai-bravo-02`. I moved the stopped CT 105 records out of the active tree on 2026-07-25 and retired the guest early on 2026-08-09 by deleting it and its root volume. The [guest record](../../Operations/Inventory/Galaxy/AI%20Bravo%2002%20Archived%20Guest%20-%202026-07-25.md) preserves the final configuration and retirement verification.

## Layout

- `Source/lore-rag/`: primary lore RAG and Discord bot source snapshot
- `Source/lore-rag-remote/`: remote deployment source snapshot
- `Source/Experimental/lore-rag/`: experimental and scratch implementation
- `Source/Legacy/`: earlier root-level implementations I keep for comparison
- `Tests/`: evaluation and remote accuracy tests
- `Documentation/Product/`: product overview
- `Documentation/Change Records/`: dated fixes, audits, and accuracy upgrades
- `Documentation/Reference/`: supporting reference material
- `Configuration/`: service units and remote-state configuration snapshots
- `Evidence/`: corpus audits and remote snapshots
- `Artifacts/`: deployment bundles and generated state

Source files that reference `/home/aibravo/lore-rag` describe the former Linux runtime.

## Key Records

- [Product overview](Documentation/Product/TNIO-Librarian-Product-Overview.md)
- [OpenClaw integration and fixes report](Documentation/Change%20Records/tnio-bot-fixes-report-2026-05-11.md), including the archived gateway service, inference command, and queue findings
- [Secondary deep corpus audit](Documentation/Change%20Records/tnio-bot-secondary-deep-corpus-audit-report-2026-05-12.md), the 2026-05-12 source-authority and overlap analysis
- [Change records](Documentation/Change%20Records/)
