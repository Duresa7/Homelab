#!/usr/bin/env python3
"""ext_rowgaps: the diagram library with a per-row vertical gap.

`Diagram(..., row_gaps={3: 48, 4: 24})` keeps `row_gap` for every row except
the listed ones, whose gap to the row below is replaced. Everything else,
including `_gap_y` and edge routing, reads `row_box` and so follows the
tightened layout automatically. Kept outside lib/diagram.py on purpose.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagram import Diagram as _Base, PALETTE, FONT, FS, text_w, fit, esc, render_png  # noqa: F401


class Diagram(_Base):
    def __init__(self, *a, row_gaps=None, **kw):
        super().__init__(*a, **kw)
        self.row_gaps = dict(row_gaps or {})

    def _gap_after(self, i):
        return self.row_gaps.get(i, self.row_gap)

    def _layout(self):
        cw = self.width - 2 * self.margin; y = self.margin + 72; self.row_box = []
        for i, row in enumerate(self.rows):
            nb = len(self.buses.get(i, [])); y += nb * 26 + (8 if nb else 0)
            its = [self.items[i2] for i2 in row["ids"]]; sz = [self._measure(it) for it in its]
            extra = cw - sum(s[0] for s in sz) - self.group_gap * (len(its) - 1)
            share = extra / len(its) if row["stretch"] or extra < 0 else 0
            x = self.margin + (0 if share else extra / 2); rh = max(s[1] for s in sz)
            for it, (w, h) in zip(its, sz): self._place(it, x, y, w + share, rh); x += w + share + self.group_gap
            self.row_box.append((y, y + rh)); y += rh + self._gap_after(i)
        self.body_bottom = y - self._gap_after(len(self.rows) - 1)
