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


def affix_aware_search(root_pattern, text, algorithm=naive_search):
    """
    Affix-aware matching: strips affixes from every word in the text,
    then uses the chosen string matching algorithm (Naive, KMP, or Boyer-Moore)
    to verify whether the stripped root matches the search pattern.
    
    Returns a list of (position, original_word) tuples.
    """
    matches = []
    pattern = root_pattern.lower()

    for word, position in tokenize(text):
        root = strip_affix(word.lower(), KNOWN_ROOTS)
        
        # Run the pattern through the selected string matching algorithm
        # A non-empty match index list of identical length confirms a valid root match
        if len(root) == len(pattern) and algorithm(pattern, root):
            matches.append((position, word))

    return matches


# Quick manual test: compares all three algorithms running inside affix-aware search
if __name__ == "__main__":
    sample_text = (
        "Masarap ang pagkain sa handaan. Gusto kong kumain, ngunit "
        "kinain na ni Maria ang natitirang kanin bago pa ako makakain."
    )
    pattern = "kain"

    print("=== Plain string matching (Baseline Naive) ===")
    plain_result = naive_search(pattern, sample_text.lower())
    print(f"Found at character indices: {plain_result}\n")

    print("=== Affix-Aware Matching (Default: Naive) ===")
    naive_affix = affix_aware_search(pattern, sample_text, algorithm=naive_search)
    for pos, w in naive_affix:
        print(f"  Found '{w}' at position {pos}")

    print("\n=== Affix-Aware Matching (Using KMP) ===")
    kmp_affix = affix_aware_search(pattern, sample_text, algorithm=kmp_search)
    print(f"Total matches found via KMP: {len(kmp_affix)}")

    print("\n=== Affix-Aware Matching (Using Boyer-Moore) ===")
    bm_affix = affix_aware_search(pattern, sample_text, algorithm=boyer_moore_search)
    print(f"Total matches found via Boyer-Moore: {len(bm_affix)}")