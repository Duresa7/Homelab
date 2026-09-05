# Qwen 3.5 2B Model Replacement

**Created:** 2026-09-04  
**Last updated:** 2026-09-04

**Date:** 2026-09-04  
**Status:** Complete

## Change

I replaced `llama3.1:8b` with `qwen3.5:2b` in Ollama on `docker-main` for lower-latency Handy transcript post-processing. I confirmed the exact tag in the official Ollama library before pulling it. The installed Qwen model has ID `324d162be6ca`, full digest `324d162be6ca5629ae4517c8710434d0bd2d665bc94dbad46e9af8fbf8a2f0df`, a 2.7 GB stored size, 2.3B parameters, and Q8_0 quantization.

I pulled and tested Qwen before stopping and deleting `llama3.1:8b`. I took no snapshot or backup because both models are reproducible downloads and the persistent Open WebUI data was outside the model deletion target.

## Handy Prompt Test

I sent requests through `http://192.168.40.35:11434/v1/chat/completions`, the same OpenAI-compatible path Handy uses. Qwen returned a cleaned transcript, and the final compact prompt converted `um please send the report tomorrow question mark` to `Please send the report tomorrow?`.

Handy's longer default cleanup prompt did not consistently remove the leading filler word or capitalize the result with this 2B model. I recorded the shorter tested prompt in the Ollama runbook instead of claiming the default passed.

## Verification

- The native Ollama generation endpoint returned `GPU OK` from `qwen3.5:2b` with thinking disabled.
- `ollama ps` reported `100% GPU`, a 4,096-token context, and a 2.4 GB loaded model size.
- NVIDIA reported 3,147 MiB in use on the 11,264 MiB GTX 1080 Ti after the Qwen request.
- The Ollama model list contained only `qwen3.5:2b`; `llama3.1:8b` was absent after its deletion.
- Open WebUI's container-network request returned only `qwen3.5:2b` with the expected full digest.
- Ollama and Open WebUI remained healthy with zero restarts. All 15 running containers had no unhealthy result.
- Free root-filesystem space increased from 50 GiB before the pull to 52 GiB after the old model was removed.
- One formatting-only verification command failed because `jq` is not installed on `docker-main`. I repeated the request without `jq`, and the raw JSON response contained `"response":"GPU OK"`.

No separate evidence transcript was retained. The verified values above were captured during the live change.

## Remaining Client Step

I still need to select the Custom provider, `http://192.168.40.35:11434/v1`, API-key placeholder `ollama`, model `qwen3.5:2b`, and the tested prompt in the Handy desktop application. The server side is ready and the endpoint passed from an internal client.
