# 3. Automatic Secure Refactoring (Finite State Transducers)

## Objective
Transform insecure code into secure code automatically.

---

## General Model

A Finite State Transducer is defined as:

T = (Q, Σ, Γ, δ, ω, q0, F)

Where:
- Σ: input alphabet (tokens)
- Γ: output alphabet (actions)
- ω: output function

---

## FST 1: Secret → Environment Variable

Q = {q0, q1}  
Σ = {HARDCODED_PASSWORD, API_KEY, AWS_API_KEY}  
Γ = {ENV_PASSWORD, ENV_API_KEY, ENV_AWS_KEY}  
q0 = q0  
F = {q1}  

Transitions:
- δ(q0, HARDCODED_PASSWORD) = q1
- δ(q0, API_KEY) = q1
- δ(q0, AWS_API_KEY) = q1

Outputs:
- ω(q0, HARDCODED_PASSWORD) = ENV_PASSWORD
- ω(q0, API_KEY) = ENV_API_KEY
- ω(q0, AWS_API_KEY) = ENV_AWS_KEY

---

## FST 2: Sensitive Print Removal

Σ = {PRINT_SENSITIVE}  
Γ = {REMOVE_SENSITIVE_PRINT}

---

## FST 3: TODO Removal

Σ = {TODO_COMMENT}  
Γ = {DELETE_LINE}

---

## FST 4: Suspicious URL

Σ = {SUSPICIOUS_URL}  
Γ = {ENV_URL}

---

## FST 5: Internal IP

Σ = {INTERNAL_IP}  
Γ = {REDACT_IP}

---

## Implementation Strategy

- Token → action using FST
- Action → concrete rewrite

---

## Justification

FSTs are required because:
- We transform input strings into output strings
- This is not just recognition (like DFA)
- It is a mapping (translation)