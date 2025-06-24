#
# A specialist helper parser for processing course description text.
# It cleans the raw text, generates dense vector embeddings for semantic search,
# and extracts relevant keywords for faceted search.
#

import re
from sentence_transformers import SentenceTransformer
from keybert import KeyBERT
from typing import List, Dict, Any, Union, Tuple, cast

class DescriptionParser:
    """
    A specialist parser for course descriptions. It handles cleaning,
    vectorization, and keyword extraction, loading the ML models only once.
    """

    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initializes the parser and loads the ML models into memory.
        """
        print("Initializing DescriptionParser: Loading ML models into memory...")
        self.embedding_model = SentenceTransformer(model_name)
        self.kw_model = KeyBERT(model=self.embedding_model)  # type: ignore
        print("DescriptionParser initialized successfully. Models are ready.")
    
    # --- NEW: Private method for cleaning description text ---
    def _clean_description_text(self, text: str) -> str:
        """
        Isolates the core course description by removing extra sections
        like 'Offering(s):', 'Restriction(s):', etc.

        Args:
            text (str): The raw description string from the source.

        Returns:
            str: A cleaned string containing only the core description.
        """
        if not text or not isinstance(text, str):
            return ""

        # This regex looks for a newline followed by a common header pattern
        # (e.g., "Word(s):"). This marks the start of the extra sections.
        # \n[\s]* : a newline, followed by any whitespace
        # ([A-Za-z ]+(\(s\))?): a word or words (like "Restriction" or "Note"),
        #                       optionally followed by "(s)"
        # : : a colon
        pattern = r"\n[\s]*([A-Za-z ]+(\(s\))?:)"
        match = re.search(pattern, text)

        if match:
            # If a header is found, take everything before it.
            clean_text = text[:match.start()]
        else:
            # If no headers are found, the text is already clean.
            clean_text = text
        
        # Return the final text with any leading/trailing whitespace removed.
        return clean_text.strip()

    def parse(self, description: str) -> Dict[str, Any]:
        """
        Takes a raw course description string, cleans it, and then returns
        its vector embedding and a list of extracted keywords.
        """
        # --- UPDATED: Cleaning is now the first step ---
        clean_description = self._clean_description_text(description)

        if not clean_description or len(clean_description) < 20:
            return {"embedding": [], "keywords": []}

        # The clean description is now used for embedding and keywords
        embedding = self._generate_embedding(clean_description)
        keywords = self._extract_keywords(clean_description)
        
        return {"embedding": embedding, "keywords": keywords}

    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generates a vector embedding for the text using the loaded model.
        """
        return self.embedding_model.encode(text).tolist()

    def _extract_keywords(self, text: str) -> List[Dict[str, Union[str, float]]]:
        """
        Extracts keywords from the text using the loaded KeyBERT model.
        """
        keywords_with_scores = cast(
            List[Tuple[str, float]],
            self.kw_model.extract_keywords(
                text,
                keyphrase_ngram_range=(1, 3),
                stop_words="english",
                top_n=10,
            )
        )
        return [{"term": term, "score": round(score, 4)} for term, score in keywords_with_scores]

# This block allows you to run the file directly to test its functionality
if __name__ == '__main__':
    print("\n" + "="*50)
    print("Running a standalone test of DescriptionParser")
    print("="*50 + "\n")
    
    parser = DescriptionParser()
    
    # --- UPDATED: Using your "dirty" example as the test case ---
    raw_test_description = "This course will introduce students to the fundamental concepts and practices of Financial Accounting. Students are expected to become adept at performing the functions related to the accounting cycle, including the preparation of financial statements.\n\n\nOffering(s):\nAlso offered through Distance Education format.\nRestriction(s):\nACCT*2220. This is a Priority Access Course. Enrolment may be restricted to particular programs or specializations. See department for more information.\nDepartment(s):\nDepartment of Management"
    
    print("--- RAW INPUT ---")
    print(f"'{raw_test_description}'\n")

    # Manually call the clean method to show the intermediate step
    cleaned_text = parser._clean_description_text(raw_test_description)
    print("--- CLEANED TEXT (before processing) ---")
    print(f"'{cleaned_text}'\n")
    
    # Call the main parse method which now uses the cleaning internally
    output = parser.parse(raw_test_description)
    
    print("--- FINAL OUTPUT ---")
    print("\nKeywords Extracted (from cleaned text):")
    if output['keywords']:
        for kw in output['keywords']:
            print(f"  - Term: {kw['term']}, Score: {kw['score']}")
    else:
        print("  - No keywords extracted.")
        
    print("\nVector Embedding Generated (from cleaned text):")
    if output['embedding']:
        print(f"  - Shape: ({len(output['embedding'])},)")
        print(f"  - First 5 dimensions: {output['embedding'][:5]}")
    else:
        print("  - No embedding generated.")

    print("\n" + "="*50)
    print("Standalone test complete.")