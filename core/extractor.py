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
        print("\n--- Starting Parse Stage ---")
        self._run_parse()
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

        # wait out any “waiting room”
        max_wait_ms   = 5 * 60_000
        poll_interval = 30_000
        elapsed       = 0
        while True:
            if await page.locator('section#course-results').count() > 0:
                break
            if elapsed >= max_wait_ms:
                print("  ! TIMEOUT waiting for course-results. Skipping this seed.")
                await context.close()
                return
            print("  • Detected waiting room. Reloading in 30 s…")
            await page.wait_for_timeout(poll_interval)
            elapsed += poll_interval
            try:
                await page.reload(wait_until='networkidle', timeout=30000)
            except PlaywrightError:
                pass

        print("  ✓ course-results is present.")
        page_count = 1

        while True:
            print(f"  • Capturing page {page_count} of {seed_url}")

            # 1) Expand all toggles once:
            try:
                await page.wait_for_timeout(1000)
                toggles = page.locator('button.esg-collapsible-group__toggle')
                count = await toggles.count()
                if count:
                    print(f"    ⟳ Expanding {count} toggles")
                    for i in range(count):
                        btn = toggles.nth(i)
                        try:
                            await btn.scroll_into_view_if_needed()
                            await btn.click(force=True, timeout=5000)
                        except PlaywrightError as e:
                            print(f"      ! toggle #{i} click failed: {e}")
                    await page.wait_for_timeout(500)
                else:
                    print("    • No toggles found on this page")
            except PlaywrightError as e:
                print(f"    ! Error during toggle expansion: {e}")

            # 2) Then perform any additional configured clicks:
            for action in self.config.get("capture_actions", []):
                if action.get("action") == "click":
                    sel = action["selector"]
                    pause_ms = action.get("wait_after_ms", 250)
                    try:
                        await page.wait_for_selector(sel, timeout=3000)
                        elems = page.locator(sel)
                        cnt = await elems.count()
                        print(f"    ⟳ Clicking {cnt} × {sel}")
                        for j in range(cnt):
                            await elems.nth(j).click(timeout=3000)
                            await page.wait_for_timeout(pause_ms)
                    except PlaywrightError:
                        print(f"    ! failed configured click on {sel}")

            # 3) Save HTML
            await page.wait_for_timeout(300)
            html = await page.content()
            fn   = self._url_to_filename(seed_url, page_count)
            (self.capture_path / fn).write_text(html, encoding='utf-8')
            print(f"    ✓ saved {fn}")

            # 4) Pagination
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

    def _run_parse(self):
        html_files = list(self.capture_path.glob("*.html"))
        print(f"Parsing {len(html_files)} HTML files…")
        rules = self.config['parser_rules'].get('course')
        if not rules:
            print("  ! ERROR: no 'course' rules in parser_rules")
            return

        for html_file in html_files:
            print(f"▶ parsing {html_file.name}")
            soup  = BeautifulSoup(html_file.read_text(encoding='utf-8'), 'html.parser')
            nodes = soup.select(rules['list_selector'])
            print(f"  • found {len(nodes)} courses")
            for node in nodes:
                parsed = self._parse_html_node(node, rules['extractors'])
                code   = parsed.get('full_title', 'UNKNOWN').split()[0].replace('*','_')
                outfn  = f"{code}.json"
                (self.raw_output_path / outfn).write_text(
                    json.dumps(parsed, indent=2, ensure_ascii=False),
                    encoding='utf-8'
                )

    def _get_page_type(self, url: str) -> Optional[str]:
        for pat in self.config.get('page_type_patterns', []):
            if re.search(pat['url_pattern'], url):
                return pat['type']
        return None

    def _parse_html_node(self, node: Tag, rules: Dict[str, Any]) -> Dict[str, Any]:
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
