"""Build the `dev` sandbox template on e2b-01.

Run from ubuntu-dev with the e2b SDK in a virtual environment and the client
variables set (E2B_DOMAIN, E2B_SANDBOX_URL, E2B_API_KEY). The build runs on
e2b-01 in a sandbox of its own and pulls python:3.12 from Docker Hub; nothing
needs Docker on the client.
"""
from e2b import Template

tpl = (
    Template()
    .from_python_image("3.12")
    .apt_install(["build-essential", "git", "curl", "ca-certificates", "gnupg", "jq", "unzip"])
    .run_cmd("curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && apt-get install -y nodejs", user="root")
    .run_cmd(
        "curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg -o /usr/share/keyrings/githubcli-archive-keyring.gpg"
        " && echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main'"
        " > /etc/apt/sources.list.d/github-cli.list && apt-get update && apt-get install -y gh",
        user="root",
    )
    .run_cmd("pip install --no-cache-dir uv", user="root")
    .run_cmd("python3 --version && node --version && npm --version && git --version && gh --version | head -1 && uv --version && gcc --version | head -1")
)

# min_free_disk_mb since 2026-11-11: the first build left 396 MB free on /.
info = Template.build(tpl, alias="dev", cpu_count=2, memory_mb=1024, min_free_disk_mb=4096,
                      on_build_logs=lambda e: print(str(e), flush=True))
print("BUILD DONE:", info)
