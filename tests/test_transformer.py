from app.transformer import transform_code


def test_password_moves_to_env_and_code_references_system_getenv():
    code = 'String password = "admin123";\n'
    result = transform_code(code)
    assert 'System.getenv("APP_PASSWORD")' in result.code
    assert result.env_updates["APP_PASSWORD"] == "admin123"


def test_api_key_moves_to_env():
    code = 'String api_key = "local-dev-key";\n'
    result = transform_code(code)
    assert 'System.getenv("APP_API_KEY")' in result.code
    assert result.env_updates["APP_API_KEY"] == "local-dev-key"


def test_sensitive_print_becomes_comment():
    code = 'System.out.println(password);\n'
    result = transform_code(code)
    assert '// Sensitive output removed' in result.code


def test_todo_comment_is_deleted():
    code = '// TODO remove before production\n'
    result = transform_code(code)
    assert result.code == '\n'


def test_suspicious_url_becomes_env_reference_in_config():
    code = 'service.url=http://internal.company.local/api\n'
    result = transform_code(code)
    assert 'service.url=${APP_BASE_URL}' in result.code
    assert result.env_updates["APP_BASE_URL"] == 'http://internal.company.local/api'
