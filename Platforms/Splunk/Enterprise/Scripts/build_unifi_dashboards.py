#!/usr/bin/env python3
"""Generate the UniFi Insights Dashboard Studio views.

The dashboards are large JSON documents. Writing them by hand invites unbalanced
braces and colour drift between panels, so they are generated instead: the
palette and the layout arithmetic live in one place here, and every panel draws
from the same tokens.

Palette is the validated dark-surface set (categorical checked with the data-viz
validator: adjacent CVD dE 8.4, normal-vision dE 19.3, all slots >= 3:1 on the
dark surface). Risk and action use the reserved status colours, never a
categorical slot, so a severity can never be mistaken for a series.

Writes to ../Configuration/unifi_insights/default/data/ui/views/.
"""

import json
import os
from xml.sax.saxutils import escape as xml_escape

# --- design tokens ---------------------------------------------------------
PLANE = "#0d0d0d"        # page background
SURFACE = "#1a1a19"      # panel surface
INK = "#ffffff"
INK_2 = "#c3c2b7"
MUTED = "#898781"

# Status palette: reserved, never reused as a series colour.
GOOD = "#0ca30c"         # allowed / low risk
WARNING = "#fab219"      # medium risk
CRITICAL = "#d03b3b"     # blocked / high risk

# Categorical, dark steps, in fixed slot order.
CAT = ["#3987e5", "#d95926", "#199e70", "#c98500",
       "#d55181", "#008300", "#9085e9", "#e66767"]

SEQ_MIN = "#cde2fb"
SEQ_MAX = "#0d366b"

# --- layout grid -----------------------------------------------------------
W = 1440
M = 20                   # side margin
GUT = 16                 # gutter
CONTENT = W - 2 * M      # 1400


def cols(n):
    """Width of one column when the content width is split n ways."""
    return (CONTENT - GUT * (n - 1)) // n


def xs(n):
    """Left edge of each of n equal columns."""
    c = cols(n)
    return [M + i * (c + GUT) for i in range(n)]


class Dash:
    def __init__(self, title, description):
        self.title = title
        self.description = description
        self.viz = {}
        self.ds = {}
        self.structure = []
        self._n = 0

    def _id(self, prefix):
        self._n += 1
        return "%s_%d" % (prefix, self._n)

    def search(self, query):
        did = self._id("ds")
        self.ds[did] = {
            "type": "ds.search",
            "options": {"query": query},
            "name": did,
        }
        return did

    def add(self, vtype, options, x, y, w, h, query=None, title=None,
            description=None):
        vid = self._id("viz")
        block = {"type": vtype, "options": options}
        if query is not None:
            block["dataSources"] = {"primary": self.search(query)}
        if title:
            block["title"] = title
        if description:
            block["description"] = description
        self.viz[vid] = block
        self.structure.append(
            {"item": vid, "type": "block",
             "position": {"x": x, "y": y, "w": w, "h": h}})
        return vid

    # -- panel helpers ------------------------------------------------------
    def header(self, text, y, h=56, size=22, color=INK, x=M, w=CONTENT):
        return self.add("splunk.markdown",
                        {"markdown": text, "fontColor": color,
                         "fontSize": size, "backgroundColor": "transparent"},
                        x, y, w, h)

    def kpi(self, title, query, x, y, w, h, color=INK, unit=None):
        opts = {
            "majorColor": color,
            "majorFontSize": 40,
            "backgroundColor": SURFACE,
            "sparklineDisplay": "off",
            "trendDisplay": "off",
            "shouldUseThousandSeparators": True,
        }
        if unit:
            opts["unit"] = unit
            opts["unitPosition"] = "after"
        return self.add("splunk.singlevalue", opts, x, y, w, h,
                        query=query, title=title)

    def render(self, height, theme="dark"):
        definition = {
            "title": self.title,
            "description": self.description,
            "visualizations": self.viz,
            "dataSources": self.ds,
            "inputs": {
                "input_time": {
                    "type": "input.timerange",
                    "options": {"token": "time", "defaultValue": "-24h@h,now"},
                    "title": "Time range",
                }
            },
            "defaults": {
                "dataSources": {
                    "ds.search": {
                        "options": {
                            "queryParameters": {
                                "earliest": "$time.earliest$",
                                "latest": "$time.latest$",
                            }
                        }
                    }
                }
            },
            "layout": {
                "type": "absolute",
                "options": {
                    "width": W,
                    "height": height,
                    "display": "auto-scale",
                    "backgroundColor": PLANE,
                },
                "structure": self.structure,
                "globalInputs": ["input_time"],
            },
        }
        body = json.dumps(definition, indent=2)
        return (
            '<dashboard version="2" theme="%s">\n'
            "  <label>%s</label>\n"
            "  <description>%s</description>\n"
            "  <definition><![CDATA[\n%s\n]]></definition>\n"
            '  <meta type="hiddenElements"><![CDATA[\n'
            '{"hideEdit":false,"hideOpenInSearch":false,"hideExport":false}\n'
            "]]></meta>\n"
            "</dashboard>\n" % (theme, xml_escape(self.title),
                                 xml_escape(self.description), body)
        )


# Common chart option blocks -------------------------------------------------
def chart_opts(colors, legend="off", stack="auto", extra=None):
    o = {
        "seriesColors": colors,
        "backgroundColor": SURFACE,
        "legendDisplay": legend,
        "showYMajorGridLines": True,
        "yAxisAbbreviation": "auto",
    }
    if stack != "auto":
        o["stackMode"] = stack
    if legend != "off":
        o["legendPlacement"] = "right"
    if extra:
        o.update(extra)
    return o


def world_map():
    """Bubble map options, matching the layer shape ES uses for splunk.map.

    splunk.choropleth.svg is not registered on this instance -- it renders
    "Missing property: svg" -- so geography is drawn as a bubble map over
    iplocation coordinates instead.
    """
    return {"layers": [{"type": "bubble"}], "backgroundColor": SURFACE}


def table_opts(count=20):
    return {
        "backgroundColor": SURFACE,
        "count": count,
        "dataOverlayMode": "none",
        "headerVisibility": "fixed",
        "rowNumbers": False,
        "wrap": False,
    }


# ---------------------------------------------------------------------------
# Dashboard 1: Flow Insights -- the Insights > Flows equivalent
# ---------------------------------------------------------------------------
def flows_dashboard():
    d = Dash("UniFi Flow Insights",
             "Every connection the gateway completed: what was allowed, what "
             "was blocked, how risky it was and where it went.")
    y = 16

    # KPI row
    c5, x5 = cols(5), xs(5)
    d.kpi("Total flows", "`unifi_flows` | stats count",
          x5[0], y, c5, 112, color=CAT[0])
    d.kpi("Blocked", "`unifi_flows` action=blocked | stats count",
          x5[1], y, c5, 112, color=CRITICAL)
    d.kpi("High risk", '`unifi_flows` risk=high | stats count',
          x5[2], y, c5, 112, color=WARNING)
    d.kpi("Countries reached",
          "`unifi_flows` dest_region=* | stats dc(dest_region)",
          x5[3], y, c5, 112, color=CAT[0])
    d.kpi("Data volume",
          "`unifi_flows` | stats sum(bytes) as b "
          "| eval v=round(b/1073741824,1) | fields v",
          x5[4], y, c5, 112, color=CAT[0], unit=" GB")
    y += 112 + GUT

    # Timeline. Series order from `by action` is alphabetical: allowed, blocked.
    d.add("splunk.area",
          chart_opts([GOOD, CRITICAL], legend="right", stack="stacked",
                     extra={"fillOpacity": 0.55, "lineWidth": 2}),
          M, y, CONTENT, 250,
          query=("`unifi_flows` "
                 "| eval a=if(action=\"allowed\",1,0), "
                 "b=if(action=\"blocked\",1,0) "
                 "| timechart minspan=5m sum(a) as Allowed, sum(b) as Blocked"),
          title="Flow volume over time",
          description="Stacked by disposition; blocked sits on top of allowed.")
    y += 250 + GUT

    d.header("## Where traffic goes", y, h=34, size=16, color=INK_2)
    y += 42

    # Geography + risk split
    geo_w = 920
    d.add("splunk.map", world_map(), M, y, geo_w, 380,
          query=("`unifi_flows` dest_zone=External | iplocation dest_ip "
                 "| search Country=* "
                 "| geostats latfield=lat longfield=lon maxzoomlevel=18 count"),
          title="Where traffic goes",
          description="Outbound flows plotted by destination location.")
    risk_x = M + geo_w + GUT
    d.add("splunk.pie",
          {"seriesColors": [CRITICAL, WARNING, GOOD],
           "backgroundColor": SURFACE,
           "showDonutHole": True,
           "legendDisplay": "bottom",
           "labelDisplay": "valuesAndPercentage",
           # Without this, any band under 1% is merged into an "Other" slice
           # and the fixed colour order no longer lines up with the bands.
           "collapseThreshold": 0,
           "showOther": False},
          risk_x, y, CONTENT - geo_w - GUT, 380,
          query=("`unifi_flows` | stats count by risk "
                 "| append [| makeresults count=3 | streamstats count as r "
                 "| eval risk=case(r==1,\"high\",r==2,\"medium\",r==3,\"low\"), "
                 "count=0 | fields risk count] "
                 "| stats sum(count) as count by risk "
                 "| eval o=case(risk=\"high\",1,risk=\"medium\",2,"
                 "risk=\"low\",3) | sort o | fields risk count"),
          title="Risk mix",
          description="UniFi's own banding: high, medium, low.")
    y += 380 + GUT

    d.header("## Top talkers", y, h=34, size=16, color=INK_2)
    y += 42

    c3, x3 = cols(3), xs(3)
    d.add("splunk.bar", chart_opts([CAT[0]]), x3[0], y, c3, 330,
          query=("`unifi_flows` src=* | stats count by src "
                 "| sort -count | head 10 | sort count"),
          title="Busiest clients")
    d.add("splunk.bar", chart_opts([CAT[2]]), x3[1], y, c3, 330,
          query=("`unifi_flows` dest_zone=External "
                 "| eval target=if(isnull(dest_domain), dest_ip, "
                 "mvindex(dest_domain,0)) "
                 "| stats count by target | sort -count | head 10 "
                 "| sort count"),
          title="Top external destinations")
    d.add("splunk.bar", chart_opts([CAT[6]]), x3[2], y, c3, 330,
          query=("`unifi_flows` app=* | stats sum(bytes) as bytes by app "
                 "| sort -bytes | head 10 | sort bytes"),
          title="Services by volume")
    y += 330 + GUT

    d.header("## Blocked traffic", y, h=34, size=16, color=INK_2)
    y += 42

    d.add("splunk.table", table_opts(50), M, y, CONTENT, 300,
          query=("`unifi_flows` action=blocked "
                 "| eval when=strftime(_time, \"%m-%d %H:%M:%S\"), "
                 "peer=if(direction=\"incoming\", src_ip, dest_ip), "
                 "where=coalesce(if(direction=\"incoming\", src_country, "
                 "dest_country), \"-\") "
                 "| table when direction peer where dest_port transport "
                 "rule risk src_zone dest_zone "
                 "| sort - when | head 200"),
          title="Blocked flows",
          description="The peer column is the outside address for an inbound "
                      "block and the target for an outbound one.")
    y += 300 + GUT

    c2, x2 = cols(2), xs(2)
    d.add("splunk.table", table_opts(15), x2[0], y, c2, 320,
          query=("`unifi_flows` | stats count by src_zone dest_zone "
                 "| sort -count | head 15"),
          title="Zone-to-zone matrix")
    d.add("splunk.table", table_opts(15), x2[1], y, c2, 320,
          query=("`unifi_flows` dest_domain=* "
                 "| stats count sum(bytes) as bytes by dest_domain "
                 "| sort -count | head 15 | `fmt_bytes(bytes)`"),
          title="Top destination domains")
    y += 320 + M

    return d.render(y)


# ---------------------------------------------------------------------------
# Dashboard 2: Threat Center
# ---------------------------------------------------------------------------
def threats_dashboard():
    d = Dash("UniFi Threat Center",
             "Intrusion detections, firewall blocks and the policies that "
             "produced them.")
    y = 16

    c5, x5 = cols(5), xs(5)
    d.kpi("Threats detected", "`unifi_threats` | stats count",
          x5[0], y, c5, 112, color=WARNING)
    d.kpi("Threats blocked", "`unifi_threats` action=blocked | stats count",
          x5[1], y, c5, 112, color=GOOD)
    d.kpi("Passed through",
          "`unifi_threats` action=allowed | stats count",
          x5[2], y, c5, 112, color=CRITICAL)
    d.kpi("Unique signatures", "`unifi_threats` | stats dc(signature)",
          x5[3], y, c5, 112, color=CAT[0])
    d.kpi("Firewall blocks",
          "`unifi_events` sc4s_class=203 | stats count",
          x5[4], y, c5, 112, color=CAT[0])
    y += 112 + GUT

    d.add("splunk.column",
          chart_opts([CRITICAL, WARNING, GOOD], legend="right",
                     stack="stacked"),
          M, y, CONTENT, 250,
          query=("`unifi_threats` "
                 "| eval h=if(severity=\"high\",1,0), "
                 "m=if(severity=\"medium\",1,0), l=if(severity=\"low\",1,0) "
                 "| timechart minspan=30m sum(h) as High, sum(m) as Medium, "
                 "sum(l) as Low"),
          title="Detections over time",
          description="Bands are UniFi's risk rating for the signature.")
    y += 250 + GUT

    d.header("## What is being detected", y, h=34, size=16, color=INK_2)
    y += 42

    d.add("splunk.table", table_opts(20), M, y, 860, 360,
          query=("`unifi_threats` signature=* "
                 "| stats count, values(severity) as risk, "
                 "dc(src) as sources, latest(_time) as last by signature "
                 "| eval last=strftime(last, \"%m-%d %H:%M\") "
                 "| sort -count | head 20"),
          title="Signatures by frequency")
    d.add("splunk.bar", chart_opts([CAT[1]]),
          M + 860 + GUT, y, CONTENT - 860 - GUT, 360,
          query=("`unifi_threats` rule=* | stats count by rule "
                 "| sort -count | head 10 | sort count"),
          title="Threat categories")
    y += 360 + GUT

    d.header("## Where it comes from", y, h=34, size=16, color=INK_2)
    y += 42

    c2, x2 = cols(2), xs(2)
    d.add("splunk.map", world_map(), x2[0], y, c2, 360,
          query=("`unifi_flows` action=blocked direction=incoming "
                 "| iplocation src_ip | search Country=* "
                 "| geostats latfield=lat longfield=lon maxzoomlevel=18 count"),
          title="Where blocked traffic comes from")
    d.add("splunk.bar", chart_opts([CRITICAL]), x2[1], y, c2, 360,
          query=("`unifi_flows` action=blocked rule=* "
                 "| stats count by rule | sort -count | head 10 "
                 "| sort count"),
          title="Blocking policies")
    y += 360 + GUT

    d.add("splunk.table", table_opts(50), M, y, CONTENT, 320,
          query=("`unifi_threats` "
                 "| eval when=strftime(_time, \"%m-%d %H:%M:%S\") "
                 "| rename cef_name as event "
                 "| table when event signature rule severity action "
                 "src dest dest_port transport src_zone dest_zone "
                 "| sort - when | head 200"),
          title="Recent detections")
    y += 320 + M

    return d.render(y)


def clients_dashboard():
    d = Dash("UniFi Client & Network Activity",
             "Who is on the network, what they are moving, and what changed "
             "on the controller.")
    y = 16

    c5, x5 = cols(5), xs(5)
    d.kpi("Active clients", "`unifi_flows` src_mac=* | stats dc(src_mac)",
          x5[0], y, c5, 112, color=CAT[0])
    d.kpi("Connects", "eventtype=unifi_cef_session_start | stats count",
          x5[1], y, c5, 112, color=GOOD)
    d.kpi("Disconnects", "eventtype=unifi_cef_session_end | stats count",
          x5[2], y, c5, 112, color=CAT[3])
    d.kpi("Config changes",
          "eventtype=unifi_cef_config_change | stats count",
          x5[3], y, c5, 112, color=WARNING)
    d.kpi("Admin logins", "eventtype=unifi_cef_admin_auth | stats count",
          x5[4], y, c5, 112, color=CAT[0])
    y += 112 + GUT

    d.add("splunk.line",
          chart_opts([GOOD, CAT[3]], legend="right",
                     extra={"lineWidth": 2, "markerDisplay": "outlined"}),
          M, y, CONTENT, 240,
          query=("`unifi_events` (eventtype=unifi_cef_session_start OR "
                 "eventtype=unifi_cef_session_end) "
                 "| eval c=if(sc4s_class IN (400,403,520),1,0), "
                 "d=if(sc4s_class IN (401,404,521),1,0) "
                 "| timechart minspan=15m sum(c) as Connects, "
                 "sum(d) as Disconnects"),
          title="Client sessions")
    y += 240 + GUT

    d.header("## Traffic by client and network", y, h=34, size=16,
             color=INK_2)
    y += 42

    c3, x3 = cols(3), xs(3)
    d.add("splunk.bar", chart_opts([CAT[0]]), x3[0], y, c3, 330,
          query=("`unifi_flows` src=* | stats sum(bytes) as bytes by src "
                 "| sort -bytes | head 10 | sort bytes"),
          title="Clients by volume")
    d.add("splunk.bar", chart_opts([CAT[2]]), x3[1], y, c3, 330,
          query=("`unifi_flows` src_network=* "
                 "| stats sum(bytes) as bytes by src_network "
                 "| sort -bytes | head 10 | sort bytes"),
          title="Networks by volume")
    d.add("splunk.pie",
          {"seriesColors": CAT, "backgroundColor": SURFACE,
           "showDonutHole": True, "legendDisplay": "bottom",
           "labelDisplay": "valuesAndPercentage"},
          x3[2], y, c3, 330,
          query=("`unifi_events` wifi_name=* | stats count by wifi_name "
                 "| sort -count | head 6"),
          title="WiFi networks")
    y += 330 + GUT

    d.header("## Controller activity", y, h=34, size=16, color=INK_2)
    y += 42

    c2, x2 = cols(2), xs(2)
    d.add("splunk.table", table_opts(25), x2[0], y, c2, 340,
          query=("`unifi_events` (eventtype=unifi_cef_config_change OR "
                 "eventtype=unifi_cef_admin_auth) "
                 "| eval when=strftime(_time, \"%m-%d %H:%M:%S\") "
                 "| rename cef_name as event, UNIFIaccessMethod as method, "
                 "UNIFIsettingsSection as section "
                 "| table when event user method section src_ip "
                 "| sort - when | head 200"),
          title="Admin and configuration activity")
    d.add("splunk.table", table_opts(25), x2[1], y, c2, 340,
          query=("`unifi_events` (eventtype=unifi_cef_session_start OR "
                 "eventtype=unifi_cef_session_end) "
                 "| eval when=strftime(_time, \"%m-%d %H:%M:%S\"), "
                 "client=coalesce(client_alias, UNIFIclientHostname, "
                 "UNIFIclientIp) "
                 "| rename cef_name as event, wifi_name as wifi, "
                 "UNIFIclientIp as client_ip "
                 "| table when event client wifi client_ip "
                 "| sort - when | head 200"),
          title="Client connect and disconnect")
    y += 340 + GUT

    d.header("## Network health and camera detections", y, h=34, size=16,
             color=INK_2)
    y += 42

    # Health events are the part of UniFi's own Insights that neither the flow
    # records nor the threat events carry: an outage, a flapping uplink, a
    # duplicate address. They are low volume, so a count by name is the whole
    # picture rather than a sample of it.
    d.add("splunk.bar", chart_opts([CAT[3]]), x2[0], y, c2, 300,
          query=("`unifi_events` eventtype=unifi_cef_device_alert "
                 "| stats count by cef_name | sort -count | head 12 "
                 "| sort count | rename cef_name as event"),
          title="Network and device health events")
    d.add("splunk.bar", chart_opts([CAT[6]]), x2[1], y, c2, 300,
          query=("`unifi_events` eventtype=unifi_protect_detection "
                 "| stats count by cef_name | sort -count | head 12 "
                 "| sort count | rename cef_name as detection"),
          title="Camera detections by type")
    y += 300 + GUT

    d.add("splunk.table", table_opts(25), M, y, CONTENT, 320,
          query=("`unifi_events` (eventtype=unifi_cef_device_alert OR "
                 "eventtype=unifi_protect_detection) "
                 "| eval when=strftime(_time, \"%m-%d %H:%M:%S\"), "
                 "device=coalesce(dvc_name, UNIFIdeviceName, dvc) "
                 "| rename cef_name as event, cef_product as product, "
                 "UNIFIcategory as category "
                 "| table when product severity event category device "
                 "| sort - when | head 200"),
          title="Recent health and detection events")
    y += 320 + M

    return d.render(y)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.normpath(os.path.join(
        here, "..", "Configuration", "unifi_insights",
        "default", "data", "ui", "views"))
    os.makedirs(out, exist_ok=True)
    for name, builder in (
            ("unifi_flow_insights", flows_dashboard),
            ("unifi_threat_center", threats_dashboard),
            ("unifi_client_activity", clients_dashboard)):
        path = os.path.join(out, name + ".xml")
        xml = builder()
        with open(path, "w") as fh:
            fh.write(xml)
        print("wrote %-28s %6d bytes" % (name + ".xml", len(xml)))


if __name__ == "__main__":
    main()
