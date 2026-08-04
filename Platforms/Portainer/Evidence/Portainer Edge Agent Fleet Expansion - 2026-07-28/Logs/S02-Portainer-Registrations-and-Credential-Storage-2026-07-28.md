# Step 2 Portainer Registrations and Credential Storage

**Created:** 2026-07-28  
**Last updated:** 2026-08-04

**Capture date:** 2026-07-28  
**Execution mechanism:** PowerShell 7, Portainer HTTPS API, `<REDACTED_PASSWORD_MANAGER_CLI>` service account  
**Working directory:** `D:\Documents\Homelab`

## API Requests

Authentication used `<REDACTED_SECRET_REFERENCE>` for the username and password. The values and returned JWT were held in memory and aren't retained.

```http
PUT /api/settings
Content-Type: application/json

{"EnforceEdgeID":true}
```

The incomplete pre-agent `docker-blue` record with no Edge ID & zero check-ins was deleted, then each target used:

```http
POST /api/endpoints
Content-Type: multipart/form-data

Name=<YOUR_TARGET>
EndpointCreationType=4
URL=https://192.168.40.35:9443
GroupID=1
ContainerEngine=docker
```

## Observed Result

| Name | Endpoint ID | Type | Edge ID present | Edge key present | Initial check-in |
|---|---:|---:|---|---|---:|
| `docker-blue` | 7 | 4 | Yes | Yes | 0 |
| `media-01` | 8 | 4 | Yes | Yes | 0 |
| `docker-network` | 9 | 4 | Yes | Yes | 0 |

Each Edge ID was 36 characters. Each Edge key was 123 characters.

## Credential Storage

I sent a Login JSON template through standard input to `<REDACTED_PASSWORD_MANAGER_CLI> item create --vault "<REDACTED_VAULT_NAME>" -`, once for each of `docker-blue`, `media-01`, and `docker-network`.

The Login username holds the Edge ID and the password holds the Edge key. A protected comparison read each field through `<REDACTED_SECRET_REFERENCE>` and returned `credential_match=true` for all three targets. No reveal command or secret-bearing output was retained.
