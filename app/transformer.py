import os
import re
from typing import Dict, List, Optional, Tuple

from pyformlang.fst import FST
from .detector import classify_line


# =========================================================
# Regex helpers
# =========================================================

PASSWORD_ASSIGN_RE = re.compile(
    r'^(?P<indent>\s*)(?:(?P<type>\w+)\s+)?(?P<var>password)\s*=\s*"(?P<value>[^"]+)"\s*;?\s*$'
)

APIKEY_ASSIGN_RE = re.compile(
    r'^(?P<indent>\s*)(?:(?P<type>\w+)\s+)?(?P<var>api[_-]?key)\s*=\s*"(?P<value>[^"]+)"\s*;?\s*$'
)

AWS_KEY_RE = re.compile(
    r'^(?P<indent>\s*).*?(?P<value>AKIA[0-9A-Z]{16}).*$'
)

PRINT_SENSITIVE_RE = re.compile(
    r'^(?P<indent>\s*)System\.out\.println\s*\(\s*(?:password|api[_-]?key)\s*\)\s*;?\s*$'
)

TODO_RE = re.compile(
    r'^(?P<indent>\s*)//\s*TODO:?.*$'
)

SUSPICIOUS_URL_RE = re.compile(
    r'^(?P<prefix>.*?)(?P<url>https?://(?:localhost|internal|dev|staging)[^\s"\']*)(?P<suffix>.*)$'
)

INTERNAL_IP_RE = re.compile(
    r'\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3})\b'
)


# =========================================================
# Utilities
# =========================================================

def _normalize_env_name(raw: str) -> str:
    text = raw.upper().replace("-", "_")
    text = re.sub(r'[^A-Z0-9_]', '_', text)
    text = re.sub(r'_+', '_', text).strip('_')
    return text


def _read_env_file(env_path: str) -> Dict[str, str]:
    env_map: Dict[str, str] = {}

    if not os.path.exists(env_path):
        return env_map

    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            env_map[key.strip()] = value.strip().strip('"')

    return env_map


def _write_env_file(env_path: str, updates: Dict[str, str]) -> None:
    if not updates:
        return

    existing = _read_env_file(env_path)
    existing.update(updates)

    lines = [f'{key}="{value}"' for key, value in sorted(existing.items())]

    os.makedirs(os.path.dirname(env_path), exist_ok=True)
    with open(env_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def _java_env_reference(indent: str, declared_type: Optional[str], variable: str, env_name: str) -> str:
    if declared_type:
        return f'{indent}{declared_type} {variable} = System.getenv("{env_name}");'
    return f'{indent}{variable} = System.getenv("{env_name}");'


def _generic_env_reference(indent: str, variable: str, env_name: str) -> str:
    return f'{indent}{variable} = ${{{env_name}}}'


# =========================================================
# FST builders
# =========================================================

def build_secret_fst() -> FST:
    """
    Input alphabet:
        HARDCODED_PASSWORD, API_KEY, AWS_API_KEY

    Output alphabet:
        ENV_PASSWORD, ENV_API_KEY, ENV_AWS_KEY
    """
    fst = FST()
    fst.add_start_state("q0")
    fst.add_final_state("q1")

    fst.add_transitions([
        ("q0", "HARDCODED_PASSWORD", "q1", ["ENV_PASSWORD"]),
        ("q0", "API_KEY", "q1", ["ENV_API_KEY"]),
        ("q0", "AWS_API_KEY", "q1", ["ENV_AWS_KEY"]),
    ])
    return fst


def build_print_fst() -> FST:
    fst = FST()
    fst.add_start_state("q0")
    fst.add_final_state("q1")

    fst.add_transitions([
        ("q0", "PRINT_SENSITIVE", "q1", ["REMOVE_SENSITIVE_PRINT"]),
    ])
    return fst


def build_todo_fst() -> FST:
    fst = FST()
    fst.add_start_state("q0")
    fst.add_final_state("q1")

    fst.add_transitions([
        ("q0", "TODO_COMMENT", "q1", ["DELETE_LINE"]),
    ])
    return fst


def build_url_fst() -> FST:
    fst = FST()
    fst.add_start_state("q0")
    fst.add_final_state("q1")

    fst.add_transitions([
        ("q0", "SUSPICIOUS_URL", "q1", ["ENV_URL"]),
    ])
    return fst


def build_ip_fst() -> FST:
    fst = FST()
    fst.add_start_state("q0")
    fst.add_final_state("q1")

    fst.add_transitions([
        ("q0", "INTERNAL_IP", "q1", ["REDACT_IP"]),
    ])
    return fst


SECRET_FST = build_secret_fst()
PRINT_FST = build_print_fst()
TODO_FST = build_todo_fst()
URL_FST = build_url_fst()
IP_FST = build_ip_fst()


# =========================================================
# FST translation helpers
# =========================================================

def _translate_with_single_symbol_fst(fst: FST, token: str) -> Optional[str]:
    outputs = list(fst.translate([token]))
    if not outputs:
        return None

    first = outputs[0]
    if isinstance(first, (list, tuple)):
        return "".join(first)
    return str(first)


def token_to_action(token: str) -> Optional[str]:
    if token in {"HARDCODED_PASSWORD", "API_KEY", "AWS_API_KEY"}:
        return _translate_with_single_symbol_fst(SECRET_FST, token)

    if token == "PRINT_SENSITIVE":
        return _translate_with_single_symbol_fst(PRINT_FST, token)

    if token == "TODO_COMMENT":
        return _translate_with_single_symbol_fst(TODO_FST, token)

    if token == "SUSPICIOUS_URL":
        return _translate_with_single_symbol_fst(URL_FST, token)

    if token == "INTERNAL_IP":
        return _translate_with_single_symbol_fst(IP_FST, token)

    return None


# =========================================================
# Concrete line rewrite functions
# =========================================================

def _rewrite_password_line(line: str) -> Tuple[str, Dict[str, str]]:
    match = PASSWORD_ASSIGN_RE.match(line)
    if not match:
        return line, {}

    indent = match.group("indent") or ""
    declared_type = match.group("type")
    variable = match.group("var")
    value = match.group("value")

    env_name = "APP_PASSWORD"
    rewritten = _java_env_reference(indent, declared_type, variable, env_name)
    return rewritten, {env_name: value}


def _rewrite_apikey_line(line: str) -> Tuple[str, Dict[str, str]]:
    match = APIKEY_ASSIGN_RE.match(line)
    if not match:
        return line, {}

    indent = match.group("indent") or ""
    declared_type = match.group("type")
    variable = match.group("var").replace("-", "_")
    value = match.group("value")

    env_name = "APP_API_KEY"
    rewritten = _java_env_reference(indent, declared_type, variable, env_name)
    return rewritten, {env_name: value}


def _rewrite_aws_key_line(line: str) -> Tuple[str, Dict[str, str]]:
    match = AWS_KEY_RE.match(line)
    if not match:
        return line, {}

    indent = match.group("indent") or ""
    value = match.group("value")

    env_name = "AWS_ACCESS_KEY_ID"
    rewritten = f'{indent}{env_name} = System.getenv("{env_name}");'
    return rewritten, {env_name: value}


def _remove_sensitive_print(line: str) -> Tuple[str, Dict[str, str]]:
    match = PRINT_SENSITIVE_RE.match(line)
    if not match:
        return line, {}
    indent = match.group("indent") or ""
    return f"{indent}// Sensitive output removed", {}


def _delete_todo_line(_: str) -> Tuple[str, Dict[str, str]]:
    return "", {}


def _rewrite_suspicious_url(line: str) -> Tuple[str, Dict[str, str]]:
    match = SUSPICIOUS_URL_RE.match(line)
    if not match:
        return line, {}

    prefix = match.group("prefix")
    url = match.group("url")
    suffix = match.group("suffix")

    env_name = "APP_BASE_URL"

    if '"' in line:
        replacement = f'${{{env_name}}}'
    else:
        replacement = f'${{{env_name}}}'

    rewritten = f"{prefix}{replacement}{suffix}"
    return rewritten, {env_name: url}


def _redact_internal_ip(line: str) -> Tuple[str, Dict[str, str]]:
    rewritten = INTERNAL_IP_RE.sub("REDACTED_INTERNAL_IP", line)
    return rewritten, {}


def apply_action(line: str, action: str) -> Tuple[str, Dict[str, str]]:
    if action == "ENV_PASSWORD":
        return _rewrite_password_line(line)

    if action == "ENV_API_KEY":
        return _rewrite_apikey_line(line)

    if action == "ENV_AWS_KEY":
        return _rewrite_aws_key_line(line)

    if action == "REMOVE_SENSITIVE_PRINT":
        return _remove_sensitive_print(line)

    if action == "DELETE_LINE":
        return _delete_todo_line(line)

    if action == "ENV_URL":
        return _rewrite_suspicious_url(line)

    if action == "REDACT_IP":
        return _redact_internal_ip(line)

    return line, {}


# =========================================================
# Public API
# =========================================================

def transform_code(
    code: str,
    classification: str,
    file_path: Optional[str] = None,
    env_path: Optional[str] = None,
) -> Tuple[str, Dict[str, str], List[Dict[str, str]]]:
    """
    Returns:
        transformed_code, env_entries_added, trace
    """

    if classification == "Safe":
        return code, {}, []

    transformed_lines: List[str] = []
    env_entries: Dict[str, str] = {}
    trace: List[Dict[str, str]] = []

    for line_number, line in enumerate(code.splitlines(), start=1):
        token = classify_line(line)
        action = token_to_action(token)

        if action is None:
            transformed_lines.append(line)
            continue

        new_line, new_env = apply_action(line, action)
        transformed_lines.append(new_line)
        env_entries.update(new_env)

        trace.append({
            "line": str(line_number),
            "token": token,
            "action": action,
            "original": line,
            "transformed": new_line,
        })

    transformed_code = "\n".join(transformed_lines)
    if code.endswith("\n"):
        transformed_code += "\n"

    if env_path:
        _write_env_file(env_path, env_entries)

    return transformed_code, env_entries, trace