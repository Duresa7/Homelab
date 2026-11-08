"""Behavior checks for the discord-open-channel plugin against Hermes's real routing.

Run on hermes-01 with Hermes's own Python, from ~/.hermes/hermes-agent:
    <hermes venv python> test_open_channel.py <plugin __init__.py> [<live hermes home>]
Uses a throwaway code and never calls Discord. With a live home, it also reads that
home's real .env through Hermes's secret loader while the chat-only profile's scope is
bound, the way the multiplexing gateway runs a routed message, and reports only
whether each key is present.
"""

import asyncio
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

SECRET = "1016933615793356820"
AI_BOT = "1568709425131290704"
GUILD = "984884989407690883"
ALLOWED, OUTSIDER, OTHER = "111", "222", "333"
TEST_CODE = "Sun-Rise_42"

failures = []


def check(ok, label):
    print(("ok   " if ok else "FAIL ") + label)
    if not ok:
        failures.append(label)


spec = importlib.util.spec_from_file_location("open_channel_under_test", sys.argv[1])
plugin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plugin)

if len(sys.argv) > 2:
    from agent.secret_scope import (
        build_profile_secret_scope, reset_secret_scope, set_multiplex_active, set_secret_scope)
    live_home = Path(sys.argv[2])
    plugin.LAUNCH_HOME = live_home
    set_multiplex_active(True)
    token = set_secret_scope(build_profile_secret_scope(live_home / "profiles" / "public"),
                             profile_home=str(live_home / "profiles" / "public"))
    try:
        for key in (plugin.CODE_ENV, "DISCORD_BOT_TOKEN", "DISCORD_ALLOWED_USERS"):
            check(bool(plugin._launch_secret(key)), f"live: {key} readable under the public profile's scope")
        check(plugin._server_code() is not None, "live: the stored code hash parses")
    finally:
        reset_secret_scope(token)
        set_multiplex_active(False)

SECRETS = {"DISCORD_ALLOWED_USERS": ALLOWED, plugin.CODE_ENV: plugin.hash_code(TEST_CODE)}
plugin._launch_secrets = lambda: SECRETS

calls = []


async def fake_cleanup(channel_id, message_id, reply):
    calls.append((channel_id, message_id, reply))

plugin._discord_cleanup = fake_cleanup

clock = [1000.0]
plugin.UNLOCKS = plugin.Unlocks(clock=lambda: clock[0])

from gateway.profile_routing import match_profile_route, parse_profile_routes

plugin._patch_profile_routes()
ROUTES = parse_profile_routes([
    {"name": "secret-channel", "platform": "discord", "guild_id": GUILD, "chat_id": SECRET, "profile": "public"},
    {"name": "ai-bot-channel", "platform": "discord", "guild_id": GUILD, "chat_id": AI_BOT, "profile": "public"},
    {"name": plugin.UNLOCK_ROUTE, "platform": "discord", "guild_id": GUILD, "chat_id": AI_BOT,
     "user_id": plugin.UNLOCK_SENTINEL, "profile": "default"},
])


def source(user, chat, thread=None, parent=None, chat_type=None):
    return SimpleNamespace(
        platform="discord", chat_type=chat_type or ("thread" if thread else "group"),
        chat_id=chat, thread_id=thread, parent_chat_id=parent, user_id=user,
        scope_id=GUILD, guild_id=GUILD, is_bot=False,
    )


def in_thread(user, thread, channel=AI_BOT):
    return source(user, thread, thread=thread, parent=channel)


def profile_for(src):
    route = match_profile_route(
        ROUTES, "discord", guild_id=GUILD, chat_id=src.chat_id, thread_id=src.thread_id,
        parent_chat_id=src.parent_chat_id, adapter_profile=None, user_id=src.user_id)
    return route.profile if route else "default (no route)"


def dispatch(src, text, message_id="m1"):
    calls.clear()
    return asyncio.run(plugin.on_dispatch(SimpleNamespace(text=text, source=src, message_id=message_id)))


SKIP = {"action": "skip", "reason": "server-code"}

check(profile_for(in_thread(OUTSIDER, "t1")) == "public", "before the code, an outsider in an #ai-bot thread gets public")
check(profile_for(in_thread(ALLOWED, "t1")) == "public", "before the code, an allowlisted user gets public too")

check(dispatch(in_thread(OUTSIDER, "t1"), TEST_CODE) == SKIP, "the code alone in a thread is dropped before the model")
check(calls == [("t1", "m1", plugin.ACCEPTED)], "the code message is deleted and answered with the accepted text")
check(profile_for(in_thread(OUTSIDER, "t1")) == "default", "after the code, that sender in that thread gets default")
check(profile_for(in_thread(OTHER, "t1")) == "public", "another sender in the same thread stays public")
check(profile_for(in_thread(OUTSIDER, "t2")) == "public", "the same sender in another thread stays public")

clock[0] += 15 * 60 - 1
check(profile_for(in_thread(OUTSIDER, "t1")) == "default", "still unlocked at 14:59")
clock[0] += 2
check(profile_for(in_thread(OUTSIDER, "t1")) == "public", "locked again after 15 minutes")

check(dispatch(source(OTHER, AI_BOT), f"<@999> {TEST_CODE}") == SKIP, "the code with an @mention in the channel is dropped")
check(calls == [(AI_BOT, "m1", plugin.ACCEPTED)], "the channel message is deleted and answered in the channel")
check(profile_for(in_thread(OTHER, "t9")) == "default", "a channel-level code unlocks that sender's new threads")

check(dispatch(in_thread(OUTSIDER, "t3"), f"please `{TEST_CODE}`, restart minecraft") == SKIP,
      "the code inside a sentence is still caught")
check(calls and calls[0][2] == plugin.ACCEPTED + plugin.RESEND, "a sentence with the code asks for the request again")

check(dispatch(in_thread(OUTSIDER, "t4"), "Sun-Rise_43") is None, "a near miss goes to the model as normal text")
check(dispatch(in_thread(OUTSIDER, "t4"), "sun-rise_42") is None, "the code is case-sensitive")
check(calls == [], "a near miss makes no Discord call")
check(profile_for(in_thread(OUTSIDER, "t4")) == "public", "a near miss unlocks nothing")

check(dispatch(in_thread(OUTSIDER, "s1", channel=SECRET), TEST_CODE) == SKIP, "the code in #secret is dropped too")
check(calls == [("s1", "m1", plugin.WRONG_CHANNEL)], "#secret answers that the code only works in #ai-bot")
check(profile_for(in_thread(OUTSIDER, "s1", channel=SECRET)) == "public", "#secret never unlocks")

check(dispatch(in_thread(OUTSIDER, "t5"), "/restart") == {"action": "skip", "reason": "open-channel-commands-allowlisted"},
      "an outsider's typed command is dropped")
check(dispatch(in_thread(ALLOWED, "t5"), "/restart") is None, "an allowlisted user's typed command passes")

runner = SimpleNamespace(config=SimpleNamespace(profile_routes=ROUTES), _adapter_profile_for_source=lambda s: None)
check(plugin.admits_outsider(runner, in_thread(OUTSIDER, "t6")), "admission lets an outsider reach public")
plugin.UNLOCKS.grant(OUTSIDER, "t6")
check(plugin.admits_outsider(runner, in_thread(OUTSIDER, "t6")), "admission lets an unlocked sender reach default")
no_channel_route = SimpleNamespace(
    config=SimpleNamespace(profile_routes=[r for r in ROUTES if r.name != "ai-bot-channel"]),
    _adapter_profile_for_source=lambda s: None)
check(not plugin.admits_outsider(no_channel_route, in_thread("444", "t7")),
      "without the #ai-bot route, an outsider is refused instead of reaching default")

SECRETS[plugin.CODE_ENV] = "garbage"
check(dispatch(in_thread(OUTSIDER, "t8"), TEST_CODE) is None, "a malformed hash unlocks nothing")
SECRETS[plugin.CODE_ENV] = plugin.hash_code(TEST_CODE)


class FakeAdapter:
    def _is_allowed_user(self, user_id, author=None, *, guild=None, is_dm=False, channel_ids=None):
        return False

    async def send(self, chat_id, content, reply_to=None, metadata=None):
        return "sent"

    async def _auto_create_thread(self, message):
        return "thread"

    def _derive_auto_thread_name(self, content):
        return content[:20]


plugin._patch_adapter_class(FakeAdapter)
adapter = FakeAdapter()
check(asyncio.run(adapter._auto_create_thread(SimpleNamespace(content=f"<@999> {TEST_CODE}"))) is None,
      "a channel message holding the code gets no auto-thread")
check(asyncio.run(adapter._auto_create_thread(SimpleNamespace(content="<@999> hello"))) == "thread",
      "a normal channel message still gets its thread")
check(adapter._derive_auto_thread_name(f"run {TEST_CODE}") == "Horus", "no thread is named after the code")
check(adapter._is_allowed_user("x", guild=object(), channel_ids=[AI_BOT]), "the adapter admits senders in #ai-bot")
check(not adapter._is_allowed_user("x", guild=object(), channel_ids=["999"]), "the adapter leaves other channels alone")


print(f"\n{len(failures)} failure(s)")
sys.exit(1 if failures else 0)
