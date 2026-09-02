"""Discord alert bot for the homelab.

Grafana posts its webhook payload to POST /grafana with a bearer secret. The
bot turns each alert in the payload into one embed and posts it to the alerts
channel as the bot user. GET /health answers 200 only once the Discord session
is ready, so the blackbox probe of this endpoint reflects real health.

Every alert carries a class, read from the `class` label and defaulting to
infrastructure. The class picks the embed colour and a title prefix so one
channel can hold outage, security and update messages and still be readable at
a glance. Added 2026-09-02.

Deployed at /home/dkadi/monitoring/alert-bot/ on monitor-01, built by the
monitoring Compose project. Configuration is environment only:

  DISCORD_TOKEN        bot token, from the password manager, never in a file
                       that is versioned
  DISCORD_CHANNEL_ID   numeric channel id for #bots
  ALERT_BOT_SECRET     shared secret Grafana sends as "Authorization: Bearer"
"""
import asyncio
import logging
import os
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


def build_embed(alert: dict) -> discord.Embed:
    labels = alert.get("labels", {})
    ann = alert.get("annotations", {})
    resolved = alert.get("status") == "resolved"
    title, color = title_and_color(labels, resolved)
    embed = discord.Embed(
        title=title[:256],
        description=(ann.get("summary") or "")[:4096],
        color=color,
        url=alert.get("dashboardURL") or alert.get("generatorURL") or None,
    )
    for key in SHOW_LABELS:
        if key in labels and labels[key]:
            embed.add_field(name=key, value=str(labels[key])[:1024], inline=True)
    if not resolved and ann.get("description"):
        embed.add_field(name="Detail", value=ann["description"][:1024], inline=False)
    if alert.get("silenceURL") and not resolved:
        embed.add_field(name="Silence", value=f"[in Grafana]({alert['silenceURL']})", inline=False)
    embed.set_footer(text=f"Grafana · {labels.get('grafana_folder', 'Homelab Alerts')}")
    return embed


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
        url=first.get("dashboardURL") or first.get("generatorURL") or None,
    )
    if first.get("silenceURL") and not resolved:
        embed.add_field(name="Silence", value=f"[in Grafana]({first['silenceURL']})", inline=False)
    embed.set_footer(text=f"Grafana · {labels.get('grafana_folder', 'Homelab Alerts')}")
    return embed


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
