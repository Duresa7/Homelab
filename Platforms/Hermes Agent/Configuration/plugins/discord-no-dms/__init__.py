"""Drop all Discord DMs at gateway ingress.

Hermes's Discord adapter always admits DMs from allowlisted users and ignores
dm_policy, so this pre_gateway_dispatch hook fails closed: a Discord event
passes only when its chat type is a server channel or thread ("group",
"thread" or "channel"). Everything else, "dm" included, is skipped. Server
messages fall through to normal handling, where DISCORD_ALLOWED_USERS and
DISCORD_ALLOWED_CHANNELS apply.
"""

import logging

log = logging.getLogger("plugins.discord-no-dms")

SERVER_CHAT_TYPES = {"group", "thread", "channel"}


def _norm(value):
    return str(getattr(value, "value", value) or "").strip().lower()


def drop_discord_dms(event, **kwargs):
    source = getattr(event, "source", None)
    if source is None:
        return None
    if _norm(getattr(source, "platform", None)) != "discord":
        return None
    chat_type = _norm(getattr(source, "chat_type", None))
    if chat_type in SERVER_CHAT_TYPES:
        return None
    log.info("dropped Discord DM from user %s (chat type %r)", getattr(source, "user_id", "?"), chat_type)
    return {"action": "skip", "reason": "discord-dms-disabled"}


def register(ctx):
    ctx.register_hook("pre_gateway_dispatch", drop_discord_dms)
