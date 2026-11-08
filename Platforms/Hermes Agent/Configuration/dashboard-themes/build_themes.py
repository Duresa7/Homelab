#!/usr/bin/env python3
"""Build the Clear dashboard themes for Hermes Agent.

Writes clear.yaml (follows the device's light or dark setting), clear-light.yaml
and clear-dark.yaml next to this script. Copy them to ~/.hermes/dashboard-themes/
on hermes-01. Edit the colors here, not in the YAML files.

Hermes derives almost every surface from two colors: `background` and `midground`
(text and controls). Utility classes inline expressions built from
`--background-base` and `--midground-base`, so `colorOverrides` has little effect.
The theme's customCSS therefore sets those variables with !important, which beats
the inline values the dashboard writes on <html>, and does it inside a
prefers-color-scheme query for the automatic theme.

Running the script also checks text contrast and exits non-zero if a pair falls
below WCAG AA (4.5:1).
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

SCHEMES = {
    "dark": {
        "background": "#1A1E25",  # blue graphite, lighter than near-black to cut halation
        "ink": "#E7EAEF",          # primary text and controls (Hermes "midground")
        "secondary": "#B9C0CB",
        "tertiary": "#959DAA",
        "accent": "#8DB7FF",       # where-am-I, keyboard focus, links
        "success": "#5FD08F",
        "warning": "#F2C14E",
        "danger": "#FF7A72",
        "series_in": "#B9C0CB",
        "series_out": "#8DB7FF",
    },
    "light": {
        "background": "#F6F7F9",
        "ink": "#1B2230",
        "secondary": "#465063",
        "tertiary": "#566070",
        "accent": "#1F5BD0",
        "success": "#126B38",
        "warning": "#8A5800",
        "danger": "#BF2B2B",
        "series_in": "#465063",
        "series_out": "#1F5BD0",
    },
}

FONT_URL = (
    "https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible+Next:wght@400;500;600;700"
    "&family=Atkinson+Hyperlegible+Mono:wght@400;600&display=swap"
)
TYPOGRAPHY = {
    "fontSans": '"Atkinson Hyperlegible Next", system-ui, -apple-system, "Segoe UI", sans-serif',
    "fontDisplay": '"Atkinson Hyperlegible Next", system-ui, -apple-system, "Segoe UI", sans-serif',
    "fontMono": '"Atkinson Hyperlegible Mono", ui-monospace, "SF Mono", Menlo, Consolas, monospace',
    "fontUrl": FONT_URL,
    "baseSize": "17px",
    "lineHeight": "1.55",
    "letterSpacing": "0",
}
LAYOUT = {"radius": "0.375rem", "density": "spacious"}

# Strong ease-out (Emil Kowalski's UI curve). Hermes has no ease-in worth keeping.
EASE_OUT = "cubic-bezier(0.23, 1, 0.32, 1)"


def tokens(name: str) -> str:
    """CSS declarations that recolor the dashboard for one scheme."""
    s = SCHEMES[name]
    lines = [
        f"color-scheme: {name};",
        f"--background-base: {s['background']} !important;",
        f"--background: {s['background']} !important;",
        f"--midground-base: {s['ink']} !important;",
        f"--midground: {s['ink']} !important;",
        f"--text-secondary: {s['secondary']} !important;",
        f"--text-tertiary: {s['tertiary']} !important;",
        f"--series-input-token: {s['series_in']} !important;",
        f"--series-output-token: {s['series_out']} !important;",
        f"--clear-accent: {s['accent']};",
        f"--clear-success: {s['success']};",
        f"--clear-warning: {s['warning']};",
        f"--clear-danger: {s['danger']};",
    ]
    if name == "dark":
        # The Models page colors its capability tags with Tailwind -600 shades meant for
        # a light page (its dark: variants never fire). Lift them for a dark page.
        lines += [
            "--color-blue-600: oklch(70.7% .165 254.624);",
            "--color-purple-600: oklch(71.4% .203 305.504);",
        ]
    else:
        # Light text shades (300/400) vanish on a light page. Map them to the status inks.
        lines += [
            f"--color-emerald-400: {s['success']};",
            f"--color-amber-300: {s['warning']};",
            f"--color-amber-400: {s['warning']};",
            f"--color-red-300: {s['danger']};",
            f"--color-red-400: {s['danger']};",
        ]
    return "\n".join("  " + line for line in lines)


SHARED_CSS = f"""
/* Type: one hyperlegible family everywhere, sentence case, no wide tracking. */
:root {{
  --font-mondwest: var(--theme-font-display) !important;
  --font-rules-expanded: var(--theme-font-display) !important;
  --font-rules-compressed: var(--theme-font-display) !important;
  --ease-in: {EASE_OUT} !important;
  --ease-out: {EASE_OUT} !important;
}}
.text-display, .uppercase {{ text-transform: none !important; }}
.text-display {{ letter-spacing: 0 !important; }}
.tracking-wide, .tracking-wider, .tracking-widest, [class*="tracking-[0."] {{
  letter-spacing: 0.01em !important;
}}
h1, h2, .font-mondwest, .font-expanded {{ letter-spacing: -0.012em; }}
.font-expanded {{ font-weight: 600; }}
/* Hermes sets labels, session titles, selects and values in monospace (font-mono, and
   font-courier, which was Courier New). The sans already tells 0/O and 1/l/I apart, so
   those move to it. Code, logs (font-mono-ui) and fields you type into stay monospace. */
.font-courier {{ font-family: var(--theme-font-mono) !important; }}
:is(.font-mono, .font-courier):not(code, pre, kbd, samp, input, textarea, pre *, code *) {{
  font-family: var(--theme-font-sans) !important;
}}
table, .font-mono, .font-mono-ui {{ font-variant-numeric: tabular-nums; }}

/* Status colors, retuned so they stay readable on either background. */
.text-success {{ color: var(--clear-success) !important; }}
.text-warning {{ color: var(--clear-warning) !important; }}
.text-warning\\/80 {{ color: color-mix(in srgb, var(--clear-warning) 80%, transparent) !important; }}
.text-warning\\/50 {{ color: color-mix(in srgb, var(--clear-warning) 60%, transparent) !important; }}
.text-destructive {{ color: var(--clear-danger) !important; }}
.text-destructive\\/70 {{ color: color-mix(in srgb, var(--clear-danger) 80%, transparent) !important; }}

/* Form fields need an edge you can see. */
.border-input {{ border-color: color-mix(in srgb, var(--midground-base) 40%, transparent) !important; }}

/* Wayfinding: the current page is marked, not hinted at with a 1px line. */
a.group\\/nav[aria-current="page"] {{
  background: color-mix(in srgb, var(--clear-accent) 13%, transparent);
  font-weight: 600;
}}
a.group\\/nav[aria-current="page"] > span.w-px {{ width: 3px; background: var(--clear-accent); }}

/* Links in chat replies, keyboard focus and text selection use the accent. */
a.text-primary.underline {{
  color: var(--clear-accent);
  text-decoration-color: color-mix(in srgb, var(--clear-accent) 45%, transparent);
}}
:focus-visible {{ outline: 2px solid var(--clear-accent) !important; outline-offset: 2px; }}
a.group\\/nav:focus-visible {{ outline-offset: -2px; }}
::selection {{ background: color-mix(in srgb, var(--clear-accent) 32%, transparent); }}

/* Press feedback: buttons answer on pointer-down. */
.transition-colors {{
  transition-property: color, background-color, border-color, outline-color,
    text-decoration-color, fill, stroke, scale !important;
}}
button:not([class*="transition"]) {{ transition: scale 140ms {EASE_OUT}; }}
button:not(:disabled):active, [role="button"]:active {{ scale: 0.97; }}

/* Reduced motion: keep fades that explain a change, drop movement. */
@media (prefers-reduced-motion: reduce) {{
  button:active, [role="button"]:active {{ scale: none !important; }}
  @keyframes toast-in {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
  @keyframes toast-out {{ from {{ opacity: 1; }} to {{ opacity: 0; }} }}
  @keyframes dialog-in {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
  @keyframes sidebar-tooltip-in {{
    from {{ opacity: 0; transform: translateY(-50%); }}
    to {{ opacity: 1; transform: translateY(-50%); }}
  }}
}}

/* Higher contrast when the device asks for it. */
@media (prefers-contrast: more) {{
  :root {{ --text-tertiary: var(--text-secondary) !important; }}
  .border-border, .border-input {{
    border-color: color-mix(in srgb, var(--midground-base) 55%, transparent) !important;
  }}
}}
@media (prefers-reduced-transparency: reduce) {{
  [class*="backdrop-blur"] {{ backdrop-filter: none !important; }}
}}
"""

HEADER = "/* Clear theme for the Hermes dashboard. Generated by build_themes.py; edit that, not this. */\n"


def css_for(mode: str) -> str:
    if mode == "auto":
        # Both blocks are scoped: an unscoped dark block would leak its dark-only
        # Tailwind remaps into light mode, since the light block doesn't reset them.
        palette_css = (
            f"@media (prefers-color-scheme: dark) {{\n:root {{\n{tokens('dark')}\n}}\n}}\n"
            f"@media (prefers-color-scheme: light) {{\n:root {{\n{tokens('light')}\n}}\n}}\n"
        )
    else:
        palette_css = f":root {{\n{tokens(mode)}\n}}\n"
    return HEADER + palette_css + SHARED_CSS


THEMES = {
    "clear": ("Clear", "Readable. Follows your device's light or dark setting.", "auto", "dark"),
    "clear-light": ("Clear Light", "Readable light theme.", "light", "light"),
    "clear-dark": ("Clear Dark", "Readable dark theme.", "dark", "dark"),
}


def q(value: str) -> str:
    """Quote a string as a YAML double-quoted scalar."""
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def theme_yaml(name: str) -> str:
    label, description, mode, palette_scheme = THEMES[name]
    s = SCHEMES[palette_scheme]
    out = [
        "# Generated by build_themes.py. Edit that file and re-run it.",
        f"name: {name}",
        f"label: {q(label)}",
        f"description: {q(description)}",
        "palette:",
        f"  background: {{ hex: {q(s['background'])}, alpha: 1 }}",
        f"  midground: {{ hex: {q(s['ink'])}, alpha: 1 }}",
        f"  foreground: {{ hex: {q(s['ink'])}, alpha: 0 }}",
        "  noiseOpacity: 0",
        "typography:",
        *[f"  {k}: {q(v)}" for k, v in TYPOGRAPHY.items()],
        "layout:",
        *[f"  {k}: {q(v)}" for k, v in LAYOUT.items()],
        "customCSS: |",
        *[("  " + line) if line else "" for line in css_for(mode).splitlines()],
    ]
    return "\n".join(out) + "\n"


# --- contrast check ---------------------------------------------------------

def _rgb(hex_: str) -> tuple[float, float, float]:
    h = hex_.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))  # type: ignore[return-value]


def _mix(a: str, b: str, pct_a: float) -> str:
    """color-mix(in srgb, a pct_a%, b)."""
    ra, rb = _rgb(a), _rgb(b)
    return "#" + "".join(f"{round((x * pct_a + y * (1 - pct_a)) * 255):02X}" for x, y in zip(ra, rb))


def _lum(hex_: str) -> float:
    def ch(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in _rgb(hex_))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(fg: str, bg: str) -> float:
    hi, lo = sorted((_lum(fg), _lum(bg)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def check() -> list[str]:
    failures = []
    for name, s in SCHEMES.items():
        surfaces = {
            "page": s["background"],
            "card": _mix(s["ink"], s["background"], 0.04),
            "muted": _mix(s["ink"], s["background"], 0.08),
            "active nav": _mix(s["accent"], s["background"], 0.13),
        }
        texts = {k: s[k] for k in ("ink", "secondary", "tertiary", "accent", "success", "warning", "danger")}
        for sname, surface in surfaces.items():
            for tname, color in texts.items():
                ratio = contrast(color, surface)
                status = "ok " if ratio >= 4.5 else "LOW"
                print(f"{status} {name:5} {tname:9} on {sname:10} {ratio:5.2f}:1")
                if ratio < 4.5:
                    failures.append(f"{name} {tname} on {sname}")
        button = contrast(s["background"], s["ink"])
        print(f"{'ok ' if button >= 4.5 else 'LOW'} {name:5} button text on ink {button:5.2f}:1")
    return failures


def main() -> int:
    failures = check()
    if failures:
        print("Contrast below 4.5:1:", ", ".join(failures), file=sys.stderr)
        return 1
    for name in THEMES:
        (HERE / f"{name}.yaml").write_text(theme_yaml(name), encoding="utf-8")
        print(f"wrote {name}.yaml")
    return 0


if __name__ == "__main__":
    sys.exit(main())
