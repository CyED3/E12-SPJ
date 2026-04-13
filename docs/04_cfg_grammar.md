# 4. Context-free grammar for “secure” configuration

## What this section is for

Think of a small language for `.env`-style files or configs with sections: assignments must be well formed, blocks may nest, and sensitive keys must **not** use a plain value like `admin123`; they should use something like `${MY_VAR}`.

You cannot fully capture **nested braces** and “they must match” with regex alone at arbitrary depth, which is why the assignment asks for a **CFG**. Here we spell out the grammar and the non-regularity argument.

---

## Terminals and non-terminals

**Terminals** (idealized tokens from a lexer):

| Symbol | Meaning |
|--------|---------|
| `LBRACE`, `RBRACE` | `{` and `}` |
| `ID` | section or key name |
| `=` | assignment |
| `STRING`, `NUMBER` | literals |
| (env reference) | pattern `${` + `ID` + `}` |

**Non-terminals:** `Config`, `Section`, `Block`, `Entry`, `Key`, `Value`, `PlainValue`.  
**Start symbol:** `Config`.

---

## Rules (EBNF-style)

```text
Config     ::= Block*
Block      ::= Section | Entry

Section    ::= 'section' ID '{' Config '}'
           |   '{' Config '}'

Entry      ::= Key '=' Value

Key        ::= ID
Value      ::= EnvRef | PlainValue
PlainValue ::= STRING | NUMBER
EnvRef     ::= '${' ID '}'

SensitiveKey ::= 'DB_PASSWORD' | 'API_KEY' | 'AWS_SECRET' | 'PASSWORD' | 'SECRET'
```

In a real validator, if `Key` is in **SensitiveKey**, then `Value` must be **only** `EnvRef`. Other keys might allow literals or references depending on policy.

---

## Examples

**Good** (secret via environment):

```text
DB_PASSWORD=${SECURE_DB_PASSWORD}
```

**Bad** under a strict policy (plaintext secret):

```text
DB_PASSWORD=admin123
```

**Nested** (shows recursion `Config` inside `Section`):

```text
section app {
  section db {
    DB_PASSWORD=${SECURE_DB_PASSWORD}
  }
}
```

---

## Why this is not a regular language

1. **Balanced braces:** counting “how many opens vs closes” at unbounded nesting depth is the standard example of something a finite automaton cannot do with finite states alone (you need stack-style memory).

2. **Recursion:** inside a section you again have `Config`, which may contain more sections. That is typical **tree-shaped** CFG structure.

Regex is still fine for **line-level hints** (“this looks like a password”), but saying “this file respects hierarchy and secret policy” calls for a grammar-based parser (courses often show **textX**; here we keep the formal design; the current `app/` code focuses on Java + regex + DFA + FST).

---

## How this ties to the repository

`app/` wires **regex → DFA → FST** for the supported file types. This grammar is the design for the **structural validation** step from the integrative task; a textX `.tx` file would be the polished implementation with clear parse errors.

For how detection and automata connect to the code, see [01_regex_doc.md](01_regex_doc.md), [02_automata.md](02_automata.md), and [03_transducer.md](03_transducer.md).
