#!/usr/bin/env python3
"""incident-response: the six-step sequence I use for a service-impacting or
security incident (restyle of the 2026-07-20 diagram, content kept). Facts:
Guides/Security-Incident-Response.md (steps, prerequisites, the report's
sections, the containment caveat; thirteen reports counted 2026-09-25),
Security/README.md."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from diagram import Diagram

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "incident-response.svg")
d = Diagram("incident-response", "Security incident response: six steps to close",
            "Scope and timeline before any change, contain the live path, correct and rotate, verify that the old path fails, then record residual risk and close",
            state="State as of 2026-09-25",
            source="Guides/Security-Incident-Response.md, Security/README.md",
            width=1640, gap=120, card_w=240)

d.group("understand", "Understand, before changing state", badge="steps 1 and 2", family="Internal")
d.card("understand", "s1", "Scope and impact", sub1="affected assets, start time, symptom, user impact", sub2="confirmed facts kept apart from hypotheses", logo="glyph:1")
d.card("understand", "s2", "Preserve the timeline", sub1="provider, service, DNS, firewall and auth events", sub2="plus my own actions, in order, time zone kept", logo="glyph:2")
d.group("need", "What you need", family="External", notes=[
    (None, "the first observed time, the affected service, the symptom and the reporter"),
    (None, "provider dashboards, service logs, DNS, firewall and authentication records"),
    (None, "every system that can reach or trust the affected component"),
    (None, "a copy of each configuration file before editing it; there are no snapshots"),
    (None, "or backups, so a rebuild from the baseline is the fallback beyond that")])

d.group("act", "Contain, then correct", badge="steps 3 and 4", family="Dmz")
d.card("act", "s3", "Contain the active path", sub1="disable the exposed route, account, tunnel or key", sub2="the narrowest action that stops it and keeps the evidence", logo="glyph:3")
d.card("act", "s4", "Correct the configuration", sub1="rotate access, remove legacy entries, repair the target", sub2="update each dependent service", logo="glyph:4")
d.group("worse", "If containment increases impact", family="Untrusted", notes=[
    (None, "restore the last known-good service route while keeping the exposed"),
    (None, "identity disabled; split availability recovery from the security"),
    (None, "correction when one rollback cannot safely restore both")])

d.group("prove", "Prove it, then close", badge="steps 5 and 6", family="Observability")
d.card("prove", "s5", "Verify service and security state", sub1="user path, backend, auth, DNS, provider status", sub2="the old value or route must fail after the new one works", logo="glyph:5")
d.card("prove", "s6", "Record residual risk and close", sub1="each follow-up with the condition that closes it", sub2="close only when stable, path disabled, results recorded", logo="glyph:6")
d.group("report", "The report, under Security/Incidents/<Service>/", family="External", notes=[
    (None, "metadata (date, service, closure status), summary, impact, affected assets,"),
    (None, "symptoms with exact error text, timeline, findings and the root cause or"),
    (None, "the standing hypothesis, corrective action with its validation, residual"),
    (None, "risk and follow-ups; kept apart from the platform's records, cross-linked."),
    (None, "Thirteen reports in eleven service folders on 2026-09-25.")])

d.row("understand", "need")
d.row("act", "worse")
d.row("prove", "report")

def align(src, dst):
    d._layout(); s, t = d.items[src], d.items[dst]
    return (t.x + t.w / 2) - (s.x + s.w / 2)

d.edge("s1", "s2", "facts first", color="blue")
d.edge("s3", "s4", "path cut", color="orange")
d.edge("s5", "s6", "old path fails", color="green")
d.edge("understand", "act", "facts and timeline recorded; nothing changed yet", color="grey", t_off=align("understand", "act"))
d.edge("act", "prove", "the new value works and the exposed path is closed", color="grey", t_off=align("act", "prove"))

d.legend_family("Internal", "understand"); d.legend_family("Dmz", "act"); d.legend_family("Observability", "prove and close")
d.legend_family("Untrusted", "when containment makes it worse"); d.legend_family("External", "inputs and the output")
d.legend_edge("next step", "solid", "blue"); d.legend_edge("guarded transition", "solid", "orange"); d.legend_edge("gate to the next row", "solid", "grey")
d.footnote("A corrective action counts only with an observed result, never a submitted command. Routine troubleshooting is not an incident and stays with the platform that owns it; when a problem becomes one, the report and the platform record link each other.")
d.footnote("This sequence does not replace a provider's own procedure. A disclosure that touches billing, legal notice or third-party user data needs the external response path as well as the technical record.")
d.render(OUT, png=os.environ.get("PNG") == "1", readme_width=int(os.environ.get("README_W", "0")) or None)
