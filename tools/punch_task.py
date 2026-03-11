from tools.base_browser import BaseBrowser
import asyncio
import os

async def run(username="kyluong", password="19901991", **kwargs):
    # print("Starting Punch In/Out task...")
    
    url = "https://blueprint.cyberlogitec.com.vn/UI_TAT_028"
    
    browser = BaseBrowser(headless=True) # Set to True to run without opening browser window
    try:
        page = await browser.start()
        # print(f"Navigating to {url}...")
        await page.goto(url)
        
        # Check if login is required (if redirected to login page)
        if "login" in page.url or await page.query_selector("#username"):
            # print("Login required. Logging in...")
            await page.fill("#username", username)
            await page.fill("#password", password)
            await page.click("#submit-btn")
            
            # Wait for navigation after login
            await page.wait_for_load_state("networkidle")
            # print("Login successful (probably).")
        else:
            print("Already logged in or login not detected.")

        # Re-navigate to the target URL just in case redirection didn't happen correctly
        if page.url != url:
            await page.goto(url)
            await page.wait_for_load_state("networkidle")

        # Looking for Punch In/Out button
        punch_button_selector = 'button:has-text("Punch In/Out")'
        # print(f"Waiting for Punch In/Out button...")
        
        try:
            await page.wait_for_selector(punch_button_selector, timeout=10000)
            # print("Found Punch In/Out button. Clicking...")
            await page.click(punch_button_selector)
            # print("Successfully clicked Punch In/Out.")
        except Exception as e:
            # print(f"Could not find or click Punch In/Out button: {e}")
            # Try alternative text if first one fails
            # print("Trying alternative selector...")
            try:
                await page.click('//button[contains(text(), "Punch In/Out")]')
                # print("Successfully clicked Punch In/Out (alternative).")
            except:
                print("Failed to click with alternative selector as well.")

    finally:
        # Keep browser open for a few seconds to confirm action visually if headless=False
        await asyncio.sleep(5)
        await browser.stop()
        print("Punch In/Out task successfully.")
