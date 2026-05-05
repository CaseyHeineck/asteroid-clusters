# CLAUDE.md — asteroid-clusters

Design decisions and project history live in the notes system at `~/Compass/CaseyHeineck/asteroid-clusters/`. Go read there if you need broader context — don't assume, look it up. For rationale behind these rules, see `~/Compass/CaseyHeineck/asteroid-clusters/asteroid-clusters-dev-context.md`.

---

## Key Files

- `PATCHNOTES.md` — append-only, authoritative record of every shipped feature. Read it when you need to know what currently exists and how it behaves.
- `git log` — the project's trajectory. Use it to understand what's been built and in what order.
- `README.md` — high-level overview of the game.

Run `/orient` at the start of a session to get up to speed.

---

## Run Commands

```
uv run python main.py   # play the game
uv run pytest -q        # run tests
```

---

## Import Organization

All imports at the top of the file — never inside functions. One continuous block, no blank lines between entries, three sections in order:

1. **Bare imports** (`import X`) — alphabetical
2. **Single-word from-imports** (`from word import Y`) — alphabetical by module
3. **Dotted from-imports** (`from word.thing import Y`) — alphabetical by full dotted path

Names within any `from X import Y` line are also alphabetical. Sections only appear if populated.

---

## Code Conventions

- **Colors**: all colors live in `constants.py`. Never hardcode an RGB tuple — always use `C.COLOR_NAME`. Add missing colors to `constants.py` first.
- **Comments**: no comments in game source files unless the WHY is genuinely non-obvious. `constants.py` and test files are the exception — use clear section headers there.

---

## Test Conventions

- One test file per source file: `tests/test_<module>.py`
- Fake/stub collaborators defined at top of test file — not mocks unless unavoidable
- Test names are the documentation — no docstrings, no inline comments explaining what a test does
- When source behavior changes, update tests in the same change
- After every change: `uv run pytest -q` must pass before considering the task done
