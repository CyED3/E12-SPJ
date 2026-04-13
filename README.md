# Chomsky – code security analyzer

This tool scans source and configuration text for risky patterns (hardcoded passwords, API keys, and similar issues). Under the hood it uses ideas from **formal languages**: regular expressions for detection, **finite automata** to label a file as Safe / Needs Review / Security Violation, and **finite-state transducers** to suggest safer rewrites. The CFG-style view of “well-formed secure configuration” is written up under `docs/`.

---

## Where things live (course checklist)

| Requirement | Location |
|-------------|----------|
| Markdown docs under `docs/` | [docs/README.md](docs/README.md) and the numbered notes |
| Setup, dependencies, usage | This file + [docs/USER_GUIDE.md](docs/USER_GUIDE.md) |
| Grammar and automata design | [docs/04_cfg_grammar.md](docs/04_cfg_grammar.md), [docs/02_automata.md](docs/02_automata.md), and the rest of `docs/` |

---

## What it does (short)

You pass a file or folder; Chomsky reports whether things look **Safe**, need **human review**, or are a clear **Security Violation** (for example hardcoded password plus printing it). If you opt in, it can try to fix issues (for example by moving literals to environment variables). Pipeline: **detect → classify → transform**; structural CFG validation for configuration is described in the docs.

---

## Dependencies

From the repo root:

```bash
pip install -r requirements.txt
```

- **pyformlang** — DFAs and FSTs.  
- **pandas** — CSV reports when scanning a whole directory.  
- **pytest** — running the test suite.

Everything else is the Python standard library (`re`, `os`, etc.).

---

## Installation

1. Clone the repository (or use the GitHub Classroom copy).  
2. (Recommended) use a virtual environment:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

   On Linux/macOS: `source .venv/bin/activate`

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

From the **project root** (the directory that contains `app/`):

```bash
python -m app.cli [path]
```

- **`path`** (optional): file or directory, relative to the project root or absolute; if not found there, the CLI also looks under `samples/`. If omitted, it lists `samples/` and asks you to type a path.  
- You are then asked whether to **apply** automatic refactoring (`y`/`n`). Read [docs/USER_GUIDE.md](docs/USER_GUIDE.md) before using `y` on real projects.

**Quick examples:**

```bash
python -m app.cli samples/insecure.java
python -m app.cli sample_project
```

---

## Code layout

`detector.py` → `classifier.py` → `transformer.py`, orchestrated by `cli.py`. Formal details (regex, DFA tuples, FST, CFG) are in `docs/`.

---

## Tests (PDF “Testing and Validation” — part 1 only for now)

```bash
python -m pytest tests -q
```

**Part 1 (this commit):** scenario tests in `tests/test_part1_scenarios.py` — insecure code, safe code, config-like snippets, and mixed cases, plus the older `test_detector.py` / `test_detector_extra.py`.

**Part 2** (unit tests for regex, DFA, FST, and CFG validation) can be added in a follow-up commit when you want it.

---

## Stack

Python 3.10+, pyformlang, pandas.

---

## Authors

- Sebastián Romero Leon  
- Paula Andrea Piedrahita  
- Jean Carlo Ocampo  

Add IDE or course section here if your instructor asks for it.
