import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src", "matching"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src", "affix"))

from naive import naive_search
from affix_aware import affix_aware_search
from affix_stripper import strip_affix, load_known_roots

DATASET_PATH = os.path.join(os.path.dirname(__file__), "..", "dataset", "root_words.csv")
KNOWN_ROOTS = load_known_roots(DATASET_PATH)


def run_comparison(raw_query, text):
    derived_root = strip_affix(raw_query.lower(), KNOWN_ROOTS)
    
    print(f"\nSearching for: '{raw_query}'")
    if derived_root != raw_query.lower():
        print(f"Derived root word: '{derived_root}' (bidirectional query stemming applied)")
    print("=" * 50)

    plain_result = naive_search(raw_query.lower(), text.lower())
    print(f"\nPlain string matching - {len(plain_result)} match(es):")
    if plain_result:
        for pos in plain_result:
            print(f"  Found at position {pos}: ...{text[max(0,pos-5):pos+len(raw_query)+5]}...")
    else:
        print("  No matches found for exact substring.")

    affix_result = affix_aware_search(raw_query, text)
    print(f"\nAffix-aware matching - {len(affix_result)} match(es):")
    if affix_result:
        for pos, word in affix_result:
            print(f"  Found '{word}' at position {pos}")
    else:
        print("  No matches found.")

    print("\n" + "=" * 50)
    diff = len(affix_result) - len(plain_result)
    print(f"Improvement: affix-aware found {diff} more match(es) than plain matching.\n")


if __name__ == "__main__":
    sample_text = (
        "Masarap ang pagkain sa handaan. Gusto kong kumain, ngunit kinain na ni "
        "Maria ang natitirang kanin bago pa ako makakain."
    )

    print("=== Tagalog Affix-Aware String Matching - Demo ===")
    print("Sample text:")
    print(f'"{sample_text}"\n')

    while True:
        pattern = input("Enter a Tagalog word to search (root or inflected, or 'quit' to exit): ").strip()
        if pattern.lower() == "quit":
            break
        if pattern:
            run_comparison(pattern, sample_text)