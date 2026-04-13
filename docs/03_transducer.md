# 3. Automatic refactoring with finite-state transducers (FST)

## What this adds compared with a DFA

An automaton **accepts or rejects** (or ends in some state). A **transducer** goes further: while reading tokens it also **emits actions** such as “replace this line” or “comment this out”. That is the “surgeon” part: we already know something is wrong, now we propose a patch.

---

## General model (for the report)

An FST can be written as:

T = (Q, Σ, Γ, δ, ω, q₀, F)

- **Σ** — what you read (security tokens).  
- **Γ** — symbolic outputs (rewrite actions).  
- **ω** — output function on transitions.

In `pyformlang` we build FSTs and then map those actions to concrete Java / config lines.

---

## FST 1: secrets → environment variable

Q = {q0, q1}  
Σ = {`HARDCODED_PASSWORD`, `API_KEY`, `AWS_API_KEY`}  
Γ = {`ENV_PASSWORD`, `ENV_API_KEY`, `ENV_AWS_KEY`}  

**Idea:** a secret token fires the matching action (password → password env, etc.).

---

## FST 2: remove dangerous prints

Σ = {`PRINT_SENSITIVE`}  
Γ = {`REMOVE_SENSITIVE_PRINT`}

---

## FST 3: strip TODO lines

Σ = {`TODO_COMMENT`}  
Γ = {`DELETE_LINE`}

---

## FST 4: odd URL → configurable value

Σ = {`SUSPICIOUS_URL`}  
Γ = {`ENV_URL`}

---

## FST 5: internal IP

Σ = {`INTERNAL_IP`}  
Γ = {`REDACT_IP`}

---

## How this maps to code

1. Token → action (via FST / transition table).  
2. Action → new line string (functions that rewrite Java or config text).

---

## Why a DFA alone is not enough

We do not want only a boolean: we want an **input → output** mapping on text. That is exactly the transducer’s job compared with a plain classifier.
