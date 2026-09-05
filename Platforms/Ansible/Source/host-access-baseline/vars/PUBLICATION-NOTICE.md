# Key Notice

**Created:** 2026-08-15  
**Last updated:** 2026-08-15

The public project carries `ai-agent-key.yml.example` in place of the deployed key file. `vars/ai-agent-key.yml` holds the real `ai-agent` public key and is gitignored.

This follows `ssh-key-automation/identities/`, which publishes a schema example and withholds the live identity files. This repository publishes no key material, and the validator fails if a real key reaches the example.

A public key is not a secret in the operational sense — it is safe to hand to a host. It is withheld here because the repository is public and the unpublished decision 0001-publication-policy treats keys as withheld. Copy the example when deploying.
