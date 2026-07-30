# S06 Repository Validation

**Created:** 2026-07-30  
**Last updated:** 2026-07-30

**Captured:** 2026-07-30 10:20:50 UTC  
**Target:** local workspace  
**Mechanism:** local shell execution  
**Shell:** PowerShell  
**Working directory:** `D:\Documents\Homelab`

## Failed Attempt

I first ran the dashboard harness from the repository root:

```powershell
node harness.js
```

**Standard output:** empty

**Standard error:**

```text
node:internal/modules/cjs/loader:1520
  throw err;
  ^

Error: Cannot find module 'D:\Documents\Homelab\harness.js'
    at Module._resolveFilename (node:internal/modules/cjs/loader:1517:15)
    at defaultResolveImpl (node:internal/modules/cjs/loader:1511:19)
    at resolveForCJSWithHooks (node:internal/modules/cjs/loader:1516:22)
    at Module._load (node:internal/modules/cjs/loader:1314:37)
    at TracingChannel.traceSync (node:diagnostics_channel:328:14)
    at wrapModuleLoad (node:internal/modules/cjs/loader:272:24)
    at Module.executeUserEntryPoint [as runMain] (node:internal/modules/run_main:171:5)
    at node:internal/main/run_main_module:36:49 {
  code: 'MODULE_NOT_FOUND',
  requireStack: []
}

Node.js v24.18.0
```

**Exit code:** `1`

The harness lives under `Mission Control`, so I corrected the working directory in the guarded validation command.

## Validation Command

```powershell
python -m unittest Platforms.Ansible.Tests.test_reconcile_semaphore
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m compileall -q Platforms/Ansible/Scripts/reconcile_semaphore.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python Platforms/Ansible/Source/ssh-key-automation/tests/validate_project.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python Platforms/Ansible/Source/fleet-updates/tests/validate_project.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python Platforms/Ansible/Source/monitoring-exporters/tests/validate_project.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Push-Location 'Mission Control'
node harness.js
$harnessExit = $LASTEXITCODE
Pop-Location
if ($harnessExit -ne 0) { exit $harnessExit }
git diff --check
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Get-Date -AsUTC -Format "'captured='yyyy-MM-dd HH:mm:ss 'UTC'"
```

## Standard Output

```text
Validation passed without identity files: live identity records are absent; 14 supported hosts, 0 unknown hosts, and 13 Semaphore templates validated.
Validation passed: 11 OS-update hosts, 6 compose hosts, 22 projects.
Validation passed: 9 node_exporter hosts, 8 cAdvisor hosts.
checks run: 1175
all passed
captured=2026-07-30 10:20:50 UTC
```

## Standard Error

```text
........
----------------------------------------------------------------------
Ran 8 tests in 0.039s

OK
warning: in the working copy of 'Platforms/Ansible/Documentation/Architecture.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'Platforms/Ansible/Documentation/Change Records/Semaphore and Ansible Project Parity - 2026-07-30.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'Platforms/Ansible/Documentation/Runbook.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'Platforms/Ansible/Documentation/TODO.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'Platforms/Ansible/Documentation/Troubleshooting/Monitoring exporter check mode cannot complete - 2026-07-30.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'Platforms/Ansible/Evidence/Semaphore and Ansible Project Parity - 2026-07-30/Evidence-Index.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'Platforms/Ansible/README.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'Platforms/Ansible/Scripts/reconcile_semaphore.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'Platforms/Ansible/Source/monitoring-exporters/README.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'Platforms/Ansible/Tests/test_reconcile_semaphore.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'TODO.md', LF will be replaced by CRLF the next time Git touches it
```

**Exit code:** `0`
