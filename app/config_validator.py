import os
from typing import Any, Dict, List

import pandas as pd
from textx import metamodel_from_file
from textx.exceptions import TextXSyntaxError


SUPPORTED_CONFIG_EXTENSIONS = {".cfg", ".conf", ".secure", ".chomsky"}

SENSITIVE_KEYS = {
    "DB_PASSWORD",
    "API_KEY",
    "SECRET_KEY",
    "AWS_ACCESS_KEY_ID",
    "APP_PASSWORD",
    "APP_API_KEY",
    "APP_BASE_URL",
    "PASSWORD",
    "SECRET",
    "TOKEN",
    "password",
    "api_key",
    "secret_key",
}


def _grammar_path() -> str:
    return os.path.join(os.path.dirname(__file__), "config_validator.tx")


def _load_metamodel():
    return metamodel_from_file(_grammar_path())


def is_supported_config_file(file_path: str) -> bool:
    _, ext = os.path.splitext(file_path)
    return ext.lower() in SUPPORTED_CONFIG_EXTENSIONS


def _walk_elements(elements, depth: int = 0):
    """
    Yields tuples:
        (kind, object, depth)
    """
    for element in elements:
        cls_name = element.__class__.__name__

        if cls_name == "Section":
            yield ("Section", element, depth)
            yield from _walk_elements(element.elements, depth + 1)
        elif cls_name in {"SensitiveAssignment", "RegularAssignment"}:
            yield ("Assignment", element, depth)


def _key_to_str(key_obj) -> str:
    if isinstance(key_obj, str):
        return key_obj

    if hasattr(key_obj, "parts"):
        return ".".join(key_obj.parts)

    return str(key_obj)


def _assignment_value_repr(assignment) -> str:
    value = assignment.value
    cls_name = value.__class__.__name__

    if cls_name == "EnvReference":
        return "${" + value.ref + "}"

    # STRING and INT may come as primitive text-like values
    return str(value)


def validate_config_text(text: str, source_name: str = "<memory>") -> Dict[str, Any]:
    """
    Returns a structured validation result for one config text.
    """
    mm = _load_metamodel()

    try:
        model = mm.model_from_str(text)
    except TextXSyntaxError as exc:
        return {
            "file": source_name,
            "parsed_ok": False,
            "secure_ok": False,
            "errors": [f"Syntax error at line {exc.line}, col {exc.col}: {exc.message}"],
            "warnings": [],
            "nested_sections": 0,
            "assignments": 0,
            "sensitive_assignments": 0,
        }
    except Exception as exc:
        return {
            "file": source_name,
            "parsed_ok": False,
            "secure_ok": False,
            "errors": [f"Unexpected parser error: {exc}"],
            "warnings": [],
            "nested_sections": 0,
            "assignments": 0,
            "sensitive_assignments": 0,
        }

    errors: List[str] = []
    warnings: List[str] = []
    nested_sections = 0
    assignments = 0
    sensitive_assignments = 0

    for kind, obj, depth in _walk_elements(model.elements):
        if kind == "Section":
            nested_sections = max(nested_sections, depth + 1)

            section_name = _key_to_str(obj.name)
            if not section_name:
                errors.append("A section without a name was found.")

        elif kind == "Assignment":
            assignments += 1
            cls_name = obj.__class__.__name__

            if cls_name == "SensitiveAssignment":
                sensitive_assignments += 1
                value_cls = obj.value.__class__.__name__

                if value_cls != "EnvReference":
                    errors.append(
                        f"Sensitive key '{obj.key}' must use an environment reference."
                    )

                if not getattr(obj.value, "ref", None):
                    errors.append(
                        f"Sensitive key '{obj.key}' has an invalid environment reference."
                    )

            elif cls_name == "RegularAssignment":
                key_name = _key_to_str(obj.key)
                value_text = _assignment_value_repr(obj)

                # If a sensitive key appears as a regular assignment, it is insecure.
                if key_name.upper() in SENSITIVE_KEYS:
                    errors.append(
                        f"Sensitive key '{key_name}' must use an environment reference."
                    )

                elif key_name.lower().endswith(("password", "secret", "token", "apikey", "api_key")):
                    warnings.append(
                        f"Key '{key_name}' looks sensitive but is not explicitly listed as sensitive."
                    )

                if value_text == "":
                    warnings.append(f"Key '{key_name}' has an empty value.")

    secure_ok = len(errors) == 0

    return {
        "file": source_name,
        "parsed_ok": True,
        "secure_ok": secure_ok,
        "errors": errors,
        "warnings": warnings,
        "nested_sections": nested_sections,
        "assignments": assignments,
        "sensitive_assignments": sensitive_assignments,
    }


def validate_config_file(file_path: str) -> Dict[str, Any]:
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    return validate_config_text(text, source_name=file_path)


def validate_repository_configs(root_path: str) -> pd.DataFrame:
    """
    Recursively validates supported config files in a repository and returns a DataFrame.
    """
    rows: List[Dict[str, Any]] = []

    for current_root, _, files in os.walk(root_path):
        for name in sorted(files):
            file_path = os.path.join(current_root, name)
            if is_supported_config_file(file_path):
                result = validate_config_file(file_path)
                rows.append({
                    "file": result["file"],
                    "parsed_ok": result["parsed_ok"],
                    "secure_ok": result["secure_ok"],
                    "nested_sections": result["nested_sections"],
                    "assignments": result["assignments"],
                    "sensitive_assignments": result["sensitive_assignments"],
                    "errors_count": len(result["errors"]),
                    "warnings_count": len(result["warnings"]),
                    "errors": " | ".join(result["errors"]),
                    "warnings": " | ".join(result["warnings"]),
                })

    if not rows:
        return pd.DataFrame(columns=[
            "file",
            "parsed_ok",
            "secure_ok",
            "nested_sections",
            "assignments",
            "sensitive_assignments",
            "errors_count",
            "warnings_count",
            "errors",
            "warnings",
        ])

    return pd.DataFrame(rows)