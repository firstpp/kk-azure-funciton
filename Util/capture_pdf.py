import Browser
from playwright import async_playwright
import asyncio
import sys


async def capture_pdf(url, filename):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await Browser.init(browser, url)
        await Browser.capture(page, filename)
        await browser.close()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(
        capture_pdf(sys.argv[1], sys.argv[2]))
    sys.exit(0)