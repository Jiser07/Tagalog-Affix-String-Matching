"""
Showcase demo - a separate, presentation-only app.

This is NOT part of the project's core deliverable (that's demo/run_demo.py).
This file exists purely to demonstrate library catalog searching using 
root-aware affix matching, bidirectional query stemming, and synonym expansion.
"""

import sys
import os
import time
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src", "matching"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src", "affix"))

from naive import naive_search
from kmp import kmp_search
from boyer_moore import boyer_moore_search
from affix_stripper import strip_affix, load_known_roots
from affix_aware import tokenize, affix_aware_search

DATASET_PATH = os.path.join(os.path.dirname(__file__), "..", "dataset", "root_words.csv")
KNOWN_ROOTS = load_known_roots(DATASET_PATH)

# --- Synonym Dictionary ---
SYNONYM_DICTIONARY = {
    "kain": ["lamon", "tsibog"],
    "lamon": ["kain"],
    "aral": ["basa", "review"],
    "basa": ["aral"],
    "sulat": ["liham"],
    "linis": ["hugas", "punas"],
    "bili": ["gastos"]
}

# --- Default library catalog ---
DEFAULT_BOOKS = [
    "Ang Masustansyang Pagkain para sa Pamilya",
    "Sino ang Kumain ng Huling Pandesal?",
    "Ang Lihim na Kinain ng Halimaw sa Gubat",
    "Ang Halimaw na Lumamon ng Buong Bayan", 
    "Mga Pangarap ng Batang Gustong Makakain Araw-araw",
    "Paano Mag-aral ng Kasaysayan",
    "Ang Guro na Palaging Nag-aral ng Bago",
    "Kuwento ng Batang Sumulat ng Liham",
    "Ang Tula na Sinulat sa Ilalim ng Buwan",
    "Paano Magsulat ng Magandang Kwento",
    "Mga Alamat na Dapat Basahin ng mga Bata",
    "Ang Binatang Bumasa ng Mahiwagang Aklat",
    "Paano Maglinis ng Malaking Bahay",
    "Ang Hardinero na Naglinis ng Paligid",
    "Linisin Natin ang Ating Bayan",
    "Tara, Maglaro Tayo sa Labas!",
    "Ang Mga Batang Naglaro sa Ulan",
    "Saan Bumili ng Murang Sapatos?",
    "Ang Regalong Binili ni Nanay"
]

# ---------------------------------------------------------------------------
# Main Application Window (Single-Tab Library Search & Performance)
# ---------------------------------------------------------------------------
class LibrarySearchApp(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=15)
        self.books = list(DEFAULT_BOOKS)

        ttk.Label(
            self, text="Library Catalog Search - Affix, Bidirectional, and Synonym Aware",
            font=("Segoe UI", 13, "bold")
        ).pack(anchor="w")
        ttk.Label(
            self,
            text="Search any Tagalog word (root or inflected form). The system automatically "
                 "normalizes the query to its root and retrieves related book titles.",
            wraplength=680, foreground="#444"
        ).pack(anchor="w", pady=(2, 10))

        search_row = ttk.Frame(self)
        search_row.pack(fill="x", pady=(0, 8))
        self.entry = ttk.Entry(search_row, width=25, font=("Segoe UI", 11))
        self.entry.pack(side="left")
        self.entry.bind("<Return>", lambda e: self.run_search())
        
        ttk.Button(search_row, text="Search", command=self.run_search).pack(side="left", padx=8)
        ttk.Button(search_row, text="⏱️ Compare Performance", command=self.show_performance).pack(side="left")

        # Feedback label for bidirectional normalization and synonyms
        self.smart_feedback_label = ttk.Label(self, text="", font=("Segoe UI", 9, "bold"), foreground="#1565C0")
        self.smart_feedback_label.pack(anchor="w", pady=(0, 5))

        self.listbox = tk.Listbox(
            self, font=("Segoe UI", 11), height=14,
            relief="solid", borderwidth=1, activestyle="none"
        )
        self.listbox.pack(fill="both", expand=True, pady=(5, 0))
        for book in self.books:
            self.listbox.insert("end", book)

        add_row = ttk.Frame(self)
        add_row.pack(fill="x", pady=(10, 8))
        ttk.Label(add_row, text="Add a book:", font=("Segoe UI", 9, "italic")).pack(side="left")
        self.add_entry = ttk.Entry(add_row, width=35, font=("Segoe UI", 10))
        self.add_entry.pack(side="left", padx=(6, 6))
        self.add_entry.bind("<Return>", lambda e: self.add_book())
        ttk.Button(add_row, text="Add Book", command=self.add_book).pack(side="left")

        legend = ttk.Frame(self)
        legend.pack(fill="x", pady=(4, 0))
        self._legend_swatch(legend, "#FFE58A", "Found by both plain and affix-aware matching")
        self._legend_swatch(legend, "#8FE3A0", "Found ONLY by affix-aware matching (the improvement)")
        self._legend_swatch(legend, "#F4A3A3", "Found ONLY by plain matching (a coincidental substring hit)")

        self.status_label = ttk.Label(self, text="", font=("Segoe UI", 10, "italic"),
                                       foreground="#333", wraplength=680)
        self.status_label.pack(anchor="w", pady=(10, 0), fill="x")

    def _legend_swatch(self, parent, color, label):
        row = ttk.Frame(parent)
        row.pack(anchor="w", pady=1)
        swatch = tk.Label(row, bg=color, width=2)
        swatch.pack(side="left", padx=(0, 6))
        ttk.Label(row, text=label, font=("Segoe UI", 9)).pack(side="left")

    def add_book(self):
        title = self.add_entry.get().strip()
        if not title:
            return
        self.books.append(title)
        self.listbox.insert("end", title)
        self.listbox.itemconfig("end", {"bg": "white", "fg": "black"})
        self.add_entry.delete(0, "end")

    def get_search_terms(self, raw_word):
        # Bidirectional query stemming: strip query to its root first
        derived_root = strip_affix(raw_word, KNOWN_ROOTS)
        search_terms = [derived_root]
        
        # Include synonyms of the derived root
        if derived_root in SYNONYM_DICTIONARY:
            search_terms.extend(SYNONYM_DICTIONARY[derived_root])
            
        return derived_root, search_terms

    def run_search(self):
        raw_word = self.entry.get().strip().lower()

        for i in range(len(self.books)):
            self.listbox.itemconfig(i, {"bg": "white", "fg": "black"})

        if not raw_word:
            self.status_label.config(text="")
            self.smart_feedback_label.config(text="")
            return

        derived_root, search_terms = self.get_search_terms(raw_word)

        # Update UI feedback
        feedback = []
        if derived_root != raw_word:
            feedback.append(f"Query normalized: '{raw_word}' ➔ root '{derived_root}'")
        if len(search_terms) > 1:
            synonyms = ", ".join(search_terms[1:])
            feedback.append(f"Synonyms included: {synonyms}")
            
        if feedback:
            self.smart_feedback_label.config(text=" | ".join(feedback))
        else:
            self.smart_feedback_label.config(text="")

        both_count = 0
        affix_only_count = 0
        plain_only_count = 0

        for i, title in enumerate(self.books):
            # Plain matching searches strictly the exact literal string typed
            plain_hit = bool(naive_search(raw_word, title.lower()))

            # Affix-aware matching searches the normalized root and synonyms
            affix_hit = False
            for term in search_terms:
                hits = [w for w, _ in tokenize(title) if strip_affix(w.lower(), KNOWN_ROOTS) == term]
                if hits:
                    affix_hit = True
                    break

            if plain_hit and affix_hit:
                self.listbox.itemconfig(i, {"bg": "#FFE58A"})
                both_count += 1
            elif affix_hit:
                self.listbox.itemconfig(i, {"bg": "#8FE3A0"})
                affix_only_count += 1
            elif plain_hit:
                self.listbox.itemconfig(i, {"bg": "#F4A3A3"})
                plain_only_count += 1

        total_affix = both_count + affix_only_count
        total_plain = both_count + plain_only_count
        diff = total_affix - total_plain
        diff_text = f"({diff:+d} vs. plain matching)" if diff != 0 else "(same as plain matching)"
        self.status_label.config(
            text=(
                f"Plain matching found {total_plain} book(s)  |  "
                f"Affix-aware matching found {total_affix} book(s)  {diff_text}"
            )
        )

    def show_performance(self):
        raw_word = self.entry.get().strip().lower()
        if not raw_word:
            messagebox.showinfo("Notice", "Please enter a word to measure performance.")
            return

        derived_root, search_terms = self.get_search_terms(raw_word)
        corpus = " ".join(self.books).lower()
        repeats = 1000

        def time_plain_algorithm(func, term, text):
            start = time.perf_counter()
            for _ in range(repeats):
                func(term, text)
            end = time.perf_counter()
            return (end - start) * 1000 / repeats

        def time_affix_algorithm(terms, text):
            start = time.perf_counter()
            for _ in range(repeats):
                for term in terms:
                    affix_aware_search(term, text)
            end = time.perf_counter()
            return (end - start) * 1000 / repeats

        # Plain search benchmarks ONLY the raw word
        time_naive = time_plain_algorithm(naive_search, raw_word, corpus)
        time_kmp = time_plain_algorithm(kmp_search, raw_word, corpus)
        time_bm = time_plain_algorithm(boyer_moore_search, raw_word, corpus)
        
        # Affix search benchmarks the derived root and its synonyms
        time_affix = time_affix_algorithm(search_terms, corpus)
        
        plain_matches = naive_search(raw_word, corpus)
        affix_matches = []
        for term in search_terms:
            affix_matches.extend(affix_aware_search(term, corpus))
        
        diff_matches = len(affix_matches) - len(plain_matches)
        fastest_baseline = min(time_naive, time_kmp, time_bm)
        overhead = time_affix - fastest_baseline

        popup = tk.Toplevel(self)
        popup.title("⏱️ Performance Metrics")
        popup.geometry("450x380")
        popup.grab_set()

        ttk.Label(popup, text=f"Performance Results for '{raw_word}'", font=("Segoe UI", 12, "bold")).pack(pady=(15, 5))
        if derived_root != raw_word:
            ttk.Label(popup, text=f"(Derived root: '{derived_root}')", font=("Segoe UI", 9, "bold"), foreground="#1565C0").pack(pady=(0, 5))
        ttk.Label(popup, text=f"Averaged over {repeats:,} runs across the catalog corpus.", font=("Segoe UI", 9, "italic")).pack(pady=(0, 15))

        frame_base = ttk.LabelFrame(popup, text=" Baseline Matching (Plain Substring) ", padding=10)
        frame_base.pack(fill="x", padx=20, pady=5)
        
        ttk.Label(frame_base, text=f"Naive Search:\t\t{time_naive:.4f} ms").pack(anchor="w")
        ttk.Label(frame_base, text=f"Knuth-Morris-Pratt:\t{time_kmp:.4f} ms").pack(anchor="w")
        ttk.Label(frame_base, text=f"Boyer-Moore:\t\t{time_bm:.4f} ms").pack(anchor="w")
        ttk.Label(frame_base, text=f"Matches Found: {len(plain_matches)}", foreground="#D32F2F", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(5,0))

        frame_affix = ttk.LabelFrame(popup, text=" Affix-Aware Matching (Root Extraction) ", padding=10)
        frame_affix.pack(fill="x", padx=20, pady=10)

        ttk.Label(frame_affix, text=f"Affix-Aware Execution:\t{time_affix:.4f} ms").pack(anchor="w")
        ttk.Label(frame_affix, text=f"Matches Found: {len(affix_matches)}", foreground="#2E7D32", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(5,0))

        if diff_matches >= 0:
            diff_text = f"retrieved {diff_matches} MORE matches"
        else:
            diff_text = f"retrieved {abs(diff_matches)} FEWER matches"

        conclusion_text = (
            f"Conclusion:\n"
            f"Affix-aware matching {diff_text}, "
            f"with a processing overhead of {overhead:.4f} ms per run compared to the fastest baseline algorithm."
        )
        ttk.Label(popup, text=conclusion_text, wraplength=400, justify="center", font=("Segoe UI", 10, "bold"), foreground="#1565C0").pack(pady=15, padx=20)
        
        ttk.Button(popup, text="Close", command=popup.destroy).pack()

# ---------------------------------------------------------------------------
def main():
    root = tk.Tk()
    root.title("Affix-Aware Tagalog Matching - Showcase Demo")
    root.geometry("780x560")

    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    header = ttk.Frame(root, padding=(15, 12))
    header.pack(fill="x")
    ttk.Label(
        header, text="Affix-Aware String Matching - Showcase Demo",
        font=("Segoe UI", 15, "bold")
    ).pack(anchor="w")
    ttk.Label(
        header,
        text="Presentation-only extra app. The core project deliverable is demo/run_demo.py.",
        font=("Segoe UI", 9), foreground="#666"
    ).pack(anchor="w")

    app_frame = LibrarySearchApp(root)
    app_frame.pack(fill="both", expand=True, padx=10, pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()