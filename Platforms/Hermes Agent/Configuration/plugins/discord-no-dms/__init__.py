"""Keep Discord DMs away from Horus.

Hermes's Discord adapter turns the DM intents on and always admits DMs from
allowlisted users, ignoring dm_policy. Two layers stop that:

1. At registration the plugin wraps discord.py's commands.Bot.__init__ so
   the dm_messages, dm_reactions and dm_typing intents are cleared before
   the bot connects. Discord then never delivers a DM event, so the adapter
   neither reacts to a DM nor dispatches it.
2. A pre_gateway_dispatch hook fails closed for anything that still arrives: a Discord event
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


DM_INTENTS = ("dm_messages", "dm_reactions", "dm_typing")


def _strip_dm_intents():
    try:
        from discord.ext import commands
    except Exception as exc:  # discord.py missing: the hook still drops DMs
        log.warning("DM intents left on, discord.py not importable: %s", exc)
        return
    if getattr(commands.Bot.__init__, "_no_dms_wrapped", False):
        return
    original = commands.Bot.__init__

    def __init__(self, *args, **kwargs):
        intents = kwargs.get("intents")
        if intents is not None:
            for name in DM_INTENTS:
                setattr(intents, name, False)
            log.info("cleared Discord DM intents (%s)", ", ".join(DM_INTENTS))
        original(self, *args, **kwargs)

    __init__._no_dms_wrapped = True
    commands.Bot.__init__ = __init__


def register(ctx):
    _strip_dm_intents()
    ctx.register_hook("pre_gateway_dispatch", drop_discord_dms)
