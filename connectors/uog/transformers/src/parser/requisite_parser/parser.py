# File: src/parser/requisite_parser/parser.py
# This file orchestrates the parsing process using the Lark library.

from pathlib import Path
from typing import Any, Dict

from lark import Lark, UnexpectedInput

# Import the transformer that will convert the parse tree into JSON
from .transformer import RequisiteTransformer

# --- Lark Parser Initialization ---
# This section builds the full path to the grammar file and initializes the parser.
# This code runs only once when the module is first imported.

GRAMMAR_PATH: Path | None = None
try:
    GRAMMAR_DIR = Path(__file__).parent / "grammars"
    GRAMMAR_PATH = GRAMMAR_DIR / "requisite.lark"
    
    with open(GRAMMAR_PATH, "r", encoding="utf-8") as f:
        grammar_definition = f.read()

    # The parser instance is created here.
    # We now add the 'import_paths' argument to tell Lark where to find 'common.lark'.
    PARSER = Lark(
        grammar_definition,
        parser="earley",
        start="start",
        import_paths=[str(GRAMMAR_DIR)]  # <--- THIS IS THE FIX
    )

except FileNotFoundError:
    # This is a critical error. If the grammar can't be found, the parser can't function.
    print(f"FATAL: Grammar file not found at path: {GRAMMAR_PATH}")
    PARSER = None
# --- End Initialization ---

def run_parser(chunk: str, debug: bool = False) -> Dict[str, Any]:
    """
    Takes a single prerequisite chunk and parses it into a structured object.
    
    Args:
        chunk: A string representing one independent prerequisite.
        debug: A flag to enable verbose logging.

    Returns:
        A dictionary representing the logical structure of the chunk.
    """
    if PARSER is None:
        return {"type": "PARSE_ERROR", "error": "Parser not initialized: grammar file missing.", "chunk": chunk}

    try:
        # The parsing happens here. Lark reads the text and applies the grammar rules.
        # We convert the chunk to uppercase to make the grammar case-insensitive.
        parse_tree = PARSER.parse(chunk.upper())

        # The transformer walks the generated tree and converts it to our desired JSON format.
        json_output = RequisiteTransformer(debug=debug).transform(parse_tree)
        
        return json_output

    except UnexpectedInput as e:
        # This block catches errors where the input string does not match the grammar.
        if debug:
            print(f"DEBUG: [run_parser] Parse failed for chunk: '{chunk}'. Error: {e}")
        
        return {
            "type": "PARSE_ERROR",
            "error": "Input does not match grammar rules.",
            "chunk": chunk
        }
