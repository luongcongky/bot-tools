from tools.base_browser import BaseBrowser
import asyncio

async def run(args):
    print("Running example task...")
    browser = BaseBrowser(headless=True)
    try:
        page = await browser.start()
        print(f"Navigating to Google...")
        await browser.navigate("https://www.google.com")
        title = await page.title()
        print(f"Page title: {title}")
    finally:
        await browser.stop()
        print("Example task finished.")
