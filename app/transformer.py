import re
from detector import classify_line

class SecureRefactoringFST:
    """
    Deterministic Finite State Transducer (FST)
    T = (Q, Σ, Γ, δ, ω, q0, F)

    Q = {q0}
    Σ = {HARDCODED_PASSWORD, API_KEY, PRINT_SENSITIVE, INTERNAL_IP, SUSPICIOUS_URL, OTHER}
    Γ = {REWRITE_PASSWORD_ENV, REWRITE_APIKEY_ENV, REMOVE_SENSITIVE_PRINT, MASK_INTERNAL_IP, REPLACE_SUSPICIOUS_URL, KEEP}
    q0 = q0
    F = {q0}
    """

    def __init__(self):
        self.state = "q0"
        self.final_states = {"q0"}

        # delta: transition function
        self.delta = {
            ("q0", "HARDCODED_PASSWORD"): "q0",
            ("q0", "API_KEY"): "q0",
            ("q0", "PRINT_SENSITIVE"): "q0",
            ("q0", "INTERNAL_IP"): "q0",
            ("q0", "SUSPICIOUS_URL"): "q0",
            ("q0", "OTHER"): "q0",
            ("q0", "AWS_API_KEY"): "q0",
            ("q0", "TODO_COMMENT"): "q0",
        }

        # omega: output function
        self.omega = {
            ("q0", "HARDCODED_PASSWORD"): "REWRITE_PASSWORD_ENV",
            ("q0", "API_KEY"): "REWRITE_APIKEY_ENV",
            ("q0", "PRINT_SENSITIVE"): "REMOVE_SENSITIVE_PRINT",
            ("q0", "INTERNAL_IP"): "MASK_INTERNAL_IP",
            ("q0", "SUSPICIOUS_URL"): "REPLACE_SUSPICIOUS_URL",
            ("q0", "AWS_API_KEY"): "MASK_AWS_KEY",
            ("q0", "TODO_COMMENT"): "KEEP",
            ("q0", "OTHER"): "KEEP",
        }

    def step(self, input_symbol: str) -> str:
        output_symbol = self.omega[(self.state, input_symbol)]
        self.state = self.delta[(self.state, input_symbol)]
        return output_symbol

def _preserve_indent(line: str, replacement: str) -> str:
    indent = re.match(r"^\s*", line).group(0)
    return f"{indent}{replacement}"

def apply_output_action(line: str, output_symbol: str) -> str:
    if output_symbol == "REWRITE_PASSWORD_ENV":
        return re.sub(
            r'\b(?:String\s+)?password\s*=\s*"[^"]+"\s*;?',
            'String password = System.getenv("APP_PASSWORD");',
            line,
        )

    if output_symbol == "REWRITE_APIKEY_ENV":
        return re.sub(
            r'\b(?:String\s+)?api[_-]?key\s*=\s*"[^"]+"\s*;?',
            'String api_key = System.getenv("APP_API_KEY")',
            line,
        )

    if output_symbol == "REMOVE_SENSITIVE_PRINT":
        return re.sub(
            r'^(\s*)System\.out\.println\s*\(\s*(password|api[_-]?key)\s*\)\s*;?',
            r'\1// Sensitive output removed',
            line
        )

    if output_symbol == "MASK_INTERNAL_IP":
        return re.sub(
            r'\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3})\b',
            'REDACTED_INTERNAL_IP',
            line
        )

    if output_symbol == "REPLACE_SUSPICIOUS_URL":
        return re.sub(
            r'https?://(?:localhost|internal|dev|staging)[^\s"\']*',
            'https://secure.company.com',
            line,
        )

    if output_symbol == "MASK_AWS_KEY":
        return re.sub(r'\bAKIA[0-9A-Z]{16}\b', 'AWS_KEY_FROM_ENV', line)

    return line


def transform_code(code: str) -> str:
    fst = SecureRefactoringFST()
    transformed_lines = []

    for line in code.splitlines():
        input_symbol = classify_line(line)
        output_symbol = fst.step(input_symbol)
        transformed_lines.append(apply_output_action(line, output_symbol))

    transformed_code = "\n".join(transformed_lines)
    if code.endswith("\n"):
        transformed_code += "\n"
    return transformed_code