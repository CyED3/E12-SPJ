# 2. Classification with deterministic finite automata (DFA)

## Intuition

We already have a **token sequence** (not raw text). We want to put the file into one of three buckets:

- **Safe** — no strong risk signals.  
- **Needs Review** — something looks off, but we do not hit the worst combination.  
- **Security Violation** — for example secret plus print, or certain tokens the assignment treats as a direct violation.

Each bucket is modeled with a separate **DFA** in `pyformlang`; the program then picks which description applies according to the rules we coded.

---

## Token alphabet

Σ = {
 `API_KEY`, `HARDCODED_PASSWORD`, `PRINT_SENSITIVE`,
 `TODO_COMMENT`, `SUSPICIOUS_URL`, `AWS_API_KEY`,
 `INTERNAL_IP`, `OTHER`
}

---

## DFA 1: “Is it really safe?”

**Type:** DFA (deterministic).

**5-tuple (short):**

- Q = {`safe_start`, `safe_ok`, `safe_reject`}  
- Σ = alphabet above  
- q₀ = `safe_start`  
- F = {`safe_ok`}  

**δ in words:** from the start, if you only ever see `OTHER` you reach “ok”. The moment any “hot” token appears you drop into reject and stay there. One stain and it is not safe.

---

## DFA 2: “Should a human review this?”

Q = {`review_start`, `review_ok`, `review_reject`}  
q₀ = `review_start`  
F = {`review_ok`}  

**Idea:** accepts suspicious or incomplete situations **without** reaching the worst case captured by the third DFA (for example some print+secret combos, or AWS key depending on the rules).

---

## DFA 3: “Is this already a violation?”

Q = {
  `violation_start`,
  `violation_secret_seen`,
  `violation_ok`,
  `violation_no`
}

q₀ = `violation_start`  
F = {`violation_ok`}  

**Transitions that matter (high level):**

- Password / API key → “secret seen” state.  
- Sensitive print after that → violation.  
- `AWS_API_KEY` can jump straight to violation depending on the design.

---

## Easy example

Sequence: `HARDCODED_PASSWORD` → `PRINT_SENSITIVE`  
**Outcome:** **Security Violation** (classic story: stored the secret and printed it).

---

## Why a finite automaton is enough here

Tokens form a **finite alphabet** and the policies we encode use **finite memory** (“have I seen a secret?”, “am I in violation?”). We are not counting arbitrarily nested parentheses in this stage; that is what the configuration grammar is for.

So a DFA is reasonable. If the event language needed unbounded nesting with a stack, we would move up to a richer model.
