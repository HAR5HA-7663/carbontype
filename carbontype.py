#!/usr/bin/env python3
"""
carbontype: read a text file, type it into the focused window like a human.
Use case: voice-dictated paragraph in Notes -> save to file -> focus the
target editor (Word desktop, Word for the web, Google Docs, ...) -> run
this -> char-by-char keystrokes so the editor's edit history shows real
typing rhythm, not a single paste event.
"""
from __future__ import annotations

import argparse
import random
import sys
import time
from pathlib import Path

from pynput.keyboard import Controller, Key


QWERTY_NEIGHBORS = {
    "a": "qwsz", "b": "vghn", "c": "xdfv", "d": "serfcx", "e": "wsdr",
    "f": "drtgvc", "g": "ftyhbv", "h": "gyujnb", "i": "ujko", "j": "huikmn",
    "k": "jiolm", "l": "kop", "m": "njk", "n": "bhjm", "o": "iklp",
    "p": "ol", "q": "wa", "r": "edft", "s": "awedxz", "t": "rfgy",
    "u": "yhji", "v": "cfgb", "w": "qase", "x": "zsdc", "y": "tghu",
    "z": "asx",
}

FAST_BIGRAMS = {
    "th", "he", "in", "er", "an", "re", "on", "at", "en", "nd",
    "ti", "es", "or", "te", "of", "ed", "is", "it", "al", "ar",
    "st", "to", "nt", "ng", "se", "ha", "as", "ou", "io", "le",
    "ve", "co", "me", "de", "hi", "ri", "ro", "ic", "ne", "ea",
}


def base_delay(wpm: int) -> float:
    # 5 chars per word average. seconds per char.
    return 60.0 / (wpm * 5.0)


def char_delay(prev: str, curr: str, base: float) -> float:
    # gaussian jitter around the base delay
    d = random.gauss(base, base * 0.35)
    bigram = (prev + curr).lower()
    if bigram in FAST_BIGRAMS:
        d *= 0.65
    if curr == " ":
        d *= 0.9
    if curr in ".!?":
        d *= 2.2          # end-of-sentence think
    elif curr in ",;:":
        d *= 1.6
    if prev == " " and curr.isupper():
        d *= 1.3          # capital after space
    return max(0.015, d)  # never instant


def typo_for(c: str) -> str | None:
    lo = c.lower()
    if lo not in QWERTY_NEIGHBORS:
        return None
    n = random.choice(QWERTY_NEIGHBORS[lo])
    return n.upper() if c.isupper() else n


def press(kb: Controller, c: str) -> None:
    if c == "\n":
        kb.press(Key.enter)
        kb.release(Key.enter)
    elif c == "\t":
        kb.press(Key.tab)
        kb.release(Key.tab)
    else:
        kb.type(c)


def backspace(kb: Controller, n: int = 1) -> None:
    for _ in range(n):
        kb.press(Key.backspace)
        kb.release(Key.backspace)
        time.sleep(random.uniform(0.04, 0.09))


def type_text(text: str, wpm: int, typo_rate: float, think_rate: float) -> None:
    kb = Controller()
    base = base_delay(wpm)
    prev = " "
    chars_since_think = 0

    for c in text:
        # occasional longer pause ("thinking")
        if chars_since_think > 25 and random.random() < think_rate:
            time.sleep(random.uniform(0.4, 1.4))
            chars_since_think = 0

        # occasional typo + correction (only on letters)
        if c.isalpha() and random.random() < typo_rate:
            wrong = typo_for(c)
            if wrong:
                press(kb, wrong)
                time.sleep(random.uniform(0.08, 0.28))
                # sometimes type a 2nd wrong char before noticing
                if random.random() < 0.25 and c.isalpha():
                    extra = typo_for(c) or wrong
                    press(kb, extra)
                    time.sleep(random.uniform(0.10, 0.30))
                    backspace(kb, 2)
                else:
                    backspace(kb, 1)
                time.sleep(random.uniform(0.05, 0.18))

        press(kb, c)
        time.sleep(char_delay(prev, c, base))
        prev = c
        chars_since_think += 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Type a text file like a human.")
    ap.add_argument("file", type=Path, help="Path to .txt file to type out")
    ap.add_argument("--wpm", type=int, default=60, help="Target words/min")
    ap.add_argument("--delay", type=int, default=5,
                    help="Seconds to wait before typing (focus target window)")
    ap.add_argument("--typo-rate", type=float, default=0.02,
                    help="Fraction of letters mistyped then corrected (0-1)")
    ap.add_argument("--think-rate", type=float, default=0.03,
                    help="Per-char chance of a longer pause (0-1)")
    ap.add_argument("--seed", type=int, default=None,
                    help="RNG seed for reproducible runs")
    args = ap.parse_args()

    if not args.file.is_file():
        print(f"error: not a file: {args.file}", file=sys.stderr)
        return 1

    if args.seed is not None:
        random.seed(args.seed)

    text = args.file.read_text(encoding="utf-8")
    if not text.strip():
        print("error: file is empty", file=sys.stderr)
        return 1

    chars = len(text)
    est_min = chars / (args.wpm * 5.0)
    print(f"{chars} chars, ~{est_min:.1f} min at {args.wpm} wpm")
    print(f"focus target window now. typing starts in {args.delay}s...")
    for i in range(args.delay, 0, -1):
        print(f"  {i}")
        time.sleep(1)
    print("typing...")
    try:
        type_text(text, args.wpm, args.typo_rate, args.think_rate)
    except KeyboardInterrupt:
        print("\naborted", file=sys.stderr)
        return 130
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
