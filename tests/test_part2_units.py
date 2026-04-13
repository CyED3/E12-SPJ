"""
Part 2 — unit tests by component

Regex / detector, DFA (classifier), FST (transformer), and CFG-style checks in tests/cfg_validation.py.
"""

from tests.cfg_validation import lint_secure_config, secure_config_ok
from app.classifier import classify_tokens, classify_tokens_detailed, run_safe_dfa, run_security_violation_dfa
from app.detector import classify_line, detect_issues, extract_tokens
from app.transformer import build_secret_fst, token_to_action, transform_code


# --- regex / extraction ---


def test_detect_issues_returns_line_and_type():
    src = 'password = "x";\n'
    hits = detect_issues(src)
    assert len(hits) >= 1
    first = hits[0]
    assert first["type"] == "HARDCODED_PASSWORD"
    assert first["line"] == 1


def test_classify_line_other_when_no_match():
    assert classify_line("int x = 2;") == "OTHER"


def test_private_ip_10_x():
    line = "host = 10.0.0.1"
    assert classify_line(line) == "INTERNAL_IP"


def test_extract_tokens_collects_types_in_order():
    code = 'password = "a";\nString api_key = "k";\n'
    toks = extract_tokens(code)
    assert "HARDCODED_PASSWORD" in toks
    assert "API_KEY" in toks


# --- DFA / classification ---


def test_empty_token_list_is_safe_for_dfa():
    assert run_safe_dfa([]) is True


def test_password_then_print_is_violation_dfa():
    toks = ["HARDCODED_PASSWORD", "PRINT_SENSITIVE"]
    assert run_security_violation_dfa(toks) is True


def test_classifier_returns_something_sensible_for_other_only():
    weird = classify_tokens_detailed(["OTHER", "OTHER"])
    assert weird["classification"] in ("Safe", "Needs Review")


def test_api_key_alone_is_not_security_violation_dfa():
    assert run_security_violation_dfa(["API_KEY"]) is False


# --- FST / transforms ---


def test_secret_fst_maps_password_token():
    fst = build_secret_fst()
    outputs = list(fst.translate(["HARDCODED_PASSWORD"]))
    assert outputs
    flat = "".join(outputs[0]) if isinstance(outputs[0], (list, tuple)) else str(outputs[0])
    assert "ENV" in flat or outputs[0] == ["ENV_PASSWORD"]


def test_token_to_action_for_sensitive_print():
    assert token_to_action("PRINT_SENSITIVE") == "REMOVE_SENSITIVE_PRINT"


def test_transform_rewrites_password_assignment():
    java = '    String password = "secret";\n'
    new_code, envs, trace = transform_code(java, classification="Needs Review")
    assert "getenv" in new_code
    assert "APP_PASSWORD" in envs
    assert len(trace) >= 1


# --- CFG-style config validation ---


def test_secure_config_ok_with_env_ref_for_password():
    cfg = """
DB_PASSWORD=${MY_DB}
"""
    assert secure_config_ok(cfg)


def test_plain_password_value_fails_lint():
    cfg = "DB_PASSWORD=1234\n"
    errs = lint_secure_config(cfg)
    assert len(errs) >= 1
    assert any("DB_PASSWORD" in e for e in errs)


def test_unbalanced_braces_reported():
    bad = """
section a {
DB_PASSWORD=${X}
"""
    errs = lint_secure_config(bad)
    assert any("brace" in e.lower() or "balanced" in e.lower() for e in errs)


def test_literal_api_key_fails():
    text = 'API_KEY="hello"\n'
    assert not secure_config_ok(text)


# --- extra tests ---


def test_only_aws_key_classified_security_violation():
    assert classify_tokens(["AWS_API_KEY"]) == "Security Violation"


def test_safe_dfa_false_when_todo_present():
    assert run_safe_dfa(["TODO_COMMENT"]) is False


def test_detect_issues_finds_todo_comment():
    src = "// TODO: fix security here\n"
    types = {f["type"] for f in detect_issues(src)}
    assert "TODO_COMMENT" in types


def test_suspicious_staging_url_is_detected():
    line = 'String u = "https://staging.myapp.internal/api";'
    assert classify_line(line) == "SUSPICIOUS_URL"


def test_nested_balanced_braces_with_env_refs_ok():
    cfg = """
section app {
  DB_PASSWORD=${DB_PWD}
  nested {
    API_KEY=${K}
  }
}
"""
    assert secure_config_ok(cfg)
