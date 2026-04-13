# User guide — Chomsky CLI

## What this is

Chomsky walks **one file** or a **whole folder** and reports security-style patterns. It is a course lab, not a commercial scanner, but it shows the full flow (detect → classify → transform) and can emit CSV reports when you analyze a directory.

Supported extensions: `.java`, `.cfg`, `.conf`, `.env`, `.txt`.

---

## Before you start

- **Python 3.10+** is enough.  
- Install packages from `requirements.txt` (see the root [README.md](../README.md)).

---

## How to run it

From the **repository root** (where the `app/` folder is):

```bash
python -m app.cli [path]
```

- **`path`** is optional: a file or directory. Relative paths are resolved from the project root first; if missing, the CLI tries under `samples/`.  
- If you **omit** `path`, it lists `samples/` and asks you to type a name.

### Copy-paste examples

```bash
python -m app.cli samples/insecure.java
python -m app.cli sample_project
python -m app.cli sample_project/src/Main.java
```

### Apply automatic refactoring?

You will see: **Apply automatic secure refactoring? (y/n)** (that string is English in the code).

- **`n`**: read-only run. Prints findings, classification, what the transducer would do, etc., **without** changing files. Safest for practice.  
- **`y`**: for **Needs Review** or **Security Violation** when the transformer actually changes text, it **writes** the file and leaves a **`.bak`** next to it. It may also create or update a **`.env`** near the file when secrets are moved to the environment.

**Practical tip:** on a real repo, use `git` or a copy of the folder before answering **`y`**. It is easy to overwrite something by mistake.

---

## Reading the output

For each file you will roughly see:

1. **DETECTED PATTERNS** — regex hits (type, line, matched text).  
2. **TOKEN SEQUENCE** — abstract labels fed to the automaton (`HARDCODED_PASSWORD`, etc.).  
3. **CLASSIFICATION** — **Safe**, **Needs Review**, or **Security Violation**, plus which DFA “won”.  
4. **TRANSFORMATION TRACE** — line-by-line transducer actions.  
5. **ENV ENTRIES** — suggested or written `.env` key/value pairs.

If you pass a **directory**, you get a short **summary** and CSV files in the **current working directory** (usually the project root):

| File | Contents |
|------|----------|
| `findings_report.csv` | All pattern matches |
| `classification_report.csv` | Classification per file |
| `transformations_report.csv` | Transformation steps |
| `env_report.csv` | Environment entries |

---

## Formal models (deep dive)

- Regex → [01_regex_doc.md](01_regex_doc.md)  
- DFA → [02_automata.md](02_automata.md)  
- FST → [03_transducer.md](03_transducer.md)  
- CFG for configs → [04_cfg_grammar.md](04_cfg_grammar.md)  

---

## Troubleshooting

- **Path not found**: check the path or try a name listed under `samples/`.  
- Files are read as **UTF-8**.  
- “Nothing happened” for a folder: maybe there are no supported extensions, or only hidden/unsupported files.
