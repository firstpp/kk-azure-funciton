import Browser
from playwright import async_playwright
import asyncio
import sys


async def main(url: str, xpath: str) -> [str]:
    async with async_playwright() as p:
        download_links = ["https://www.uob.co.th/personal/loans/person-loan/personal-loan-uob-instant-cash.page"]

        browser = await p.chromium.launch()
        page = await Browser.init(browser, url)

        elems = await page.querySelectorAll(xpath)
        for ele in elems:
            download_links.append(await ele.getAttribute('href'))

        await browser.close()
        return '|'.join(download_links)

if __name__ == "__main__":
    print(asyncio.get_event_loop().run_until_complete(
        main(sys.argv[1], sys.argv[2])))
    sys.exit(0)
