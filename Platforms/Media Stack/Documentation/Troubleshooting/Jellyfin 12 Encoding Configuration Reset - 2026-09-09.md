# Jellyfin 12 Encoding Configuration Reset

**Created:** 2026-09-09  
**Last updated:** 2026-09-09

## Symptom and cause

During the [Jellyfin 12 upgrade](../Change%20Records/Jellyfin%2012%20Upgrade%20-%202026-09-09.md), Jellyfin started and passed its health check, but logged:

```text
Error loading configuration file: /config/config/encoding.xml
System.InvalidOperationException: There is an error in XML document (30, 35).
Instance validation error: '' is not a valid value for EncoderPreset.
```

The serializer rejected the old empty preset. The resulting file contained default settings: hardware acceleration `none`, tone mapping disabled, and HEVC encoding disabled. A direct FFmpeg hardware test passed, so that test alone did not establish that Jellyfin's saved settings were correct.

## Repair and verification

I stopped only `jellyfin` and edited `/opt/media-stack/config/jellyfin/config/encoding.xml`. I restored the [documented settings](../Media%20Settings%20Research%20-%202026-07-17.md): hardware acceleration `qsv`, tone mapping enabled, HEVC encoding enabled, and H.264, VC-1, HEVC, MPEG-2, VP8, and VP9 hardware decoding. I retained the newly generated valid `EncoderPreset=auto`. QSV device remained blank; AV1, HEVC RExt, VPP tone mapping, and Intel low-power encoders remained disabled.

After starting the container, I checked logs bounded to its new start time. Startup completed with zero error or fatal entries. The file retained `qsv`, `auto`, tone mapping enabled, and HEVC encoding enabled. Jellyfin reported 12.0.0 and healthy; both web clients returned HTTP 200. The synthetic QSV H.264 test passed again with exit code 0.

I restored these values from the documented baseline; I did not retain the pre-upgrade XML, so I cannot establish every previous setting. I kept no separate terminal capture for diagnosis, repair, or verification. Real client playback and HDR tone mapping remain untested in this session.
