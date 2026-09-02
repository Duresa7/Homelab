"""Discord alert bot for the homelab.

Grafana posts its webhook payload to POST /grafana with a bearer secret. The
bot turns each alert in the payload into one embed and posts it to the alerts
channel as the bot user. GET /health answers 200 only once the Discord session
is ready, so the blackbox probe of this endpoint reflects real health.

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

import discord
from aiohttp import web

log = logging.getLogger("alert-bot")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

TOKEN = os.environ["DISCORD_TOKEN"]
CHANNEL_ID = int(os.environ["DISCORD_CHANNEL_ID"])
SECRET = os.environ["ALERT_BOT_SECRET"]
PORT = int(os.environ.get("PORT", "8080"))

COLOR = {"critical": 0xE03131, "warning": 0xF08C00, "info": 0x1971C2, "resolved": 0x2F9E44}
# Labels worth a field of their own, in display order. Anything else stays out
# of the embed so the message says what is wrong rather than listing metadata.
SHOW_LABELS = ("host", "name", "node", "id", "instance", "mountpoint", "ups", "status")

client = discord.Client(intents=discord.Intents.default())


def build_embed(alert: dict) -> discord.Embed:
    labels = alert.get("labels", {})
    ann = alert.get("annotations", {})
    resolved = alert.get("status") == "resolved"
    severity = "resolved" if resolved else labels.get("severity", "warning")
    name = labels.get("alertname", "Alert")
    title = ("Resolved: " if resolved else f"{severity.upper()}: ") + name
    embed = discord.Embed(
        title=title[:256],
        description=(ann.get("summary") or "")[:4096],
        color=COLOR.get(severity, COLOR["warning"]),
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
    channel = client.get_channel(CHANNEL_ID) or await client.fetch_channel(CHANNEL_ID)
    posted = 0
    for alert in alerts:
        msg = await channel.send(embed=build_embed(alert))
        posted += 1
        log.info("posted %s %s as message %s", alert.get("status"), alert.get("labels", {}).get("alertname"), msg.id)
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
