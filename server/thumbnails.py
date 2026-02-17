"""
Page thumbnail generator using Playwright
Captures screenshots of each page and saves as thumbnails
"""
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

THUMB_WIDTH = 400
THUMB_HEIGHT = 225  # 16:9
VIEWPORT_WIDTH = 1920
VIEWPORT_HEIGHT = 1080

async def generate_thumbnails(server_url: str = "http://localhost:8080"):
    """Generate thumbnails for all pages in pages.json"""
    pages_file = Path(__file__).parent.parent / "client" / "pages" / "pages.json"
    thumb_dir = Path(__file__).parent.parent / "client" / "thumbnails"
    thumb_dir.mkdir(exist_ok=True)

    with open(pages_file) as f:
        pages = json.load(f)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT},
            device_scale_factor=1
        )

        results = []
        for page_def in pages:
            page_id = page_def["id"]
            page_file = page_def["file"]
            url = f"{server_url}/pages/{page_file}"
            out_path = thumb_dir / f"{page_id}.png"

            try:
                page = await context.new_page()
                await page.goto(url, wait_until="networkidle", timeout=15000)
                # Give animations a moment to render
                await page.wait_for_timeout(2000)
                await page.screenshot(path=str(out_path))
                await page.close()

                # Resize with Pillow
                from PIL import Image
                img = Image.open(out_path)
                img = img.resize((THUMB_WIDTH, THUMB_HEIGHT), Image.LANCZOS)
                img.save(out_path, optimize=True)

                results.append({"id": page_id, "status": "ok", "path": f"/thumbnails/{page_id}.png"})
                print(f"  OK: {page_id}")
            except Exception as e:
                results.append({"id": page_id, "status": "error", "error": str(e)})
                print(f"  FAIL: {page_id}: {e}")

        await browser.close()

    return results


if __name__ == "__main__":
    print("Generating page thumbnails...")
    results = asyncio.run(generate_thumbnails())
    print(f"\nDone: {sum(1 for r in results if r['status'] == 'ok')}/{len(results)} succeeded")
