# 1. Detection with regular expressions

## What this stage is for

Before any automaton runs, the file is just text. **Regex** picks up patterns that often go wrong in real repos (keys, hardcoded passwords, bad prints, etc.). The output is not a final yes/no yet: we build a **token list** that the classifier consumes later.

In plain terms: first we flag “this looks like X”, without fully deciding final severity.

---

## Patterns and the languages they approximate

### 1. AWS-style API key

**Regex:** `AKIA[0-9A-Z]{16}`

**Language (idea):** strings that start with `AKIA` followed by exactly sixteen uppercase alphanumeric characters.

---

### 2. Hardcoded password

**Regex:** `(?:String\s+)?password\s*=\s*"[^"]+"`

**What we match:** assignments to a variable named `password` with a string literal (optional leading `String` in Java).

**Typical example:** `password = "admin123"`

---

### 3. API key in a variable

**Regex:** `(?:String\s+)?api[_-]?key\s*=\s*"[^"]+"`

**What we match:** `api_key`, `api-key`, `apikey`, etc., with a string literal.

---

### 4. Sensitive print

**Regex:** `^\s*System\.out\.println\s*\(\s*(?:password|api[_-]?key)\s*\)\s*;?\s*$`

**What we match:** lines that print `password` or the API key. Together with the previous case, that is the main story for a “strong” violation.

---

### 5. TODO comments

**Regex:** `//\s*TODO:?.*`

**Idea:** technical debt markers; sometimes harmless, sometimes “we still need to fix something risky here”.

---

### 6. Suspicious URL

**Regex:** `https?://(?:localhost|internal|dev|staging)[^\s"']*`

**Idea:** URLs pointing at internal or dev-style hosts that should not ship to production as-is.

---

### 7. Private IP

**Regex:** `\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3})\b`

**Idea:** common private IPv4 ranges (10.x, 192.168.x, 172.16–31.x).

---

## Where it lives in code

- `detect_issues()` — returns matches with context.  
- `extract_tokens()` — builds the token sequence for the file.  
- `classify_line()` — picks the label for a single line.

Anything that does not match an “interesting” pattern effectively becomes `OTHER` for the next stage.
