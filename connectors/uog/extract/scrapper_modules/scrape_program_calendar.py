import logging
from urllib.parse import urldefrag
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

# Sections to scrape: display name -> slug prefix
SECTION_SLUGS = {
    'Overview':                   'text',
    'Major':                      'requirementstext',
    'Area of Concentration':      'areaofconcentrationtext',
    'Co-op':                      'cooptext',
    'Minor':                      'minortext',
    'Certificate':                'certificatetext',
}

async def scrape_program(program: dict, browser, semaphore) -> dict:
    """
    Scrape calendar sections for a given program using the shared Browser.

    Args:
        program: Dict containing at least 'name' and 'calendar_url'.
        browser: A playwright.async_api.Browser instance.
        semaphore: asyncio.Semaphore for concurrency control.

    Returns:
        A dict with 'name', 'degree', 'calendar_url', and a 'sections' dict.
    """
    result = {
        'name':           program.get('name'),
        'degree':         program.get('degree'),
        'calendar_url':   None,
        'calendar_error': None,
        'sections':       {}
    }

    async with semaphore:
        # Create a fresh context for isolation
        context = await browser.new_context()
        page = await context.new_page()

        try:
            cal_url = program.get('calendar_url')
            if not cal_url:
                err = 'Missing calendar_url'
                result['calendar_error'] = err
                logger.warning(f"• {err} for {program.get('name')}")
                return result

            # Strip any URL fragment
            base_url, _ = urldefrag(cal_url)
            result['calendar_url'] = base_url
            logger.info(f"Scraping '{program['name']}' at {base_url}")

            await page.goto(base_url, timeout=60000)

            # Iterate through each defined section
            for sec_name, slug in SECTION_SLUGS.items():
                tab_id = f"#{slug}tab"
                cont_id = f"#{slug}container"
                result['sections'][sec_name] = None

                try:
                    locator = page.locator(tab_id)
                    if await locator.count() == 0:
                        # logger.info(f"  • No tab '{sec_name}' for {program['name']}")
                        continue

                    # Activate tab
                    await locator.first.click(timeout=10000)
                    await page.wait_for_selector(f"div{cont_id}", timeout=20000)

                    # Expand all collapsible content blocks
                    await page.evaluate(f"""
                        document.querySelectorAll('div{cont_id} .toggle-content')
                                .forEach(el => el.style.display = 'block');
                        document.querySelectorAll('div{cont_id} button[aria-expanded="false"]')
                                .forEach(btn => btn.setAttribute('aria-expanded', 'true'));
                    """
                    )

                    container = page.locator(f"div{cont_id}")
                    if sec_name == 'Overview':
                        # Extract paragraphs
                        paras = [
                            (await p.inner_text()).strip()
                            for p in await container.locator('p').all()
                            if (await p.inner_text()).strip()
                        ]
                        # Extract collapsibles
                        groups = []
                        for wrap in await container.locator('div.toggle-wrap').all():
                            hdr = (await wrap.locator('button').first.inner_text()).strip()
                            ct = (await wrap.locator('div.toggle-content').first.inner_text()).strip()
                            groups.append({'header': hdr, 'content': ct})
                        result['sections'][sec_name] = {'paragraphs': paras, 'collapsibles': groups}
                    else:
                        text = await container.inner_text()
                        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
                        result['sections'][sec_name] = lines

                except PlaywrightTimeoutError as te:
                    msg = f"Timeout on section '{sec_name}': {te}"
                    logger.warning(msg)
                    result['sections'][f"{sec_name}_error"] = msg
                except Exception as e:
                    msg = str(e)
                    logger.error(f"Error on section '{sec_name}': {msg}")
                    result['sections'][f"{sec_name}_error"] = msg

        except Exception as e:
            msg = str(e)
            logger.error(f"Fatal error scraping {program.get('name')}: {msg}")
            result['calendar_error'] = msg

        finally:
            # Clean up this context
            await context.close()

    return result

# Note: the driver script programs_with_sections.py will import this function,
# create the playwright context and Browser instance, and manage concurrency.
