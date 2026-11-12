"""Build the `dev` sandbox template on e2b-01: Ubuntu 26.04 with current toolchains.

Run from ubuntu-dev with the e2b SDK in a virtual environment and the client
variables set (E2B_DOMAIN, E2B_SANDBOX_URL, E2B_API_KEY). The build runs on
e2b-01 and pulls ubuntu:26.04 from Docker Hub.

Python: Ubuntu's own 3.14 stays at /usr/bin/python3; uv installs the newest
3.15 under /opt/uv/python and puts python, python3 and python3.15 in
/usr/local/bin, which comes first on PATH. Node: the current LTS line (26)
from NodeSource. Until 2026-11-11 this template was python:3.12 on Debian.
"""
from e2b import Template

UV_ENV = "UV_PYTHON_INSTALL_DIR=/opt/uv/python UV_PYTHON_BIN_DIR=/usr/local/bin"

tpl = (
    Template()
    .from_image("ubuntu:26.04")
    .set_user("root")
    .apt_install([
        "build-essential", "pkg-config", "git", "curl", "wget", "ca-certificates", "gnupg",
        "jq", "unzip", "zip", "python3", "python3-venv", "python3-pip", "python3-dev",
    ])
    .run_cmd("curl -fsSL https://deb.nodesource.com/setup_26.x | bash - && apt-get install -y nodejs")
    .run_cmd(
        "curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg -o /usr/share/keyrings/githubcli-archive-keyring.gpg"
        " && echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main'"
        " > /etc/apt/sources.list.d/github-cli.list && apt-get update && apt-get install -y gh"
    )
    .run_cmd("curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin UV_NO_MODIFY_PATH=1 sh")
    .run_cmd(f"{UV_ENV} uv python install 3.15 --default && chmod -R a+rX /opt/uv")
    .set_user("user")
    .run_cmd(
        "python3 --version && /usr/bin/python3 --version && node --version && npm --version"
        " && git --version && gh --version | head -1 && uv --version && gcc --version | head -1"
        " && . /etc/os-release && echo $PRETTY_NAME"
    )
)

# min_free_disk_mb: the 2026-11-11 Debian build first left 396 MB free on /.
info = Template.build(tpl, alias="dev", cpu_count=2, memory_mb=1024, min_free_disk_mb=4096,
                      on_build_logs=lambda e: print(str(e), flush=True))
print("BUILD DONE:", info)
