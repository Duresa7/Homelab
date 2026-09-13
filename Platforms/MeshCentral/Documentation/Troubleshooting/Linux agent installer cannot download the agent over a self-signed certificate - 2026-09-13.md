# Linux agent installer cannot download the agent over a self-signed certificate

**Created:** 2026-09-13  
**Last updated:** 2026-09-13

**Investigated:** 2026-09-13

**Context:** Installing the Linux agent on `ubuntu-dev` at `192.168.40.179`, against the MeshCentral server at `192.168.40.39`, which serves a self-signed certificate for `CN=192.168.40.39`.

**Symptom:** The install command the browser generates fails twice over. Plain `wget` of the installer refuses the certificate and writes a zero-byte file:

```
ERROR: The certificate of '192.168.40.39' is not trusted.
ERROR: The certificate of '192.168.40.39' doesn't have a known issuer.
```

Adding `--no-check-certificate` to the outer command downloads `meshinstall.sh` (5,769 bytes) and gets past the device group check, but the script then fails on its own download of the agent binary:

```
Downloading agent #6...
ERROR: The certificate of '192.168.40.39' is not trusted.
curl: (60) SSL certificate OpenSSL verify result: unable to get local issuer certificate (20)
--2026-09-13 01:07:15--  http://192.168.40.39/meshagents?id=6
Connecting to 192.168.40.39:80... failed: Connection refused.
Unable to download agent at: http://192.168.40.39/meshagents?id=6.
```

**Root cause:** Two things compound. `meshinstall.sh` fetches the agent and its settings with bare `wget $url/...` and `curl -L --output ...`, carrying no certificate flags, so neither tool accepts the server's self-signed certificate. When that fails the script rewrites the URL to `http://` and retries, and this deployment publishes only `192.168.40.39:443`, so port 80 refuses the connection. The flag on the outer command only covers fetching the installer; it does not reach the downloads inside it.

**Fix:** Patch the downloaded script before running it. Four lines need it, at 153, 159, 167, and 172:

```bash
sed -i 's|wget \$url|wget --no-check-certificate $url|g; s|curl -L --output|curl -k -L --output|g' meshinstall.sh
sudo ./meshinstall.sh https://192.168.40.39 '<REDACTED_GROUP_KEY>'
```

The device group key must stay in single quotes. The key issued for this group contains a `$` followed by letters, which a shell would expand inside double quotes, and the installer would then reject it or bind the agent to the wrong group. A related failure is running the command with the placeholder text still in place, which returns `Device group identifier is not correct, must be at least 64 characters long.`

**Verification:** The patched run downloaded the agent (3,757,520 bytes) and its settings (35,924 bytes), reported `...Installing service [DONE]` and `-> Starting service... [OK]`. On `ubuntu-dev`, `systemctl is-active meshagent` returns `active` and the unit is `enabled`, running since 01:08:15 AM EDT from `/usr/local/mesh_services/meshagent/`. On the server at 01:08 AM EDT the device list holds `ubuntu-dev` alongside `DuresaGamingPC` and `HQ-MGT01`, with three established TCP 443 connections from `192.168.40.179`.

I removed `meshinstall.sh`, its backup, and the root-owned `meshagent` and `meshagent.msh` left in `/tmp`. The `.msh` file carries the device group key, so it does not stay on the host; the installed copy under `/usr/local/mesh_services/meshagent/` is the one the service reads.

**What would remove the need for the patch:** giving the server a DNS name and a certificate the machines already trust. Publishing port 80 would also let the script's fallback work, but it would fetch the agent over plaintext, so the certificate is the better fix.
