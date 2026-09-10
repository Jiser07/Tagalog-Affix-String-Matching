def boyer_moore_search(pattern, text):
    """
    Boyer-Moore String Matching (bad character heuristic only).
    Returns a list of starting indices where `pattern` is found in `text`.
    """
    matches = []
    n = len(text)
    m = len(pattern)

    if m == 0:
        return matches

    # Last occurrence of each character in the pattern
    last = {}
    for i in range(m):
        last[pattern[i]] = i

    s = 0  # current alignment (shift) of the pattern against the text

    while s <= n - m:
        j = m - 1

        # Compare pattern to text from the right end of the current window
        while j >= 0 and pattern[j] == text[s + j]:
            j -= 1

        if j < 0:
            # Full match found at this alignment
            matches.append(s)
            s += 1  # move forward by 1 so overlapping matches aren't missed
        else:
            # Mismatch: use the bad character rule to decide how far to shift
            bad_char = text[s + j]
            last_occurrence = last.get(bad_char, -1)
            shift = j - last_occurrence
            s += max(1, shift)

    return matches


# Quick manual test
if __name__ == "__main__":
    print("Script started")
    sample_text = "Masarap ang pagkain sa handaan. Gusto kong kumain, ngunit kinain na ni Maria ang natitirang kanin bago pa ako makakain."
    pattern = "kain"
    print("About to search...")
    result = boyer_moore_search(pattern, sample_text)
    print(f"Pattern '{pattern}' found at positions: {result}")