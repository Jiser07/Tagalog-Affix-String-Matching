def naive_search(pattern, text):
    """
    Naive String Matching.
    Returns a list of starting indices where `pattern` is found in `text`.
    """
    matches = []
    n = len(text)
    m = len(pattern)

    for i in range(n - m + 1):
        if text[i:i+m] == pattern:
            matches.append(i)

    return matches


# Quick manual test — you can run this file directly to check it works
if __name__ == "__main__":
    sample_text = "Masarap ang pagkain sa handaan. Gusto kong kumain, ngunit kinain na ni Maria ang natitirang kanin bago pa ako makakain."
    pattern = "kain"
    result = naive_search(pattern, sample_text)
    print(f"Pattern '{pattern}' found at positions: {result}")