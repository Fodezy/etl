# File: update_golden_dataset.py
# Description: Merges newly parsed requisites into a cumulative golden dataset,
#              with options to force-update, add a specific course, remove entries,
#              or exclude courses from merging.

import json
import argparse
import sys
from pathlib import Path

# --- Path Setup ---
try:
    # Get the absolute path of the directory where this script is located.
    SCRIPT_DIR = Path(__file__).resolve().parent
except NameError:
    # Fallback for interactive environments
    SCRIPT_DIR = Path.cwd()

# Define the paths for the input (newly parsed) and the golden dataset files
NEW_DATA_PATH = SCRIPT_DIR / "parsed_requisites.json"
GOLDEN_DATASET_PATH = SCRIPT_DIR / "Golden_DataSet.json"


def load_json_file(file_path: Path) -> list:
    """Safely loads a JSON file containing a list of objects."""
    if not file_path.exists():
        print(f"ℹ️  Info: '{file_path.name}' not found. Starting with an empty dataset.")
        return []
    if file_path.stat().st_size == 0:
        print(f"ℹ️  Info: '{file_path.name}' exists but is empty. Starting with an empty dataset.")
        return []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"❌ Error: Could not read or parse '{file_path.name}'. Aborting.")
        print(f"   Error details: {e}")
        sys.exit(1)


def save_json_file(file_path: Path, data: list):
    """Safely saves a list of objects to a JSON file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        print(f"❌ Error: Could not write to '{file_path.name}'.")
        print(f"   Error details: {e}")
        sys.exit(1)


def main():
    """
    Main function to manage the golden dataset.
    """
    parser = argparse.ArgumentParser(
        description="Manage the golden dataset. By default, merges all new data from 'parsed_requisites.json'."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-a", "--add",
        type=str,
        metavar="COURSE_CODE",
        help="Merge only a specific course code from 'parsed_requisites.json'."
    )
    group.add_argument(
        "-r", "--remove",
        type=str,
        metavar="COURSE_CODE",
        help="Remove a specific course code from the golden dataset."
    )
    parser.add_argument(
        "-x", "--exclude",
        type=str,
        metavar="COURSE_CODES",
        help="Comma-separated list of course codes to exclude from merging."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="When merging, overwrite an existing course entry with the new one."
    )
    args = parser.parse_args()

    # Exclude cannot be used with removal mode
    if args.remove and args.exclude:
        print("❌ Error: --exclude cannot be used with --remove")
        sys.exit(1)

    # --- REMOVAL MODE ---
    if args.remove:
        course_to_remove = args.remove.strip()
        print(f"▶️  Attempting to remove '{course_to_remove}'...")
        golden_data_list = load_json_file(GOLDEN_DATASET_PATH)
        if not golden_data_list:
            print("Golden dataset is empty. Nothing to remove.")
            sys.exit(0)

        initial_count = len(golden_data_list)
        updated_list = [
            item for item in golden_data_list
            if item.get('course_code') != course_to_remove
        ]

        if len(updated_list) < initial_count:
            save_json_file(GOLDEN_DATASET_PATH, updated_list)
            print(f"✅ Successfully removed '{course_to_remove}'. Dataset now has {len(updated_list)} records.")
        else:
            print(f"ℹ️  Info: Course code '{course_to_remove}' not found in the golden dataset.")
        sys.exit(0)

    # --- MERGE MODE ---
    print("▶️  Starting merge process...")
    golden_data_list = load_json_file(GOLDEN_DATASET_PATH)

     # --- one-time cleanup: drop any entries without course_code ---
    cleaned = [item for item in golden_data_list if "course_code" in item]
    if len(cleaned) != len(golden_data_list):
        print(f"⚠️  Dropped {len(golden_data_list) - len(cleaned)} bad entries from golden dataset")
        golden_data_list = cleaned
        
    new_data_list = load_json_file(NEW_DATA_PATH)

    if not new_data_list:
        print("ℹ️  'parsed_requisites.json' is empty. Nothing to merge.")
        sys.exit(0)

    # NEW: build dict, but skip any entries without 'course_code'
    golden_data_dict = {}
    for item in golden_data_list:
        code = item.get('course_code')
        if not code:
            print(f"⚠️  Warning: skipping entry without 'course_code': {item}")
            continue
        golden_data_dict[code] = item
    print(f"✅ Loaded {len(golden_data_dict)} valid records from '{GOLDEN_DATASET_PATH.name}'.")


    # Determine which items from the new data to process
    if args.add:
        course_to_add = args.add.strip()
        found_item = next(
            (item for item in new_data_list if item.get('course_code') == course_to_add),
            None
        )
        if found_item:
            items_to_process = [found_item]
            print(f"Found '{course_to_add}' in 'parsed_requisites.json'. Preparing to merge.")
        else:
            print(f"❌ Error: Course code '{course_to_add}' not found in 'parsed_requisites.json'.")
            sys.exit(1)
    else:
        items_to_process = new_data_list
        print(f"Preparing to merge all {len(items_to_process)} records from 'parsed_requisites.json'.")

    # Apply exclusion list if provided
    exclude_codes = []
    if args.exclude:
        exclude_codes = [code.strip() for code in args.exclude.split(',') if code.strip()]
        if exclude_codes:
            print(f"▶️  Excluding courses: {', '.join(exclude_codes)}")
            items_to_process = [
                item for item in items_to_process
                if item.get('course_code') not in exclude_codes
            ]

    # --- Core Merge Logic ---
    records_added = 0
    records_updated = 0
    records_ignored = 0

    for new_item in items_to_process:
        course_code = new_item.get('course_code')
        if not course_code:
            continue

        if course_code in golden_data_dict:
            if args.force:
                golden_data_dict[course_code] = new_item
                records_updated += 1
            else:
                records_ignored += 1
        else:
            golden_data_dict[course_code] = new_item
            records_added += 1

    final_dataset_list = list(golden_data_dict.values())
    save_json_file(GOLDEN_DATASET_PATH, final_dataset_list)

    print("\n--- Merge Summary ---")
    print(f"New records added:           {records_added}")
    print(f"Records updated (--force):   {records_updated}")
    print(f"Duplicate records ignored:   {records_ignored}")
    print("-------------------------------")
    print(f"✅ Successfully wrote {len(final_dataset_list)} total records to '{GOLDEN_DATASET_PATH.name}'.")


if __name__ == "__main__":
    main()
