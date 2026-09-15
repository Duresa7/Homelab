#!/usr/bin/env python3
"""Panel and layout primitives for the Homelab Grafana dashboards.

Everything the generator draws goes through this module, so the whole set shares
one look: the same line weight, the same legend shape, the same threshold
colours, the same row banding. Editing a constant here changes every dashboard
at once, which is the reason the dashboards are generated rather than hand-kept.

Three conventions are load-bearing:

- A panel carries its number and nothing else. No markdown bands under row
  headers, no sparklines inside stat tiles, no table legends under graphs, and
  no description unless the value is computed in a way the title cannot say.
- Colour is either state or resource. A stat tile, table cell or bar gauge is
  coloured by its thresholds, so green, amber and red keep meaning something. A
  single-series graph wears the tint of its resource from `TINT`, so CPU is the
  same colour on every dashboard; an informational tile wears the neutral tint.
  Multi-series graphs use `palette-classic-by-name`, which hashes the series
  name, so a host keeps its colour when a filter changes how many series are on
  screen.
- Panels are placed by `Grid`, never by hand-written gridPos. Hand-placed panels
  drift the moment a panel's height changes, and Grafana silently reflows them
  into an order nobody chose.
"""
from __future__ import annotations

import copy

DS = {"type": "prometheus", "uid": "bfgnkdi47u5tsa"}

# ---------------------------------------------------------------- house style

# 2px lines, no point markers. A single series gets a soft gradient under the
# line (see timeseries()); overlapping series stay unfilled so eight of them
# remain legible. Areas opt in explicitly via `stack=`.
TS_CUSTOM = {
    "drawStyle": "line",
    "lineInterpolation": "linear",
    "lineWidth": 2,
    "fillOpacity": 0,
    "gradientMode": "none",
    "showPoints": "never",
    "pointSize": 5,
    "spanNulls": False,
    "insertNulls": False,
    "axisBorderShow": False,
    "axisCenteredZero": False,
    "axisColorMode": "text",
    "axisLabel": "",
    "axisPlacement": "auto",
    "barAlignment": 0,
    "scaleDistribution": {"type": "linear"},
    "stacking": {"group": "A", "mode": "none"},
    "thresholdsStyle": {"mode": "off"},
    "hideFrom": {"legend": False, "tooltip": False, "viz": False},
}

LEGEND_LIST = {
    "showLegend": True,
    "displayMode": "list",
    "placement": "bottom",
    "calcs": [],
}
LEGEND_OFF = {"showLegend": False, "displayMode": "list", "placement": "bottom", "calcs": []}

TOOLTIP_MULTI = {"mode": "multi", "sort": "desc"}
TOOLTIP_SINGLE = {"mode": "single", "sort": "none"}

BY_NAME = {"mode": "palette-classic-by-name"}

# One hue per resource. A single-series graph about CPU is this salmon on every
# dashboard, memory is always this blue, and a count that judges nothing is the
# neutral lavender. None of the six is a threshold colour, so a tinted line is
# never mistaken for a state.
TINT = {
    "compute": "#F0776C",
    "memory":  "#7EB6FF",
    "storage": "#D48CF0",
    "network": "#5FD0C8",
    "power":   "#F5D66B",
    "neutral": "#AFA6F5",
}


def fixed(color: str) -> dict:
    return {"mode": "fixed", "fixedColor": color}


def thresholds(*steps, mode: str = "absolute") -> dict:
    """thresholds(('green', None), ('yellow', 80), ('red', 90))."""
    return {
        "mode": mode,
        "steps": [{"color": c, "value": v} for c, v in steps],
    }


GREEN_ONLY = thresholds(("green", None))
TEXT_ONLY = thresholds(("text", None))
# A stat tile that reports a fact rather than judging one: uptime, cores, RAM.
INFO = thresholds((TINT["neutral"], None))


def out_of(n: int) -> str:
    """A unit that renders `5 / 5`: the count, then the denominator in smaller type.

    No leading space. Grafana maps `suffix:X` to toFixedUnit(X, false), which
    returns `{ text, suffix: " " + unit }` and so supplies the space itself; a
    space here would render a double space."""
    return "suffix:/ %d" % n

# Shared operational thresholds, so "80% is amber" means the same thing on every
# dashboard rather than being re-invented per panel.
PCT_USED = thresholds(("green", None), ("yellow", 80), ("orange", 90), ("red", 95))
PCT_LOAD = thresholds(("green", None), ("yellow", 70), ("orange", 85), ("red", 95))
LOAD_PER_CORE = thresholds(("green", None), ("yellow", 1), ("orange", 2), ("red", 4))
TEMP_F = thresholds(("blue", None), ("green", 100), ("yellow", 158), ("orange", 176), ("red", 194))
BAD_ABOVE_ZERO = thresholds(("green", None), ("red", 1))
GOOD_ABOVE_ZERO = thresholds(("red", None), ("green", 1))
CERT_DAYS = thresholds(("red", None), ("orange", 14), ("yellow", 30), ("green", 60))

# Value mappings used often enough to be worth naming.
MAP_UP_DOWN = [
    {"type": "value", "options": {"0": {"text": "DOWN", "color": "red", "index": 0},
                                  "1": {"text": "UP", "color": "green", "index": 1}}}
]
MAP_OK_FAIL = [
    {"type": "value", "options": {"0": {"text": "FAILED", "color": "red", "index": 0},
                                  "1": {"text": "OK", "color": "green", "index": 1}}}
]
MAP_YES_NO = [
    {"type": "value", "options": {"0": {"text": "no", "color": "text", "index": 0},
                                  "1": {"text": "yes", "color": "text", "index": 1}}}
]


def mapping(pairs: dict, default: tuple | None = None) -> list:
    """mapping({0: ('DOWN', 'red'), 1: ('UP', 'green')})."""
    options = {str(k): {"text": t, "color": c, "index": i}
               for i, (k, (t, c)) in enumerate(pairs.items())}
    out = [{"type": "value", "options": options}]
    if default:
        out.append({"type": "special", "options": {"match": "null",
                                                   "result": {"text": default[0], "color": default[1], "index": 99}}})
    return out


# ------------------------------------------------------------------- targets

def q(expr: str, legend: str = "", ref: str = "A", instant: bool = False,
      fmt: str | None = None, interval: str | None = None, hide: bool = False) -> dict:
    t = {"refId": ref, "expr": expr, "datasource": DS}
    if legend:
        t["legendFormat"] = legend
    if instant:
        t["instant"] = True
        t["range"] = False
    if fmt:
        t["format"] = fmt
    if interval:
        t["interval"] = interval
    if hide:
        t["hide"] = True
    return t


def tq(expr: str, ref: str = "A") -> dict:
    """An instant query shaped for a table panel."""
    return q(expr, ref=ref, instant=True, fmt="table")


# --------------------------------------------------------------------- panels

def _base(kind: str, title: str, w: int, h: int, desc: str = "") -> dict:
    p = {"type": kind, "title": title, "datasource": DS,
         "gridPos": {"h": h, "w": w, "x": 0, "y": 0}}
    if desc:
        p["description"] = desc
    return p


def timeseries(title, targets, *, w=12, h=8, unit="short", desc="", legend=None,
               tooltip=None, thr=None, color=None, tint=None, minv=None, maxv=None,
               decimals=None, stack=False, fill=None, width=None, overrides=None,
               points=False, min_zero=True, log=False, thr_style=None) -> dict:
    """`tint` names a TINT key and fixes the line colour. It is the default for a
    single query, since one line has no identity to distinguish; a graph with
    several queries colours by series name unless `color` says otherwise."""
    p = _base("timeseries", title, w, h, desc)
    custom = copy.deepcopy(TS_CUSTOM)
    # One query can still draw many lines: `topk(5, ...)` with a `{{host}}`
    # legend is five series. Only a query with a fixed legend is one line.
    single = (len(targets) == 1 and not stack
              and "{{" not in targets[0].get("legendFormat", ""))
    if stack:
        custom["stacking"] = {"group": "A", "mode": "normal"}
        custom["fillOpacity"] = 22 if fill is None else fill
        custom["lineWidth"] = 1
    elif single and fill is None:
        custom["fillOpacity"] = 14
        custom["gradientMode"] = "opacity"
    if fill is not None:
        custom["fillOpacity"] = fill
    if width is not None:
        custom["lineWidth"] = width
    if points:
        custom["showPoints"] = "auto"
    if log:
        custom["scaleDistribution"] = {"type": "log", "log": 10}
    if thr_style:
        custom["thresholdsStyle"] = {"mode": thr_style}
    if color is None:
        if tint:
            color = fixed(TINT[tint])
        elif single:
            color = fixed(TINT["neutral"])
        else:
            color = BY_NAME
    defaults = {
        "custom": custom,
        "unit": unit,
        "color": color,
        "thresholds": thr or TEXT_ONLY,
        "mappings": [],
    }
    if minv is not None or min_zero:
        defaults["min"] = 0 if minv is None else minv
    if maxv is not None:
        defaults["max"] = maxv
    if decimals is not None:
        defaults["decimals"] = decimals
    p["fieldConfig"] = {"defaults": defaults, "overrides": overrides or []}
    p["options"] = {"legend": legend or LEGEND_LIST,
                    "tooltip": tooltip or TOOLTIP_MULTI}
    p["targets"] = targets
    return p


def stat(title, targets, *, w=6, h=5, unit="short", desc="", thr=None, mappings=None,
         color_mode="value", graph="none", text_mode="auto", decimals=None,
         no_value="no data", calc="lastNotNull", overrides=None, orientation="auto",
         maxv=None, minv=None, links=None) -> dict:
    """One large centred number, coloured by its thresholds. A tile with no
    thresholds of its own is a fact, not a judgement, and wears the neutral tint."""
    p = _base("stat", title, w, h, desc)
    defaults = {
        "unit": unit,
        "mappings": mappings or [],
        "thresholds": thr or INFO,
        "color": {"mode": "thresholds"},
        "noValue": no_value,
    }
    if decimals is not None:
        defaults["decimals"] = decimals
    if maxv is not None:
        defaults["max"] = maxv
    if minv is not None:
        defaults["min"] = minv
    if links:
        defaults["links"] = links
    p["fieldConfig"] = {"defaults": defaults, "overrides": overrides or []}
    p["options"] = {
        "reduceOptions": {"calcs": [calc], "fields": "", "values": False},
        "colorMode": color_mode,
        "graphMode": graph,
        "justifyMode": "center",
        "textMode": text_mode,
        "orientation": orientation,
        "wideLayout": True,
        "showPercentChange": False,
        "percentChangeColorMode": "standard",
    }
    p["targets"] = targets
    return p


def bargauge(title, targets, *, w=12, h=8, unit="percent", desc="", thr=None,
             minv=0, maxv=100, decimals=None, display="basic", orientation="horizontal",
             calc="lastNotNull", no_value="no data", mappings=None, overrides=None) -> dict:
    p = _base("bargauge", title, w, h, desc)
    defaults = {
        "unit": unit,
        "thresholds": thr or PCT_USED,
        "color": {"mode": "thresholds"},
        "mappings": mappings or [],
        "noValue": no_value,
    }
    if minv is not None:
        defaults["min"] = minv
    if maxv is not None:
        defaults["max"] = maxv
    if decimals is not None:
        defaults["decimals"] = decimals
    p["fieldConfig"] = {"defaults": defaults, "overrides": overrides or []}
    p["options"] = {
        "reduceOptions": {"calcs": [calc], "fields": "", "values": False},
        "displayMode": display,
        "orientation": orientation,
        "showUnfilled": True,
        "valueMode": "text",
        "namePlacement": "auto",
        "sizing": "auto",
        "minVizWidth": 8,
        "minVizHeight": 16,
        "maxVizHeight": 300,
    }
    p["targets"] = targets
    return p


def gauge(title, targets, *, w=6, h=6, unit="percent", desc="", thr=None,
          minv=0, maxv=100, decimals=None, calc="lastNotNull", no_value="no data") -> dict:
    p = _base("gauge", title, w, h, desc)
    p["fieldConfig"] = {"defaults": {
        "unit": unit, "min": minv, "max": maxv,
        "thresholds": thr or PCT_USED,
        "color": {"mode": "thresholds"},
        "mappings": [], "noValue": no_value,
        **({"decimals": decimals} if decimals is not None else {}),
    }, "overrides": []}
    p["options"] = {
        "reduceOptions": {"calcs": [calc], "fields": "", "values": False},
        "showThresholdLabels": False,
        "showThresholdMarkers": True,
        "minVizWidth": 75, "minVizHeight": 75, "sizing": "auto",
    }
    p["targets"] = targets
    return p


def table(title, targets, *, w=24, h=10, desc="", transformations=None,
          overrides=None, unit="short", thr=None, sort=None, no_value="no data",
          footer=False, decimals=None, mappings=None, filterable=True) -> dict:
    p = _base("table", title, w, h, desc)
    defaults = {
        "unit": unit,
        "custom": {
            "align": "auto",
            "cellOptions": {"type": "auto"},
            "inspect": False,
            "filterable": filterable,
        },
        "thresholds": thr or TEXT_ONLY,
        "color": {"mode": "thresholds"},
        "mappings": mappings or [],
        "noValue": no_value,
    }
    if decimals is not None:
        defaults["decimals"] = decimals
    p["fieldConfig"] = {"defaults": defaults, "overrides": overrides or []}
    p["options"] = {
        "showHeader": True,
        "cellHeight": "sm",
        "footer": {"show": footer, "reducer": ["sum"], "countRows": False, "fields": ""},
        "sortBy": [{"displayName": sort[0], "desc": sort[1]}] if sort else [],
    }
    p["targets"] = targets
    p["transformations"] = transformations or []
    return p


def state_timeline(title, targets, *, w=24, h=9, desc="", mappings=None, thr=None,
                   unit="short", legend=None, row_height=0.9, show_value="never",
                   overrides=None, merge=True) -> dict:
    p = _base("state-timeline", title, w, h, desc)
    p["fieldConfig"] = {"defaults": {
        "unit": unit,
        "custom": {
            "lineWidth": 0,
            "fillOpacity": 80,
            "spanNulls": False,
            "insertNulls": False,
            "hideFrom": {"legend": False, "tooltip": False, "viz": False},
        },
        "mappings": mappings or [],
        "thresholds": thr or TEXT_ONLY,
        "color": {"mode": "thresholds"},
        "noValue": "no data",
    }, "overrides": overrides or []}
    p["options"] = {
        "mergeValues": merge,
        "showValue": show_value,
        "alignValue": "center",
        "rowHeight": row_height,
        "perPage": 20,
        "legend": legend or LEGEND_LIST,
        "tooltip": {"mode": "single", "sort": "none"},
    }
    p["targets"] = targets
    return p


def heatmap(title, targets, *, w=12, h=9, desc="", unit="s", scheme="Turbo") -> dict:
    p = _base("heatmap", title, w, h, desc)
    p["options"] = {
        "calculate": True,
        "calculation": {"xBuckets": {"mode": "size"}, "yBuckets": {"mode": "count"}},
        "cellGap": 1,
        "cellValues": {},
        "color": {"mode": "scheme", "scheme": scheme, "steps": 64, "reverse": False,
                  "exponent": 0.5, "fill": "dark-orange", "scale": "exponential"},
        "exemplars": {"color": "rgba(255,0,255,0.7)"},
        "filterValues": {"le": 1e-9},
        "legend": {"show": True},
        "rowsFrame": {"layout": "auto"},
        "showValue": "never",
        "tooltip": {"mode": "single", "showColorScale": False, "yHistogram": False},
        "yAxis": {"axisPlacement": "left", "reverse": False, "unit": unit},
    }
    p["fieldConfig"] = {"defaults": {"custom": {"hideFrom": {"legend": False, "tooltip": False, "viz": False},
                                                "scaleDistribution": {"type": "linear"}}},
                        "overrides": []}
    p["targets"] = targets
    return p


# --------------------------------------------------------------- field config

def override(matcher_id: str, matcher_opts, props: list) -> dict:
    return {"matcher": {"id": matcher_id, "options": matcher_opts},
            "properties": [{"id": k, "value": v} for k, v in props]}


def by_name(name: str, props: list) -> dict:
    return override("byName", name, props)


def by_regex(pattern: str, props: list) -> dict:
    return override("byRegexp", pattern, props)


def cell_gauge(minv=0, maxv=100) -> list:
    """Table cell drawn as a thin bar: the right form for comparing magnitude
    down a column, and it keeps the number readable beside it."""
    return [("custom.cellOptions", {"type": "gauge", "mode": "basic", "valueDisplayMode": "text"}),
            ("min", minv), ("max", maxv)]


CELL_COLOR_BG = ("custom.cellOptions", {"type": "color-background", "mode": "basic",
                                        "applyToRow": False, "wrapText": False})
CELL_COLOR_TEXT = ("custom.cellOptions", {"type": "color-text"})


# -------------------------------------------------------------------- layout

class Grid:
    """Places panels on Grafana's 24-column grid so no gridPos is written by hand.

    Panels are added in reading order and wrap when the row fills. `section()`
    opens a collapsible row: one thin titled rule, and nothing under it but the
    panels. The row is a place to fold a dashboard, not a place to write.
    """

    def __init__(self):
        self.panels: list[dict] = []
        self._y = 0
        self._x = 0
        self._line_h = 0

    def _newline(self):
        if self._x:
            self._y += self._line_h
            self._x = 0
            self._line_h = 0

    def add(self, panel: dict) -> dict:
        w = panel["gridPos"]["w"]
        h = panel["gridPos"]["h"]
        if self._x + w > 24:
            self._newline()
        panel["gridPos"]["x"] = self._x
        panel["gridPos"]["y"] = self._y
        self._x += w
        self._line_h = max(self._line_h, h)
        if self._x >= 24:
            self._newline()
        self.panels.append(panel)
        return panel

    def extend(self, panels):
        for p in panels:
            self.add(p)

    def section(self, title: str, collapsed: bool = False):
        self._newline()
        row = {"type": "row", "title": title, "collapsed": collapsed, "panels": [],
               "gridPos": {"h": 1, "w": 24, "x": 0, "y": self._y}}
        self.panels.append(row)
        self._y += 1
        return row

    def collapsed_section(self, title: str, panels: list):
        """A row that carries its children, so they cost nothing until opened."""
        self._newline()
        inner = Grid()
        inner.extend(panels)
        for p in inner.panels:
            p["gridPos"]["y"] += self._y + 1
        row = {"type": "row", "title": title, "collapsed": True,
               "panels": inner.panels,
               "gridPos": {"h": 1, "w": 24, "x": 0, "y": self._y}}
        self.panels.append(row)
        self._y += 1
        return row


# ---------------------------------------------------------------- dashboards

def dash_links(include_nodes: bool = True) -> list:
    links = [{
        "asDropdown": True, "icon": "external link", "includeVars": False,
        "keepTime": True, "tags": ["homelab"], "targetBlank": False,
        "title": "Homelab", "tooltip": "Every topic dashboard", "type": "dashboards", "url": "",
    }]
    if include_nodes:
        links.append({
            "asDropdown": True, "icon": "external link", "includeVars": False,
            "keepTime": True, "tags": ["node"], "targetBlank": False,
            "title": "Nodes", "tooltip": "One dashboard per host", "type": "dashboards", "url": "",
        })
    return links


def dashboard(uid, title, grid: Grid, *, tags, description="", refresh="30s",
              time_from="now-6h", templating=None, links=None) -> dict:
    return {
        "uid": uid,
        "title": title,
        "description": description,
        "tags": tags,
        "timezone": "browser",
        # Provisioning runs with allowUiUpdates false, so Grafana refuses to
        # persist a browser edit either way. Leaving this true keeps panel-edit
        # and Explore reachable, which is how you read a query without hunting
        # for it in git.
        "editable": True,
        "graphTooltip": 1,
        "refresh": refresh,
        "schemaVersion": 39,
        "time": {"from": time_from, "to": "now"},
        "timepicker": {},
        "links": links if links is not None else dash_links(),
        "templating": {"list": templating or []},
        "panels": grid.panels,
    }


def var_query(name, label, query, *, multi=True, all_=True, current_text="All",
              current_value="$__all", regex="", sort=1, description="") -> dict:
    v = {
        "name": name, "label": label, "type": "query", "datasource": DS,
        "query": {"query": query, "refId": name},
        "refresh": 1, "regex": regex, "sort": sort,
        "includeAll": all_, "multi": multi,
        "options": [], "hide": 0,
    }
    if description:
        v["description"] = description
    if all_:
        v["allValue"] = ".*"
    if multi:
        v["current"] = {"selected": True, "text": [current_text], "value": [current_value]}
    else:
        v["current"] = {"selected": True, "text": current_text, "value": current_value}
    return v


def var_custom(name, label, values, *, multi=False, all_=False, description="") -> dict:
    first = values[0]
    v = {
        "name": name, "label": label, "type": "custom",
        "query": ",".join(values), "includeAll": all_, "multi": multi,
        "options": [{"selected": i == 0, "text": x, "value": x} for i, x in enumerate(values)],
        "current": {"selected": True, "text": [first] if multi else first,
                    "value": [first] if multi else first},
        "hide": 0,
    }
    if description:
        v["description"] = description
    if all_:
        v["allValue"] = ".*"
    return v


def var_constant(name, value) -> dict:
    """A hidden constant, used to keep a hostname in one place on a node board."""
    return {"name": name, "type": "constant", "query": value, "hide": 2,
            "current": {"selected": False, "text": value, "value": value},
            "options": [{"selected": True, "text": value, "value": value}],
            "skipUrlSync": True}
