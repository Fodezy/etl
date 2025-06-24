#!/usr/bin/env python3
# etl/core/extractor.py

import asyncio
import json
import re
import time
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.parse import quote_plus, unquote_plus

from bs4 import BeautifulSoup, Tag
from playwright.async_api import async_playwright, Error as PlaywrightError
from concurrent.futures import ThreadPoolExecutor # <-- NEW IMPORT
from tqdm import tqdm                             # <-- NEW IMPORT

from .utils.config_loader import load_config

class AsyncCoreExtractor:
    """
    An async, parallel extractor driven by a school-specific configuration.
    Launches one Chromium process and spawns a BrowserContext+Page per seed URL,
    all captured concurrently.
    """

    def __init__(self, school_name: str):
        print(f"Initializing AsyncCoreExtractor for '{school_name}'...")
        self.school_name = school_name
        self.config = load_config(school_name)

        project_root = Path(__file__).resolve().parent.parent
        self.capture_path    = project_root / "output" / self.school_name / "html"
        self.raw_output_path = project_root / "connectors" / self.school_name / "extract" / "raw"

        self.capture_path.mkdir(parents=True, exist_ok=True)
        self.raw_output_path.mkdir(parents=True, exist_ok=True)
        print("Output directories ready.")

    async def run(self) -> str:
        print("\n--- Starting Async Capture Stage ---")
        await self._run_capture()
        print("\n--- Starting Parse Stage (Multithreaded) ---")
        self._run_parse() # This will now run with threads
        print("\n--- Extraction Complete ---")
        return str(self.raw_output_path)

    def _url_to_filename(self, url: str, page_num: int) -> str:
        sanitized = quote_plus(url.split('?')[-1])
        return f"{sanitized}_page_{page_num}.html"

    def _filename_to_url(self, filename: str) -> str:
        return unquote_plus(filename.split('_page_')[0])

    async def _run_capture(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            seeds = self.config.get("seed_urls", [])
            tasks = [self._capture_seed(browser, url) for url in seeds]
            await asyncio.gather(*tasks)
            await browser.close()

    async def _capture_seed(self, browser, seed_url: str):
        print(f"→ [Task] {seed_url}")
        context = await browser.new_context()
        page    = await context.new_page()

        try:
            await page.goto(seed_url, wait_until='networkidle', timeout=30000)
        except PlaywrightError as e:
            print(f"  ! ERROR navigating to {seed_url}: {e}")
            await context.close()
            return

        print("  • Waiting for course results or virtual queue...")
        try:
            await page.wait_for_selector(
                'section#course-results',
                timeout=600_000
            )
            print("  ✓ course-results is present.")
        except PlaywrightError:
            print(f"  ! TIMEOUT waiting for course-results after 10 minutes. Skipping this seed.")
            await context.close()
            return

        page_count = 1

        while True:
            print(f"  • Capturing page {page_count} of {seed_url}")
            try:
                toggles = page.locator('button.esg-collapsible-group__toggle')
                count = await toggles.count()
                if count:
                    print(f"    ⟳ Expanding {count} toggles...")
                    for i in range(count):
                        try:
                            btn = toggles.nth(i)
                            await btn.scroll_into_view_if_needed(timeout=5000)
                            await btn.click(force=True, timeout=5000)
                            await page.wait_for_timeout(250)
                        except PlaywrightError:
                            print(f"      ! Could not click toggle #{i}. Stopping expansion for this page.")
                            break
                else:
                    print("    • No toggles found on this page")
            except PlaywrightError as e:
                print(f"    ! A critical error occurred during toggle expansion: {e}")

            for action in self.config.get("capture_actions", []):
                # ... (rest of capture logic is unchanged)
                pass

            await page.wait_for_timeout(300)
            html = await page.content()
            fn   = self._url_to_filename(seed_url, page_count)
            (self.capture_path / fn).write_text(html, encoding='utf-8')
            print(f"    ✓ saved {fn}")

            next_sel = self.config.get("pagination_next_selector")
            if not next_sel:
                break
            next_btn = page.locator(next_sel)
            if await next_btn.is_visible() and await next_btn.is_enabled():
                print("    → clicking ‘Next Page’")
                await next_btn.click()
                await page.wait_for_load_state('networkidle', timeout=10000)
                page_count += 1
                await page.wait_for_timeout(500)
            else:
                break
        await context.close()

    # --- NEW WORKER METHOD for multithreading ---
    def _parse_single_file(self, html_file: Path):
        """Parses one HTML file to extract course data."""
        try:
            rules = self.config['parser_rules']['course']
            soup = BeautifulSoup(html_file.read_text(encoding='utf-8'), 'html.parser')
            nodes = soup.select(rules['list_selector'])
            
            for node in nodes:
                parsed = self._parse_html_node(node, rules['extractors'])
                code = parsed.get('full_title', 'UNKNOWN').split()[0].replace('*', '_')
                outfn = f"{code}.json"
                (self.raw_output_path / outfn).write_text(
                    json.dumps(parsed, indent=2, ensure_ascii=False),
                    encoding='utf-8'
                )
        except Exception as e:
            print(f"Error parsing {html_file.name}: {e}")

    # --- UPDATED METHOD to use the thread pool ---
    def _run_parse(self):
        """Finds all HTML files and processes them in parallel using a thread pool."""
        html_files = list(self.capture_path.glob("*.html"))
        if not html_files:
            print("No HTML files found to parse.")
            return
            
        print(f"Found {len(html_files)} HTML files to parse.")
        
        # Use a ThreadPoolExecutor to parse files in parallel
        # max_workers can be tuned, but 10 is a reasonable default for I/O-heavy tasks
        with ThreadPoolExecutor(max_workers=10) as executor:
            # tqdm will create a progress bar for the parsing process
            list(tqdm(executor.map(self._parse_single_file, html_files), total=len(html_files), desc="Parsing HTML Files"))
        
        print("Finished parsing all files.")

    def _get_page_type(self, url: str) -> Optional[str]:
        # ... (this method is unchanged)
        for pat in self.config.get('page_type_patterns', []):
            if re.search(pat['url_pattern'], url):
                return pat['type']
        return None

    def _parse_html_node(self, node: Tag, rules: Dict[str, Any]) -> Dict[str, Any]:
        # ... (this method is unchanged)
        data: Dict[str, Any] = {}
        for field, rule in rules.items():
            if rule.get('type') == 'list':
                data[field] = [
                    self._parse_html_node(child, rule['extractors'])
                    for child in node.select(rule['list_selector'])
                ]
            elif 'css' in rule:
                el = node.select_one(rule['css'])
                data[field] = el.get_text(strip=True) if el else None
        return data

if __name__ == "__main__":
    extractor = AsyncCoreExtractor("uog")
    asyncio.run(extractor.run())