#!/usr/bin/env python3
"""Rebuild every diagram: normalise logos, run each spec, render PNGs, validate.

    python3 build.py            # logos and SVGs into Assets/Diagrams/ (PNG=1 for 2x PNGs beside them)
    python3 build.py --readme   # also render each SVG scaled to 900 px (README width)
    python3 build.py --check    # validate Assets/Diagrams/*.svg only, no rendering
"""
import glob, os, re, subprocess, sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
FORBIDDEN = ("<script", "<foreignObject", 'href="http', "url(http", chr(0x2014))

def check(path):
    svg = open(path, encoding="utf-8").read()
    root = ET.fromstring(svg)
    for bad in FORBIDDEN:
        assert bad not in svg, f"{path}: contains {bad!r}"
    for attr in ("width", "height", "viewBox"):
        assert root.get(attr), f"{path}: missing {attr}"
    text = re.sub(r"data:image/svg\+xml;base64,[A-Za-z0-9+/=]+", "", svg)  # the embedded logos are not prose
    assert not re.search(r"\b([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}\b", text), f"{path}: MAC-like string"
    assert not re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text), f"{path}: email-like string"
    print(f"ok  {os.path.relpath(path, HERE)}  {root.get('width')}x{root.get('height')}  {len(svg) // 1024} KiB")

def main(argv):
    if "--check" not in argv:
        subprocess.run([sys.executable, os.path.join(HERE, "logos", "build_logos.py")], check=True, stdout=subprocess.DEVNULL)
        env = dict(os.environ, README_W="900" if "--readme" in argv else "0")
        for spec in sorted(glob.glob(os.path.join(HERE, "specs", "*.py"))):
            subprocess.run([sys.executable, spec], check=True, env=env)
    for svg in sorted(glob.glob(os.path.join(HERE, "..", "*.svg"))):
        check(svg)

if __name__ == "__main__":
    main(sys.argv[1:])
