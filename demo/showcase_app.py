"""
Showcase demo — a separate, presentation-only app.

This is NOT part of the project's core deliverable (that's demo/run_demo.py).
This file exists purely to make two of the project's real capabilities easier
to show live: searching Tagalog text by root word, and spotting reworded
content that shares a root even when the surface spelling changed.

Everything shown here runs on the same affix_stripper.py / affix_aware.py /
naive.py modules already built and tested — no new matching logic is added.
"""

import sys
import os
import tkinter as tk
from tkinter import ttk

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src", "matching"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src", "affix"))

from naive import naive_search
from affix_stripper import strip_affix, load_known_roots
from affix_aware import tokenize, affix_aware_search

DATASET_PATH = os.path.join(os.path.dirname(__file__), "..", "dataset", "root_words.csv")
KNOWN_ROOTS = load_known_roots(DATASET_PATH)

# --- Sample text used in the Search Demo tab ---
SEARCH_SAMPLE_TEXT = (
    "Kumain si Maria ng masarap na pagkain kahapon. Kinain din niya ang natitirang "
    "kanin. Kailangan niyang mag-aral mamayang gabi. Noong isang linggo, naglinis "
    "siya ng bahay at nagpinta ng bagong dingding. Palagi siyang ngumiti tuwing may "
    "bisita. Gusto niyang bumili ng bagong libro at sumulat ng sariling kuwento."
)

# --- Sample paired texts for the Shared Root Highlighter tab ---
TEXT_A_SAMPLE = (
    "Kumain si Maria ng masarap na pagkain kahapon. Ngumiti siya nang malapad at "
    "sumulat ng bagong tula."
)
TEXT_B_SAMPLE = (
    "Kinain ni Maria ang masarap na pagkain noong isang araw. Makangiti pa rin siya "
    "nang malapad habang sinulat niya ang bagong tula."
)


# ---------------------------------------------------------------------------
# Tab 1: Search Demo
# ---------------------------------------------------------------------------
class SearchDemoTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=15)

        ttk.Label(
            self, text="Search Demo — Plain vs. Affix-Aware Matching",
            font=("Segoe UI", 13, "bold")
        ).pack(anchor="w")

        ttk.Label(
            self,
            text="Type a Tagalog root word (try: kain, sulat, ngiti, linis, pinta, bili) "
                 "and search the text below.",
            wraplength=650, foreground="#444"
        ).pack(anchor="w", pady=(2, 10))

        search_row = ttk.Frame(self)
        search_row.pack(fill="x", pady=(0, 10))
        self.entry = ttk.Entry(search_row, width=25, font=("Segoe UI", 11))
        self.entry.pack(side="left")
        self.entry.bind("<Return>", lambda e: self.run_search())
        ttk.Button(search_row, text="Search", command=self.run_search).pack(side="left", padx=8)

        self.text_widget = tk.Text(
            self, wrap="word", height=10, font=("Segoe UI", 11),
            relief="solid", borderwidth=1, padx=10, pady=10
        )
        self.text_widget.pack(fill="both", expand=True)
        self.text_widget.insert("1.0", SEARCH_SAMPLE_TEXT)
        self.text_widget.config(state="disabled")

        self.text_widget.tag_configure("both_found", background="#FFE58A")
        self.text_widget.tag_configure("affix_only", background="#8FE3A0")

        legend = ttk.Frame(self)
        legend.pack(fill="x", pady=(10, 0))
        self._legend_swatch(legend, "#FFE58A", "Found by both plain and affix-aware matching")
        self._legend_swatch(legend, "#8FE3A0", "Found ONLY by affix-aware matching (the improvement)")

        self.status_label = ttk.Label(self, text="", font=("Segoe UI", 10, "italic"),
                                       foreground="#333", wraplength=680)
        self.status_label.pack(anchor="w", pady=(10, 0), fill="x")

    def _legend_swatch(self, parent, color, label):
        row = ttk.Frame(parent)
        row.pack(anchor="w", pady=1)
        swatch = tk.Label(row, bg=color, width=2)
        swatch.pack(side="left", padx=(0, 6))
        ttk.Label(row, text=label, font=("Segoe UI", 9)).pack(side="left")

    def run_search(self):
        word = self.entry.get().strip().lower()
        self.text_widget.config(state="normal")
        self.text_widget.tag_remove("both_found", "1.0", "end")
        self.text_widget.tag_remove("affix_only", "1.0", "end")

        if not word:
            self.text_widget.config(state="disabled")
            return

        full_text = self.text_widget.get("1.0", "end-1c")
        plain_positions = naive_search(word, full_text.lower())
        affix_matches = affix_aware_search(word, full_text)  # list of (position, word)

        plain_ranges = [(p, p + len(word)) for p in plain_positions]

        both_count = 0
        affix_only_count = 0

        for pos, matched_word in affix_matches:
            start_idx = f"1.0+{pos}c"
            end_idx = f"1.0+{pos + len(matched_word)}c"
            overlaps_plain = any(
                not (end <= pos or start >= pos + len(matched_word))
                for start, end in plain_ranges
            )
            if overlaps_plain:
                self.text_widget.tag_add("both_found", start_idx, end_idx)
                both_count += 1
            else:
                self.text_widget.tag_add("affix_only", start_idx, end_idx)
                affix_only_count += 1

        total_affix = both_count + affix_only_count
        self.status_label.config(
            text=(
                f"Plain matching found {len(plain_ranges)} match(es)  |  "
                f"Affix-aware matching found {total_affix} match(es)  "
                f"({affix_only_count} more than plain matching)"
            )
        )
        self.text_widget.config(state="disabled")


# ---------------------------------------------------------------------------
# Tab 2: Shared Root Highlighter
# ---------------------------------------------------------------------------
class SharedRootTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=15)

        ttk.Label(
            self, text="Shared Root Highlighter — Spotting Reworded Text",
            font=("Segoe UI", 13, "bold")
        ).pack(anchor="w")

        ttk.Label(
            self,
            text="Text B is a reworded version of Text A (different affixes, same roots). "
                 "Compare to see which reworded words a plain search would miss.",
            wraplength=650, foreground="#444"
        ).pack(anchor="w", pady=(2, 10))

        ttk.Label(self, text="Text A (original):", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.text_a = tk.Text(self, wrap="word", height=4, font=("Segoe UI", 11),
                               relief="solid", borderwidth=1, padx=8, pady=8)
        self.text_a.pack(fill="x", pady=(2, 10))
        self.text_a.insert("1.0", TEXT_A_SAMPLE)

        ttk.Label(self, text="Text B (reworded):", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.text_b = tk.Text(self, wrap="word", height=4, font=("Segoe UI", 11),
                               relief="solid", borderwidth=1, padx=8, pady=8)
        self.text_b.pack(fill="x", pady=(2, 10))
        self.text_b.insert("1.0", TEXT_B_SAMPLE)

        self.text_b.tag_configure("shared_root", background="#8FE3A0")

        ttk.Button(self, text="Compare", command=self.run_compare).pack(anchor="w", pady=(0, 10))

        legend = ttk.Frame(self)
        legend.pack(fill="x")
        row = ttk.Frame(legend)
        row.pack(anchor="w")
        tk.Label(row, bg="#8FE3A0", width=2).pack(side="left", padx=(0, 6))
        ttk.Label(row, text="Word in Text B whose root also appears in Text A "
                             "(found by affix-aware matching)", font=("Segoe UI", 9)).pack(side="left")

        self.status_label = ttk.Label(self, text="", font=("Segoe UI", 10, "italic"), foreground="#333")
        self.status_label.pack(anchor="w", pady=(10, 0))

    def run_compare(self):
        self.text_b.tag_remove("shared_root", "1.0", "end")

        text_a_content = self.text_a.get("1.0", "end-1c")
        text_b_content = self.text_b.get("1.0", "end-1c")

        # Roots present in Text A, and the exact word form Text A used for each
        roots_in_a = {}
        for word, pos in tokenize(text_a_content):
            root = strip_affix(word.lower(), KNOWN_ROOTS)
            if root in KNOWN_ROOTS and root not in roots_in_a:
                roots_in_a[root] = word.lower()

        text_b_lower = text_b_content.lower()
        shared_count = 0
        plain_would_catch = 0

        for word, pos in tokenize(text_b_content):
            root = strip_affix(word.lower(), KNOWN_ROOTS)
            if root in roots_in_a:
                start_idx = f"1.0+{pos}c"
                end_idx = f"1.0+{pos + len(word)}c"
                self.text_b.tag_add("shared_root", start_idx, end_idx)
                shared_count += 1

        # Fair plain-matching comparison: would searching Text A's exact
        # wording for each shared root actually find it in Text B?
        for root, original_word in roots_in_a.items():
            if original_word in text_b_lower:
                plain_would_catch += 1

        total_reworded_roots = len(roots_in_a)
        self.status_label.config(
            text=(
                f"Affix-aware matching found {shared_count} shared-root word(s) in Text B.  "
                f"Searching Text A's exact original wording would have only found "
                f"{plain_would_catch} of {total_reworded_roots} reworded root(s)."
            )
        )


# ---------------------------------------------------------------------------
def main():
    root = tk.Tk()
    root.title("Affix-Aware Tagalog Matching — Showcase Demo")
    root.geometry("750x600")

    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    header = ttk.Frame(root, padding=(15, 12))
    header.pack(fill="x")
    ttk.Label(
        header, text="Affix-Aware String Matching — Showcase Demo",
        font=("Segoe UI", 15, "bold")
    ).pack(anchor="w")
    ttk.Label(
        header,
        text="Presentation-only extra examples. The project's actual deliverable is demo/run_demo.py.",
        font=("Segoe UI", 9), foreground="#666"
    ).pack(anchor="w")

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)

    notebook.add(SearchDemoTab(notebook), text="  Search Demo  ")
    notebook.add(SharedRootTab(notebook), text="  Shared Root Highlighter  ")

    root.mainloop()


if __name__ == "__main__":
    main()
