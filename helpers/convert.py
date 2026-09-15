#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "resvg-py",
#     "fonttools",
#     "brotli",
# ]
# ///
"""Render a diagram-design HTML file's inline <svg> to a PNG next to it.

Playwright/Chromium needs system shared libraries (libnspr4, libnss3,
libX11, ...) that this sandbox has no root access to install, so this
renders the extracted <svg> block directly with resvg (a dependency-free
Rust SVG renderer) instead of screenshotting a real browser.

resvg does not fetch @font-face rules from Google Fonts, so the fonts the
diagram references (Geist, Geist Mono) are downloaded once, converted from
woff2 to ttf (resvg doesn't read woff2), and cached under
``helpers/.fonts/`` for reuse on later runs.
"""

import re
import sys
import urllib.request
from pathlib import Path

FONTS_DIR = Path(__file__).parent / ".fonts"
FONT_CSS_URL = (
    "https://fonts.googleapis.com/css2"
    "?family=Geist:wght@400;500;600"
    "&family=Geist+Mono:wght@400;500;600"
)
# A browser User-Agent is required or Google Fonts serves legacy .ttf-only CSS.
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"


def _download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read()


def ensure_fonts() -> list[str]:
    """Return local .ttf paths for every font-weight the diagram uses, downloading
    and converting them from Google Fonts on first run, then caching."""
    ttf_paths = sorted(FONTS_DIR.glob("*.ttf"))
    if ttf_paths:
        return [str(p) for p in ttf_paths]

    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    css = _download(FONT_CSS_URL).decode("utf-8")
    woff2_urls = sorted(set(re.findall(r"https://[^)]+\.woff2", css)))
    if not woff2_urls:
        raise RuntimeError("Could not find any @font-face woff2 URLs in Google Fonts CSS")

    from fontTools.ttLib import TTFont

    for url in woff2_urls:
        woff2_bytes = _download(url)
        woff2_path = FONTS_DIR / Path(url).name
        woff2_path.write_bytes(woff2_bytes)

        font = TTFont(str(woff2_path))
        font.flavor = None
        ttf_path = woff2_path.with_suffix(".ttf")
        font.save(str(ttf_path))
        woff2_path.unlink()
        ttf_paths.append(ttf_path)

    return [str(p) for p in ttf_paths]


def extract_svg(html: str) -> str:
    match = re.search(r"<svg[\s\S]*?</svg>", html)
    if not match:
        raise ValueError("No <svg> block found in the source HTML")
    return match.group(0)


def convert_html_to_png(html_path: Path, png_path: Path, scale: float = 2.0) -> None:
    import resvg_py

    svg = extract_svg(html_path.read_text(encoding="utf-8"))
    font_files = ensure_fonts()

    png_bytes = resvg_py.svg_to_bytes(
        svg_string=svg,
        zoom=scale,
        font_files=font_files,
        skip_system_fonts=True,
    )
    png_path.write_bytes(bytes(png_bytes))


if __name__ == "__main__":
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("docs/architecture-diagram.html")
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(".png")
    convert_html_to_png(src, out)
    size_kb = out.stat().st_size / 1024
    print(f"Wrote {out} ({size_kb:.0f} KB)")
