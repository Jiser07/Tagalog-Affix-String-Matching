import re
import sys
import os

# Allow importing from sibling folders (src/affix)
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "affix"))

from affix_stripper import strip_affix
from naive import naive_search


def tokenize(text):
    """
    Splits text into words, keeping track of where each word
    starts in the original text (needed to report accurate positions).
    """
    tokens = []
    for match in re.finditer(r"[A-Za-zÀ-ÿ]+", text):
        tokens.append((match.group(), match.start()))
    return tokens


def affix_aware_search(root_pattern, text):
    """
    Affix-aware matching: strips affixes from every word in the text,
    then checks whether the stripped root matches the search pattern.
    Returns a list of (position, original_word) tuples.
    """
    matches = []
    for word, position in tokenize(text):
        root = strip_affix(word.lower())
        if root == root_pattern.lower():
            matches.append((position, word))
    return matches


# Quick manual test — compare plain vs. affix-aware on the same text
if __name__ == "__main__":
    sample_text = "Masarap ang pagkain sa handaan. Gusto kong kumain, ngunit kinain na ni Maria ang natitirang kanin bago pa ako makakain."
    pattern = "kain"

    plain_result = naive_search(pattern, sample_text)
    affix_result = affix_aware_search(pattern, sample_text)

    print("=== Plain string matching ===")
    print(f"Found at positions: {plain_result}")

    print("\n=== Affix-aware matching ===")
    for position, word in affix_result:
        print(f"  Found '{word}' (root: '{pattern}') at position {position}")