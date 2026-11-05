"""Drop all Discord DMs at gateway ingress.

Hermes's Discord adapter always admits DMs from allowlisted users and ignores
dm_policy, so this pre_gateway_dispatch hook skips any Discord event whose
chat type is "dm". Server-channel messages fall through to normal handling,
where DISCORD_ALLOWED_USERS and DISCORD_ALLOWED_CHANNELS apply.
"""

import logging

log = logging.getLogger("plugins.discord-no-dms")


def _platform_name(source):
    platform = getattr(source, "platform", None)
    return str(getattr(platform, "value", platform) or "").lower()


def drop_discord_dms(event, **kwargs):
    source = getattr(event, "source", None)
    if source is None:
        return None
    if _platform_name(source) == "discord" and getattr(source, "chat_type", "") == "dm":
        log.info("dropped Discord DM from user %s", getattr(source, "user_id", "?"))
        return {"action": "skip", "reason": "discord-dms-disabled"}
    return None


def register(ctx):
    ctx.register_hook("pre_gateway_dispatch", drop_discord_dms)
