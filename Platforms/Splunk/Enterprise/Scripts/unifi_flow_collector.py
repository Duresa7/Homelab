#!/usr/bin/env python3
"""Poll UniFi Traffic Flows and forward them to Splunk HEC.

The UniFi CEF syslog export carries events only: admin logins, client
connect/disconnect, threat alerts. The per-connection records behind
Insights > Flows -- allow/block decisions, risk bands, source region, policy
attribution, byte and packet counts -- live only on the controller's private
v2 API. This collector reads that API and writes the records to the netfw
index so the same view can be built in Splunk.

Configuration comes from /etc/unifi-flow-collector/env (mode 600, root-owned).
Fields are emitted under Common Information Model names where the meaning
matches, so ES data models populate without a translation layer.

Runs as a systemd service; state persists in
/var/lib/unifi-flow-collector/checkpoint.json across restarts.
"""

import base64
import http.cookiejar
import json
import logging
import os
import signal
import ssl
import sys
import time
import urllib.error
import urllib.request
from collections import OrderedDict

ENV_PATH = "/etc/unifi-flow-collector/env"
STATE_DIR = "/var/lib/unifi-flow-collector"
CHECKPOINT = os.path.join(STATE_DIR, "checkpoint.json")

# Array filters the endpoint requires present in the body. All empty: no
# server-side filtering, every flow comes back.
QUERY_ARRAYS = (
    "risk", "action", "direction", "protocol", "service", "source_mac",
    "source_ip", "source_host", "source_network_id", "destination_domain",
    "destination_ip", "destination_region", "policy", "policy_type",
    "source_port", "source_domain", "source_zone_id", "source_region",
    "destination_host", "destination_mac", "destination_port",
    "destination_network_id", "destination_zone_id", "in_network_id",
    "out_network_id", "next_ai_query", "except_for",
)

# Overlap re-queried each poll so a flow that lands late is still picked up;
# duplicates are dropped by flow id.
OVERLAP_SECONDS = 300
# Bound on remembered flow ids. At ~10k flows/hour a 300s overlap is ~850
# ids, so this holds many multiples of the window.
SEEN_LIMIT = 40000
MAX_PAGES = 200
HEC_BATCH = 250

log = logging.getLogger("unifi-flow-collector")


def load_env(path=ENV_PATH):
    env = {}
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip()
    return env


class UniFiSession:
    """Cookie session against UniFi OS, re-authenticating when it expires."""

    def __init__(self, host, username, password, verify_ssl=False):
        self.host = host
        self.username = username
        self.password = password
        ctx = ssl.create_default_context()
        if not verify_ssl:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        self.ctx = ctx
        self.csrf = None
        self.opener = None

    def login(self):
        jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPSHandler(context=self.ctx),
            urllib.request.HTTPCookieProcessor(jar),
        )
        body = json.dumps({
            "username": self.username,
            "password": self.password,
            "rememberMe": True,
        }).encode()
        req = urllib.request.Request(
            "https://%s/api/auth/login" % self.host,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        resp = self.opener.open(req, timeout=20)
        self.csrf = (resp.headers.get("X-Updated-CSRF-Token")
                     or resp.headers.get("X-CSRF-Token"))
        if not self.csrf:
            # Older firmware omits the header and carries the token in the JWT.
            token = next((c.value for c in jar if c.name == "TOKEN"), None)
            if token:
                payload = token.split(".")[1]
                payload += "=" * (-len(payload) % 4)
                self.csrf = json.loads(
                    base64.urlsafe_b64decode(payload)).get("csrfToken")
        log.info("authenticated to UniFi controller at %s", self.host)

    def post(self, path, payload, _retry=True):
        if self.opener is None:
            self.login()
        headers = {"Content-Type": "application/json"}
        if self.csrf:
            headers["X-CSRF-Token"] = self.csrf
        req = urllib.request.Request(
            "https://%s%s" % (self.host, path),
            data=json.dumps(payload).encode(),
            headers=headers,
            method="POST",
        )
        try:
            with self.opener.open(req, timeout=60) as resp:
                updated = resp.headers.get("X-Updated-CSRF-Token")
                if updated:
                    self.csrf = updated
                return json.load(resp)
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403) and _retry:
                log.info("session rejected (HTTP %s), re-authenticating", exc.code)
                self.login()
                return self.post(path, payload, _retry=False)
            raise


def _name_of(side):
    """Best human label for a flow endpoint, falling back to the address."""
    for key in ("client_name", "device_name", "host_name"):
        value = side.get(key)
        if value:
            return value
    return side.get("ip")


def flatten(flow, controller):
    """Map one controller flow record onto flat, CIM-named fields.

    CIM Network_Traffic uses src/dest/bytes/packets/transport/app/action, and
    UniFi's own allowed|blocked already matches the CIM action vocabulary, so
    the values pass through unchanged. UniFi-only attributes that carry the
    Insights meaning -- risk, zones, region, policy -- keep their own names.
    """
    src = flow.get("source") or {}
    dst = flow.get("destination") or {}
    traffic = flow.get("traffic_data") or {}
    policies = flow.get("policies") or []
    inbound = flow.get("in") or {}
    outbound = flow.get("out") or {}

    event = {
        "flow_id": flow.get("id"),
        "action": flow.get("action"),
        "risk": flow.get("risk"),
        "app": flow.get("service"),
        "service": flow.get("service"),
        "transport": (flow.get("protocol") or "").lower() or None,
        "protocol": flow.get("protocol"),
        "direction": flow.get("direction"),
        "count": flow.get("count"),
        "vendor_product": "UniFi Network",
        "dvc": controller,

        "src": _name_of(src),
        "src_ip": src.get("ip"),
        "src_port": src.get("port"),
        "src_mac": src.get("mac"),
        "src_name": src.get("client_name"),
        "src_host": src.get("host_name"),
        "src_device": src.get("device_name"),
        "src_device_model": src.get("device_model"),
        "src_oui": src.get("client_oui"),
        "src_network": src.get("network_name"),
        "src_subnet": src.get("subnet"),
        "src_zone": src.get("zone_name"),
        "src_region": src.get("region"),

        "dest": _name_of(dst),
        "dest_ip": dst.get("ip"),
        "dest_port": dst.get("port"),
        "dest_mac": dst.get("mac"),
        "dest_name": dst.get("client_name"),
        "dest_host": dst.get("host_name"),
        "dest_device": dst.get("device_name"),
        "dest_device_model": dst.get("device_model"),
        "dest_oui": dst.get("client_oui"),
        "dest_network": dst.get("network_name"),
        "dest_subnet": dst.get("subnet"),
        "dest_zone": dst.get("zone_name"),
        "dest_region": dst.get("region"),

        "in_network": inbound.get("network_name"),
        "out_network": outbound.get("network_name"),

        "bytes": traffic.get("bytes_total"),
        "bytes_in": traffic.get("bytes_rx"),
        "bytes_out": traffic.get("bytes_tx"),
        "packets": traffic.get("packets_total"),
        "packets_in": traffic.get("packets_rx"),
        "packets_out": traffic.get("packets_tx"),
    }

    domains = dst.get("domains") or []
    if domains:
        # Multivalue in Splunk; the first is what Insights shows as the label.
        event["dest_domain"] = domains if len(domains) > 1 else domains[0]
    src_domains = src.get("domains") or []
    if src_domains:
        event["src_domain"] = src_domains if len(src_domains) > 1 else src_domains[0]

    duration_ms = flow.get("duration_milliseconds")
    if duration_ms is not None:
        event["duration_ms"] = duration_ms
        event["duration"] = round(duration_ms / 1000.0, 3)
    for key, field in (("flow_start_time", "flow_start"), ("flow_end_time", "flow_end")):
        if flow.get(key) is not None:
            event[field] = flow[key] / 1000.0

    if policies:
        event["rule"] = [p.get("name") or p.get("internal_type")
                         for p in policies if p.get("name") or p.get("internal_type")]
        event["policy_type"] = [p.get("type") for p in policies if p.get("type")]
        event["policy_internal_type"] = [p.get("internal_type")
                                         for p in policies if p.get("internal_type")]
        # An IPS match carries the signature category that classified it
        # (EMERGING_P2P, EMERGING_SCAN, ...); it is the only place the reason
        # for a high risk band is stated.
        event["ips_category"] = [p.get("ips_category") for p in policies
                                 if p.get("ips_category")]
        for field in ("rule", "policy_type", "policy_internal_type",
                      "ips_category"):
            value = event.get(field)
            if isinstance(value, list):
                # Collapse to a scalar when there is only one, so `stats by rule`
                # behaves the way a reader expects.
                deduped = list(OrderedDict.fromkeys(value))
                event[field] = deduped[0] if len(deduped) == 1 else deduped

    # A blocked flow is what Insights highlights; make it directly searchable
    # rather than requiring action="blocked" everywhere.
    event["is_blocked"] = 1 if flow.get("action") == "blocked" else 0
    event["is_external"] = 1 if "External" in (src.get("zone_name"),
                                               dst.get("zone_name")) else 0

    # Drop nulls, empty strings and empty lists so the indexed JSON carries only
    # fields that actually have a value.
    return {k: v for k, v in event.items()
            if v is not None and v != "" and v != []}


class Checkpoint:
    def __init__(self, path=CHECKPOINT):
        self.path = path
        self.last_time_ms = 0
        self.seen = OrderedDict()
        self._load()

    def _load(self):
        try:
            with open(self.path) as fh:
                data = json.load(fh)
            self.last_time_ms = data.get("last_time_ms", 0)
            for flow_id in data.get("seen", []):
                self.seen[flow_id] = None
            log.info("resumed checkpoint: last_time_ms=%s seen=%d",
                     self.last_time_ms, len(self.seen))
        except FileNotFoundError:
            log.info("no checkpoint, starting fresh")
        except (ValueError, OSError) as exc:
            log.warning("unreadable checkpoint (%s), starting fresh", exc)

    def mark(self, flow_id, time_ms):
        self.seen[flow_id] = None
        if time_ms > self.last_time_ms:
            self.last_time_ms = time_ms
        while len(self.seen) > SEEN_LIMIT:
            self.seen.popitem(last=False)

    def is_new(self, flow_id):
        return flow_id not in self.seen

    def save(self):
        tmp = self.path + ".tmp"
        with open(tmp, "w") as fh:
            json.dump({"last_time_ms": self.last_time_ms,
                       "seen": list(self.seen)}, fh)
        os.replace(tmp, self.path)


class HecWriter:
    def __init__(self, url, token, index, sourcetype="unifi:flow",
                 source="unifi:traffic-flows", host=None, verify_ssl=False):
        self.url = url
        self.token = token
        self.index = index
        self.sourcetype = sourcetype
        self.source = source
        self.host = host
        ctx = ssl.create_default_context()
        if not verify_ssl:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPSHandler(context=ctx))

    def send(self, events):
        """events: list of (epoch_seconds, dict). Returns count written."""
        written = 0
        for start in range(0, len(events), HEC_BATCH):
            chunk = events[start:start + HEC_BATCH]
            payload = "".join(
                json.dumps({
                    "time": ts,
                    "host": self.host,
                    "source": self.source,
                    "sourcetype": self.sourcetype,
                    "index": self.index,
                    "event": ev,
                }) for ts, ev in chunk).encode()
            req = urllib.request.Request(
                self.url, data=payload,
                headers={"Authorization": "Splunk %s" % self.token,
                         "Content-Type": "application/json"},
                method="POST")
            with self.opener.open(req, timeout=60) as resp:
                body = json.load(resp)
            if body.get("code") != 0:
                raise RuntimeError("HEC rejected batch: %s" % body)
            written += len(chunk)
        return written


_stop = False


def _handle_signal(signum, _frame):
    global _stop
    log.info("received signal %s, finishing current poll then exiting", signum)
    _stop = True


def poll_once(session, hec, checkpoint, site, page_size, lookback_seconds):
    now_ms = int(time.time() * 1000)
    if checkpoint.last_time_ms:
        start_ms = checkpoint.last_time_ms - OVERLAP_SECONDS * 1000
    else:
        start_ms = now_ms - lookback_seconds * 1000

    path = "/proxy/network/v2/api/site/%s/traffic-flows" % site
    pending = []
    fetched = 0

    for page in range(MAX_PAGES):
        query = {field: [] for field in QUERY_ARRAYS}
        query.update({
            "timestampFrom": start_ms,
            "timestampTo": now_ms,
            "pageNumber": page,
            "pageSize": page_size,
            "search_text": "",
            "skip_count": False,
        })
        envelope = session.post(path, query)
        flows = envelope.get("data") or []
        fetched += len(flows)

        for flow in flows:
            flow_id = flow.get("id")
            time_ms = flow.get("time")
            if not flow_id or time_ms is None:
                continue
            if not checkpoint.is_new(flow_id):
                continue
            pending.append((time_ms / 1000.0, flatten(flow, session.host)))
            checkpoint.mark(flow_id, time_ms)

        if not envelope.get("has_next") or not flows:
            break
    else:
        log.warning("hit page cap of %d; window may be under-collected", MAX_PAGES)

    written = hec.send(pending) if pending else 0
    checkpoint.save()
    log.info("poll: fetched=%d new=%d written=%d window=%ds",
             fetched, len(pending), written, (now_ms - start_ms) // 1000)
    return written


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        stream=sys.stdout,
    )
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    env = load_env()
    os.makedirs(STATE_DIR, exist_ok=True)

    session = UniFiSession(env["UNIFI_HOST"], env["UNIFI_USERNAME"],
                           env["UNIFI_PASSWORD"],
                           env.get("UNIFI_VERIFY_SSL", "false").lower() == "true")
    hec = HecWriter(env["HEC_URL"], env["HEC_TOKEN"], env.get("HEC_INDEX", "netfw"),
                    host=env.get("HEC_HOST", "unifi-gateway"))
    checkpoint = Checkpoint()

    site = env.get("UNIFI_SITE", "default")
    interval = int(env.get("POLL_INTERVAL_SECONDS", "120"))
    lookback = int(env.get("LOOKBACK_SECONDS", "900"))
    page_size = int(env.get("PAGE_SIZE", "1000"))

    once = "--once" in sys.argv
    log.info("starting: site=%s interval=%ds page_size=%d index=%s",
             site, interval, page_size, hec.index)

    backoff = 0
    while not _stop:
        started = time.time()
        try:
            poll_once(session, hec, checkpoint, site, page_size, lookback)
            backoff = 0
        except Exception as exc:  # keep the service alive across controller blips
            backoff = min(backoff * 2 or 30, 600)
            log.error("poll failed (%s); retrying in %ds", exc, backoff)
            # Force a fresh login next attempt in case the session is the problem.
            session.opener = None

        if once:
            break
        delay = backoff or max(1, interval - (time.time() - started))
        end = time.time() + delay
        while not _stop and time.time() < end:
            time.sleep(min(1, end - time.time()))

    log.info("stopped")


if __name__ == "__main__":
    main()
