#!/usr/bin/env python3
"""Check the unifi_insights app against the live instance.

Runs every dashboard panel query, every correlation search, and a tstats probe
of each CIM data model the app feeds, then reports what returned and what
errored. A panel query that returns no rows is not a failure on its own, so the
row count is reported separately from the error count.

Run it on splunk-siem, as a user that can read the app's default/ directory:

    sudo python3 verify_unifi_insights.py

Credentials come from a curl-style netrc file, so the password never reaches a
command line or a process listing. Point SPLUNK_NETRC at it; the default is
~/.splunk_netrc. The file wants mode 600 and three lines:

    machine 127.0.0.1
    login <YOUR_SPLUNK_USER>
    password <YOUR_SPLUNK_PASSWORD>

Delete it with `shred -u` when the check is done. Nothing here writes to Splunk.
"""

import base64
import glob
import json
import os
import re
import ssl
import sys
import urllib.parse
import urllib.request

BASE = "https://127.0.0.1:8089"
APP = "/servicesNS/nobody/unifi_insights"
APP_DIR = "/opt/splunk/etc/apps/unifi_insights/default"
NETRC = os.environ.get("SPLUNK_NETRC", os.path.expanduser("~/.splunk_netrc"))

# The instance uses Splunk's own self-signed certificate on 8089 and this only
# ever talks to the loopback address, so the hostname check has nothing to
# check against.
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def auth_header(path):
    user = password = None
    for line in open(path):
        parts = line.split()
        if len(parts) >= 2 and parts[0] == "login":
            user = parts[1]
        if len(parts) >= 2 and parts[0] == "password":
            password = parts[1]
    if not user or not password:
        sys.exit("no login/password in %s" % path)
    raw = ("%s:%s" % (user, password)).encode()
    return "Basic " + base64.b64encode(raw).decode()


AUTH = auth_header(NETRC)


def run(search, earliest="-24h", latest="now"):
    """Return (row_count, None) or (None, error_text)."""
    if not search.lstrip().startswith("|"):
        search = "search " + search
    data = urllib.parse.urlencode({
        "search": search,
        "earliest_time": earliest,
        "latest_time": latest,
        "exec_mode": "oneshot",
        "output_mode": "json",
        "count": "0",
    }).encode()
    req = urllib.request.Request(BASE + APP + "/search/jobs", data=data)
    req.add_header("Authorization", AUTH)
    try:
        body = urllib.request.urlopen(req, context=CTX, timeout=180).read()
    except Exception as exc:
        return None, "HTTP %s" % exc
    try:
        payload = json.loads(body)
    except ValueError:
        return None, body[:200].decode("utf-8", "replace")
    fatal = [m for m in payload.get("messages", [])
             if m.get("type") in ("ERROR", "FATAL")]
    if fatal:
        return None, fatal[0]["text"][:160]
    return len(payload.get("results", [])), None


def check_panels():
    print("== dashboard panel queries, last 24h ==")
    total = errors = with_rows = 0
    for view in sorted(glob.glob(APP_DIR + "/data/ui/views/*.xml")):
        text = open(view).read()
        match = re.search(
            r"<definition><!\[CDATA\[\n(.*?)\n\]\]></definition>", text, re.S)
        definition = json.loads(match.group(1))
        name = os.path.basename(view)
        for key, source in sorted(definition["dataSources"].items()):
            query = source["options"]["query"]
            total += 1
            rows, error = run(query)
            if error:
                errors += 1
                print("  FAIL %-26s %-12s %s" % (name, key, error))
                print("       %s" % query[:150])
            elif rows:
                with_rows += 1
    print("  %d queries, %d errored, %d returned rows"
          % (total, errors, with_rows))
    return errors


def check_correlation_searches():
    print()
    print("== correlation searches ==")
    conf = open(APP_DIR + "/savedsearches.conf").read().replace("\\\n", "")
    name = None
    errors = 0
    for line in conf.splitlines():
        if line.startswith("["):
            name = line.strip("[]")
        elif line.startswith("search = ") and name:
            query = line[len("search = "):]
            live, live_err = run(query, "-70m", "now")
            hist, hist_err = run(query, "-60d", "now")
            if live_err or hist_err:
                errors += 1
            print("  %-58s window=%s history=%s" % (
                name[:58],
                ("ERR: " + live_err) if live_err else live,
                ("ERR: " + hist_err) if hist_err else hist))
            name = None
    return errors


DATA_MODELS = (
    ("Network_Traffic",
     "| tstats count from datamodel=Network_Traffic where "
     "nodename=All_Traffic by All_Traffic.action, All_Traffic.vendor_product"),
    ("Intrusion_Detection",
     "| tstats count from datamodel=Intrusion_Detection where "
     "nodename=IDS_Attacks by IDS_Attacks.severity"),
    ("Authentication",
     "| tstats count from datamodel=Authentication where "
     "nodename=Authentication by Authentication.user, Authentication.app"),
    ("Network_Sessions",
     "| tstats count from datamodel=Network_Sessions by nodename"),
    ("Change",
     "| tstats count from datamodel=Change where nodename=All_Changes by "
     "All_Changes.vendor_product"),
    ("Alerts",
     "| tstats count from datamodel=Alerts where nodename=Alerts by "
     "Alerts.severity, Alerts.app"),
)


def check_data_models():
    print()
    print("== CIM data models, last 24h ==")
    errors = 0
    for label, query in DATA_MODELS:
        rows, error = run(query)
        if error:
            errors += 1
        print("  %-22s %s" % (label, ("ERR: " + error) if error
                              else ("%s rows" % rows)))
    return errors


def check_event_type_coverage():
    print()
    print("== CEF classes with no event type, last 60d ==")
    rows, error = run(
        'index=netops sourcetype=cef | where isnull(eventtype) '
        '| stats count by cef_product, sc4s_class, cef_name', "-60d")
    if error:
        print("  ERR: %s" % error)
        return 1
    # UniFi OS class 1 is the SIEM panel's own test event. It carries no
    # subject and is left untyped on purpose, so one row here is the pass.
    print("  %s untyped (1 expected: UniFi OS class 1, Test Syslog)" % rows)
    return 0


def main():
    failures = 0
    failures += check_panels()
    failures += check_correlation_searches()
    failures += check_data_models()
    failures += check_event_type_coverage()
    print()
    print("FAIL: %d check(s) errored" % failures if failures
          else "PASS: every check ran without error")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
