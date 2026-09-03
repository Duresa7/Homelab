"""Discord alert bot for the homelab.

Grafana posts its webhook payload to POST /grafana with a bearer secret. The
bot turns each alert in the payload into one embed and posts it to the alerts
channel as the bot user. GET /health answers 200 only once the Discord session
is ready, so the blackbox probe of this endpoint reflects real health.

Every alert carries a class, read from the `class` label and defaulting to
infrastructure. The class picks the embed colour and a title prefix so one
channel can hold outage, security and update messages and still be readable at
a glance. Added 2026-09-02.

Splunk posts its webhook alert action to POST /splunk. Splunk's webhook cannot
send a header, so that endpoint is guarded by source address instead: only
SPLUNK_SOURCE_IP is accepted, and the UniFi policy "Allow splunk-siem to alert
bot" is what lets that one address reach this port at all. Every Splunk alert
is class security. Added 2026-09-02.

Deployed at /home/dkadi/monitoring/alert-bot/ on monitor-01, built by the
monitoring Compose project. Configuration is environment only:

  DISCORD_TOKEN        bot token, from the password manager, never in a file
                       that is versioned
  DISCORD_CHANNEL_ID   numeric channel id for #bots
  ALERT_BOT_SECRET     shared secret Grafana sends as "Authorization: Bearer"
  SPLUNK_SOURCE_IP     the one address allowed to POST /splunk, splunk-siem
"""
import asyncio
import logging
import os
import re
import sys
from collections import OrderedDict

import discord
from aiohttp import web

log = logging.getLogger("alert-bot")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

TOKEN = os.environ["DISCORD_TOKEN"]
CHANNEL_ID = int(os.environ["DISCORD_CHANNEL_ID"])
SECRET = os.environ["ALERT_BOT_SECRET"]
PORT = int(os.environ.get("PORT", "8080"))
SPLUNK_SOURCE_IP = os.environ.get("SPLUNK_SOURCE_IP", "192.168.72.3")

# Infrastructure alerts colour by severity. The other two classes colour by
# class, because "a security event" and "an update is waiting" are the whole
# message and severity adds little.
SEVERITY_COLOR = {"critical": 0xE03131, "warning": 0xF08C00, "info": 0x1971C2}
CLASS_STYLE = {
    "infrastructure": {"prefix": "", "color": None},
    "security": {"prefix": "SECURITY ", "color": 0x7048E8},
    "updates": {"prefix": "UPDATES ", "color": 0x1C7ED6},
}
RESOLVED_COLOR = 0x2F9E44
# Labels worth a field of their own, in display order. Anything else stays out
# of the embed so the message says what is wrong rather than listing metadata.
SHOW_LABELS = ("host", "name", "node", "id", "instance", "mountpoint", "device", "disk", "ups", "status")
# Splunk result fields worth a line each, in display order. A saved search
# names its own columns, so this is the union across the searches that post
# here; anything absent is skipped, anything else in the result is ignored.
SPLUNK_FIELDS = (
    "src", "src_ip", "dest_ip", "dest_port", "ports", "rule", "signature", "action",
    "count", "targets", "agent.name", "Machine", "Last", "Silent", "user",
    "rule.id", "rule.level", "rule.description", "syscheck.path", "src_zone", "dest_zone",
)
# A notification carrying this many alerts with the same name and status is
# collapsed into one embed that lists them, so a host going down or a batch of
# update notices is one message rather than a wall of identical cards.
CONDENSE_AT = 4

client = discord.Client(intents=discord.Intents.default())


def alert_class(labels: dict) -> str:
    cls = labels.get("class", "infrastructure")
    return cls if cls in CLASS_STYLE else "infrastructure"


def title_and_color(labels: dict, resolved: bool) -> tuple[str, int]:
    style = CLASS_STYLE[alert_class(labels)]
    name = labels.get("alertname", "Alert")
    if resolved:
        return f"Resolved: {style['prefix']}{name}", RESOLVED_COLOR
    severity = labels.get("severity", "warning")
    color = style["color"] if style["color"] is not None else SEVERITY_COLOR.get(severity, SEVERITY_COLOR["warning"])
    return f"{style['prefix']}{severity.upper()}: {name}", color

# Discord rejects the whole message with "Invalid Form Body" if any embed field
# value passes 1024 characters or the embed as a whole passes 6000. Grafana's
# silence link carries a matcher for every label on the alert, and an alert
# built from a metric with many labels (wud_containers has fifteen) produces a
# link well past 1024 characters. The first Updates batch failed on exactly
# that, and Grafana retried it every half hour until the bot was fixed.
FIELD_LIMIT = 1024
EMBED_LIMIT = 6000


# Discord also rejects an embed whose url is not "well formed", and its idea
# of well formed includes a dot in the host. Splunk builds its results link
# from the server's own name, which was the bare hostname splunk-siem until
# the apps set alert_actions.conf hostname; this keeps one bad link from
# taking the whole message down.
URL_OK = re.compile(r"^https?://[^/\s]+\.[^/\s]+")


def safe_url(url: str | None) -> str | None:
    if url and URL_OK.match(url):
        return url
    return None


def add_silence_field(embed: discord.Embed, silence_url: str | None, resolved: bool) -> None:
    if not silence_url or resolved:
        return
    value = f"[in Grafana]({silence_url})"
    if len(value) <= FIELD_LIMIT:
        embed.add_field(name="Silence", value=value, inline=False)


def fit_embed(embed: discord.Embed) -> discord.Embed:
    """Trim the description until the embed is under Discord's total size."""
    while len(embed) > EMBED_LIMIT and embed.description:
        excess = len(embed) - EMBED_LIMIT
        embed.description = embed.description[: max(0, len(embed.description) - excess - 1)] + "…"
    if len(embed) > EMBED_LIMIT:
        embed.clear_fields()
    return embed


def build_embed(alert: dict) -> discord.Embed:
    labels = alert.get("labels", {})
    ann = alert.get("annotations", {})
    resolved = alert.get("status") == "resolved"
    title, color = title_and_color(labels, resolved)
    embed = discord.Embed(
        title=title[:256],
        description=(ann.get("summary") or "")[:4096],
        color=color,
        url=safe_url(alert.get("dashboardURL") or alert.get("generatorURL")),
    )
    for key in SHOW_LABELS:
        if key in labels and labels[key]:
            embed.add_field(name=key, value=str(labels[key])[:1024], inline=True)
    if not resolved and ann.get("description"):
        embed.add_field(name="Detail", value=ann["description"][:1024], inline=False)
    add_silence_field(embed, alert.get("silenceURL"), resolved)
    embed.set_footer(text=f"Grafana · {labels.get('grafana_folder', 'AlphaSec United Alerts')}")
    return fit_embed(embed)


def build_condensed_embed(alerts: list[dict]) -> discord.Embed:
    first = alerts[0]
    labels = first.get("labels", {})
    resolved = first.get("status") == "resolved"
    title, color = title_and_color(labels, resolved)
    lines = []
    for alert in alerts:
        summary = (alert.get("annotations", {}).get("summary") or "").strip()
        subject = alert.get("labels", {}).get("host") or alert.get("labels", {}).get("name") or alert.get("labels", {}).get("instance") or ""
        lines.append(f"• {summary}" if summary else f"• {subject}")
    embed = discord.Embed(
        title=f"{title} ({len(alerts)})"[:256],
        description="\n".join(lines)[:4096],
        color=color,
        url=safe_url(first.get("dashboardURL") or first.get("generatorURL")),
    )
    add_silence_field(embed, first.get("silenceURL"), resolved)
    embed.set_footer(text=f"Grafana · {labels.get('grafana_folder', 'AlphaSec United Alerts')}")
    return fit_embed(embed)


def embeds_for(alerts: list[dict]) -> list[discord.Embed]:
    groups: "OrderedDict[tuple, list[dict]]" = OrderedDict()
    for alert in alerts:
        key = (alert.get("labels", {}).get("alertname"), alert.get("status"))
        groups.setdefault(key, []).append(alert)
    embeds = []
    for group in groups.values():
        if len(group) >= CONDENSE_AT:
            embeds.append(build_condensed_embed(group))
        else:
            embeds.extend(build_embed(a) for a in group)
    return embeds


async def post_embeds(embeds: list[discord.Embed], source: str) -> int:
    channel = client.get_channel(CHANNEL_ID) or await client.fetch_channel(CHANNEL_ID)
    posted = 0
    for embed in embeds:
        msg = await channel.send(embed=embed)
        posted += 1
        log.info("posted %s from %s as message %s", embed.title, source, msg.id)
    return posted


async def handle_grafana(request: web.Request) -> web.Response:
    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {SECRET}":
        log.warning("rejected webhook from %s: bad or missing bearer", request.remote)
        return web.Response(status=401, text="unauthorized")
    try:
        payload = await request.json()
    except Exception:
        return web.Response(status=400, text="body is not json")
    alerts = payload.get("alerts") or []
    if not client.is_ready():
        log.error("received %d alert(s) but discord session not ready", len(alerts))
        return web.Response(status=503, text="discord not ready")
    posted = await post_embeds(embeds_for(alerts), "grafana")
    return web.json_response({"posted": posted, "alerts": len(alerts)})


def build_splunk_embed(payload: dict) -> discord.Embed:
    result = payload.get("result") or {}
    name = payload.get("search_name") or "Splunk alert"
    # The saved searches are named "<Source> - <what happened>"; the source
    # becomes part of the footer and the rest is the title.
    source, _, what = name.partition(" - ")
    if not what:
        source, what = "Splunk", name
    style = CLASS_STYLE["security"]
    embed = discord.Embed(
        title=f"{style['prefix']}{what}"[:256],
        description=(result.get("description") or result.get("summary") or "")[:4096] or None,
        color=style["color"],
        url=safe_url(payload.get("results_link")),
    )
    for key in SPLUNK_FIELDS:
        value = result.get(key)
        if value in (None, "", [], "null"):
            continue
        if isinstance(value, list):
            value = ", ".join(str(v) for v in value[:12])
        embed.add_field(name=key, value=str(value)[:1024], inline=True)
    embed.set_footer(text=f"Splunk · {source} · {payload.get('app') or ''}".rstrip(" ·"))
    return fit_embed(embed)


async def handle_splunk(request: web.Request) -> web.Response:
    if request.remote != SPLUNK_SOURCE_IP:
        log.warning("rejected splunk webhook from %s: not %s", request.remote, SPLUNK_SOURCE_IP)
        return web.Response(status=403, text="forbidden")
    try:
        payload = await request.json()
    except Exception:
        return web.Response(status=400, text="body is not json")
    if not client.is_ready():
        log.error("received splunk alert %s but discord session not ready", payload.get("search_name"))
        return web.Response(status=503, text="discord not ready")
    posted = await post_embeds([build_splunk_embed(payload)], f"splunk sid={payload.get('sid')}")
    return web.json_response({"posted": posted})


async def handle_health(_: web.Request) -> web.Response:
    if client.is_ready():
        return web.Response(text="ok")
    return web.Response(status=503, text="discord not ready")


@client.event
async def on_ready():
    log.info("discord ready as %s (id %s), posting to channel %s", client.user, client.user.id, CHANNEL_ID)


async def main() -> None:
    app = web.Application()
    app.router.add_post("/grafana", handle_grafana)
    app.router.add_post("/splunk", handle_splunk)
    app.router.add_get("/health", handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", PORT).start()
    log.info("http listening on :%d", PORT)
    async with client:
        await client.start(TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
