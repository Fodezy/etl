import asyncio
import json
import logging
from urllib.parse import urljoin
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# Configure logging
token = "%(asctime)s %(levelname)-8s %(message)s"
logging.basicConfig(level=logging.INFO, format=token, datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

# Base URL and concurrency limit
PROGRAMS_URL = "https://www.uoguelph.ca/programs/undergraduate"
MAX_CONCURRENT = 5

async def fetch_calendar(meta, browser, semaphore):
    """
    Fetch the academic calendar link for a single program entry.
    """
    async with semaphore:
        ctx = await browser.new_context()
        page = await ctx.new_page()
        try:
            url = meta['page_url']
            # logger.info(f"Visiting for calendar: {url}")
            try:
                await page.goto(url, timeout=60000)
                await page.wait_for_load_state('domcontentloaded', timeout=30000)
            except PlaywrightTimeoutError:
                logger.warning(f" Timeout loading {url}")

            cal = None
            ac = page.locator("text=Academic Calendar")
            if await ac.count() > 0:
                href = await ac.first.get_attribute('href') or ''
                cal = href if href.startswith('http') else urljoin(url, href)
                # logger.info(f"  Found Academic Calendar → {cal}")
            else:
                # logger.info("  No Academic Calendar link; defaulting to page_url")
                cal = url

            return {**meta, 'calendar_url': cal}
        finally:
            await ctx.close()

async def scrape_program_list():
    """
    Scrape the UofG undergraduate programs page and enrich with calendar links concurrently.
    Returns a list of dicts with 'name', 'degree', 'types', 'page_url', and 'calendar_url'.
    """
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)

        # 1) Load tiles and collect metadata
        ctx0 = await browser.new_context()
        page0 = await ctx0.new_page()
        logger.info(f"Loading program listings: {PROGRAMS_URL}")
        await page0.goto(PROGRAMS_URL, timeout=60000)
        GRID = "div.mt-5.grid a.group"
        await page0.wait_for_selector(GRID, timeout=30000)

        program_tiles = []
        cards = await page0.query_selector_all(GRID)
        for card in cards:
            text = await card.inner_text()
            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            name   = lines[0] if len(lines)>0 else ''
            degree = lines[1] if len(lines)>1 else ''
            types  = [t.strip() for t in lines[2].split(',')] if len(lines)>2 else []
            href   = await card.get_attribute('href') or ''
            page_url = href if href.startswith('http') else urljoin(PROGRAMS_URL, href)
            program_tiles.append({'name':name,'degree':degree,'types':types,'page_url':page_url})
        await ctx0.close()

        logger.info(f"Collected metadata for {len(program_tiles)} programs.")

        # 2) Fetch calendar links in parallel
        sem   = asyncio.Semaphore(MAX_CONCURRENT)
        tasks = [asyncio.create_task(fetch_calendar(meta, browser, sem)) for meta in program_tiles]
        results = await asyncio.gather(*tasks)

        await browser.close()
        return results

if __name__ == '__main__':
    programs = asyncio.run(scrape_program_list())
    print(json.dumps(programs, indent=2))
