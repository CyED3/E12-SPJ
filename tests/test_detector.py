from app.detector import extract_tokens

def test_extract_password_token():
    code = 'String password = "admin123";'
    tokens = extract_tokens(code)
    assert "HARDCODED_PASSWORD" in tokens

def test_extract_print_sensitive():
    code = 'System.out.println(password);'
    tokens = extract_tokens(code)
    assert "PRINT_SENSITIVE" in tokens