"""Build one of E2B's published templates on e2b-01 from a clone of its repository.

    python build-upstream-template.py code-interpreter <clone>/template
    python build-upstream-template.py desktop <clone>/template

Run from ubuntu-dev with the e2b SDK and the client variables set, and with an
SSH tunnel to e2b-01's port 5008 open (`ssh -N -L 5008:127.0.0.1:5008
dkadi@192.168.80.30`): both templates copy local files in, and the upload URL the
API hands out is http://127.0.0.1:5008/... . The template definitions are
upstream's own `template.py`; only the size differs where noted.
"""
import sys

from e2b import Template

which, src = sys.argv[1], sys.argv[2]
sys.path.insert(0, src)
import template as upstream  # noqa: E402  (upstream's template.py)

if which == "code-interpreter":
    # Upstream build_prod.py: alias code-interpreter-v1, 2 vCPU, 2048 MiB.
    # The e2b-code-interpreter SDK creates from that alias by default.
    tpl, alias, cpu, mem = upstream.make_template(), "code-interpreter-v1", 2, 2048
    # Its pip step fills the build VM's default disk on Embed (Errno 28), so ask
    # for free space explicitly.
    disk = 10240
elif which == "desktop":
    # Upstream builds at 8 vCPU / 8192 MiB, which does not fit e2b-01's hugepage
    # pool. Each build step restores the previous step's snapshot while the old VM
    # still holds its pages, so a step briefly needs twice the memory: 4096 MiB
    # failed with "mmap memfd: cannot allocate memory" against the 3072-page pool.
    # 4 vCPU / 2048 MiB here. The e2b-desktop SDK creates from "desktop".
    tpl, alias, cpu, mem = upstream.template_with_user_workdir, "desktop", 4, 2048
    disk = 8192
else:
    sys.exit("which must be code-interpreter or desktop")

info = Template.build(tpl, alias=alias, cpu_count=cpu, memory_mb=mem, min_free_disk_mb=disk,
                      on_build_logs=lambda e: print(str(e), flush=True))
print("BUILD DONE:", info)
