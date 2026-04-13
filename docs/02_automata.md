# 2. Security Classification (Finite Automata)

## Objective
Classify files into:
- Safe
- Needs Review
- Security Violation

The input is a sequence of tokens from the detection phase.

---

## Alphabet

Σ = {
 API_KEY, HARDCODED_PASSWORD, PRINT_SENSITIVE,
 TODO_COMMENT, SUSPICIOUS_URL, AWS_API_KEY,
 INTERNAL_IP, OTHER
}

---

## DFA 1: SafeClassifier

Type: Deterministic Finite Automaton (DFA)

5-tuple:

Q = {safe_start, safe_ok, safe_reject}  
Σ = as defined above  
q0 = safe_start  
F = {safe_ok}  

Transition function δ:
- δ(safe_start, OTHER) = safe_ok
- δ(safe_start, x≠OTHER) = safe_reject
- δ(safe_ok, OTHER) = safe_ok
- δ(safe_ok, x≠OTHER) = safe_reject
- δ(safe_reject, x) = safe_reject

---

## DFA 2: NeedsReviewClassifier

Q = {review_start, review_ok, review_reject}  
q0 = review_start  
F = {review_ok}  

Accepts files with:
- suspicious patterns
- but no confirmed violations

---

## DFA 3: SecurityViolationClassifier

Q = {
  violation_start,
  violation_secret_seen,
  violation_ok,
  violation_no
}

q0 = violation_start  
F = {violation_ok}  

Key transitions:
- password/api → secret_seen
- secret_seen + print → violation
- AWS_API_KEY → violation

---

## Interpretation

The automata operate on sequences of tokens, not raw text.

Example:
HARDCODED_PASSWORD → PRINT_SENSITIVE → Security Violation

---

## Justification

Finite automata are sufficient because:
- The language of token sequences is regular
- Only finite memory is needed