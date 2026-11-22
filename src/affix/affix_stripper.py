import csv

def load_known_roots(csv_path):
    known_roots = set()
    try:
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                known_roots.add(row["root"].strip().lower())
    except FileNotFoundError:
        print(f"Error: dataset file not found at '{csv_path}'. "
              f"Affix stripping will proceed without dictionary validation.")
    return known_roots


def strip_reduplication(word):
    """
    Attempts to remove a reduplicated first syllable, used in Tagalog to mark
    present/future (imperfective) tense (e.g. "kakain" -> "kain", "aaral" -> "aral").
    Returns the de-reduplicated candidate, or None if no pattern is found.
    """
    vowels = "aeiou"
    # Vowel-initial reduplication: single vowel repeated (e.g. "aaral" -> "aral")
    if len(word) >= 2 and word[0] == word[1] and word[0] in vowels:
        return word[1:]
    # Consonant+vowel reduplication: first two letters repeated
    # (e.g. "kakain" -> "kain", "babalot" -> "balot")
    if len(word) >= 4 and word[0:2] == word[2:4]:
        return word[2:]
    return None


def strip_affix(word, known_roots=None):
    """
    Attempts to reduce a Tagalog word to its likely root.

    1. If the word is already a known root in the dataset, return it as-is.
    2. Otherwise, generate candidates using prefix, infix, and suffix rules.
    3. If known_roots is provided, return the candidate that exists in the dataset.
    4. If no candidate matches a known root, retain the original word.
    """
    word = word.lower()

    # SAFETY CHECK 1: If word is already a known root (e.g. "kain"), do NOT strip it!
    if known_roots and word in known_roots:
        return word

    candidates = []

    def add_candidate(c):
        candidates.append(c)
        redup = strip_reduplication(c)
        if redup:
            candidates.append(redup)

    # --- Infix candidates ---
    if len(word) > 3 and word[1:3] in ("um", "in"):
        add_candidate(word[0] + word[3:])
    if len(word) > 4 and word[2:4] in ("um", "in"):
        add_candidate(word[0:2] + word[4:])

    # --- Prefix candidates ---
    for prefix in ["nag", "mag", "pag", "maka"]:
        if word.startswith(prefix + "-"):
            add_candidate(word[len(prefix) + 1:])
        elif word.startswith(prefix):
            add_candidate(word[len(prefix):])

    # --- Suffix candidates ---
    for suffix in ["in", "an"]:
        if word.endswith(suffix) and len(word) - len(suffix) >= 2:
            stripped = word[:-len(suffix)]
            if stripped.endswith("h") and len(stripped) > 1 and stripped[-2] in "aeiou":
                stripped = stripped[:-1]
            add_candidate(stripped)

    # Prefer a candidate that is an actual known root in the dataset
    if known_roots:
        for c in candidates:
            if c in known_roots:
                return c
        # SAFETY CHECK 2: If none of the candidates are real roots, do NOT return a broken fragment!
        return word

    # Fallback when no dataset is provided
    if candidates:
        return candidates[0]
    return word


# Quick manual test
if __name__ == "__main__":
    test_cases = [
        ("kumain", "kain"),
        ("kinain", "kain"),
        ("kainin", "kain"),
        ("kain", "kain"),       # Base root must remain kain!
        ("nag-aral", "aral"),
        ("mag-aral", "aral"),
        ("aral", "aral"),       # Base root must remain aral!
        ("sumulat", "sulat"),
        ("basahin", "basa"),
        ("makakain", "kain"),
    ]

    for word, expected_root in test_cases:
        result = strip_affix(word)
        status = "PASS" if result == expected_root else "FAIL"
        print(f"[{status}] strip_affix('{word}') = '{result}' (expected '{expected_root}')")