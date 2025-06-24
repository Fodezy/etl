# extract_tags.py
from keybert import KeyBERT

# Your example course description
course_description = "This course is a detailed study of the compilation process. Topics include interpreters, overall design implementation of a compiler, techniques for parsing, building and manipulating intermediate representations of a program, implementation of important features, code generation and optimization."

# 1. Initialize the KeyBERT model
# By default, KeyBERT uses 'all-MiniLM-L6-v2' (which you've already downloaded)
# You can explicitly set it if you prefer: kw_model = KeyBERT(model='all-MiniLM-L6-v2')
print("Initializing KeyBERT model...")
kw_model = KeyBERT()
print("KeyBERT model initialized.")

# 2. Extract keywords/keyphrases
# keyphrase_ngram_range: defines the min and max length of the extracted keyphrases.
#    (1, 1) for single words, (1, 2) for single words and two-word phrases, etc.
# stop_words: removes common words (like 'the', 'is')
# top_n: number of keywords/keyphrases to extract
print(f"\nExtracting keywords for: '{course_description[:80]}...'")
keywords = kw_model.extract_keywords(
    course_description,
    keyphrase_ngram_range=(1, 3), # Look for single words, two-word, or three-word phrases
    stop_words='english',         # Filter out common English stop words
    top_n=10                      # Get the top 10 most relevant keywords/phrases
)

# 3. Print the extracted keywords
print("\nExtracted Keywords/Tags:")
for keyword, score in keywords:
    print(f"- {keyword} (Score: {score:.4f})")

# Example with different settings
print("\n--- Example with different settings (single words only) ---")
keywords_single_word = kw_model.extract_keywords(
    course_description,
    keyphrase_ngram_range=(1, 1), # Only extract single words
    stop_words='english',
    top_n=5
)
for keyword, score in keywords_single_word:
    print(f"- {keyword} (Score: {score:.4f})")