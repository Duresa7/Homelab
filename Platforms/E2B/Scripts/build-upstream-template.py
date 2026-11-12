"""Build E2B's Code Interpreter or Desktop template on e2b-01, moved to Ubuntu 26.04.

    python build-upstream-template.py code-interpreter <clone>/template
    python build-upstream-template.py desktop <clone>/template

<clone> is a clone of e2b-dev/code-interpreter at
c49b78602c29e44d07e196604de515dfa6b12744 or e2b-dev/desktop at
91f23acaab7312e847596acc44e6f7763f56917f. The script copies its template folder
to a temporary directory, applies ../Configuration/<name>-ubuntu-26.04.patch
there, and builds from upstream's own template.py. The clone is left untouched.

Run from ubuntu-dev with the e2b SDK, the client variables set, and an SSH tunnel
to e2b-01's port 5008 open (`ssh -N -L 5008:127.0.0.1:5008 dkadi@192.168.80.30`):
both templates copy local files in, and the upload URL the API hands out is
http://127.0.0.1:5008/... .
"""
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

from e2b import Template

which, src = sys.argv[1], pathlib.Path(sys.argv[2]).resolve()
if which not in ("code-interpreter", "desktop"):
    sys.exit("which must be code-interpreter or desktop")
patch = pathlib.Path(__file__).resolve().parent.parent / "Configuration" / f"{which}-ubuntu-26.04.patch"

work = pathlib.Path(tempfile.mkdtemp(prefix=f"e2b-{which}-")) / "template"
shutil.copytree(src, work)
subprocess.run(["patch", "-p2", "--forward", "--batch", "-d", str(work), "-i", str(patch)], check=True)
sys.path.insert(0, str(work))
# Upstream resolves its copied files relative to the working directory.
os.chdir(work)
import template as upstream  # noqa: E402  (upstream's template.py, patched)

if which == "code-interpreter":
    # Upstream's alias and size, which the e2b-code-interpreter SDK defaults to.
    # Kernels: Python and JavaScript always, plus Bash; R and Java left out.
    # Its pip step needs more than the build's default free space (Errno 28).
    tpl, alias, cpu, mem, disk = upstream.make_template(kernels=["bash"]), "code-interpreter-v1", 2, 2048, 10240
else:
    # Upstream builds at 8 vCPU / 8192 MiB, which does not fit e2b-01's hugepage
    # pool. Each build step restores the previous step's snapshot while the old VM
    # still holds its pages, so a step briefly needs twice the memory: 4096 MiB
    # failed with "mmap memfd: cannot allocate memory" against the 3072-page pool.
    # The e2b-desktop SDK creates from "desktop".
    tpl, alias, cpu, mem, disk = upstream.template_with_user_workdir, "desktop", 4, 2048, 8192

info = Template.build(tpl, alias=alias, cpu_count=cpu, memory_mb=mem, min_free_disk_mb=disk,
                      on_build_logs=lambda e: print(str(e), flush=True))
print("BUILD DONE:", info)
