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
import random
import tkinter as tk
from tkinter import ttk

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src", "matching"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src", "affix"))

from naive import naive_search
from affix_stripper import strip_affix, load_known_roots
from affix_aware import tokenize, affix_aware_search

DATASET_PATH = os.path.join(os.path.dirname(__file__), "..", "dataset", "root_words.csv")
KNOWN_ROOTS = load_known_roots(DATASET_PATH)

# --- Preset sample texts for the Search Demo tab: (text, suggested search words) ---
SEARCH_PRESETS = [
    (
        "Kumain si Maria ng masarap na pagkain kahapon. Kinain din niya ang natitirang "
        "kanin. Kailangan niyang mag-aral mamayang gabi. Noong isang linggo, naglinis "
        "siya ng bahay at nagpinta ng bagong dingding. Palagi siyang ngumiti tuwing may "
        "bisita. Gusto niyang bumili ng bagong libro at sumulat ng sariling kuwento.",
        "kain, aral, linis, pinta, ngiti, bili, sulat"
    ),
    (
        "Nag-akay si Pedro ng kanyang lolo papunta sa simbahan. Nag-atras ang sasakyan "
        "dahil sa makipot na daan. Nag-asar ang mga bata sa kanilang kapatid. Nag-uwi "
        "kami ng maraming pasalubong galing sa probinsya.",
        "akay, atras, asar, uwi"
    ),
    (
        "Bumalot si Ana ng regalo para sa kaibigan niya. Binalot niya ito gamit ang "
        "makulay na papel. Bumantay si Tomas sa bahay buong gabi. Binantay ng aso ang "
        "bakuran mula sa mga magnanakaw. Nag-ulit ang guro ng leksyon kanina.",
        "balot, bantay, ulit"
    ),
]

# --- Preset paired texts for the Shared Root Highlighter tab: (text_a, text_b) ---
SHARED_ROOT_PRESETS = [
    (
        "Kumain si Maria ng masarap na pagkain kahapon. Ngumiti siya nang malapad at "
        "sumulat ng bagong tula.",
        "Kinain ni Maria ang masarap na pagkain noong isang araw. Makangiti pa rin siya "
        "nang malapad habang sinulat niya ang bagong tula."
    ),
    (
        "Bumalot si Ana ng regalo kahapon. Bumantay si Tomas sa tindahan buong araw. "
        "Nag-ulit ang guro ng leksyon kanina.",
        "Binalot ni Ana ang regalo noong isang araw. Binantay ni Tomas ang tindahan sa "
        "buong araw. Nag-ulit din ang guro ng parehong leksyon."
    ),
]


# ---------------------------------------------------------------------------
# Tab 1: Search Demo
# ---------------------------------------------------------------------------
class SearchDemoTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=15)
        self.custom_mode = False
        self.current_index = None

        ttk.Label(
            self, text="Search Demo — Plain vs. Affix-Aware Matching",
            font=("Segoe UI", 13, "bold")
        ).pack(anchor="w")

        button_row = ttk.Frame(self)
        button_row.pack(fill="x", pady=(8, 6))
        ttk.Button(button_row, text="🔄 Refresh Paragraph", command=self.refresh_paragraph).pack(side="left")
        ttk.Button(button_row, text="✏️ Write My Own", command=self.use_custom_text).pack(side="left", padx=(8, 0))

        self.hint_label = ttk.Label(self, text="", font=("Segoe UI", 9, "italic"), foreground="#666")
        self.hint_label.pack(anchor="w", pady=(0, 10))

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

        self.text_widget.tag_configure("both_found", background="#FFE58A")
        self.text_widget.tag_configure("affix_only", background="#8FE3A0")
        self.text_widget.tag_configure("plain_only", background="#F4A3A3")

        legend = ttk.Frame(self)
        legend.pack(fill="x", pady=(10, 0))
        self._legend_swatch(legend, "#FFE58A", "Found by both plain and affix-aware matching")
        self._legend_swatch(legend, "#8FE3A0", "Found ONLY by affix-aware matching (the improvement)")
        self._legend_swatch(legend, "#F4A3A3", "Found ONLY by plain matching (a coincidental substring hit)")

        self.status_label = ttk.Label(self, text="", font=("Segoe UI", 10, "italic"),
                                       foreground="#333", wraplength=680)
        self.status_label.pack(anchor="w", pady=(10, 0), fill="x")

        self.refresh_paragraph()

    def _legend_swatch(self, parent, color, label):
        row = ttk.Frame(parent)
        row.pack(anchor="w", pady=1)
        swatch = tk.Label(row, bg=color, width=2)
        swatch.pack(side="left", padx=(0, 6))
        ttk.Label(row, text=label, font=("Segoe UI", 9)).pack(side="left")

    def refresh_paragraph(self):
        self.custom_mode = False
        choices = [i for i in range(len(SEARCH_PRESETS)) if i != self.current_index]
        self.current_index = random.choice(choices) if choices else 0
        text, suggested_words = SEARCH_PRESETS[self.current_index]

        self.text_widget.config(state="normal")
        self.text_widget.delete("1.0", "end")
        self.text_widget.insert("1.0", text)
        self.text_widget.tag_remove("both_found", "1.0", "end")
        self.text_widget.tag_remove("affix_only", "1.0", "end")
        self.text_widget.config(state="disabled")

        self.hint_label.config(text=f"Try searching: {suggested_words}")
        self.status_label.config(text="")

    def use_custom_text(self):
        self.custom_mode = True
        self.text_widget.config(state="normal")
        self.text_widget.delete("1.0", "end")
        self.text_widget.tag_remove("both_found", "1.0", "end")
        self.text_widget.tag_remove("affix_only", "1.0", "end")
        self.hint_label.config(text="Type or paste your own Tagalog text below, then search it.")
        self.status_label.config(text="")

    def run_search(self):
        word = self.entry.get().strip().lower()
        self.text_widget.config(state="normal")
        self.text_widget.tag_remove("both_found", "1.0", "end")
        self.text_widget.tag_remove("affix_only", "1.0", "end")
        self.text_widget.tag_remove("plain_only", "1.0", "end")

        if not word:
            if not self.custom_mode:
                self.text_widget.config(state="disabled")
            return

        full_text = self.text_widget.get("1.0", "end-1c")
        plain_positions = naive_search(word, full_text.lower())
        affix_matches = affix_aware_search(word, full_text)
        all_tokens = tokenize(full_text)

        plain_ranges = [(p, p + len(word)) for p in plain_positions]
        affix_ranges = [(pos, pos + len(matched_word)) for pos, matched_word in affix_matches]

        def overlaps(range_a, range_b):
            return not (range_a[1] <= range_b[0] or range_a[0] >= range_b[1])

        both_count = 0
        affix_only_count = 0

        for pos, matched_word in affix_matches:
            span = (pos, pos + len(matched_word))
            start_idx = f"1.0+{span[0]}c"
            end_idx = f"1.0+{span[1]}c"
            if any(overlaps(span, pr) for pr in plain_ranges):
                self.text_widget.tag_add("both_found", start_idx, end_idx)
                both_count += 1
            else:
                self.text_widget.tag_add("affix_only", start_idx, end_idx)
                affix_only_count += 1

        # Plain-only matches: a plain hit whose containing word wasn't also
        # found by affix-aware matching (e.g. a coincidental substring inside
        # an unrelated or unsupported word form, like "punta" inside "papunta").
        plain_only_count = 0
        for p_start, p_end in plain_ranges:
            if any(overlaps((p_start, p_end), ar) for ar in affix_ranges):
                continue  # already covered by an affix-aware match, not plain-only
            enclosing = next((t for t in all_tokens if t[1] <= p_start < t[1] + len(t[0])), None)
            if enclosing:
                token_word, token_start = enclosing
                span = (token_start, token_start + len(token_word))
            else:
                span = (p_start, p_end)
            start_idx = f"1.0+{span[0]}c"
            end_idx = f"1.0+{span[1]}c"
            self.text_widget.tag_add("plain_only", start_idx, end_idx)
            plain_only_count += 1

        total_affix = both_count + affix_only_count
        diff = total_affix - len(plain_ranges)
        diff_text = f"({diff:+d} vs. plain matching)" if diff != 0 else "(same as plain matching)"
        extra = f"  |  {plain_only_count} plain-only hit(s) shown in red" if plain_only_count else ""
        self.status_label.config(
            text=(
                f"Plain matching found {len(plain_ranges)} match(es)  |  "
                f"Affix-aware matching found {total_affix} match(es)  {diff_text}{extra}"
            )
        )
        if not self.custom_mode:
            self.text_widget.config(state="disabled")


# ---------------------------------------------------------------------------
# Tab 2: Shared Root Highlighter
# ---------------------------------------------------------------------------
class SharedRootTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=15)
        self.custom_mode = False
        self.current_index = None

        ttk.Label(
            self, text="Shared Root Highlighter — Spotting Reworded Text",
            font=("Segoe UI", 13, "bold")
        ).pack(anchor="w")

        button_row = ttk.Frame(self)
        button_row.pack(fill="x", pady=(8, 6))
        ttk.Button(button_row, text="🔄 Refresh Paragraph", command=self.refresh_paragraph).pack(side="left")
        ttk.Button(button_row, text="✏️ Write My Own", command=self.use_custom_text).pack(side="left", padx=(8, 0))

        ttk.Label(
            self,
            text="Text B is a reworded version of Text A (different affixes, same roots). "
                 "Compare to see which reworded words a plain search would miss.",
            wraplength=650, foreground="#444"
        ).pack(anchor="w", pady=(8, 10))

        ttk.Label(self, text="Text A (original):", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.text_a = tk.Text(self, wrap="word", height=4, font=("Segoe UI", 11),
                               relief="solid", borderwidth=1, padx=8, pady=8)
        self.text_a.pack(fill="x", pady=(2, 10))

        ttk.Label(self, text="Text B (reworded):", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.text_b = tk.Text(self, wrap="word", height=4, font=("Segoe UI", 11),
                               relief="solid", borderwidth=1, padx=8, pady=8)
        self.text_b.pack(fill="x", pady=(2, 10))

        self.text_b.tag_configure("shared_root", background="#8FE3A0")
        self.text_b.tag_configure("identical_word", background="#FFE58A")

        ttk.Button(self, text="Compare", command=self.run_compare).pack(anchor="w", pady=(0, 10))

        legend = ttk.Frame(self)
        legend.pack(fill="x")
        row1 = ttk.Frame(legend)
        row1.pack(anchor="w", pady=1)
        tk.Label(row1, bg="#8FE3A0", width=2).pack(side="left", padx=(0, 6))
        ttk.Label(row1, text="Reworded into a different form, still caught (only affix-aware "
                              "matching would find this)", font=("Segoe UI", 9)).pack(side="left")
        row2 = ttk.Frame(legend)
        row2.pack(anchor="w", pady=1)
        tk.Label(row2, bg="#FFE58A", width=2).pack(side="left", padx=(0, 6))
        ttk.Label(row2, text="Same exact word repeated from Text A (plain matching would "
                              "find this too)", font=("Segoe UI", 9)).pack(side="left")

        self.status_label = ttk.Label(self, text="", font=("Segoe UI", 10, "italic"),
                                       foreground="#333", wraplength=680)
        self.status_label.pack(anchor="w", pady=(10, 0), fill="x")

        self.refresh_paragraph()

    def refresh_paragraph(self):
        self.custom_mode = False
        choices = [i for i in range(len(SHARED_ROOT_PRESETS)) if i != self.current_index]
        self.current_index = random.choice(choices) if choices else 0
        text_a, text_b = SHARED_ROOT_PRESETS[self.current_index]

        self.text_a.delete("1.0", "end")
        self.text_b.delete("1.0", "end")
        self.text_a.insert("1.0", text_a)
        self.text_b.insert("1.0", text_b)
        self.text_b.tag_remove("shared_root", "1.0", "end")
        self.text_b.tag_remove("identical_word", "1.0", "end")
        self.status_label.config(text="")

    def use_custom_text(self):
        self.custom_mode = True
        self.text_a.delete("1.0", "end")
        self.text_b.delete("1.0", "end")
        self.text_b.tag_remove("shared_root", "1.0", "end")
        self.text_b.tag_remove("identical_word", "1.0", "end")
        self.status_label.config(text="Type your own Text A and Text B, then click Compare.")

    def run_compare(self):
        self.text_b.tag_remove("shared_root", "1.0", "end")
        self.text_b.tag_remove("identical_word", "1.0", "end")

        text_a_content = self.text_a.get("1.0", "end-1c")
        text_b_content = self.text_b.get("1.0", "end-1c")

        roots_in_a = {}
        for word, pos in tokenize(text_a_content):
            root = strip_affix(word.lower(), KNOWN_ROOTS)
            if root in KNOWN_ROOTS and root not in roots_in_a:
                roots_in_a[root] = word.lower()

        reworded_count = 0
        identical_count = 0

        for word, pos in tokenize(text_b_content):
            root = strip_affix(word.lower(), KNOWN_ROOTS)
            if root in roots_in_a:
                start_idx = f"1.0+{pos}c"
                end_idx = f"1.0+{pos + len(word)}c"
                if word.lower() == roots_in_a[root]:
                    self.text_b.tag_add("identical_word", start_idx, end_idx)
                    identical_count += 1
                else:
                    self.text_b.tag_add("shared_root", start_idx, end_idx)
                    reworded_count += 1

        total_shared = reworded_count + identical_count
        self.status_label.config(
            text=(
                f"{total_shared} shared-root word(s) found in Text B — "
                f"{reworded_count} reworded into a different form (green, only affix-aware "
                f"catches these), {identical_count} repeated exactly from Text A (yellow, "
                f"plain matching would catch these too)."
            )
        )


# ---------------------------------------------------------------------------
def main():
    root = tk.Tk()
    root.title("Affix-Aware Tagalog Matching — Showcase Demo")
    root.geometry("780x640")

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