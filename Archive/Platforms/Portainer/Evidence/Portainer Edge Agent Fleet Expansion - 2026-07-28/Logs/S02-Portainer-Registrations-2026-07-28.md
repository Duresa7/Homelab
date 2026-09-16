# Step 2 Portainer Registrations

**Created:** 2026-07-28  
**Last updated:** 2026-08-04

**Capture date:** 2026-07-28  
**Execution mechanism:** PowerShell 7, Portainer HTTPS API  
**Working directory:** `D:\Documents\Homelab`

## API Requests

Authentication used a stored secret reference rather than a typed password. The values and the returned JWT were held in memory and aren't retained.

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

## Edge Credential Handling

Each target's Edge ID and Edge key were stored outside this repository and never written to any file in it. A protected comparison read each stored value back and returned `credential_match=true` for `docker-blue`, `media-01`, and `docker-network`. No reveal command and no secret-bearing output was retained.
