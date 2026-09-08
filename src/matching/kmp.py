def build_lps(pattern):
    """
    Builds the 'longest prefix suffix' table used by KMP
    to know how far to skip ahead on a mismatch.
    """
    m = len(pattern)
    lps = [0] * m
    length = 0
    i = 1

    while i < m:
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        else:
            if length != 0:
                length = lps[length - 1]
            else:
                lps[i] = 0
                i += 1

    return lps


def kmp_search(pattern, text):
    """
    Knuth-Morris-Pratt (KMP) String Matching.
    Returns a list of starting indices where `pattern` is found in `text`.
    """
    matches = []
    n = len(text)
    m = len(pattern)

    if m == 0:
        return matches

    lps = build_lps(pattern)

    i = 0  # index for text
    j = 0  # index for pattern

    while i < n:
        if text[i] == pattern[j]:
            i += 1
            j += 1
            if j == m:
                matches.append(i - j)
                j = lps[j - 1]
        else:
            if j != 0:
                j = lps[j - 1]
            else:
                i += 1

    return matches


# Quick manual test
if __name__ == "__main__":
    sample_text = "Masarap ang pagkain sa handaan. Gusto kong kumain, ngunit kinain na ni Maria ang natitirang kanin bago pa ako makakain."
    pattern = "kain"
    result = kmp_search(pattern, sample_text)
    print(f"Pattern '{pattern}' found at positions: {result}")