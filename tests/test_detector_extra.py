from app.detector import detect_issues, extract_tokens


def test_extract_tokens_from_java_violation():
    code = 'String password = "admin123";\nSystem.out.println(password);'
    tokens = extract_tokens(code)
    assert "HARDCODED_PASSWORD" in tokens
    assert "PRINT_SENSITIVE" in tokens


def test_detect_insecure_config_values():
    code = 'db.password="legacy-pass"\npublic.endpoint=http://staging.example.local'
    findings = detect_issues(code)
    labels = [f["type"] for f in findings]
    assert "HARDCODED_PASSWORD" in labels or "PLAIN_CONFIG_VALUE" in labels
    assert "SUSPICIOUS_URL" in labels


def test_detect_aws_key_in_env():
    code = 'AWS_ACCESS_KEY_ID="AKIA1234567890ABCDEF"'
    tokens = extract_tokens(code)
    assert "AWS_API_KEY" in tokens
