import asyncio
import json
from pathlib import Path
from .scrapper_modules.scrape_program_list import scrape_program_list
async def main_async():
    # 1. Scrape the list of undergraduate programs concurrently
    print("Stage 3: Scraping program list...")
    programs = await scrape_program_list()

    # 2. Write to data/programs/program_catalog.json
    base_dir = Path(__file__).resolve().parent
    output_dir = base_dir / "data" / "programs"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "program_catalog.json"

    with output_file.open("w", encoding="utf-8") as f:
        json.dump(programs, f, ensure_ascii=False, indent=2)

    print(f"Stage 3: Saved {len(programs)} programs to {output_file}")
    return programs


def main():
    # Run the async scraper
    programs = asyncio.run(main_async())

    # Basic validation
    data_file = Path(__file__).resolve().parent / "data" / "programs" / "program_catalog.json"
    saved = json.loads(data_file.read_text(encoding="utf-8"))
    print(f"✔ program_catalog.json contains {len(saved)} entries")

if __name__ == "__main__":
    main()
