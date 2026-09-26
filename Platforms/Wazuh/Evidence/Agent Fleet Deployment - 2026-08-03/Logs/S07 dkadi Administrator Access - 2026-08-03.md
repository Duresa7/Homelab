# S07 dkadi Administrator Access

**Created:** 2026-08-03  
**Last updated:** 2026-08-03

**Captured:** 2026-08-03 07:40 through 07:44 EDT  
**Target:** `security-01` Wazuh indexer, dashboard, & server API RBAC  
**Mechanism:** SSH Manager MCP through `ansible-01`; local indexer and Wazuh API calls

## Starting state

The internal indexer user `dkadi` existed with backend role `admin`. The live `all_access` mapping grants that backend role full indexer access, and dashboard `run_as` was already `true`.

Wazuh server RBAC did not contain a rule for `dkadi`. The `administrator` role had only its two default rules, which matched `elastic` and `admin`. This left `dkadi` with indexer administration but without matching Wazuh server administration.

## Change

I created an online SQLite backup before changing RBAC:

```text
/var/ossec/api/configuration/security/rbac.db.pre-dkadi-admin-20260803T114102Z
```

The backup is owned by `wazuh:wazuh`, mode `0640`, & is 102400 bytes.

I used the configured `wazuh-wui` service identity without printing its credential or token. The Wazuh API created rule ID 100:

```json
{
  "name": "wui_dkadi_admin",
  "rule": {
    "FIND": {
      "user_name": "dkadi"
    }
  }
}
```

I linked rule 100 to role ID 1, `administrator`. The API returned `error: 0` and reported rules 1, 2, & 100 on that role.

## Verification

I requested a fresh authorization-context token for `dkadi`, then used it for read-only administrator checks. The result was:

```json
{
  "run_as_user": "dkadi",
  "security_config_http": 200,
  "rbac_mode": "white",
  "effective_role": "administrator",
  "administrator_policy_count": 23,
  "mapping_rule_id": 100
}
```

The Wazuh manager, indexer, & dashboard remained enabled and running. The local dashboard returned HTTP `302`, and the unauthenticated API root returned expected HTTP `401`.

## Rollback

The narrow rollback is to unlink rule ID 100 from role ID 1 through `DELETE /security/roles/1/rules?rule_ids=100`, then delete rule 100 through `DELETE /security/rules?rule_ids=100`. The database backup is an emergency recovery point; restoring it would also discard any Wazuh RBAC changes made after 2026-08-03 07:41 EDT.
