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
    present/future (imperfective) tense — e.g. "kakain" -> "kain" (from
    "kumakain"), "aaral" -> "aral" (from "nag-aaral").
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
    word = word.lower()
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

    if known_roots:
        for c in candidates:
            if c in known_roots:
                return c
    if candidates:
        return candidates[0]
    return word