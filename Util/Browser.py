import asyncio
from playwright import async_playwright
import playwright


async def init(browser: playwright.browser.Browser, url) -> playwright.page.Page:
    page = await browser.newPage()
    await page.setViewportSize(
        width=1680,
        height=1050
    )
    await page.goto(url, waitUntil="load")
    await page.emulateMedia('screen')
    return page


async def capture(page: playwright.page.Page, filename):
    height = str(await page.evaluate('''() => document.documentElement.offsetHeight ''')) + 'px'
    width = str(await page.evaluate('''() => document.documentElement.offsetWidth ''')) + 'px'

    await page.pdf(
        path=filename,
        printBackground=True,
        width=width,
        height=height
    )