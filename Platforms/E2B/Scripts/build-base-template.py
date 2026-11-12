"""Build the `base` sandbox template on e2b-01: a minimal Ubuntu 26.04.

Embed builds `base` itself from E2B's e2bdev/base image on its first start, and
afterwards leaves any ready `base` alone unless FORCE_REBUILD=1 is set in
/opt/e2b/.env. This replaces it with Ubuntu 26.04 at the same size. Embed's
smoke test runs `echo` and `python3 -m http.server` in it, so Python 3 stays.

Run from ubuntu-dev with the e2b SDK and the client variables set.
"""
from e2b import Template

tpl = (
    Template()
    .from_image("ubuntu:26.04")
    .set_user("root")
    .apt_install(["python3", "python3-venv", "python3-pip", "curl", "wget", "ca-certificates", "git", "unzip"])
    .set_user("user")
    .run_cmd("python3 --version && . /etc/os-release && echo $PRETTY_NAME")
)

info = Template.build(tpl, alias="base", cpu_count=2, memory_mb=512, min_free_disk_mb=2048,
                      on_build_logs=lambda e: print(str(e), flush=True))
print("BUILD DONE:", info)
