# 1. Code Preprocessing and Tokenization (Regular Expressions)

## Objective
The goal of this module is to detect insecure patterns in source code and configuration files using regular expressions. The output is a sequence of abstract tokens representing potential security issues.

This corresponds to the lexical level of analysis, where files are treated as strings over a finite alphabet.

---

## Regular Expressions and Languages

### 1. AWS API Key

Regex:
AKIA[0-9A-Z]{16}

Language:
L_AWS = { "AKIA"x | x ∈ [0-9A-Z]^{16} }

Description:
Recognizes strings starting with "AKIA" followed by exactly 16 uppercase alphanumeric characters.

---

### 2. Hardcoded Password

Regex:
(?:String\s+)?password\s*=\s*"[^"]+"

Language:
Assignments where a variable named "password" is assigned a string literal.

Example:
password = "admin123"

---

### 3. API Key

Regex:
(?:String\s+)?api[_-]?key\s*=\s*"[^"]+"

Language:
Assignments to variables named api_key, api-key, or apikey.

---

### 4. Sensitive Print

Regex:
^\s*System\.out\.println\s*\(\s*(?:password|api[_-]?key)\s*\)\s*;?\s*$

Language:
Lines printing sensitive variables.

---

### 5. TODO Comment

Regex:
//\s*TODO:?.*

Language:
Single-line comments indicating unfinished or unsafe code.

---

### 6. Suspicious URL

Regex:
https?://(?:localhost|internal|dev|staging)[^\s"']*

Language:
URLs pointing to internal or development environments.

---

### 7. Internal IP

Regex:
\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3})\b

Language:
Private IPv4 addresses.

---

## Implementation

- detect_issues(): extracts matches
- extract_tokens(): produces token sequence
- classify_line(): assigns a token per line

---