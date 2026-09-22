import sys
import os
import csv
import time
from collections import defaultdict

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src", "matching"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src", "affix"))

from naive import naive_search
from kmp import kmp_search
from boyer_moore import boyer_moore_search
from affix_stripper import strip_affix, load_known_roots
from affix_aware import tokenize

DATASET_PATH = os.path.join(os.path.dirname(__file__), "..", "dataset", "root_words.csv")


def load_dataset(csv_path):
    try:
        with open(csv_path, encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        print(f"Error: dataset file not found at '{csv_path}'. Cannot run evaluation.")
        return []


def evaluate_recall(rows, known_roots):
    """
    For each unique root, checks how many of its known affixed forms are
    correctly retrieved by (a) plain substring matching and (b) affix-aware
    matching, using a small test text built from that root's own forms.
    """
    forms_by_root = defaultdict(list)
    for r in rows:
        forms_by_root[r["root"].lower()].append(r["affixed_form"].lower())

    per_root_results = []
    total_forms = 0
    total_baseline_found = 0
    total_affix_found = 0

    for root, forms in forms_by_root.items():
        test_text = " ".join(forms)
        tokens = [w for w, _ in tokenize(test_text)]

        baseline_found = sum(1 for w in tokens if root in w)
        affix_found = sum(1 for w in tokens if strip_affix(w, known_roots) == root)

        total_forms += len(forms)
        total_baseline_found += baseline_found
        total_affix_found += affix_found

        per_root_results.append({
            "root": root,
            "num_forms": len(forms),
            "baseline_found": baseline_found,
            "affix_aware_found": affix_found,
        })

    return per_root_results, total_forms, total_baseline_found, total_affix_found


def evaluate_execution_time(rows, known_roots, repeats=20):
    """
    Measures execution time of each matching approach over the full
    dataset's affixed forms joined into one larger corpus, repeated
    several times for a more stable average.
    """
    corpus = " ".join(r["affixed_form"].lower() for r in rows)
    sample_pattern = rows[0]["root"].lower()

    def timeit(func, *args):
        start = time.perf_counter()
        for _ in range(repeats):
            func(*args)
        end = time.perf_counter()
        return (end - start) / repeats

    naive_time = timeit(naive_search, sample_pattern, corpus)
    kmp_time = timeit(kmp_search, sample_pattern, corpus)
    bm_time = timeit(boyer_moore_search, sample_pattern, corpus)

    def affix_aware_over_corpus(pattern, text):
        return [w for w, _ in tokenize(text) if strip_affix(w, known_roots) == pattern]

    affix_time = timeit(affix_aware_over_corpus, sample_pattern, corpus)

    return {
        "corpus_length_chars": len(corpus),
        "naive_avg_seconds": naive_time,
        "kmp_avg_seconds": kmp_time,
        "boyer_moore_avg_seconds": bm_time,
        "affix_aware_avg_seconds": affix_time,
    }


def main():
    rows = load_dataset(DATASET_PATH)
    known_roots = load_known_roots(DATASET_PATH)

    print(f"Loaded {len(rows)} dataset rows across {len(known_roots)} unique roots.\n")

    print("=== RECALL EVALUATION ===")
    per_root, total_forms, total_baseline, total_affix = evaluate_recall(rows, known_roots)

    baseline_recall = total_baseline / total_forms * 100
    affix_recall = total_affix / total_forms * 100

    print(f"Total affixed forms tested: {total_forms}")
    print(f"Plain matching recall:      {total_baseline}/{total_forms} = {baseline_recall:.1f}%")
    print(f"Affix-aware recall:         {total_affix}/{total_forms} = {affix_recall:.1f}%")
    print(f"Improvement:                +{affix_recall - baseline_recall:.1f} percentage points\n")

    output_path = os.path.join(os.path.dirname(__file__), "..", "dataset", "recall_results.csv")
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["root", "num_forms", "baseline_found", "affix_aware_found"])
        writer.writeheader()
        writer.writerows(per_root)
    print(f"Full per-root recall breakdown saved to: {output_path}\n")

    print("=== EXECUTION TIME EVALUATION ===")
    timing = evaluate_execution_time(rows, known_roots)
    print(f"Corpus size: {timing['corpus_length_chars']} characters")
    print(f"Naive String Matching:  {timing['naive_avg_seconds']*1000:.4f} ms (avg)")
    print(f"KMP:                    {timing['kmp_avg_seconds']*1000:.4f} ms (avg)")
    print(f"Boyer-Moore:            {timing['boyer_moore_avg_seconds']*1000:.4f} ms (avg)")
    print(f"Affix-Aware Matching:   {timing['affix_aware_avg_seconds']*1000:.4f} ms (avg)")


if __name__ == "__main__":
    main()