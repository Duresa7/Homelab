# Diagram generator

**Created:** 2026-09-24  
**Last updated:** 2026-09-25

The eighteen diagrams in `Assets/Diagrams/` are generated from declarative Python specs by a stdlib-only library. Everything rebuilds with one command from this folder; nothing is hand-drawn.

```
Generator/
  lib/diagram.py        the library (about 400 lines); lib/ext_rowgaps.py adds row-gap control
  specs/*.py            one spec per diagram; imports the library and writes ../<name>.svg (PNG=1 adds a 2x PNG)
  logos/*.svg           square-viewBox product marks, see logos/SOURCES.md
  logos/build_logos.py  normalises logos/_raw and logos/_si into logos/*.svg
  build.py              runs everything and validates every SVG in Assets/Diagrams/
```

## Visual system

### Palette

One place: `PALETTE` at the top of `lib/diagram.py`. Chrome is neutral grey; each zone family has a tint (fill), a stroke, and a text colour that reads on white.

| Family | Fill | Stroke | Text | Used for |
|---|---|---|---|---|
| Internal | `#EEF4FB` | `#9CBBE0` | `#1D4F80` | Management, Personal-A, Secure, Secure Client, the UniFi fabric |
| Untrusted | `#FCEDEC` | `#E4A2A0` | `#8E2622` | IoT |
| Dmz | `#FFF2E3` | `#EDB578` | `#8A4B0E` | DMZ 30 |
| Identity | `#F3EEFB` | `#BCA6E3` | `#4E2E86` | IDENTITY-A 65 |
| Mgmt | `#EEF2F4` | `#A9B7C3` | `#33434F` | MGMT-A 70, Cluster-Net 71, the Galaxy nodes |
| Observability | `#EAF6EE` | `#93CBA3` | `#1F5C31` | Security-A 72, MONITOR-A 73 |
| Servers | `#E7F5F7` | `#8DC9D0` | `#145C64` | SERVERS-A 80 |
| Access | `#FFF7E0` | `#E6C56A` | `#6B4E07` | Access-A 85 |
| External | `#F4F4F6` | `#BEC2CC` | `#4A4F5A` | the Internet row, power, notes |

Edge colours (`PALETTE["edges"]`): blue `#2B6CB0` publishing and HTTPS, orange `#C05621` security telemetry, green `#2F855A` monitoring, purple `#6B46C1` identity, teal `#2C7A7B` VPN and mesh, grey `#718096` plain traffic and power.

Node colours (`PALETTE["nodes"]`): grey `#495057`, purple `#6B3FA0`, blue `#1D5FB0`, red `#B02A2A`, green `#22773B`. A guest card carries its node as a 8 px stripe on its left edge; on galaxy-cluster the node frame's header strip takes the same colour. The names are literal, so no legend lookup is needed beyond the first glance.

Text: ink `#1F2933`, muted `#5C6873`, faint `#8B949E`, borders `#D0D7DE`. Warnings (green-server) use amber `#B7791F`.

### Card anatomy

220 x 84 px (the width is per row: a row that is over-full shrinks its cards, a row with room stretches them). White fill, 1 px `#D0D7DE` border, 8 px radius, a 5 percent black offset shadow.

```
+---------------------------------------------+
|[stripe] (logo 28)  Name, 13 px bold          |
|                    sub1, 11 px muted         |
|                    sub2, 11 px muted         |
|                    [16 px icon][icon]...     |
+---------------------------------------------+
```

- Logo at x+10, vertically centred. `logo="glyph:AB"` draws a rounded square with the text instead (used for WAN 2, Jedi PC, VLAN chips).
- Text column starts at x+46 and ends 8 px before the right edge. `fit()` truncates with an ellipsis and prints a warning to stderr; a warning is a bug in the spec's wording, not something to ship.
- `icons=[...]` draws up to about six 16 px marks on the bottom row. Marks that are wordmarks (Action1) or muddy at 16 px (NUT) stay in text.
- `badge="VLAN 40"` puts a grey pill top right; `node="grey"` draws the stripe; `warn=True` gives the border the amber colour; `span=2` lets a card take two grid columns.

### Groups

Tinted container with a 30 px header strip (stroke colour at 28 percent, or the node colour at 85 percent when `accent` is set), title 13 px bold in the family text colour, optional badge pill on the right. `notes=[(icon, "text"), ...]` renders 11 px lines under the header; a line starting with `!` renders in amber. Groups size to their contents on an 8 px grid; `cols` fixes the card grid; `flow="col"` stacks nested groups vertically; `frame=False` (via `d.stack()`) stacks groups with no chrome.

### Type scale

`FONT = Inter, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif`. Sizes 11 (subtitles, labels, legend, footer), 13 (card names, group titles, diagram subtitle), 15 (reserved), 22 (title). Nothing is drawn below 11 px at 1x. Width estimates use Helvetica AFM advance widths per character, regular and bold, padded 6 percent so Inter and Segoe UI do not clip; Chrome on this workstation falls back to Liberation Sans, which is metric-identical to Arial.

### Spacing

8 px grid. Card gap 12, group padding 12, gap between nested groups 16, gap between top-level groups 24, row gap 56 (edges route through it), page margin 40, header block 72, legend 44 below the last row.

### Edges

Orthogonal, 1.6 px, 6 px rounded bends, arrowhead marker per colour. `style="dashed"` (6 4) marks tunnels, VPNs and the mesh; `dotted` exists. The router picks sides automatically (vertical when the target is above or below, horizontal otherwise) and offers hints:

- `x="left" | "right" | "mid:<id>[:+dx]" | "between:<a>,<b>"` puts the vertical trunk in the page margin, over an element, or between two elements.
- `y="gap:<row>[:+dy]" | "mid:<id>[:+dy]"` puts the horizontal run in a row gap (several edges share a gap at different `dy`).
- `s_off`, `t_off` slide the anchor along the side so several edges can enter one card.
- Labels are 11 px pills. The default position is the point where the path crosses a row gap; `label_seg` picks a segment, `label_x`, `label_y`, `label_anchor` override outright (used for margin-routed edges so the pill sits in a gap rather than off the page).

`d.bus(row, label, members)` draws a horizontal bus above a row with a stub into each member (the Corosync rings).

### Title block, legend, footer

Title 22 px, subtitle 13 px, "State as of YYYY-MM-DD" pill top right. The legend lists every family present (label via `legend_family`), the edge styles (`legend_edge`), icons (`legend_icon`) and node stripes (`legend_badge`), wrapping as needed. Footnotes then a `Source:` line naming the record paths the diagram was drawn from.

## Adding or updating a diagram

1. Copy a spec in `specs/`. Declare groups (`d.group`), cards (`d.card(group, id, name, ...)`), rows (`d.row(...)`, top to bottom), then edges. Ids are plain strings; every edge names two ids.
2. Take facts only from the current records (for the 2026-09-24 set, `.scratch/reorg/BRIEF.md`); put the record paths in `source=`.
3. Run `python3 specs/<name>.py`. Read the stderr: any `warning: truncated` means shorten the text. Run it again with `PNG=1` and open `../<name>.png`; look for cards touching borders, labels on headers, lines through cards, empty swimlanes.
4. Set `README_W=900` to also write `../<name>.900.png`, the size GitHub shows in a README column; names, logos and frames must still read there.
5. Add any new product to `logos/build_logos.py` and `logos/SOURCES.md`.

## Rebuilding everything

```
cd Assets/Diagrams/Generator
python3 build.py            # logos, every SVG into Assets/Diagrams/, validation (PNG=1 adds 2x PNGs)
python3 build.py --readme   # plus the 900 px renders
python3 build.py --check    # validation only
```

PNGs come from `google-chrome --headless=new --no-sandbox --disable-gpu --hide-scrollbars --force-device-scale-factor=2 --window-size=W,H --screenshot=...` against a one-line HTML wrapper that sets the image width, which is also how the 900 px check scales the same SVG.

## Staying GitHub-safe

- One `<svg>` with `width`, `height` and `viewBox`; GitHub scales it to the column width.
- No `<script>`, no `<foreignObject>`, no `<style>` in the outer document, no `http` reference anywhere. Logos are data URIs inside `<symbol>`; nested `<svg>` inside a data URI is fine for Chrome, Firefox, Safari and GitHub's `<img>` rendering.
- Fonts are a system stack; nothing is fetched. Widths are estimated, so a viewer with Inter sees the same layout with slightly wider glyphs inside the same padding.
- `build.py --check` parses every SVG with `xml.etree`, asserts the attributes, and rejects em dashes, MAC-like and email-like strings, so a withheld value cannot ride in through a spec.
- File sizes: 120 to 245 KiB each, dominated by the embedded logos; each logo is embedded once per diagram regardless of how many cards use it.
