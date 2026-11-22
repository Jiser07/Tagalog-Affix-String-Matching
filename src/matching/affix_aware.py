import re
import sys
import os

# Allow importing from sibling folders (src/affix)
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "affix"))

from affix_stripper import strip_affix, load_known_roots
from naive import naive_search
from kmp import kmp_search
from boyer_moore import boyer_moore_search

DATASET_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "dataset", "root_words.csv")
KNOWN_ROOTS = load_known_roots(DATASET_PATH)


def tokenize(text):
    """
    Splits text into words, keeping track of where each word
    starts in the original text. Treats a single hyphen inside a word
    (e.g. "mag-aral") as part of that word, not a word boundary.
    """
    tokens = []
    for match in re.finditer(r"[A-Za-zÀ-ÿ]+(?:-[A-Za-zÀ-ÿ]+)?", text):
        tokens.append((match.group(), match.start()))
    return tokens


def affix_aware_search(root_pattern, text, algorithm=naive_search, known_roots=None):
    """
    Affix-aware matching:
    1. Normalizes the search query to its root form (bidirectional / query stemming).
    2. Strips affixes from every word in the text.
    3. Uses the chosen string matching algorithm (Naive, KMP, or Boyer-Moore)
       to verify if the stripped root matches the derived query root.
    
    Returns a list of (position, original_word) tuples.
    """
    roots = known_roots if known_roots is not None else KNOWN_ROOTS
    matches = []
    
    # Normalize the query to its root if the user typed an inflected form (e.g. "kumain" -> "kain")
    pattern = strip_affix(root_pattern.lower(), roots)

    for word, position in tokenize(text):
        root = strip_affix(word.lower(), roots)
        
        # Run the pattern through the selected string matching algorithm
        if len(root) == len(pattern) and algorithm(pattern, root):
            matches.append((position, word))

    return matches


# Quick manual test
if __name__ == "__main__":
    sample_text = (
        "Masarap ang pagkain sa handaan. Gusto kong kumain, ngunit "
        "kinain na ni Maria ang natitirang kanin bago pa ako makakain."
    )
    
    # Test with an inflected query word instead of a bare root
    query = "kumain"

    print(f"Searching with inflected query: '{query}'")
    print("=" * 50)
    
    plain_result = naive_search(query, sample_text.lower())
    print(f"Plain matching finds literal '{query}' at index: {plain_result}")

    affix_result = affix_aware_search(query, sample_text)
    print(f"\nAffix-aware matching derives root and finds {len(affix_result)} related forms:")
    for pos, w in affix_result:
        print(f"  Found '{w}' at position {pos}")