# Ubuntu 26.04 Templates and Storage Cleanup

**Created:** 2026-11-12  
**Last updated:** 2026-11-12

**Implementation date:** 2026-11-11, 11:15 PM, to 2026-11-12, 12:10 AM Eastern  
**Status:** Complete.  
**Affected systems:** `e2b-01` (VM 113 on `grey-server`), `ubuntu-dev`, Grey's `local-lvm` thin pool

The four templates from the [deployment](Embed%20Trial%20Deployment%20-%202026-11-11.md) and the [extra templates](Extra%20Templates%20and%20Disk%20Growth%20-%202026-11-11.md) sat on old bases: `base` on Debian 12 with Python 3.11, `dev` on the `python:3.12` image, Code Interpreter on Debian with Python 3.13, and Desktop on Ubuntu 22.04. I rebuilt all four on Ubuntu 26.04 under the same names, then wrote a cleanup for the build layers Embed never removes and deleted 138.1 GiB of them.

## 1. Build scripts

| Template | Script | Base and contents |
|---|---|---|
| `base` | [build-base-template.py](../../Scripts/build-base-template.py) (new) | `ubuntu:26.04` with `python3`, `python3-venv`, `python3-pip`, `curl`, `wget`, `ca-certificates`, `git`, `unzip`; 2 vCPU, 512 MiB, `min_free_disk_mb` 2048 |
| `dev` | [build-dev-template.py](../../Scripts/build-dev-template.py) (rewritten) | `ubuntu:26.04`; `build-essential`, `pkg-config`, Python headers and venv; Node 26 from NodeSource; `gh` from its signed apt repository; `uv`, which installs Python 3.15 under `/opt/uv/python` as the default `python3` in `/usr/local/bin` while Ubuntu's 3.14 stays at `/usr/bin/python3`; 2 vCPU, 1024 MiB, `min_free_disk_mb` 4096 |
| `code-interpreter-v1` | [build-upstream-template.py](../../Scripts/build-upstream-template.py) with [code-interpreter-ubuntu-26.04.patch](../../Configuration/code-interpreter-ubuntu-26.04.patch) | Upstream `e2b-dev/code-interpreter` at `c49b78602c29e44d07e196604de515dfa6b12744`, patched; kernels Python, JavaScript (Deno), TypeScript (Deno) and Bash; 2 vCPU, 2048 MiB, `min_free_disk_mb` 10240 |
| `desktop` | [build-upstream-template.py](../../Scripts/build-upstream-template.py) with [desktop-ubuntu-26.04.patch](../../Configuration/desktop-ubuntu-26.04.patch) | Upstream `e2b-dev/desktop` at `91f23acaab7312e847596acc44e6f7763f56917f`, patched; 4 vCPU, 2048 MiB, `min_free_disk_mb` 8192 |

`build-upstream-template.py` now copies upstream's `template` folder to a temporary directory, applies the patch there with `patch -p2 --forward --batch`, changes into that directory and imports upstream's `template.py`. The clone stays untouched.

Both patches carry the same Ubuntu 26.04 changes: `PIP_BREAK_SYSTEM_PACKAGES=1` in the build environment, because 26.04 refuses system-wide `pip` installs (PEP 668), and `signed-by` keyrings in place of `apt-key`, which apt 3 no longer ships. Desktop's patch also drops `unminimize`, replaces `netcat` with `netcat-openbsd`, adds `gnupg` and `dbus-x11`, and adds the Mozilla PPA with `add-apt-repository -y`. Code Interpreter's patch adds Ubuntu's Python packages, removes upstream's system `pip` upgrade, moves Node to the `setup_26.x` line, replaces the JavaScript kernel (section 3), and moves four Python pins to releases with Python 3.14 wheels or builds: pandas 2.3.3, scikit-learn 1.7.2, scikit-image 0.26.0, spacy 3.8.18, with `gensim` removed and the server's pydantic at 2.12.5.

## 2. Builds

I built from `ubuntu-dev` with SDK 2.63.0, one template at a time, with the port 5008 tunnel to `e2b-01` open for the two upstream templates.

| Template | Template ID | Build ID | Result |
|---|---|---|---|
| `base` | `qyqe3t68mh6s7zb3m0hq` | `ab7f87c8-f594-4084-8212-0c7f7986383a` | Built in 58 seconds at 11:23 PM. |
| `dev` | `jvylpmrv69ldm22c3kbp` | `a5a21027-d46a-42b5-a622-795e679fd897` | Built in 1m5s at 11:24 PM. |
| `code-interpreter-v1` | `4xuy5aah8ryhqs0mjudq` | `b183ec62-ded7-480c-9ad8-82e6e38a108e` | Built in 1m14s at 11:58 PM, the sixth attempt, with the earlier steps cached. |
| `desktop` | `sy8jv5fcwn5cn7ewpnrk` | `3a123129-a02e-42e1-87aa-8e6deffdb7a1` | Built in 6m47s at 11:52 PM, the third attempt. |

Desktop's first attempt, at 11:28 PM, stopped before any step: `ValueError: No files found in files/google-chrome.desktop`. Upstream's `copy()` steps resolve paths against the working directory, and the script now changes into the patched copy before importing it. The second built in 6m45s, but `Sandbox.create()` in `e2b-desktop` 2.7.2 raised `Could not start XFCE`. Inside a sandbox, `xfce4-session` ran while `xfwm4` and `xfdesktop` did not, and the session logged `dbus-launch not found, the desktop will not work properly!`: Ubuntu 26.04 does not pull in `dbus-x11`. The patch now installs it.

Code Interpreter failed five times before it built:

| Time | Step | Error | Change |
|---|---|---|---|
| 11:28 PM | 12 of 30, `npm install -g` of E2B's `ijavascript` fork | `zeromq` 5.3.1 under Node 26.13.1: `v8config.h:13:2: error: #error "C++20 or later required."` | Retried with `CXXFLAGS=-std=gnu++20` |
| 11:31 PM | 12 of 30 | `nan_callbacks_12_inl.h:175:53: error: no matching function for call to 'Nan::FunctionCallbackInfo<v8::Value>::FunctionCallbackInfo(...)'` | Section 3 |
| 11:43 PM | 14 of 30, `pip install bash_kernel` | `An internal error occurred` | Section 4 |
| 11:46 PM | 19 of 30 | `Building wheel for pydantic-core ... finished with status 'error'`, PyO3 0.22.2 with Python 3.14 | Server pydantic 2.12.5, which has a 3.14 wheel |
| 11:54 PM | none | Built in 48 seconds, but the Deno kernel's output came back with ANSI colour codes: `[32m"linux"[39m` | `"env": {"NO_COLOR": "1"}` added to the kernelspec |

## 3. JavaScript kernel

E2B's `ijavascript` fork depends on `zeromq` 5 and `nan`, which build only against Node 20, end of life since April 2026. In a throwaway `dev` sandbox the same install with `CXXFLAGS=-std=gnu++20` failed under Node 24.22.3 (`nan_callbacks_12_inl.h:175:53`) and Node 22.23.5 (`nan.h:2546:19: error: no matching function for call to 'v8::ObjectTemplate::SetAccessor(...)'`), as it had under 26.13.1.

I replaced it with Deno's own Jupyter kernel. The patch installs Deno 2.9.8 to `/usr/local/bin` with `curl -fsSL https://deno.land/install.sh | DENO_INSTALL=/usr/local sh -s -- -y`, registers it with `deno jupyter --install --name javascript --display JavaScript --force`, so E2B's server finds it under the name it already uses, and adds `NO_COLOR=1` to `/root/.local/share/jupyter/kernels/javascript/kernel.json` with `jq`. `require` is not defined in that kernel; Node modules load as `import fs from "node:fs"` and npm packages as `import x from "npm:<package>"`.

## 4. Memory pool

The 11:43 PM failure came from the hugepage pool, not the template. A 4 vCPU, 2048 MiB `medsim-blender` sandbox from my separate medsim work had been running since 10:42 PM, and my Desktop test sandbox held another 2048 MiB. A 2048 MiB build step briefly needs 4096 MiB because the previous step's VM still holds its pages, and the 3072-page pool is 6 GiB. Built with nothing else of mine running, the same step passed.

## 5. Verification

Each test created a sandbox through NPM and killed it afterwards.

| Template | Result |
|---|---|
| `base` | `Ubuntu 26.04.1 LTS`, user `user`, Python 3.14.4, 9.4G free on `/`. |
| `dev` | `python3` is 3.15.2 at `/usr/local/bin/python3`, `/usr/bin/python3` 3.14.4; Node v26.13.1, npm 11.20.0, git 2.53.0, gh 2.103.3, uv 0.13.7, gcc 15.2.0; 9.0G free. `uv pip install --system` is refused, and an install into a virtual environment worked. |
| `code-interpreter-v1` | With `e2b-code-interpreter` 2.11.9: create in 0.18 seconds; Python 3.14.4 kept `x` from one `run_code` to the next (`42`); pandas 2.3.3 and scikit-learn 1.7.2 imported, and a plot returned `png` and `chart` results; JavaScript printed `js 42`, TypeScript returned `42`, a `node:` import returned `linux` in plain text; Bash printed `bash 5.3.9(1)-release`. |
| `desktop` | With `e2b-desktop` 2.7.2: create in 5.25 seconds with Xfce running; Firefox 140.17.0esr, Google Chrome 157.0.8103.78, VS Code 1.146.0, `xfce4-session` 4.20.4; noVNC answered `200` on port 6080; a screenshot showed the desktop. |

The first Bash check failed with `syntax error near unexpected token '('`. My test command had expanded `$BASH_VERSION` on `ubuntu-dev` before sending it, and the version string's parentheses broke the remote line; sent quoted, it printed the version above.

## 6. Storage cleanup

At 11:59 PM, Embed's smoke test (`docker compose --profile test run --rm smoke`) stopped at its preflight, `service "preflight" didn't complete successfully: exit 1`, because `/` read 262 of 292 GB used with 18 GB free, below the 20 GiB preflight requires. The running services were not touched, and the API kept answering `200` through NPM. But the next `up`, after any reboot, would have refused to start. `/var/lib/e2b/storage/templates` held 244 GB; `/orchestrator/build` held 2.7 GB, down from 54 GB after the earlier builds.

Embed stores every build step as a directory under `/var/lib/e2b/storage/templates`, named by build ID. A template's final build is a diff whose `memfile.header` and `rootfs.ext4.header` map data to earlier layers by ID, so a directory is safe to remove only when no live build reaches it. [storage-gc.py](../../Scripts/storage-gc.py) works that out. Its roots are the newest uploaded or successful build of each template, every build still waiting or building, every build a paused sandbox's snapshot names, and every build of a `medsim-` template. From those, it follows each build ID found in a header, `metadata.json` or `snapfile`, as a 16-byte UUID or as text. It only reports unless run with `--delete`, and with `--delete` it refuses while any build is waiting or building, because a running build's new layers are not referenced yet.

Run as root on `e2b-01`:

```
build dirs: 283; roots: 14 (4 without a directory: ['6419d420', '65101150', 'e620043f', 'f94cebf3'])
live: 133 dirs, 105.8 GiB
unreferenced: 150 dirs, 138.1 GiB
```

The four roots without a directory are failed `medsim-blender` and `medsim-tools` builds. The 150 unreferenced directories, grouped by the build that created them:

| Source | Directories | Size |
|---|---|---|
| Step layers of the Debian-era `code-interpreter-v1`, `desktop` and two `dev` builds | 71 | 63.4 GiB |
| Failed `medsim-blender` and `medsim-tools` attempts, 11:32, 11:35 and 11:55 PM | 33 | 49.7 GiB |
| Failed `desktop` and `code-interpreter-v1` attempts, 9:12 PM, 9:39 PM and 11:45 PM | 25 | 18.0 GiB |
| Step layers of the 48-second `code-interpreter-v1` build whose output kept ANSI colours | 15 | 4.1 GiB |
| Final builds of superseded templates (Debian `dev` twice, `code-interpreter-v1` twice, `desktop` twice) | 6 | 2.9 GiB |

At 12:05 AM, `python3 /root/storage-gc.py --delete` printed `deleted 150 dirs`. `/` then read 121 of 292 GB used, 158 GB free, 44%, and the template store 106 GB. A sandbox from each of the six templates then started:

```
base: ok in 1405 ms | os 26.04
dev: ok in 1077 ms | os 26.04
code-interpreter-v1: ok in 1342 ms | os 26.04
desktop: ok in 1214 ms | os 26.04
medsim-blender: ok in 1041 ms | os 24.04
medsim-tools: ok in 1084 ms | os 24.04
```

The smoke test then passed: `smoke: ok sandbox=inwid92403ukcldaw422n port 8080 reached through http://127.0.0.1:3002`, exit `0`. Its `base-template` service runs with `FORCE_REBUILD=0` and left my `base` in place: a sandbox from it afterwards read `Ubuntu 26.04.1 LTS` and Python 3.14.4.

`fstrim -v /` on `e2b-01` returned `72.2 GiB (77508517888 bytes) trimmed`. On Grey, `local-lvm` then read 64.74% used with 293,488,849 KiB available, against 67.91% and 267,103,153 KiB after the disk growth, and `vm-113-disk-1` read 41.97% of 300 GiB.

## 7. Skill

The [e2b-sandbox skill](https://github.com/Duresa7/tools-and-scripts/tree/main/ai-configs/skills/e2b-sandbox) now puts Python packages in a virtual environment, covers the Deno kernel's `node:` and `npm:` imports, starts its SDK template example from `ubuntu:26.04`, and lists `externally-managed-environment`, `apt-key: command not found` and the doubled step memory among build failures (`tools-and-scripts` commit `a4ba2be`).

## Left open

- **Layers still accumulate.** Nothing in Embed removes them; I run `storage-gc.py` after a round of builds, report first, and delete only with no build in progress.
