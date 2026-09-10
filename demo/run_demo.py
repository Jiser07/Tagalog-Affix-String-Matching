import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src", "matching"))

from naive import naive_search
from affix_aware import affix_aware_search


def run_comparison(pattern, text):
    print(f"\nSearching for root word: '{pattern}'")
    print("=" * 50)

    plain_result = naive_search(pattern, text)
    print(f"\nPlain string matching — {len(plain_result)} match(es):")
    if plain_result:
        for pos in plain_result:
            print(f"  Found at position {pos}: ...{text[max(0,pos-5):pos+len(pattern)+5]}...")
    else:
        print("  No matches found.")

    affix_result = affix_aware_search(pattern, text)
    print(f"\nAffix-aware matching — {len(affix_result)} match(es):")
    if affix_result:
        for pos, word in affix_result:
            print(f"  Found '{word}' at position {pos}")
    else:
        print("  No matches found.")

    print("\n" + "=" * 50)
    print(f"Improvement: affix-aware found {len(affix_result) - len(plain_result)} more match(es) than plain matching.\n")


if __name__ == "__main__":
    sample_text = (
        "Masarap ang pagkain sa handaan. Gusto kong kumain, ngunit kinain na ni "
        "Maria ang natitirang kanin bago pa ako makakain."
    )

    print("=== Tagalog Affix-Aware String Matching — Demo ===")
    print("Sample text:")
    print(f'"{sample_text}"\n')

    while True:
        pattern = input("Enter a Tagalog root word to search (or 'quit' to exit): ").strip()
        if pattern.lower() == "quit":
            break
        if pattern:
            pattern = pattern.lower()
            run_comparison(pattern, sample_text)