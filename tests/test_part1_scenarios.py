"""
Part 1 — scenario-style tests (light integration)

We test small "stories" rather than single functions: insecure code, clean code,
config-like blobs, and mixes. That matches the PDF ask for insecure patterns,
safe code, insecure configuration, and mixed cases.
"""

from pathlib import Path

import pytest

from app.classifier import classify_tokens_detailed
from app.detector import detect_issues, extract_tokens
from app.transformer import transform_code


def _tokens_from(code: str):
    return extract_tokens(code)


def _classify(code: str):
    return classify_tokens_detailed(_tokens_from(code))


# --- should come out Safe (no risky tokens) ---


def test_boring_java_class_is_safe():
    code = """
public class Demo {
    public static void main(String[] args) {
        System.out.println("hello world");
    }
}
"""
    res = _classify(code)
    assert res["classification"] == "Safe", "should not invent issues when nothing is there"


def test_mostly_empty_file_is_safe():
    assert _classify("// just a random comment")["classification"] == "Safe"


# --- classic insecure patterns from the assignment ---


def test_hardcoded_password_plus_print_is_violation():
    # the textbook combo
    bad_java = '''String password = "admin123";
System.out.println(password);
'''
    res = _classify(bad_java)
    assert res["classification"] == "Security Violation"


def test_standalone_aws_key_is_detected():
    line = 'String x = "AKIA1234567890ABCDEF";'
    assert "AWS_API_KEY" in _tokens_from(line)


# --- config-like snippets ---


def test_config_snippet_with_internal_url_and_password():
    # sometimes .conf files look like this
    blob = '''
db.password="legacy-pass"
public.endpoint=http://staging.example.local/svc
'''
    findings = detect_issues(blob)
    types_found = {h["type"] for h in findings}
    assert "HARDCODED_PASSWORD" in types_found
    assert "SUSPICIOUS_URL" in types_found


# --- mixed: good and bad in one file ---


def test_mixed_todo_and_password_without_print_goes_to_review_or_worse():
    # tech debt + secret but no print -> not the full textbook violation path
    mix = """
// TODO: fix this when we can
String password = "12345";
"""
    res = _classify(mix)
    assert res["classification"] in ("Needs Review", "Security Violation")


def test_api_key_and_print_together_is_violation():
    c = '''String api_key = "sk-test-123";
System.out.println(api_key);
'''
    assert _classify(c)["classification"] == "Security Violation"


# --- optional smoke on real sample files from the repo ---


@pytest.mark.parametrize(
    "filename, expected_label",
    [
        ("safe.java", "Safe"),
        ("insecure.java", None),  # we only check it runs; label can vary with edits
    ],
)
def test_samples_on_disk_smoke(filename, expected_label):
    base = Path(__file__).resolve().parent.parent / "samples" / filename
    if not base.exists():
        pytest.skip("sample file missing on this machine")
    text = base.read_text(encoding="utf-8")
    res = _classify(text)
    if expected_label:
        assert res["classification"] == expected_label


def test_transform_does_nothing_when_marked_safe():
    out, envs, trace = transform_code("class X {}", classification="Safe")
    assert out.strip() == "class X {}".strip()
    assert envs == {}
    assert trace == []
