#!/usr/bin/env python3
"""
HedgeDoc Presentation → PDF Converter
======================================
Usage:
  python hedgedoc_to_pdf.py <URL> [options]

Examples:
  python hedgedoc_to_pdf.py https://hedgedoc.example.com/p/my-slides
  python hedgedoc_to_pdf.py https://hedgedoc.example.com/p/my-slides -o output.pdf
  python hedgedoc_to_pdf.py https://hedgedoc.example.com/p/my-slides --width 1920 --height 1080
"""

import argparse
import time
from io import BytesIO

from PIL import Image
from playwright.sync_api import sync_playwright


# ── helpers ──────────────────────────────────────────────────────────────────

def ensure_slideshow_url(url: str) -> str:
    """Append /slide suffix if missing (HedgeDoc convention)."""
    url = url.rstrip("/")
    if not url.endswith("/slide"):
        url += "/slide"
    return url


def perform_login(page) -> None:
    """Click the HedgeDoc Sign In button and wait for the user to finish logging in."""
    print("🔐  Waiting for Sign in button...")
    page.wait_for_selector("button.ui-signin", timeout=15_000)
    page.click("button.ui-signin")
    print("🔑  Login dialog opened. Please log in — export starts automatically after login.")
    page.wait_for_selector("button.ui-signin", state="detached", timeout=300_000)
    print("🔓  Login detected — starting export...")


def slides_to_pdf(images: list[Image.Image], output_path: str) -> None:
    """Save a list of PIL Images as a single multi-page PDF."""
    if not images:
        raise ValueError("No images to save.")

    rgb_images = [img.convert("RGB") for img in images]
    first, rest = rgb_images[0], rgb_images[1:]
    first.save(output_path, save_all=True, append_images=rest)
    print(f"\n✅  Saved {len(images)}-slide PDF → {output_path}")


# ── core scraper ─────────────────────────────────────────────────────────────

def capture_slides(
    url: str,
    width: int = 1280,
    height: int = 720,
    wait_ms: int = 800,
    max_slides: int = 300,
    headless: bool = True,
    login: bool = False,
) -> list[Image.Image]:
    """
    Open a HedgeDoc reveal.js presentation and screenshot every slide.

    Navigation strategy:
      1. Press → to advance.
      2. After each keypress, compare the new screenshot to the previous one.
         If they are identical the presentation has looped back to the first
         slide — we stop.
      3. Hard cap at max_slides to avoid infinite loops on broken decks.
    """
    url = ensure_slideshow_url(url)
    print(f"🌐  Opening  {url}")

    screenshots: list[bytes] = []

    if login:
        headless = False

    with sync_playwright() as pw:
        browser = pw.firefox.launch(headless=headless)
        page = browser.new_page(viewport={"width": width, "height": height})

        # Load the presentation
        page.goto(url, wait_until="networkidle", timeout=30_000)
        if login:
            perform_login(page)
        time.sleep(wait_ms / 1000 * 2)          # extra settle time for JS init

        if not login and page.query_selector("button.ui-signin"):
            raise SystemExit(
                "🔒  This presentation requires login. Re-run with --login to authenticate first."
            )

        # Hide the cursor / controls that might appear in screenshots
        page.evaluate("""() => {
            const style = document.createElement('style');
            style.textContent = '.reveal .controls, .reveal .progress { display: none !important; }';
            document.head.appendChild(style);
        }""")

        def has_next_slide() -> bool:
            """Return True if the next-slide button is present and enabled."""
            btn = page.query_selector("button.navigate-right.enabled")
            return btn is not None

        slide_num = 1

        while slide_num <= max_slides:
            time.sleep(wait_ms / 1000)
            png = page.screenshot(full_page=False)
            screenshots.append(png)
            print(f"📸  Slide {slide_num}", end="\r", flush=True)

            if not has_next_slide():
                print(f"\n⛔  No more slides after slide {slide_num} — stopping.")
                break

            # Advance to the next slide
            page.keyboard.press("ArrowRight")
            slide_num += 1
        else:
            print(f"\n⚠️  Reached max_slides limit ({max_slides}).")

        browser.close()

    print(f"\n📄  Captured {len(screenshots)} slide(s).")

    # Convert raw PNG bytes → PIL Images
    return [Image.open(BytesIO(b)) for b in screenshots]


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Convert a HedgeDoc reveal.js presentation to a PDF.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("url", help="HedgeDoc presentation URL")
    p.add_argument(
        "-o", "--output",
        default="",
        help="Output PDF path (default: <slide-id>.pdf in current directory)",
    )
    p.add_argument("--width",  type=int, default=1280, help="Viewport width  (default: 1280)")
    p.add_argument("--height", type=int, default=720,  help="Viewport height (default: 720)")
    p.add_argument(
        "--wait", type=int, default=800,
        help="Milliseconds to wait after each slide navigation (default: 800)",
    )
    p.add_argument(
        "--max-slides", type=int, default=300,
        help="Safety cap on slide count (default: 300)",
    )
    p.add_argument(
        "--no-headless", action="store_true",
        help="Show the browser window while capturing (useful for debugging)",
    )
    p.add_argument(
        "--login", action="store_true",
        help="Open the browser visually, click Sign in, and wait for manual login before capturing.",
    )
    return p.parse_args()


def default_output_path(url: str) -> str:
    """Derive a sensible filename from the URL slug."""
    slug = url.rstrip("/").split("/")[-1].replace("/slide", "") or "presentation"
    if slug == "slide":
        slug = url.rstrip("/").split("/")[-2]
    return f"{slug}.pdf"


def main() -> None:
    args = parse_args()

    output = args.output or default_output_path(args.url)
    if not output.endswith(".pdf"):
        output += ".pdf"

    print(f"📐  Viewport : {args.width}×{args.height}")
    print(f"⏱   Wait     : {args.wait} ms/slide")
    print(f"💾  Output   : {output}\n")

    images = capture_slides(
        url=args.url,
        width=args.width,
        height=args.height,
        wait_ms=args.wait,
        max_slides=args.max_slides,
        headless=not args.no_headless,
        login=args.login,
    )

    slides_to_pdf(images, output)


if __name__ == "__main__":
    main()
