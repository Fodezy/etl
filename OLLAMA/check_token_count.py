# File: check_token_count.py
# Description: A utility to load a prompt template and accurately count its
#              tokens using the official Llama 3 tokenizer.

import sys
from pathlib import Path
from transformers import AutoTokenizer

# --- Configuration ---
# This is the Hugging Face identifier for the Llama 3 8B model's tokenizer
TOKENIZER_NAME = "meta-llama/Meta-Llama-3-8B-Instruct"
CONTEXT_WINDOW_SIZE = 8192

# --- Path Setup ---
try:
    SCRIPT_DIR = Path(__file__).resolve().parent
except NameError:
    # Fallback for interactive environments
    SCRIPT_DIR = Path.cwd()

PROMPT_TEMPLATE_PATH = SCRIPT_DIR / "prompt_template.txt"


def main():
    """
    Loads the prompt, counts its tokens, and prints a summary.
    """
    print("▶️  Loading tokenizer...")
    try:
        # This will download the tokenizer files from Hugging Face the first time it's run
        tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_NAME)
        print("✅ Tokenizer loaded successfully.")
    except Exception as e:
        print("\n❌ Error: Could not load the tokenizer from Hugging Face.")
        print("   Please ensure you have an internet connection and have installed the required packages:")
        print("   pip install transformers torch sentencepiece")
        print(f"   Python Error: {e}")
        sys.exit(1)

    print(f"\n▶️  Reading prompt template from: '{PROMPT_TEMPLATE_PATH}'...")
    try:
        with open(PROMPT_TEMPLATE_PATH, "r", encoding="utf-8") as f:
            prompt_text = f.read()
    except FileNotFoundError:
        print(f"❌ Error: Prompt template not found at '{PROMPT_TEMPLATE_PATH}'")
        sys.exit(1)

    # Encode the text to get the list of token IDs
    tokens = tokenizer.encode(prompt_text)
    token_count = len(tokens)
    
    # Calculate the percentage of the context window used
    percentage_used = (token_count / CONTEXT_WINDOW_SIZE) * 100

    # --- Print Summary ---
    print("\n--- Prompt Context Usage ---")
    print(f"Token Count:         {token_count}")
    print(f"Max Context Window:    {CONTEXT_WINDOW_SIZE}")
    print(f"Percentage Used:     {percentage_used:.2f}%")
    print("----------------------------")

    if percentage_used > 75:
        print("\n⚠️  Warning: Your prompt is using a significant portion of the available context.")
        print("   Consider moving to a fine-tuned model in the future to reduce prompt size.")
    else:
        print("\nℹ️  Your prompt size is well within the acceptable limits.")


if __name__ == "__main__":
    # You may need to install the required libraries first:
    # pip install transformers torch sentencepiece
    main()
