import re
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "affix"))

from affix_stripper import strip_affix, load_known_roots
from naive import naive_search

DATASET_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "dataset", "root_words.csv")
KNOWN_ROOTS = load_known_roots(DATASET_PATH)


def tokenize(text):
    tokens = []
    for match in re.finditer(r"[A-Za-zÀ-ÿ]+", text):
        tokens.append((match.group(), match.start()))
    return tokens


def affix_aware_search(root_pattern, text):
    matches = []
    for word, position in tokenize(text):
        root = strip_affix(word.lower(), KNOWN_ROOTS)
        if root == root_pattern.lower():
            matches.append((position, word))
    return matches


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