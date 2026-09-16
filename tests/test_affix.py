import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src", "affix"))

from affix_stripper import strip_affix


def test_strip_affix():
    test_cases = [
        ("kumain", "kain"),
        ("kinain", "kain"),
        ("kainin", "kain"),
        ("nag-aral", "aral"),
        ("mag-aral", "aral"),
        ("sumulat", "sulat"),
        ("basahin", "basa"),
        ("makakain", "kain"),  # documenting current behavior, see note below
    ]

    passed = 0
    failed = 0

    for word, expected in test_cases:
        result = strip_affix(word)
        if result == expected:
            passed += 1
        else:
            failed += 1
            print(f"[FAIL] strip_affix('{word}') = '{result}', expected '{expected}'")

    print(f"\n{passed} passed, {failed} failed out of {len(test_cases)} total.")


if __name__ == "__main__":
    test_strip_affix()