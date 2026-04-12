import os
import shutil
import sys
from typing import Dict, List

from .detector import detect_issues, extract_tokens
from .classifier import classify_tokens_detailed
from .transformer import transform_code
import pandas as pd

SUPPORTED_EXTENSIONS = {".java", ".cfg", ".conf", ".env", ".txt"}
AUTO_FIX_CLASSES = {"Needs Review", "Security Violation"}


def is_supported_file(file_path: str) -> bool:
    _, ext = os.path.splitext(file_path)
    return ext.lower() in SUPPORTED_EXTENSIONS


def resolve_input_path(base_dir: str) -> str:
    samples_dir = os.path.join(base_dir, "samples")

    if len(sys.argv) > 1:
        user_input = sys.argv[1].strip()
    else:
        print("Available sample files/folders:")
        if os.path.exists(samples_dir):
            for name in sorted(os.listdir(samples_dir)):
                print(f" - {name}")
        print()
        user_input = input("Enter a file or folder to analyze: ").strip()

    if not user_input:
        raise ValueError("No input path was provided.")

    if os.path.isabs(user_input):
        path = user_input
    else:
        path = os.path.join(base_dir, user_input)
        if not os.path.exists(path):
            path = os.path.join(samples_dir, user_input)

    if not os.path.exists(path):
        raise FileNotFoundError(f"Path not found: {path}")

    return path


def should_apply_fix(classification: str, changed: bool) -> bool:
    return classification in AUTO_FIX_CLASSES and changed


def write_backup_and_fix(file_path: str, transformed: str) -> str:
    backup_path = file_path + ".bak"
    shutil.copyfile(file_path, backup_path)
    with open(file_path, "w", encoding="utf-8") as output_file:
        output_file.write(transformed)
    return backup_path


def analyze_file(file_path: str, apply_fixes: bool = False) -> Dict:
    with open(file_path, "r", encoding="utf-8") as file:
        code = file.read()

    findings = detect_issues(code)
    tokens = extract_tokens(code)

    classification_result = classify_tokens_detailed(tokens)
    classification = classification_result["classification"]

    env_path = os.path.join(os.path.dirname(file_path), ".env")
    trace = []
    env_entries = {}

    if classification == "Safe":
        transformed = code
        changed = False
    else:
        transformed, env_entries, trace = transform_code(
            code=code,
            classification=classification,
            file_path=file_path,
            env_path=env_path,
        )
        changed = transformed != code

    fixable = should_apply_fix(classification, changed)
    backup_path = None

    print("\n" + "=" * 70)
    print(f"ANALYZED FILE: {file_path}")

    print("\nDETECTED PATTERNS:")
    if not findings:
        print("No issues found.")
    else:
        for finding in findings:
            print(
                f"- {finding['type']} | line={finding.get('line', '?')} | "
                f"match={finding['match']}"
            )

    print("\nTOKEN SEQUENCE:")
    print(classification_result["tokens"])

    print("\nCLASSIFICATION:")
    print(classification)
    print(f"Accepted by: {classification_result['accepted_by']}")
    print(f"Final state: {classification_result['final_state']}")

    print("\nTRANSFORMATION TRACE:")
    if not trace:
        print("No transducer execution needed.")
    else:
        for step in trace:
            print(
                f"Line {step['line']} | token={step['token']} -> action={step['action']}"
            )

    print("\nTRANSFORMATION STATUS:")
    if changed:
        print("Secure refactoring available.")
    else:
        print("No transformation needed.")

    if env_entries:
        print("\nENV ENTRIES:")
        for key, value in env_entries.items():
            print(f"- {key}={value}")

    if apply_fixes and fixable:
        backup_path = write_backup_and_fix(file_path, transformed)
        print(f"\nChanges applied to: {file_path}")
        print(f"Backup created at: {backup_path}")
    elif apply_fixes and classification == "Safe":
        print("\nTransformation skipped because the file was classified as Safe.")

    findings_df = build_findings_df(file_path, findings)
    classification_df = build_classification_df(
        file_path=file_path,
        classification_result=classification_result,
        findings_count=len(findings),
        changed=changed,
        fix_applied=backup_path is not None,
    )
    transformations_df = build_transformations_df(file_path, trace)
    env_df = build_env_df(file_path, env_entries)

    return {
        "file": file_path,
        "classification": classification,
        "accepted_by": classification_result["accepted_by"],
        "final_state": classification_result["final_state"],
        "tokens": classification_result["tokens"],
        "findings_count": len(findings),
        "changed": changed,
        "fix_applied": backup_path is not None,
        "trace": trace,
        "env_entries": env_entries,
        "findings_df": findings_df,
        "classification_df": classification_df,
        "transformations_df": transformations_df,
        "env_df": env_df,
    }


def analyze_directory(dir_path: str, apply_fixes: bool = False) -> List[Dict]:
    results = []

    for root, _, files in os.walk(dir_path):
        for name in sorted(files):
            file_path = os.path.join(root, name)
            if is_supported_file(file_path):
                results.append(analyze_file(file_path, apply_fixes=apply_fixes))

    if not results:
        print("\nNo supported files were found in the directory.")
        return []

    print("\n" + "=" * 70)
    print("REPOSITORY SUMMARY")
    print("=" * 70)

    for result in results:
        print(
            f"{result['file']} -> {result['classification']} "
            f"({result['accepted_by']}, {result['final_state']}) | "
            f"tokens={result['tokens']} | findings={result['findings_count']} | "
            f"changed={result['changed']} | fix_applied={result['fix_applied']}"
        )

    all_findings_df = pd.concat(
        [r["findings_df"] for r in results if not r["findings_df"].empty],
        ignore_index=True
    ) if any(not r["findings_df"].empty for r in results) else pd.DataFrame()

    all_classification_df = pd.concat(
        [r["classification_df"] for r in results if not r["classification_df"].empty],
        ignore_index=True
    ) if any(not r["classification_df"].empty for r in results) else pd.DataFrame()

    all_transformations_df = pd.concat(
        [r["transformations_df"] for r in results if not r["transformations_df"].empty],
        ignore_index=True
    ) if any(not r["transformations_df"].empty for r in results) else pd.DataFrame()

    all_env_df = pd.concat(
        [r["env_df"] for r in results if not r["env_df"].empty],
        ignore_index=True
    ) if any(not r["env_df"].empty for r in results) else pd.DataFrame()

    if not all_findings_df.empty:
        all_findings_df.to_csv("findings_report.csv", index=False)

    if not all_classification_df.empty:
        all_classification_df.to_csv("classification_report.csv", index=False)

    if not all_transformations_df.empty:
        all_transformations_df.to_csv("transformations_report.csv", index=False)

    if not all_env_df.empty:
        all_env_df.to_csv("env_report.csv", index=False)

    print("\nReports generated:")
    print("- findings_report.csv")
    print("- classification_report.csv")
    print("- transformations_report.csv")
    print("- env_report.csv")

    return results

# Data frames

def build_findings_df(file_path: str, findings: List[Dict]) -> pd.DataFrame:
    rows = []
    for finding in findings:
        rows.append({
            "file": file_path,
            "type": finding["type"],
            "match": finding["match"],
            "start": finding["start"],
            "end": finding["end"],
            "line": finding["line"],
            "column": finding["column"],
            "secret_value": finding["secret_value"],
            "severity": finding["severity"],
        })
    return pd.DataFrame(rows)


def build_classification_df(
    file_path: str,
    classification_result: Dict,
    findings_count: int,
    changed: bool,
    fix_applied: bool,
) -> pd.DataFrame:
    return pd.DataFrame([{
        "file": file_path,
        "classification": classification_result["classification"],
        "accepted_by": classification_result["accepted_by"],
        "final_state": classification_result["final_state"],
        "tokens": ", ".join(classification_result["tokens"]),
        "findings_count": findings_count,
        "changed": changed,
        "fix_applied": fix_applied,
    }])


def build_transformations_df(file_path: str, trace: List[Dict]) -> pd.DataFrame:
    rows = []
    for step in trace:
        rows.append({
            "file": file_path,
            "line": step["line"],
            "token": step["token"],
            "action": step["action"],
            "original": step["original"],
            "transformed": step["transformed"],
        })
    return pd.DataFrame(rows)


def build_env_df(file_path: str, env_entries: Dict[str, str]) -> pd.DataFrame:
    rows = []
    for key, value in env_entries.items():
        rows.append({
            "file": file_path,
            "env_key": key,
            "env_value": value,
        })
    return pd.DataFrame(rows)


def main() -> None:
    base_dir = os.path.dirname(os.path.dirname(__file__))

    try:
        input_path = resolve_input_path(base_dir)
        apply_fixes_answer = input("Apply automatic secure refactoring? (y/n): ").strip().lower()
        apply_fixes = apply_fixes_answer == "y"

        if os.path.isfile(input_path):
            analyze_file(input_path, apply_fixes=apply_fixes)
        elif os.path.isdir(input_path):
            analyze_directory(input_path, apply_fixes=apply_fixes)
        else:
            print("The provided path is neither a file nor a directory.")
    except Exception as exc:
        print(f"\nError: {exc}")


if __name__ == "__main__":
    main()