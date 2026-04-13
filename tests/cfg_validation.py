# Small validator for "secure-style" config rules from the course write-up.
# Lives under tests/ with the suite that exercises CFG-style checks.
# Not a full textX parser: we enforce sensitive key => ${VAR} and naive brace balance.

from __future__ import annotations

import re
from typing import List

_ENV_REF = re.compile(r"^\$\{[A-Za-z][A-Za-z0-9_]*\}$")


def _is_sensitive_key(key: str) -> bool:
    k = key.upper().replace("-", "_")
    if "PASSWORD" in k or "SECRET" in k:
        return True
    if k in {"API_KEY", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "TOKEN"}:
        return True
    return False


def lint_secure_config(text: str) -> List[str]:
    """
    Return a list of human-readable errors. Empty list means the basic lint passed.
    """
    errors: List[str] = []

    opens = text.count("{")
    closes = text.count("}")
    if opens != closes:
        errors.append(f"unbalanced braces: {opens} '{{' vs {closes} '}}'")

    for line_no, raw in enumerate(text.splitlines(), start=1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if line in ("{", "}"):
            continue
        if "=" not in line:
            continue

        key, rest = line.split("=", 1)
        key = key.strip()
        value = rest.strip().strip('"').strip("'")

        if not _is_sensitive_key(key):
            continue

        if not _ENV_REF.match(value):
            preview = value if len(value) <= 40 else value[:40] + "..."
            errors.append(
                f"line {line_no}: sensitive key {key!r} should use ${{VAR}}, "
                f"not a literal like {preview!r}"
            )

    return errors


def secure_config_ok(text: str) -> bool:
    return len(lint_secure_config(text)) == 0
