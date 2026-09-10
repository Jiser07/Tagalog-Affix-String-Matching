def strip_affix(word):
    """
    Attempts to reduce a Tagalog word to its likely root by stripping
    common prefixes, infixes, and suffixes. Stops after the first
    successful strip, since a word normally carries one affix pattern.
    """

    # --- Infixes: check first, since their position pattern is distinctive ---
    if len(word) > 3 and word[1:3] == "um":
        return word[0] + word[3:]
    if len(word) > 3 and word[1:3] == "in":
        return word[0] + word[3:]

    # --- Prefixes (handles both hyphenated and non-hyphenated forms) ---
    for prefix in ["nag", "mag", "pag", "maka"]:
        if word.startswith(prefix + "-"):
            return word[len(prefix) + 1:]
        if word.startswith(prefix):
            return word[len(prefix):]

    # --- Suffixes ---
    for suffix in ["in", "an"]:
        if word.endswith(suffix) and len(word) - len(suffix) >= 2:
            stripped = word[:-len(suffix)]
            # Linking consonant rule: e.g. "basa" + "-in" -> "basahin"
            if stripped.endswith("h") and len(stripped) > 1 and stripped[-2] in "aeiou":
                stripped = stripped[:-1]
            return stripped

    # No known affix pattern matched — assume it's already a root
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
    ]

    for word, expected_root in test_cases:
        result = strip_affix(word)
        status = "PASS" if result == expected_root else "FAIL"
        print(f"[{status}] strip_affix('{word}') = '{result}' (expected '{expected_root}')")