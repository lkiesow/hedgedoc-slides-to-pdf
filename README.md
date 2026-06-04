# hedgedoc-slides-to-pdf

Convert a [HedgeDoc](https://hedgedoc.org/) reveal.js presentation to a multi-page PDF by automatically screenshotting each slide using a headless Firefox browser.

## How it works

The script opens the presentation URL in a headless Firefox instance (via Playwright), navigates through every slide using the `→` arrow key, screenshots each one, and stitches the images into a single PDF. It stops when the `navigate-right` button is disabled (end of deck) or the safety cap on slide count is reached.

## Requirements

- Python 3.10+
- [Playwright](https://playwright.dev/python/) with the Firefox browser
- [Pillow](https://pillow.readthedocs.io/)

Install dependencies:

```bash
python -m venv venv
. ./venv/bin/activate
pip install playwright pillow
python -m playwright install firefox
```

## Usage

```
python hedgedoc_to_pdf.py <URL> [options]
```

### Arguments

| Argument          | Description                                                                       |
|-------------------|-----------------------------------------------------------------------------------|
| `url`             | HedgeDoc presentation URL (the `/slide` suffix is added automatically if missing) |
| `-o`, `--output`  | Output PDF path (default: `<slide-id>.pdf` in the current directory)              |
| `--width`         | Viewport width in pixels (default: `1280`)                                        |
| `--height`        | Viewport height in pixels (default: `720`)                                        |
| `--wait`          | Milliseconds to wait after each slide navigation (default: `800`)                 |
| `--max-slides`    | Safety cap on the number of slides (default: `300`)                               |
| `--no-headless`   | Show the browser window while capturing (useful for debugging)                    |

### Examples

```bash
# Basic usage — output file named after the slide ID
python hedgedoc_to_pdf.py https://hedgedoc.example.com/p/my-slides

# Custom output path
python hedgedoc_to_pdf.py https://hedgedoc.example.com/p/my-slides -o slides.pdf

# HD resolution with a longer wait time for slow connections
python hedgedoc_to_pdf.py https://hedgedoc.example.com/p/my-slides --width 1920 --height 1080 --wait 1500
```

## Notes

- The progress bar and reveal.js controls are hidden in screenshots so they do not appear in the PDF.
- If slides look cut off or unrendered, try increasing `--wait`.
- Use `--no-headless` to watch the browser navigate through slides — helpful when debugging layout issues.
