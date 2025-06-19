import json
from pathlib import Path

def convert_json_to_jsonl(input_filename, output_filename):
    """
    Reads a file containing a JSON array of objects and writes the data
    to a new file in JSON Lines (.jsonl) format.

    Args:
        input_filename (str): The path to the source JSON file.
        output_filename (str): The path for the destination .jsonl file.
    """
    try:
        # Open the source JSON file and load the entire array
        with open(input_filename, 'r', encoding='utf-8') as f_in:
            data = json.load(f_in)
        
        # Ensure the loaded data is a list
        if not isinstance(data, list):
            print(f"Error: The input file '{input_filename}' does not contain a JSON array (list).")
            return

        # Open the destination .jsonl file for writing
        with open(output_filename, 'w', encoding='utf-8') as f_out:
            # Iterate through each object in the list
            for record in data:
                # Convert the Python dictionary object back to a JSON string
                # Ensure no extra newlines are added by dumps, we'll add our own
                json_string = json.dumps(record, separators=(',', ':'))
                
                # Write the JSON string as a single line, followed by a newline character
                f_out.write(json_string + '\n')

        print(f"Successfully converted '{input_filename}' to '{output_filename}'.")
        print(f"Total records written: {len(data)}")

    except FileNotFoundError:
        print(f"Error: The input file '{input_filename}' was not found.")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{input_filename}'. Please ensure it is a valid JSON file.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# --- Main Execution ---
if __name__ == "__main__":
    # Determine the directory this script lives in:
    script_dir = Path(__file__).resolve().parent

    # Build full paths to the source and destination:
    source_json_file      = script_dir / 'Golden_DataSet_Final.json'
    destination_jsonl_file = script_dir / 'Golden_DataSet_Final.jsonl'

    convert_json_to_jsonl(str(source_json_file), str(destination_jsonl_file))

