"""Who may talk to Horus in the open Discord channels, and which Horus answers.

DISCORD_ALLOWED_USERS is one list for the whole bot, so Hermes cannot admit
everyone in one channel while keeping full access to named people. This plugin
opens the channels in CHANNELS to every sender:

- #secret: everyone gets the chat-only `public` profile, and gateway lifecycle
  notices stay out of it.
- #ai-bot: everyone gets `public` until they type the server code. A correct
  code unlocks the full `default` profile (terminal, Executor SSH) for that
  person in that thread for 15 minutes. A code typed in the channel itself
  unlocks all of that person's #ai-bot threads.

The code never reaches the model. The Discord adapter checks every message
against HORUS_SERVER_CODE_HASH (an HMAC of the code, in ~/.hermes/.env), deletes
a message that contains the code, answers it, and drops it before Hermes batches,
routes or records it. The chat-only profile has no tools that touch a server, so
nothing a sender says to it can stand in for the code.

The check cannot be a pre_gateway_dispatch hook. A multiplexing gateway routes a
message first and runs that hook with the routed profile's plugins, and the
chat-only profile has none, so a locked sender's code would never be checked.

Routing lives in config.yaml (gateway.profile_routes). A channel route sends
#ai-bot to `public`. Route UNLOCK_ROUTE sends #ai-bot to `default` for user_id
UNLOCK_SENTINEL, which no Discord account has, so it matches only through the
patched ProfileRoute.matches and only for an unlocked sender.

Patches, each failing closed:
1. DiscordAdapter._is_allowed_user admits server messages in an open channel or
   its threads. Slash-command interactions keep the normal allowlist.
2. GatewayAuthorizationMixin._principal_authorized admits a sender in an open
   channel only when the routes send them to a profile other than `default`, or
   through UNLOCK_ROUTE. A missing route shuts the channel instead of opening
   full access.
3. ProfileRoute.matches answers UNLOCK_ROUTE from the unlock table.
4. DiscordAdapter.send keeps lifecycle notices out of quiet channels.
5. DiscordAdapter._auto_create_thread and _derive_auto_thread_name skip a
   message holding the code, so the code never becomes a thread title.
6. DiscordAdapter._enqueue_text_event and handle_message drop what screen()
   refuses. Every Discord message passes one of them before routing, including
   one sent while Horus is still answering. Text batching merges a burst into its
   first message, so typed text is screened before it joins a batch.
"""

import asyncio
import contextvars
import hashlib
import hmac
import logging
import re
import secrets
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger("plugins.discord-open-channel")

# The profile this plugin is installed in (~/.hermes). A multiplexing gateway keeps every
# profile's .env out of os.environ, so secrets are read from this profile's scope instead.
LAUNCH_HOME = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class ChannelPolicy:
    label: str
    quiet: bool
    unlockable: bool


CHANNELS = {
    "1016933615793356820": ChannelPolicy("#secret", quiet=True, unlockable=False),
    "1568709425131290704": ChannelPolicy("#ai-bot", quiet=False, unlockable=True),
}
OPEN_CHANNELS = frozenset(CHANNELS)
QUIET_CHANNELS = frozenset(cid for cid, policy in CHANNELS.items() if policy.quiet)

UNLOCK_ROUTE = "ai-bot-server-code"
UNLOCK_SENTINEL = "server-code-unlocked"
UNLOCK_SECONDS = 15 * 60
CODE_ENV = "HORUS_SERVER_CODE_HASH"

ACCEPTED = "Password accepted. Unlocked for 15 minutes."
RESEND = " Send your request again."
WRONG_CHANNEL = "That code only works in #ai-bot."

DISCORD_API = "https://discord.com/api/v10"
SERVER_CHAT_TYPES = {"group", "thread", "channel"}

# Lifecycle notices kept out of quiet channels. Templates with {fields} match on
# the text before the first field.
NOTICE_KEYS = (
    "gateway.shutdown.notice_restart",
    "gateway.shutdown.notice_shutdown",
    "gateway.shutdown.cron_interrupted",
    "gateway.startup.restarted",
    "gateway.startup.online",
    "gateway.draining",
    "gateway.restart.in_progress",
    "gateway.restart.restarting",
    "gateway.busy.drain_queued",
    "gateway.busy.drain_rejected",
    "gateway.busy.drain_rejected_new_work",
)

_in_slash_auth = contextvars.ContextVar("discord_open_channel_slash", default=False)


# ── the server code ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ServerCode:
    salt: bytes
    digest: bytes

    @classmethod
    def parse(cls, raw):
        try:
            scheme, salt, digest = (raw or "").strip().split("$")
            code = cls(bytes.fromhex(salt), bytes.fromhex(digest))
        except ValueError:
            return None
        if scheme != "v1" or len(code.salt) < 16 or len(code.digest) != 32:
            return None
        return code

    def matches(self, candidate):
        mac = hmac.new(self.salt, candidate.encode("utf-8"), hashlib.sha256).digest()
        return hmac.compare_digest(mac, self.digest)


def hash_code(code):
    """The HORUS_SERVER_CODE_HASH value for a code."""
    salt = secrets.token_bytes(16)
    return "v1$%s$%s" % (salt.hex(), hmac.new(salt, code.encode("utf-8"), hashlib.sha256).hexdigest())


def _launch_secrets():
    try:
        from agent.secret_scope import build_profile_secret_scope
        return build_profile_secret_scope(LAUNCH_HOME)
    except Exception as exc:
        log.warning("open channel: cannot read %s/.env: %s", LAUNCH_HOME, type(exc).__name__)
        return {}


def _launch_secret(name):
    return str(_launch_secrets().get(name) or "")


_code_cache = ("", None)


def _server_code():
    global _code_cache
    raw = _launch_secret(CODE_ENV)
    if raw != _code_cache[0]:
        _code_cache = (raw, ServerCode.parse(raw))
        if raw and _code_cache[1] is None:
            log.warning("%s is malformed; nobody can unlock full Horus", CODE_ENV)
    return _code_cache[1]


_MENTION = re.compile(r"<@[!&]?\d+>")
_EDGE = "`'\".,!?;:()[]{}<>*_~|"
_MAX_WORDS = 200
_MAX_WINDOW = 8


def find_code(code, text):
    """(found, other_text): whether text holds the code, alone or inside a sentence."""
    body = _MENTION.sub(" ", text or "").strip()
    if not body:
        return False, False
    if code.matches(body.strip(_EDGE)):
        return True, False
    words = body.split()[:_MAX_WORDS]
    for size in range(1, min(_MAX_WINDOW, len(words)) + 1):
        for start in range(len(words) - size + 1):
            if code.matches(" ".join(words[start:start + size]).strip(_EDGE)):
                return True, len(body.split()) > size
    return False, False


def _holds_code(text):
    code = _server_code()
    return code is not None and find_code(code, str(text or ""))[0]


# ── unlocks ─────────────────────────────────────────────────────────────────

class Unlocks:
    """(user id, scope id) -> monotonic expiry. A scope is a thread, or a channel
    whose threads it covers through their parent_chat_id."""

    def __init__(self, clock=time.monotonic):
        self._until = {}
        self._clock = clock
        self._lock = threading.Lock()

    def grant(self, user_id, scope_id):
        with self._lock:
            self._until[(str(user_id), str(scope_id))] = self._clock() + UNLOCK_SECONDS

    def active(self, user_id, scope_ids):
        now = self._clock()
        with self._lock:
            for key in [key for key, until in self._until.items() if until <= now]:
                del self._until[key]
            return any((str(user_id), str(scope)) in self._until for scope in scope_ids if scope)


UNLOCKS = Unlocks()


# ── sources ─────────────────────────────────────────────────────────────────

def _norm(value):
    return str(getattr(value, "value", value) or "").strip().lower()


def _allowlisted(user_id):
    raw = _launch_secret("DISCORD_ALLOWED_USERS")
    ids = {part.strip() for part in raw.split(",") if part.strip()}
    return str(user_id or "") in ids


def _server_source(source):
    return (
        source is not None
        and _norm(getattr(source, "platform", None)) == "discord"
        and _norm(getattr(source, "chat_type", None)) in SERVER_CHAT_TYPES
        and not getattr(source, "is_bot", False)
    )


def _channel_policy(source):
    if not _server_source(source):
        return None
    for name in ("chat_id", "parent_chat_id"):
        policy = CHANNELS.get(str(getattr(source, name, "") or ""))
        if policy is not None:
            return policy
    return None


# ── 1 and 4: the Discord adapter ────────────────────────────────────────────

def _notice_prefixes():
    try:
        from agent.i18n import t
    except Exception as exc:
        log.warning("notice filter limited to metadata markers, agent.i18n unavailable: %s", exc)
        return ()
    prefixes = []
    for key in NOTICE_KEYS:
        try:
            text = str(t(key))
        except Exception:
            continue
        if text == key:
            continue
        head = text.split("{", 1)[0].strip()
        if len(head) >= 8:
            prefixes.append(head)
    return tuple(prefixes)


def _is_lifecycle_notice(content, metadata):
    if isinstance(metadata, dict) and metadata.get("non_conversational") is True:
        return True
    text = str(content or "").strip()
    return any(text.startswith(prefix) for prefix in _notice_prefixes())


def _patch_adapter_class(cls):
    if getattr(cls, "_open_channel_patched", False):
        return
    original_allowed = cls._is_allowed_user
    original_send = cls.send
    original_slash = getattr(cls, "_evaluate_slash_authorization", None)

    def _is_allowed_user(self, user_id, author=None, *, guild=None, is_dm=False, channel_ids=None):
        if (
            not is_dm
            and guild is not None
            and channel_ids
            and not _in_slash_auth.get()
            and {str(c) for c in channel_ids} & OPEN_CHANNELS
        ):
            return True
        return original_allowed(
            self, user_id, author, guild=guild, is_dm=is_dm, channel_ids=channel_ids,
        )

    async def send(self, chat_id, content, reply_to=None, metadata=None):
        if str(chat_id) in QUIET_CHANNELS and _is_lifecycle_notice(content, metadata):
            log.info("kept a gateway notice out of quiet channel %s", chat_id)
            from gateway.platforms.base import SendResult
            return SendResult(success=False, error="notice suppressed in quiet channel")
        return await original_send(self, chat_id, content, reply_to=reply_to, metadata=metadata)

    cls._is_allowed_user = _is_allowed_user
    cls.send = send

    original_handle = cls.handle_message
    original_enqueue = getattr(cls, "_enqueue_text_event", None)

    async def handle_message(self, event):
        if screen(event) is None:
            return await original_handle(self, event)
        event._gateway_accepted = False

    cls.handle_message = handle_message
    if original_enqueue is not None:
        def _enqueue_text_event(self, event):
            if screen(event) is None:
                return original_enqueue(self, event)
        cls._enqueue_text_event = _enqueue_text_event
    else:
        log.warning("server code: DiscordAdapter._enqueue_text_event not found, "
                    "a code inside a burst of messages may stay visible")

    # The adapter auto-threads an @mention in the channel, naming the thread from the
    # message, before it builds the event screen() sees. A message holding the code
    # gets no thread, and no thread is ever named after it.
    original_auto_thread = getattr(cls, "_auto_create_thread", None)
    if original_auto_thread is not None:
        async def _auto_create_thread(self, message, *args, **kwargs):
            if _holds_code(getattr(message, "content", "")):
                return None
            return await original_auto_thread(self, message, *args, **kwargs)
        cls._auto_create_thread = _auto_create_thread
    else:
        log.warning("server code: DiscordAdapter._auto_create_thread not found")
    original_thread_name = getattr(cls, "_derive_auto_thread_name", None)
    if original_thread_name is not None:
        def _derive_auto_thread_name(self, content, *args, **kwargs):
            if _holds_code(content):
                return "Horus"
            return original_thread_name(self, content, *args, **kwargs)
        cls._derive_auto_thread_name = _derive_auto_thread_name

    if original_slash is not None:
        def _evaluate_slash_authorization(self, interaction):
            token = _in_slash_auth.set(True)
            try:
                return original_slash(self, interaction)
            finally:
                _in_slash_auth.reset(token)
        cls._evaluate_slash_authorization = _evaluate_slash_authorization

    cls._open_channel_patched = True
    log.info("opened Discord channel(s) %s to every sender", ", ".join(sorted(OPEN_CHANNELS)))


def _patch_loaded_adapters():
    found = False
    for module in list(sys.modules.values()):
        cls = getattr(module, "DiscordAdapter", None)
        if isinstance(cls, type) and hasattr(cls, "_is_allowed_user") and hasattr(cls, "send"):
            try:
                _patch_adapter_class(cls)
                found = True
            except Exception as exc:
                log.warning("could not patch %s.DiscordAdapter: %s", module.__name__, exc)
    return found


def _hook_bot_init():
    """The adapter module may load after this plugin, so patch it when the bot is built."""
    try:
        from discord.ext import commands
    except Exception as exc:
        log.warning("open channel disabled, discord.py not importable: %s", exc)
        return
    if getattr(commands.Bot.__init__, "_open_channel_wrapped", False):
        return
    original = commands.Bot.__init__

    def __init__(self, *args, **kwargs):
        if not _patch_loaded_adapters():
            log.warning("open channel disabled, DiscordAdapter not found")
        original(self, *args, **kwargs)

    __init__._open_channel_wrapped = True
    commands.Bot.__init__ = __init__


# ── 2: the gateway's own check ──────────────────────────────────────────────

def admits_outsider(runner, source):
    """True when the routes give this sender the chat-only profile or an unlock."""
    try:
        from gateway.profile_routing import match_profile_route
        route = match_profile_route(
            runner.config.profile_routes, _norm(source.platform),
            guild_id=getattr(source, "scope_id", None) or getattr(source, "guild_id", None),
            chat_id=source.chat_id, thread_id=source.thread_id,
            parent_chat_id=source.parent_chat_id,
            adapter_profile=runner._adapter_profile_for_source(source),
            user_id=source.user_id,
        )
    except Exception as exc:
        log.warning("open channel refused a sender, route lookup failed: %s", exc)
        return False
    return route is not None and (route.profile != "default" or route.name == UNLOCK_ROUTE)


def _patch_gateway_authz():
    try:
        from gateway.authz_mixin import GatewayAuthorizationMixin as mixin
    except Exception as exc:
        log.warning("open channel disabled, gateway authz not importable: %s", exc)
        return
    if getattr(mixin, "_open_channel_patched", False):
        return
    original = mixin._principal_authorized

    def _principal_authorized(self, source, *args, **kwargs):
        if (
            _channel_policy(source) is not None
            and getattr(source, "user_id", None)
            and admits_outsider(self, source)
        ):
            return True
        return original(self, source, *args, **kwargs)

    mixin._principal_authorized = _principal_authorized
    mixin._open_channel_patched = True


# ── 3: the unlock route ─────────────────────────────────────────────────────

def _patch_profile_routes():
    try:
        from gateway.profile_routing import ProfileRoute
    except Exception as exc:
        log.warning("server code disabled, profile routing not importable: %s", exc)
        return
    if getattr(ProfileRoute, "_server_code_patched", False):
        return
    original = ProfileRoute.matches

    def matches(self, platform, *args, **kwargs):
        if self.name == UNLOCK_ROUTE and self.user_id == UNLOCK_SENTINEL:
            sender = kwargs.get("user_id")
            scopes = (kwargs.get("thread_id"), kwargs.get("chat_id"), kwargs.get("parent_chat_id"))
            if not (sender and UNLOCKS.active(sender, scopes)):
                return False
            kwargs = {**kwargs, "user_id": UNLOCK_SENTINEL}
        return original(self, platform, *args, **kwargs)

    ProfileRoute.matches = matches
    ProfileRoute._server_code_patched = True
    log.info("server code unlocks route %s for %d minutes", UNLOCK_ROUTE, UNLOCK_SECONDS // 60)


# ── inbound messages ────────────────────────────────────────────────────────

async def _discord_cleanup(channel_id, message_id, reply):
    token = _launch_secret("DISCORD_BOT_TOKEN")
    if not token:
        log.warning("server code: no DISCORD_BOT_TOKEN, message left in %s", channel_id)
        return
    import httpx
    try:
        async with httpx.AsyncClient(
            base_url=DISCORD_API, headers={"Authorization": f"Bot {token}"}, timeout=10,
        ) as client:
            if message_id:
                deleted = await client.delete(f"/channels/{channel_id}/messages/{message_id}")
                if deleted.status_code != 204:
                    log.warning("server code: could not delete the message in %s (HTTP %s)",
                                channel_id, deleted.status_code)
            posted = await client.post(
                f"/channels/{channel_id}/messages",
                json={"content": reply, "allowed_mentions": {"parse": []}},
            )
            if posted.status_code >= 300:
                log.warning("server code: reply failed in %s (HTTP %s)", channel_id, posted.status_code)
    except Exception as exc:
        log.warning("server code: Discord call failed in %s: %s", channel_id, type(exc).__name__)


_CLEANUPS = set()


def _clean_up_later(channel_id, message_id, reply):
    task = asyncio.get_running_loop().create_task(_discord_cleanup(channel_id, message_id, reply))
    _CLEANUPS.add(task)
    task.add_done_callback(_CLEANUPS.discard)


def screen(event):
    """Why a Discord message must not reach the gateway, or None. A message holding the
    code grants its unlock here and is deleted and answered in the background."""
    source = getattr(event, "source", None)
    if getattr(event, "internal", False) or not _server_source(source):
        return None
    code = _server_code()
    text = str(getattr(event, "text", "") or "")
    if code is not None:
        found, other_text = find_code(code, text)
        if found:
            policy = _channel_policy(source)
            if policy is not None and policy.unlockable:
                UNLOCKS.grant(source.user_id, source.thread_id or source.chat_id)
                reply = ACCEPTED + (RESEND if other_text else "")
                log.info("server code accepted for user %s in %s", source.user_id, source.chat_id)
            else:
                reply = WRONG_CHANNEL
                log.info("server code refused outside #ai-bot for user %s in %s",
                         source.user_id, source.chat_id)
            message_id = getattr(event, "message_id", None) or getattr(
                getattr(event, "raw_message", None), "id", None)
            _clean_up_later(source.chat_id, message_id, reply)
            return "server-code"
    if (
        _channel_policy(source) is not None
        and not _allowlisted(source.user_id)
        and text.lstrip().startswith("/")
    ):
        log.info("dropped a command in open channel %s from user %s", source.chat_id, source.user_id)
        return "open-channel-commands-allowlisted"
    return None


def register(ctx):
    if _server_code() is None:
        log.warning("%s unset; nobody can unlock full Horus in #ai-bot", CODE_ENV)
    _patch_loaded_adapters()
    _hook_bot_init()
    _patch_gateway_authz()
    _patch_profile_routes()
