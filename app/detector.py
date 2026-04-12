import re
from typing import Dict, List

PATTERNS = {
    "API_KEY": r'(?:String\s+)?api[_-]?key\s*=\s*"[^"]+"',
    "HARDCODED_PASSWORD": r'(?:String\s+)?password\s*=\s*"[^"]+"',
    "PRINT_SENSITIVE": r'^\s*System\.out\.println\s*\(\s*(?:password|api[_-]?key)\s*\)\s*;?\s*$',
    "TODO_COMMENT": r'//\s*TODO:?.*',
    "SUSPICIOUS_URL": r'https?://(?:localhost|internal|dev|staging)[^\s"\']*',
    "AWS_API_KEY": r'AKIA[0-9A-Z]{16}',
    "INTERNAL_IP": r'\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3})\b',

}

def _line_and_column_from_index(text: str, index: int) -> tuple[int, int]:
    line = text.count("\n", 0, index) + 1
    last_newline = text.rfind("\n", 0, index)
    column = index + 1 if last_newline == -1 else index - last_newline
    return line, column


def _severity_for(label: str) -> str:
    if label in {"AWS_API_KEY", "PRINT_SENSITIVE"}:
        return "high"
    if label in {"API_KEY", "HARDCODED_PASSWORD"}:
        return "medium"
    return "low"


def detect_issues(code: str) -> List[dict]:
    findings = []

    for label, pattern in PATTERNS.items():
        for match in re.finditer(pattern, code, flags=re.MULTILINE):
            start = match.start()
            end = match.end()
            line, column = _line_and_column_from_index(code, start)

            secret_value = None
            if "secret" in match.re.groupindex:
                secret_value = match.group("secret")

            findings.append({
                "type": label,
                "match": match.group(0),
                "start": start,
                "end": end,
                "line": line,
                "column": column,
                "secret_value": secret_value,
                "severity": _severity_for(label),
            })

    findings.sort(key=lambda x: (x["line"], x["start"]))
    return findings

def extract_tokens(code: str) -> List[str]:
    findings = detect_issues(code)
    return [f["type"] for f in findings]

def classify_line(line: str) -> str:
    stripped = line.strip()
    for label, pattern in PATTERNS.items():
        if re.search(pattern, stripped):
            return label
    return "OTHER"