# MeshCentral Troubleshooting

**Created:** 2026-09-13  
**Last updated:** 2026-09-13

One problem per record.

- [Linux agent installer cannot download the agent over a self-signed certificate - 2026-09-13](Linux%20agent%20installer%20cannot%20download%20the%20agent%20over%20a%20self-signed%20certificate%20-%202026-09-13.md). `meshinstall.sh` runs `wget` and `curl` with no certificate flags and falls back to port 80, which this deployment does not publish. Patch the downloaded script before running it.
