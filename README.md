# carbontype

Replay a text file into the focused window as real keystrokes — gaussian
timing jitter, common-bigram speedups, sentence-end pauses, occasional
typos with backspace corrections. Each character becomes a discrete OS-level
keyboard event, so editors that record edit history (Word desktop, Word for
the web, Google Docs) see real typing rhythm instead of a single paste.

Built for the workflow:

> dictate a paragraph (macOS Voice Control, Whisper, etc.) into a notes app
> → save as `.txt` → focus your real editor → `carbontype essay.txt`

---

## Quickstart for AI agents

If you're an automated agent (Claude Code, Cursor, etc.) and the user gave
you this repo's URL, the entire install fits in three commands:

```bash
git clone https://github.com/<owner>/carbontype.git ~/tools/carbontype
cd ~/tools/carbontype
./setup.sh
```

`setup.sh` is idempotent. It:

1. Finds a Python ≥ 3.10 on `PATH` (installs `python@3.12` via Homebrew on
   macOS if missing).
2. Creates `./.venv`.
3. `pip install -r requirements.txt` (only `pynput`).
4. `chmod +x` the entry points.
5. Prints the macOS Accessibility permission note.

Then verify with:

```bash
./carbontype sample.txt --wpm 60 --delay 5
```

The user must focus the destination window within `--delay` seconds.

### macOS Accessibility permission (one-time, manual)

`pynput` needs Accessibility access. The first run will be blocked and macOS
will surface a permission dialog. The user must open
`System Settings → Privacy & Security → Accessibility` and enable the
terminal application that invoked the script (Terminal.app, iTerm, the
VS Code integrated terminal, etc.). This is a system-level grant and cannot
be automated by the agent.

If you (the agent) want to surface the right setting page directly, run:

```bash
open "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
```

### Linux / Windows

`pynput` supports both. On Linux it pulls in `python-xlib` automatically and
needs an X11 session (Wayland support is partial). On Windows it works
out of the box.

---

## Usage

```text
carbontype <file.txt> [--wpm N] [--delay N] [--typo-rate F]
                      [--think-rate F] [--seed N]
```

| Flag           | Default  | Description                                                |
| -------------- | -------- | ---------------------------------------------------------- |
| `--wpm`        | `60`     | Target words per minute (5 chars/word).                    |
| `--delay`      | `5`      | Seconds to wait before typing, so you can focus the target. |
| `--typo-rate`  | `0.02`   | Per-letter probability of a typo + backspace correction.   |
| `--think-rate` | `0.03`   | Per-character probability of a longer "thinking" pause.    |
| `--seed`       | random   | RNG seed for reproducible runs.                            |

Examples:

```bash
./carbontype essay.txt                        # default 60 wpm
./carbontype essay.txt --wpm 80               # faster
./carbontype essay.txt --wpm 40 --delay 8     # slower, more focus time
./carbontype essay.txt --typo-rate 0.04       # 4% typos
./carbontype essay.txt --seed 42              # reproducible
```

`Ctrl+C` aborts.

---

## How it works

### Per-character delay

Each keystroke waits `gauss(base, base * 0.35)` seconds, where
`base = 60 / (wpm * 5)`. Adjustments:

- 0.65× when the previous + current letter form a common English bigram
  (`th`, `he`, `in`, `er`, `an`, `re`, ...). Captures the "fast roll" effect.
- 2.2× after `.`, `!`, `?` — end-of-sentence think.
- 1.6× after `,`, `;`, `:` — clause break.
- 1.3× when a capital letter follows a space — shift key fumble.
- 0.9× for space — slightly faster than letters.

Floor of 15 ms so nothing fires instantly.

### Typos

With probability `typo-rate` on each letter:

1. Type a random QWERTY neighbor of the intended letter.
2. Occasionally (25 %) type a second wrong letter before noticing.
3. Pause briefly (the "oh, no" delay).
4. Backspace 1 or 2 times.
5. Pause briefly (the "find the right key" delay).
6. Type the correct letter.

### Thinking pauses

Every ~25+ chars, with probability `think-rate` per character, sleep for
`uniform(0.4, 1.4)` seconds. Simulates mid-sentence pauses, scrolling,
checking notes, etc.

---

## Files

```
carbontype/
├── carbontype       # zsh wrapper -> .venv/bin/python carbontype.py
├── carbontype.py    # main script
├── requirements.txt # pynput
├── setup.sh         # idempotent installer
├── sample.txt       # smoke-test passage
└── .gitignore
```

---

## Disclaimer

`carbontype` is a general-purpose keyboard automation tool. Use it for what
you'd use AutoHotkey, xdotool, or any macro recorder for: accessibility,
demos, dictation-rhythm reconstruction, automated testing. Do not use it to
misrepresent authorship or to bypass academic-integrity controls. The author
ships the tool; the user owns the choice.

## License

MIT
