#!/usr/bin/env python3
"""diagram.py: declarative, self-contained SVG architecture diagrams (stdlib only).

A spec builds a Diagram, declares groups, cards, edges and rows, then calls
render(). Layout is automatic: rows stack top to bottom, groups size to their
contents on an 8 px grid, cards share a column width per row. Logos are embedded
as base64 data URIs inside <symbol> elements and referenced with <use>.
"""
import base64, math, os, subprocess, sys, tempfile
import xml.etree.ElementTree as ET

FONT = "Inter, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
FS = {"small": 11, "body": 13, "head": 15, "title": 22}
GRID = 8

PALETTE = {
    "ink": "#1F2933", "muted": "#5C6873", "faint": "#8B949E", "border": "#D0D7DE",
    "card": "#FFFFFF", "page": "#FFFFFF", "badge": "#EEF1F4", "badge_text": "#3D4852",
    "warn": "#B7791F", "warn_bg": "#FFF8E6",
    # family: (fill, stroke, text)
    "families": {
        "Internal":      ("#EEF4FB", "#9CBBE0", "#1D4F80"),
        "Untrusted":     ("#FCEDEC", "#E4A2A0", "#8E2622"),
        "Dmz":           ("#FFF2E3", "#EDB578", "#8A4B0E"),
        "Identity":      ("#F3EEFB", "#BCA6E3", "#4E2E86"),
        "Mgmt":          ("#EEF2F4", "#A9B7C3", "#33434F"),
        "Observability": ("#EAF6EE", "#93CBA3", "#1F5C31"),
        "Servers":       ("#E7F5F7", "#8DC9D0", "#145C64"),
        "Access":        ("#FFF7E0", "#E6C56A", "#6B4E07"),
        "External":      ("#F4F4F6", "#BEC2CC", "#4A4F5A"),
    },
    "edges": {"blue": "#2B6CB0", "orange": "#C05621", "red": "#C53030", "green": "#2F855A",
              "purple": "#6B46C1", "grey": "#718096", "teal": "#2C7A7B"},
    # node badge: (fill, text)
    "nodes": {"grey": ("#E9ECEF", "#495057"), "purple": ("#EFE5FB", "#6B3FA0"),
              "blue": ("#E1EDFB", "#1D5FB0"), "red": ("#FBE3E3", "#B02A2A"), "green": ("#E2F4E6", "#22773B")},
}

# Arial-like advance widths per 1000 em (Helvetica AFM values), regular and bold.
_ASCII = " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"
_REG = [278,278,355,556,556,889,667,191,333,333,389,584,278,333,278,278]+[556]*10+[278,278,584,584,584,556,1015,
        667,667,722,722,667,611,778,722,278,500,667,556,833,722,778,667,778,722,667,611,722,667,944,667,667,611,
        278,278,278,469,556,333,556,556,500,556,556,278,556,556,222,222,500,222,833,556,556,556,556,333,500,278,
        556,500,722,500,500,500,334,260,334,584]
_BOLD = [278,333,474,556,556,889,722,238,333,333,389,584,278,333,278,278]+[556]*10+[333,333,584,584,584,611,975,
        722,722,722,722,667,611,778,722,278,556,722,611,833,722,778,667,778,722,667,611,722,667,944,667,667,611,
        333,278,333,584,556,333,556,611,556,611,556,333,611,611,278,278,556,278,889,611,611,611,611,389,556,333,
        611,556,778,556,556,500,389,280,389,584]
_WREG, _WBOLD = dict(zip(_ASCII, _REG)), dict(zip(_ASCII, _BOLD))

def text_w(s, size, bold=False):
    """Estimated rendered width, padded 6 percent so Inter or Segoe never clip."""
    t = _WBOLD if bold else _WREG
    return sum(t.get(c, 620) for c in s) / 1000 * size * 1.06

def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def fit(s, size, avail, bold=False):
    if text_w(s, size, bold) <= avail: return s
    while s and text_w(s + "...", size, bold) > avail: s = s[:-1]
    print(f"warning: truncated '{s}...' to fit {avail:.0f}px", file=sys.stderr)
    return s + "..."

def snap(v): return int(math.ceil(v / GRID) * GRID)


class Card:
    def __init__(self, id, name, sub1="", sub2="", logo=None, icons=(), badge=None, node=None, span=1, warn=False):
        self.id, self.name, self.sub1, self.sub2, self.logo = id, name, sub1, sub2, logo
        self.icons, self.badge, self.node, self.span, self.warn = list(icons), badge, node, span, warn
        self.x = self.y = self.w = self.h = 0; self.parent = None

class Group:
    def __init__(self, id, title, badge=None, family="External", cols=None, flow="row", notes=(), frame=True, accent=None):
        self.id, self.title, self.badge, self.family, self.cols, self.flow = id, title, badge, family, cols, flow
        self.notes, self.frame, self.accent = list(notes), frame, accent
        self.children = []; self.parent = None; self.x = self.y = self.w = self.h = 0

class Edge:
    def __init__(self, src, dst, label="", style="solid", color="grey", from_side=None, to_side=None,
                 x=None, y=None, s_off=0, t_off=0, arrows="end", label_seg=None, label_x=None, label_y=None, label_anchor="middle"):
        self.__dict__.update(locals()); del self.__dict__["self"]

class Bus:
    def __init__(self, label, members, style="solid", color="grey"):
        self.label, self.members, self.style, self.color = label, members, style, color


class Diagram:
    def __init__(self, name, title, subtitle="", state="State as of 2026-09-24", source="", width=1600,
                 card_w=220, card_h=84, gap=12, pad=12, group_gap=24, row_gap=56, margin=40, logo_dir=None):
        self.name, self.title, self.subtitle, self.state, self.source, self.width = name, title, subtitle, state, source, width
        self.card_w, self.card_h, self.gap, self.pad, self.group_gap, self.row_gap, self.margin = card_w, card_h, gap, pad, group_gap, row_gap, margin
        self.header_h, self.logo_px, self.icon_px = 30, 28, 16
        self.logo_dir = logo_dir or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logos")
        self.items, self.rows, self.edges, self.buses, self.footnotes = {}, [], [], {}, []
        self.legend_families, self.legend_edges, self.legend_icons, self.legend_badges = {}, [], [], []
        self._logos = {}

    # ----- declaration -------------------------------------------------------
    def group(self, id, title, **kw):
        g = Group(id, title, **kw); self.items[id] = g; return g
    def stack(self, id, *ids):
        g = Group(id, "", frame=False, flow="col"); self.items[id] = g
        for i in ids: self.items[i].parent = g; g.children.append(self.items[i])
        return g
    def nest(self, parent, *ids):
        p = self.items[parent]
        for i in ids: self.items[i].parent = p; p.children.append(self.items[i])
    def card(self, group, id, name, **kw):
        c = Card(id, name, **kw); self.items[id] = c; g = self.items[group]; c.parent = g; g.children.append(c); return c
    def edge(self, src, dst, label="", **kw):
        self.edges.append(Edge(src, dst, label, **kw))
    def bus(self, row_index, label, members, **kw):
        self.buses.setdefault(row_index, []).append(Bus(label, members, **kw))
    def row(self, *ids, stretch=True):
        self.rows.append({"ids": list(ids), "stretch": stretch})
    def footnote(self, text): self.footnotes.append(text)
    def legend_family(self, family, label): self.legend_families[family] = label
    def legend_edge(self, label, style="solid", color="grey"): self.legend_edges.append((label, style, color))
    def legend_icon(self, logo, label): self.legend_icons.append((logo, label))
    def legend_badge(self, label, color): self.legend_badges.append((label, color))

    # ----- measurement and placement -----------------------------------------
    def _notes_h(self, g): return len(g.notes) * 16 + (4 if g.notes else 0)
    def _grid(self, g):
        cards = g.children; cols = g.cols or sum(c.span for c in cards) or 1
        pos, r, c = [], 0, 0
        for card in cards:
            if c + card.span > cols: r += 1; c = 0
            pos.append((r, c)); c += card.span
        return cols, r + 1, pos
    def _measure(self, el):
        if isinstance(el, Card): return (self.card_w * el.span + self.gap * (el.span - 1), self.card_h)
        hdr, pad = (self.header_h, self.pad) if el.frame else (0, 0)
        nh = self._notes_h(el); kids = el.children
        if kids and isinstance(kids[0], Card):
            cols, rows, _ = self._grid(el)
            w, h = cols * self.card_w + (cols - 1) * self.gap, rows * self.card_h + (rows - 1) * self.gap
        elif kids:
            sz = [self._measure(k) for k in kids]; gg = self.gap + 4
            if el.flow == "row": w, h = sum(s[0] for s in sz) + gg * (len(sz) - 1), max(s[1] for s in sz)
            else: w, h = max(s[0] for s in sz), sum(s[1] for s in sz) + gg * (len(sz) - 1)
        else:
            w, h = max(self.card_w, max([text_w(t, FS["small"]) + 20 for _, t in el.notes] + [0])), 0
        if el.notes: w = max(w, max(text_w(t, FS["small"]) + (20 if i else 0) for i, t in el.notes))
        return (snap(w + 2 * pad), snap(h + hdr + 2 * pad + nh))
    def _place(self, el, x, y, w, h):
        el.x, el.y, el.w, el.h = x, y, w, h
        if isinstance(el, Card): return
        hdr, pad = (self.header_h, self.pad) if el.frame else (0, 0)
        ix, iy, iw, ih = x + pad, y + hdr + pad + self._notes_h(el), w - 2 * pad, h - hdr - 2 * pad - self._notes_h(el)
        kids = el.children
        if not kids: return
        if isinstance(kids[0], Card):
            cols, rows, pos = self._grid(el); cw = (iw - (cols - 1) * self.gap) / cols
            for card, (r, c) in zip(kids, pos):
                self._place(card, ix + c * (cw + self.gap), iy + r * (self.card_h + self.gap), cw * card.span + self.gap * (card.span - 1), self.card_h)
            return
        sz = [self._measure(k) for k in kids]; gg = self.gap + 4
        if el.flow == "row":
            share = (iw - sum(s[0] for s in sz) - gg * (len(sz) - 1)) / len(sz); cx = ix
            for k, (kw, kh) in zip(kids, sz): self._place(k, cx, iy, kw + share, ih); cx += kw + share + gg
        else:
            share = (ih - sum(s[1] for s in sz) - gg * (len(sz) - 1)) / len(sz); cy = iy
            for k, (kw, kh) in zip(kids, sz): self._place(k, ix, cy, iw, kh + share); cy += kh + share + gg
    def _layout(self):
        cw = self.width - 2 * self.margin; y = self.margin + 72; self.row_box = []
        for i, row in enumerate(self.rows):
            nb = len(self.buses.get(i, [])); y += nb * 26 + (8 if nb else 0)
            its = [self.items[i2] for i2 in row["ids"]]; sz = [self._measure(it) for it in its]
            extra = cw - sum(s[0] for s in sz) - self.group_gap * (len(its) - 1)
            share = extra / len(its) if row["stretch"] or extra < 0 else 0
            x = self.margin + (0 if share else extra / 2); rh = max(s[1] for s in sz)
            for it, (w, h) in zip(its, sz): self._place(it, x, y, w + share, rh); x += w + share + self.group_gap
            self.row_box.append((y, y + rh)); y += rh + self.row_gap
        self.body_bottom = y - self.row_gap

    # ----- geometry helpers ---------------------------------------------------
    def _row_of(self, el):
        while el.parent is not None: el = el.parent
        for i, row in enumerate(self.rows):
            if el.id in row["ids"]: return i
        raise KeyError(el.id)
    def _gap_y(self, i, delta=0):
        return (self.row_box[i][1] + self.row_box[i + 1][0]) / 2 + delta
    def _rx(self, spec):
        if spec is None or isinstance(spec, (int, float)): return spec
        key, _, rest = spec.partition(":"); parts = rest.split(":") if rest else []
        if key in ("left", "right"):
            return (self.margin / 2 if key == "left" else self.width - self.margin / 2) + (float(rest) if rest else 0)
        if key == "mid": e = self.items[parts[0]]; return e.x + e.w / 2 + (float(parts[1]) if len(parts) > 1 else 0)
        if key == "between":
            a, b = [self.items[i] for i in parts[0].split(",")]; return (a.x + a.w + b.x) / 2
        raise ValueError(spec)
    def _ry(self, spec):
        if spec is None or isinstance(spec, (int, float)): return spec
        key, _, rest = spec.partition(":"); parts = rest.split(":") if rest else []
        if key == "gap": return self._gap_y(int(parts[0]), float(parts[1]) if len(parts) > 1 else 0)
        if key == "mid": e = self.items[parts[0]]; return e.y + e.h / 2 + (float(parts[1]) if len(parts) > 1 else 0)
        raise ValueError(spec)
    def _anchor(self, el, side, off):
        return {"top": (el.x + el.w / 2 + off, el.y), "bottom": (el.x + el.w / 2 + off, el.y + el.h),
                "left": (el.x, el.y + el.h / 2 + off), "right": (el.x + el.w, el.y + el.h / 2 + off)}[side]
    def _route(self, e):
        s, t = self.items[e.src], self.items[e.dst]
        fs, ts = e.from_side, e.to_side
        if fs is None or ts is None:
            if t.y >= s.y + s.h: a = ("bottom", "top")
            elif t.y + t.h <= s.y: a = ("top", "bottom")
            elif t.x >= s.x + s.w: a = ("right", "left")
            else: a = ("left", "right")
            fs, ts = fs or a[0], ts or a[1]
        p0, p1 = self._anchor(s, fs, e.s_off), self._anchor(t, ts, e.t_off)
        X, Y = self._rx(e.x), self._ry(e.y); V = ("top", "bottom")
        def chan(el, side):  # free horizontal channel just outside an element's row
            r = self._row_of(el)
            return self._gap_y(r) if side == "bottom" else self._gap_y(r - 1)
        if fs in V and ts in V:
            y1 = Y if Y is not None else (chan(s, fs) if X is not None or fs == ts else (p0[1] + p1[1]) / 2)
            y2 = Y if Y is not None else (chan(t, ts) if X is not None or fs == ts else y1)
            pts = [p0, (p0[0], y1), (X if X is not None else p1[0], y1), (X if X is not None else p1[0], y2), (p1[0], y2), p1]
        elif fs not in V and ts not in V:
            xm = X if X is not None else (p0[0] + p1[0]) / 2
            pts = [p0, (xm, p0[1]), (xm, p1[1]), p1]
        elif fs in V:
            y1 = Y if Y is not None else (chan(s, fs) if X is not None else p1[1])
            pts = [p0, (p0[0], y1)] + ([(X, y1), (X, p1[1])] if X is not None else []) + [p1]
        else:
            y2 = Y if Y is not None else (chan(t, ts) if X is not None else p0[1])
            pts = [p0] + ([(X, p0[1]), (X, y2)] if X is not None else []) + [(p1[0], y2), p1]
        out = [pts[0]]  # drop duplicates and collinear midpoints
        for p in pts[1:]:
            if abs(p[0] - out[-1][0]) < .5 and abs(p[1] - out[-1][1]) < .5: continue
            if len(out) >= 2 and ((abs(out[-2][0] - out[-1][0]) < .5 and abs(out[-1][0] - p[0]) < .5) or
                                  (abs(out[-2][1] - out[-1][1]) < .5 and abs(out[-1][1] - p[1]) < .5)): out[-1] = p
            else: out.append(p)
        return out

    # ----- drawing -----------------------------------------------------------
    def _logo_sym(self, key):
        if key in self._logos or key is None or key.startswith("glyph:"): return
        path = os.path.join(self.logo_dir, key + ".svg")
        if not os.path.exists(path): print(f"warning: no logo file for '{key}', drawing a glyph", file=sys.stderr); return
        b64 = base64.b64encode(open(path, "rb").read()).decode()
        self._logos[key] = (f'<symbol id="lg-{key}" viewBox="0 0 24 24"><image width="24" height="24" '
                            f'href="data:image/svg+xml;base64,{b64}"/></symbol>')
    def _logo(self, key, x, y, size):
        if key is None: return ""
        self._logo_sym(key)
        if key in self._logos: return f'<use href="#lg-{key}" x="{x:g}" y="{y:g}" width="{size}" height="{size}"/>'
        txt = key[6:] if key.startswith("glyph:") else "?"; fs = 11 if len(txt) <= 2 else 9
        return (f'<rect x="{x:g}" y="{y:g}" width="{size}" height="{size}" rx="6" fill="{PALETTE["badge"]}" stroke="{PALETTE["border"]}"/>'
                f'<text x="{x + size / 2:g}" y="{y + size / 2 + fs * .36:g}" font-size="{fs}" font-weight="700" fill="{PALETTE["badge_text"]}" text-anchor="middle">{esc(txt)}</text>')
    def _pill(self, x, y, text, fill, color, stroke=None, size=11, anchor="start"):
        w = text_w(text, size, True) + 12; h = size + 7
        if anchor == "end": x -= w
        elif anchor == "middle": x -= w / 2
        st = f' stroke="{stroke}"' if stroke else ""
        return (f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h}" rx="{h / 2}" fill="{fill}"{st}/>'
                f'<text x="{x + w / 2:g}" y="{y + h / 2 + size * .36:g}" font-size="{size}" font-weight="600" fill="{color}" text-anchor="middle">{esc(text)}</text>'), w
    def _draw_card(self, c):
        o = []; x, y, w, h = c.x, c.y, c.w, c.h
        o.append(f'<rect x="{x + 1:g}" y="{y + 2:g}" width="{w:g}" height="{h}" rx="8" fill="#000" opacity="0.05"/>')
        stroke = PALETTE["warn"] if c.warn else PALETTE["border"]
        o.append(f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h}" rx="8" fill="{PALETTE["card"]}" stroke="{stroke}"/>')
        if c.node:  # coloured stripe on the left edge names the Galaxy node
            o.append(f'<path d="M{x + 8:g} {y + .5:g}a8 8 0 0 0 -8 8v{h - 16}a8 8 0 0 0 8 8z" fill="{PALETTE["nodes"][c.node][1]}"/>')
        lp = self.logo_px; o.append(self._logo(c.logo, x + 10, y + (h - lp) / 2, lp))
        tx = x + 10 + lp + 8; right = x + w - 8; bw = 0
        if c.badge:
            p, bw = self._pill(right, y + 8, c.badge, PALETTE["badge"], PALETTE["badge_text"], anchor="end"); o.append(p); bw += 6
        name = fit(c.name, FS["body"], right - tx - bw, True)
        o.append(f'<text x="{tx:g}" y="{y + 22}" font-size="{FS["body"]}" font-weight="700" fill="{PALETTE["ink"]}">{esc(name)}</text>')
        if c.sub1: o.append(f'<text x="{tx:g}" y="{y + 39}" font-size="{FS["small"]}" fill="{PALETTE["muted"]}">{esc(fit(c.sub1, FS["small"], right - tx))}</text>')
        if c.sub2: o.append(f'<text x="{tx:g}" y="{y + 54}" font-size="{FS["small"]}" fill="{PALETTE["muted"]}">{esc(fit(c.sub2, FS["small"], right - tx))}</text>')
        for i, ic in enumerate(c.icons):  # icon row sits under the text column
            o.append(self._logo(ic, tx + i * (self.icon_px + 5), y + h - self.icon_px - 8, self.icon_px))
        return "".join(o)
    def _draw_group(self, g):
        o = []
        if g.frame:
            fill, stroke, text = PALETTE["families"][g.family]
            o.append(f'<rect x="{g.x:g}" y="{g.y:g}" width="{g.w:g}" height="{g.h:g}" rx="10" fill="{fill}" stroke="{stroke}"/>')
            hfill, hop = (PALETTE["nodes"][g.accent][1], 0.85) if g.accent else (stroke, 0.28)
            if g.accent: text = "#FFFFFF"
            o.append(f'<path d="M{g.x + 10:g} {g.y:g}h{g.w - 20:g}a10 10 0 0 1 10 10v{self.header_h - 10}H{g.x:g}v-{self.header_h - 10}a10 10 0 0 1 10 -10z" fill="{hfill}" opacity="{hop}"/>')
            bw = 0
            if g.badge:
                bf, bt = ("#FFFFFF", PALETTE["nodes"][g.accent][1]) if g.accent else (text, "#FFFFFF")
                p, bw = self._pill(g.x + g.w - 10, g.y + 6, g.badge, bf, bt, anchor="end"); o.append(p)
            o.append(f'<text x="{g.x + 12:g}" y="{g.y + 20}" font-size="{FS["body"]}" font-weight="700" fill="{text}">{esc(fit(g.title, FS["body"], g.w - 30 - bw, True))}</text>')
            ny = g.y + self.header_h + self.pad + 12
            for icon, line in g.notes:
                col = PALETTE["warn"] if line.startswith("!") else PALETTE["muted"]; line = line.lstrip("!")
                o.append(self._logo(icon, g.x + self.pad, ny - 12, 14) if icon else "")
                o.append(f'<text x="{g.x + self.pad + (20 if icon else 0):g}" y="{ny}" font-size="{FS["small"]}" fill="{col}">{esc(line)}</text>'); ny += 16
        for k in g.children: o.append(self._draw_card(k) if isinstance(k, Card) else self._draw_group(k))
        return "".join(o)
    def _draw_edge(self, e):
        pts = self._route(e); col = PALETTE["edges"][e.color]
        d = f"M{pts[0][0]:g} {pts[0][1]:g}"
        for i in range(1, len(pts) - 1):
            a, b, c = pts[i - 1], pts[i], pts[i + 1]
            r = min(6, math.dist(a, b) / 2, math.dist(b, c) / 2)
            ux, uy = (b[0] - a[0]) / (math.dist(a, b) or 1), (b[1] - a[1]) / (math.dist(a, b) or 1)
            vx, vy = (c[0] - b[0]) / (math.dist(b, c) or 1), (c[1] - b[1]) / (math.dist(b, c) or 1)
            d += f"L{b[0] - ux * r:g} {b[1] - uy * r:g}Q{b[0]:g} {b[1]:g} {b[0] + vx * r:g} {b[1] + vy * r:g}"
        d += f"L{pts[-1][0]:g} {pts[-1][1]:g}"
        dash = ' stroke-dasharray="6 4"' if e.style == "dashed" else (' stroke-dasharray="2 3"' if e.style == "dotted" else "")
        ms = f' marker-start="url(#arr-{e.color})"' if e.arrows == "both" else ""
        o = [f'<path d="{d}" fill="none" stroke="{col}" stroke-width="1.6"{dash} marker-end="url(#arr-{e.color})"{ms}/>']
        if e.label:
            segs = [(math.dist(pts[i], pts[i + 1]), i) for i in range(len(pts) - 1)]
            gaps = [self._gap_y(r) for r in range(len(self.row_box) - 1)]
            cross = [(i, gy) for i in range(len(segs)) for gy in gaps  # vertical segments crossing a row gap
                     if abs(pts[i][0] - pts[i + 1][0]) < .5 and min(pts[i][1], pts[i + 1][1]) <= gy <= max(pts[i][1], pts[i + 1][1])]
            if e.label_seg is not None: i = e.label_seg if e.label_seg >= 0 else e.label_seg + len(segs)
            else: i = cross[0][0] if cross else max(segs)[1]
            (ax, ay), (bx, by) = pts[i], pts[i + 1]
            mx, my = (ax + bx) / 2, (ay + by) / 2
            for ci, gy in cross:
                if ci == i: my = gy; break
            if e.label_x is not None: mx = self._rx(e.label_x)
            if e.label_y is not None: my = self._ry(e.label_y)
            o.append(self._pill(mx, my - 9, e.label, "#FFFFFF", col, stroke=col, anchor=e.label_anchor)[0])
        return "".join(o)
    def _draw_bus(self, i, buses):
        o = []; y0 = self.row_box[i][0] - 8 - 26 * len(buses)
        for k, b in enumerate(buses):
            y = y0 + k * 26 + 13; col = PALETTE["edges"][b.color]; mem = [self.items[m] for m in b.members]
            xs = [m.x + m.w / 2 + (k - (len(buses) - 1) / 2) * 12 for m in mem]
            dash = ' stroke-dasharray="6 4"' if b.style == "dashed" else ""
            o.append(f'<path d="M{min(xs):g} {y:g}H{max(xs):g}" stroke="{col}" stroke-width="1.6" fill="none"{dash}/>')
            for m, x in zip(mem, xs):
                o.append(f'<path d="M{x:g} {y:g}V{m.y:g}" stroke="{col}" stroke-width="1.6" fill="none"{dash}/>')
                o.append(f'<circle cx="{x:g}" cy="{y:g}" r="3" fill="{col}"/>')
            lx = (xs[0] + xs[1]) / 2 if len(xs) > 1 else xs[0]
            o.append(self._pill(lx, y - 9, b.label, "#FFFFFF", col, stroke=col, anchor="middle")[0])
        return "".join(o)
    def _draw_legend(self, y):
        o, x, x0 = [], self.margin, self.margin
        def item(w):
            nonlocal x, y
            if x + w > self.width - self.margin: x = x0; y += 24
            return x
        fams = [f for f in PALETTE["families"] if any(isinstance(g, Group) and g.frame and g.family == f for g in self.items.values())]
        for f in fams:
            fill, stroke, text = PALETTE["families"][f]; label = self.legend_families.get(f, f)
            x = item(text_w(label, 11) + 34)
            o.append(f'<rect x="{x}" y="{y - 12}" width="18" height="14" rx="3" fill="{fill}" stroke="{stroke}"/>')
            o.append(f'<text x="{x + 24}" y="{y - 1}" font-size="11" fill="{PALETTE["muted"]}">{esc(label)}</text>'); x += text_w(label, 11) + 40
        for label, style, color in self.legend_edges:
            x = item(text_w(label, 11) + 44); col = PALETTE["edges"][color]
            dash = ' stroke-dasharray="6 4"' if style == "dashed" else ""
            o.append(f'<path d="M{x} {y - 5}h26" stroke="{col}" stroke-width="1.6"{dash} marker-end="url(#arr-{color})"/>')
            o.append(f'<text x="{x + 34}" y="{y - 1}" font-size="11" fill="{PALETTE["muted"]}">{esc(label)}</text>'); x += text_w(label, 11) + 50
        for logo, label in self.legend_icons:
            x = item(text_w(label, 11) + 32); o.append(self._logo(logo, x, y - 13, 16))
            o.append(f'<text x="{x + 22}" y="{y - 1}" font-size="11" fill="{PALETTE["muted"]}">{esc(label)}</text>'); x += text_w(label, 11) + 38
        for label, color in self.legend_badges:
            x = item(text_w(label, 11) + 34); col = PALETTE["nodes"][color][1]
            o.append(f'<rect x="{x}" y="{y - 12}" width="18" height="14" rx="3" fill="{PALETTE["card"]}" stroke="{PALETTE["border"]}"/><rect x="{x}" y="{y - 12}" width="5" height="14" rx="2" fill="{col}"/>')
            o.append(f'<text x="{x + 24}" y="{y - 1}" font-size="11" fill="{PALETTE["muted"]}">{esc(label)}</text>'); x += text_w(label, 11) + 40
        return "".join(o), y + 12

    def render(self, out_svg, png=True, readme_width=None):
        self._layout()
        body = []
        for row in self.rows:
            for i in row["ids"]: body.append(self._draw_group(self.items[i]) if isinstance(self.items[i], Group) else self._draw_card(self.items[i]))
        for i, bl in self.buses.items(): body.append(self._draw_bus(i, bl))
        for e in self.edges: body.append(self._draw_edge(e))
        legend, ly = self._draw_legend(self.body_bottom + 44)
        fy = ly + 8
        foot = [f'<text x="{self.margin}" y="{fy + 4}" font-size="11" fill="{PALETTE["faint"]}">{esc(t)}</text>' for fy, t in
                [(fy + i * 16, t) for i, t in enumerate(self.footnotes + [f"Source: {self.source}"])]]
        H = snap(fy + 16 * (len(self.footnotes) + 1) + 12); W = self.width
        defs = "".join(self._logos.values()) + "".join(
            f'<marker id="arr-{k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0 0L10 5L0 10z" fill="{v}"/></marker>' for k, v in PALETTE["edges"].items())
        head = (f'<text x="{self.margin}" y="{self.margin + 18}" font-size="{FS["title"]}" font-weight="700" fill="{PALETTE["ink"]}">{esc(self.title)}</text>'
                f'<text x="{self.margin}" y="{self.margin + 40}" font-size="{FS["body"]}" fill="{PALETTE["muted"]}">{esc(self.subtitle)}</text>'
                + self._pill(W - self.margin, self.margin + 4, self.state, PALETTE["badge"], PALETTE["badge_text"], anchor="end")[0])
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">'
               f'<defs>{defs}</defs><rect width="{W}" height="{H}" fill="{PALETTE["page"]}"/>{head}{"".join(body)}{legend}{"".join(foot)}</svg>')
        ET.fromstring(svg)  # must parse as XML
        for bad in ("<script", "<foreignObject", 'href="http'):
            assert bad not in svg, bad
        os.makedirs(os.path.dirname(os.path.abspath(out_svg)), exist_ok=True)
        with open(out_svg, "w", encoding="utf-8") as f: f.write(svg)
        print(f"{out_svg}: {W}x{H}, {len(svg) // 1024} KiB")
        if png: render_png(out_svg, out_svg[:-4] + ".png", W, H)
        if readme_width: render_png(out_svg, out_svg[:-4] + f".{readme_width}.png", readme_width, math.ceil(H * readme_width / W), scale=1)
        return out_svg


def render_png(svg_path, png_path, w, h, scale=2):
    """Screenshot the SVG with headless Chrome; a small HTML wrapper scales it to w."""
    html = tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, dir=os.path.dirname(os.path.abspath(svg_path)))
    html.write(f'<!doctype html><html><body style="margin:0;background:#fff"><img src="file://{os.path.abspath(svg_path)}" style="width:{w}px;display:block"></body></html>')
    html.close()
    cmd = ["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars", f"--force-device-scale-factor={scale}",
           f"--window-size={w},{h}", f"--screenshot={png_path}", f"file://{html.name}"]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=90)
    os.unlink(html.name); print(f"{png_path}: {w * scale}x{h * scale}")
