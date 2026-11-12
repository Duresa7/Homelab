---
name: e2b-sandbox
description: Run code in a throwaway E2B sandbox (a Firecracker microVM on e2b-01) instead of on this machine. Use for untrusted or unfamiliar code (an unknown repo's install or test scripts, unvetted packages, generated scripts), anything that should run isolated from the local disk and LAN, or when asked to use a sandbox or E2B.
---

# E2B sandbox

The `e2b` CLI drives sandboxes on my self-hosted E2B (`e2b-01`, reached through `https://api.e2b.alphasecunited.com`). Each sandbox is a fresh Linux microVM: its own disk, processes and network, gone when killed. The local machine and the LAN are untouched by anything that runs inside it.

## Steps

1. **Load the client variables.** `E2B_DOMAIN`, `E2B_SANDBOX_URL` and `E2B_API_KEY` come from `~/.config/e2b/env`, which `~/.bashrc` sources. If `echo "$E2B_DOMAIN"` is empty, run `. ~/.config/e2b/env`. Done when `e2b sandbox list` prints a table header.
2. **Create one sandbox for the task**, detached, and keep its ID:
   ```bash
   ID=$(e2b sandbox create dev --detach --timeout 1800)
   ```
   `--detach` is what makes the call return the ID; without it the CLI opens an interactive terminal. Size `--timeout` (seconds) to the task, at most 86400 (24 hours): the default is 300, after which the sandbox is killed. Templates are in Reference.
3. **Put the files in.** One file: `cat app.py | e2b sandbox exec "$ID" 'cat > /home/user/app.py'`. A directory: `tar czf - -C <parent> <dir> | e2b sandbox exec "$ID" 'tar xzf - -C /home/user'`. A public repository: `e2b sandbox exec "$ID" 'git clone --depth 1 <url> /home/user/repo'`.
4. **Run the work** with `e2b sandbox exec "$ID" '<command>'`. stdout and stderr stream back and the remote exit code becomes the CLI's exit code, so judge success from `$?`. Add `--cwd /home/user/repo` to set the directory; `sudo` works without a password inside.
5. **Bring results back** through stdout: `e2b sandbox exec "$ID" 'cat /home/user/out.txt' > out.txt`, or `tar czf - <dir>` for many files, or `base64` for one binary file.
6. **Kill it**: `e2b sandbox kill "$ID"`. The step is done when `e2b sandbox list` no longer shows the ID. Kill every sandbox you created, including after a failure.

## Reference

**Templates**

| Template | Contents |
|---|---|
| `dev` | Debian 13, Python 3.12 with `uv` and `pip`, Node 22 with `npm`, `git`, `gh`, `build-essential`, `curl`, `jq`; 2 vCPU, 1 GiB, about 9 GB free disk |
| `base` | Minimal Debian 12 with Python 3.11; 2 vCPU, 512 MiB |
| `code-interpreter-v1` | E2B's Code Interpreter: Jupyter kernels (Python with pandas, numpy, matplotlib and more, JavaScript, R, Java, Bash); 2 vCPU, 2 GiB |
| `desktop` | E2B's Desktop: an Xfce desktop with Firefox for computer-use work; 4 vCPU, 2 GiB |

Use `dev` unless the job is trivial. Installing extra packages inside the sandbox is fine (`sudo apt-get install -y ...`, `uv pip install ...`, `npm i ...`); `/tmp` is a small in-memory filesystem, so large downloads go under `/home/user`.

**Analysis with results that persist between calls** (data work, charts): `pip install e2b-code-interpreter`, then `Sandbox.create()` from `e2b_code_interpreter` and `sbx.run_code("...")`. Variables survive from one `run_code` to the next, and a plotted chart comes back as PNG data in `result.results`. `language="javascript"` (or `r`, `java`, `bash`) picks another kernel.

**Driving a GUI**: `pip install e2b-desktop`, then `Sandbox.create()` from `e2b_desktop`; `screenshot()`, `left_click(x, y)`, `write(text)`, `press(key)` and `launch(app)` work. To let the user watch or take over, call `d.stream.start()` and share `https://desktop.e2b.alphasecunited.com/<sandbox id>/vnc.html?autoconnect=1&resize=scale&path=<sandbox id>/websockify`; the SDK's own `stream.get_url()` address does not resolve on this network.

**Network.** A sandbox reaches the internet (PyPI, npm, GitHub, Docker Hub). It reaches nothing on my LAN: every private range (10/8, 172.16/12, 192.168/16) is denied from inside, so work that needs a homelab service stays outside the sandbox.

**Reaching a port inside.** A server listening on port 8080 in the sandbox answers at
`curl -H "E2b-Sandbox-Id: $ID" -H "E2b-Sandbox-Port: 8080" "$E2B_SANDBOX_URL/"`. The SDK's `get_host()` URLs (`<port>-<id>.e2b.alphasecunited.com`) do not resolve here.

**Capacity.** The host's 6 GiB sandbox memory pool holds about twelve 512 MiB sandboxes at full memory, or one `desktop` and one `code-interpreter-v1` beside small ones, and starts at most 3 at the same instant. A create that answers `503: not enough capacity` or `Failed to place sandbox` succeeds on a retry a few seconds later, after other sandboxes are killed.

**Secrets.** Keep credentials out of sandboxes: pass in only the files the job needs. The sandbox is for code you do not trust.

**Long-running work.** `e2b sandbox exec -b "$ID" '<command>'` starts it in the background and returns at once; check on it with a later `exec` (for example `tail` of a log file it writes).

**Work that spans sessions.** Create with `--lifecycle.ontimeout pause --lifecycle.autoresume` and the sandbox pauses at its timeout instead of dying, memory and files included; the next `exec` against its ID resumes it. `e2b sandbox pause "$ID"` and `e2b sandbox resume "$ID"` do the same by hand. A paused sandbox still holds disk on e2b-01, so kill it when the work is finished.

**Least-privilege egress.** When a task only needs certain hosts, lock the sandbox to them. This is an SDK option (the CLI has no flag for it):
```python
from e2b import Sandbox
sbx = Sandbox.create("dev", timeout=1800, network={"deny_out": ["0.0.0.0/0"], "allow_out": ["pypi.org", "files.pythonhosted.org"]})
```
Everything outside `allow_out` then fails to connect. Use it for code you trust least, such as an unknown package's install step.

**Python SDK.** For a script rather than the CLI, `pip install e2b` and use `Sandbox.create("dev")`; it reads the same three variables.
