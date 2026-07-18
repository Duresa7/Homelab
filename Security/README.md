# Security

**Created:** 2026-07-09  
**Last updated:** 2026-07-15

Security contains security operations records rather than deployed security products.

- `Incidents/` — security and service-impacting incident reports
- `Assessments/` — audits, reviews, and risk assessments
- `Hardening/` — cross-system hardening standards and records
  - [Linux Host Baseline Standard](Hardening/Linux-Host-Baseline-Standard.md) — required baseline for every new Linux VM and LXC

Running products such as Splunk and Wazuh remain under `Platforms/` because they are deployed services. Their incident, assessment, or cross-system hardening records may link into this category.
