import csv
import os


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


def strip_affix(word, known_roots=None):
    """
    Attempts to reduce a Tagalog word to its likely root.

    If `known_roots` (a set of lowercase root words) is provided, the function
    generates every plausible candidate root using the supported affix rules,
    then prefers whichever candidate is an actual known root. This resolves
    cases where a simple heuristic alone would guess wrong (e.g., a word that
    coincidentally contains "in" at the position the -in- infix would occupy,
    but is not actually using that infix).

    If no `known_roots` is given, or none of the candidates match a known
    root, the function falls back to a fixed priority order: infix, then
    prefix, then suffix.
    """
    word = word.lower()
    candidates = []

    # --- Infix candidates ---
    # Standard case: infix inserted after the first consonant (position 1)
    if len(word) > 3 and word[1:3] in ("um", "in"):
        candidates.append(word[0] + word[3:])
    # Consonant-cluster case: infix inserted after a 2-letter initial cluster
    # (e.g. "ng") at position 2
    if len(word) > 4 and word[2:4] in ("um", "in"):
        candidates.append(word[0:2] + word[4:])

    # --- Prefix candidates ---
    for prefix in ["nag", "mag", "pag", "maka"]:
        if word.startswith(prefix + "-"):
            candidates.append(word[len(prefix) + 1:])
        elif word.startswith(prefix):
            candidates.append(word[len(prefix):])

    # --- Suffix candidates ---
    for suffix in ["in", "an"]:
        if word.endswith(suffix) and len(word) - len(suffix) >= 2:
            stripped = word[:-len(suffix)]
            if stripped.endswith("h") and len(stripped) > 1 and stripped[-2] in "aeiou":
                stripped = stripped[:-1]
            candidates.append(stripped)

    # Prefer a candidate that is a known root, if we have a reference list
    if known_roots:
        for c in candidates:
            if c in known_roots:
                return c

    # Fallback: no dictionary match (or no dictionary given at all)
    if candidates:
        return candidates[0]

    return word


# Quick manual test against known examples
if __name__ == "__main__":
    test_cases = [
        ("kumain", "kain"),
        ("kinain", "kain"),
        ("kainin", "kain"),
        ("nag-aral", "aral"),
        ("mag-aral", "aral"),
        ("sumulat", "sulat"),
        ("basahin", "basa"),
        ("makakain", "kain"),
    ]

    for word, expected_root in test_cases:
        result = strip_affix(word)
        status = "PASS" if result == expected_root else "FAIL"
        print(f"[{status}] strip_affix('{word}') = '{result}' (expected '{expected_root}')")