import random
import time
import re
import logging
import json
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import sync_playwright, ElementHandle, TimeoutError as PlaywrightTimeoutError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

# User-agent pool for stealth
UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    " (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15"
    " (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/118.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0",
]

# Regex to split subject text
PATTERN = re.compile(r"^(.+?)(?: \((.+)\))?$")


def launch_browser(headless: bool = True):
    """
    Launch Playwright browser with a random UA and stealth settings.
    Returns (pw, browser, page).
    """
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=headless)
    context = browser.new_context(
        user_agent=random.choice(UA_LIST),
        viewport={
            'width': random.randint(1200, 1600),
            'height': random.randint(700, 1000)
        }
    )
    page = context.new_page()
    page.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
    )
    return pw, browser, page


def load_subjects() -> list[dict]:
    """
    Scrape the UofG Courses page and return a list of subjects.
    Each entry is {'text': display_text, 'href': link_href}.
    """
    pw, browser, page = launch_browser(headless=True)
    try:
        url = "https://colleague-ss.uoguelph.ca/Student/Courses"
        # logger.info(f"Navigating to subjects page: {url}")
        page.goto(url, timeout=60000)
        page.wait_for_selector("a.esg-list-group__item", timeout=30000)
        time.sleep(random.uniform(1.0, 2.5))

        anchors = page.query_selector_all("a.esg-list-group__item")
        raw = []
        for el in anchors:
            text = el.inner_text().strip() if el.inner_text() else ""
            href = el.get_attribute("href") or ""
            raw.append({'text': text, 'href': href})
        # logger.info(f"Found {len(raw)} subjects.")
        return raw
    except PlaywrightTimeoutError as e:
        logger.error(f"Timeout loading subjects: {e}")
        return []
    except Exception as e:
        logger.error(f"Error scraping subjects: {e}", exc_info=True)
        return []
    finally:
        browser.close()
        pw.stop()


def parse_subjects(raw: list[dict]) -> list[dict]:
    """
    Normalize raw subject list into structured entries:
      {
        'text': full display text,
        'name': base name,
        'specialization': optional specialization,
        'code': subject code
      }
    """
    parsed = []
    for entry in raw:
        text = entry.get('text', '')
        href = entry.get('href', '')
        m = PATTERN.match(text)
        if m is not None:
            # here Pylance knows m is a Match, not None
            name = m.group(1)
            spec = m.group(2) or ''
        else:
            name = text
            spec = ''

        # extract code param
        query = parse_qs(urlparse(href).query)
        code = query.get('subjects', [''])[0]
        parsed.append({
            'text': text,
            'name': name,
            'specialization': spec,
            'code': code
        })
    return parsed


def load_courses(subject_text: str) -> list[dict]:
    """
    Given the exact subject display text, navigate and scrape its courses.
    Returns list of course dicts.
    """
    pw, browser, page = launch_browser(headless=True)
    courses = []
    try:
        base = "https://colleague-ss.uoguelph.ca/Student/Courses"
        # logger.info(f"Navigating to courses page: {base}")
        page.goto(base, timeout=60000)
        page.wait_for_selector("a.esg-list-group__item", timeout=30000)
        time.sleep(random.uniform(1.0, 2.5))

        # click the subject link by exact text
        locator = page.locator("a.esg-list-group__item").filter(
            has_text=re.compile(f"^{re.escape(subject_text)}$")
        )
        if locator.count() == 0:
            logger.error(f"No link found for subject: {subject_text}")
            return []
        locator.first.click()

        page.wait_for_selector("#course-resultul > li", timeout=60000)
        time.sleep(random.uniform(1.0, 2.5))

        items = page.query_selector_all("#course-resultul > li")
        for li in items:
            try:
                title_el = li.query_selector("h3 span")
                title = title_el.inner_text().strip() if title_el else "N/A"

                desc_el = li.query_selector(
                    ".search-coursedatarow .search-coursedescription"
                )
                desc = desc_el.inner_text().strip() if desc_el else ''

                def get_field(label: str) -> str:
                    sel = f".search-coursedataheader:has-text('{label}') + div span"
                    fe = li.query_selector(sel)
                    return fe.inner_text().strip() if fe else 'N/A'

                offerings    = get_field("Offering(s)")
                restrictions = get_field("Restriction(s)")
                departments  = get_field("Department(s)")
                requisites   = get_field("Requisites")
                location     = get_field("Locations")
                offered      = get_field("Offered")

                m = re.match(
                    r"^(?P<code>\S+)\s+(?P<name>.+?) \((?P<credits>[\d.]+ .*?)\)$",
                    title
                )
                code    = m.group('code')    if m else ''
                name    = m.group('name')    if m else title
                credits = m.group('credits') if m else ''

                course = {
                    'code': code,
                    'name': name,
                    'credits': credits,
                    'description': desc,
                    'offerings': offerings,
                    'restrictions': restrictions,
                    'departments': departments,
                    'requisites': requisites,
                    'location': location,
                    'offered': offered,
                    'sections': []
                }

                # expand sections
                toggle = li.query_selector("button.esg-collapsible-group__toggle")
                if toggle:
                    toggle.click()
                    li.wait_for_selector("li.search-nestedaccordionitem", timeout=10000)
                    secs = li.query_selector_all(
                        "li.search-nestedaccordionitem"
                    )
                    for sec in secs:
                        try:
                            # Section code
                            code_elem: ElementHandle | None = sec.query_selector(
                                "a.search-sectiondetailslink"
                            )
                            if code_elem is None:
                                # nothing to pull here—skip or set a default
                                continue
                            sec_code = code_elem.inner_text().strip()
                            # Section name
                            name_elem: ElementHandle | None = sec.query_selector(
                                "span[id^='section-title']"
                            )
                            if name_elem is None:
                                sec_name = ""
                            else:
                                sec_name = name_elem.inner_text().strip()
                            # Seats available
                            seats_elem: ElementHandle | None = sec.query_selector(
                                "span.search-seatsavailabletext"
                            )
                            if seats_elem is None:
                                seats = ""
                            else:
                                seats = seats_elem.inner_text().strip()

                            times = []
                            for row in sec.query_selector_all(
                                "tr.search-sectionrow"
                            ):
                                dt_el = row.query_selector(
                                    "td.search-sectiondaystime"
                                )
                                day_time = dt_el.inner_text().strip() if dt_el else 'TBD'
                                md_el = row.query_selector(
                                    "span[id*='meeting-dates']"
                                )
                                dates = md_el.inner_text().strip() if md_el else 'N/A'
                                loc_el = row.query_selector(
                                    "td.search-sectionlocations"
                                )
                                loc    = loc_el.inner_text().strip() if loc_el else 'N/A'
                                inst_el = row.query_selector(
                                    "td.search-sectioninstructormethods"
                                )
                                instr   = inst_el.inner_text().strip() if inst_el else 'N/A'
                                times.append({
                                    'day_time': day_time,
                                    'dates':    dates,
                                    'location': loc,
                                    'instructor': instr
                                })
                            course['sections'].append({
                                'section_code': sec_code,
                                'section_name': sec_name,
                                'seats':        seats,
                                'meetings':     times
                            })
                        except Exception:
                            continue

                courses.append(course)
            except Exception as e:
                logger.error(f"Course parse error: {e}")
                continue

        # logger.info(f"Completed scraping {len(courses)} courses for {subject_text}")
        return courses

    except PlaywrightTimeoutError as e:
        logger.error(f"Timeout loading courses for {subject_text}: {e}")
        return []
    except Exception as e:
        logger.error(f"Error scraping courses for {subject_text}: {e}")
        return []
    finally:
        browser.close()
        pw.stop()


# Optional quick CLI
if __name__ == '__main__':
    raw = load_subjects()
    parsed = parse_subjects(raw)
    print(json.dumps(parsed, indent=2))
