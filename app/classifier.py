from pyformlang.finite_automaton import DeterministicFiniteAutomaton, State, Symbol

SIGMA = {
    "API_KEY",
    "HARDCODED_PASSWORD",
    "PRINT_SENSITIVE",
    "TODO_COMMENT",
    "SUSPICIOUS_URL",
    "AWS_API_KEY",
    "INTERNAL_IP",
    "OTHER",
}


def normalize_token(token: str) -> str:
    return token if token in SIGMA else "OTHER"


# =========================================================
# 1. SAFE CLASSIFIER
# =========================================================
def build_safe_dfa():
    """
    Accepts only files with no risky tokens.
    Accepted examples:
        []
        ["OTHER"]
        ["OTHER", "OTHER"]

    Rejected examples:
        ["TODO_COMMENT"]
        ["API_KEY"]
        ["AWS_API_KEY"]
    """
    dfa = DeterministicFiniteAutomaton()

    q_start = State("safe_start")
    q_safe = State("safe_ok")
    q_reject = State("safe_reject")

    dfa.add_start_state(q_start)
    dfa.add_final_state(q_safe)

    # From start
    dfa.add_transition(q_start, Symbol("OTHER"), q_safe)

    for token in SIGMA - {"OTHER"}:
        dfa.add_transition(q_start, Symbol(token), q_reject)

    # From safe
    dfa.add_transition(q_safe, Symbol("OTHER"), q_safe)

    for token in SIGMA - {"OTHER"}:
        dfa.add_transition(q_safe, Symbol(token), q_reject)

    # Reject sink
    for token in SIGMA:
        dfa.add_transition(q_reject, Symbol(token), q_reject)

    return dfa


def run_safe_dfa(tokens):
    if not tokens:
        return True

    dfa = build_safe_dfa()
    current_state = State("safe_start")

    for token in tokens:
        symbol = Symbol(normalize_token(token))
        next_state = dfa._transition_function(current_state, symbol)

        if isinstance(next_state, (list, set, tuple)):
            current_state = next(iter(next_state))
        else:
            current_state = next_state

    return current_state.value  == "safe_ok"


# =========================================================
# 2. NEEDS REVIEW CLASSIFIER
# =========================================================
def build_needs_review_dfa():
    """
    Accepts files with suspicious patterns or secrets,
    but NOT confirmed violations.

    Accepted examples:
        ["TODO_COMMENT"]
        ["SUSPICIOUS_URL"]
        ["INTERNAL_IP"]
        ["API_KEY"]
        ["HARDCODED_PASSWORD"]

    Rejected examples:
        ["AWS_API_KEY"]
        ["HARDCODED_PASSWORD", "PRINT_SENSITIVE"]
        ["API_KEY", "PRINT_SENSITIVE"]
    """
    dfa = DeterministicFiniteAutomaton()

    q_start = State("review_start")
    q_review = State("review_ok")
    q_reject = State("review_reject")

    dfa.add_start_state(q_start)
    dfa.add_final_state(q_review)

    review_tokens = {
        "API_KEY",
        "HARDCODED_PASSWORD",
        "TODO_COMMENT",
        "SUSPICIOUS_URL",
        "INTERNAL_IP",
        "PRINT_SENSITIVE",
    }

    # From start
    dfa.add_transition(q_start, Symbol("OTHER"), q_start)

    for token in review_tokens:
        dfa.add_transition(q_start, Symbol(token), q_review)

    dfa.add_transition(q_start, Symbol("AWS_API_KEY"), q_reject)

    # From review
    dfa.add_transition(q_review, Symbol("OTHER"), q_review)

    for token in review_tokens:
        dfa.add_transition(q_review, Symbol(token), q_review)

    dfa.add_transition(q_review, Symbol("AWS_API_KEY"), q_reject)

    # Reject sink
    for token in SIGMA:
        dfa.add_transition(q_reject, Symbol(token), q_reject)

    return dfa


def run_needs_review_dfa(tokens):
    if not tokens:
        return False

    normalized_tokens = [normalize_token(token) for token in tokens]
    token_set = set(normalized_tokens)

    # Absolute violation rules must be rejected here
    if "AWS_API_KEY" in token_set:
        return False

    if "PRINT_SENSITIVE" in token_set and "HARDCODED_PASSWORD" in token_set:
        return False

    if "PRINT_SENSITIVE" in token_set and "API_KEY" in token_set:
        return False

    dfa = build_needs_review_dfa()
    current_state = State("review_start")

    for token in normalized_tokens:
        symbol = Symbol(token)
        next_state = dfa._transition_function(current_state, symbol)

        if isinstance(next_state, (list, set, tuple)):
            current_state = next(iter(next_state))
        else:
            current_state = next_state

    return current_state.value  == "review_ok"


# =========================================================
# 3. SECURITY VIOLATION CLASSIFIER
# =========================================================
def build_security_violation_dfa():
    """
    Accepts only confirmed security violations.

    Accepted examples:
        ["AWS_API_KEY"]
        ["HARDCODED_PASSWORD", "PRINT_SENSITIVE"]
        ["API_KEY", "PRINT_SENSITIVE"]

    Rejected examples:
        []
        ["TODO_COMMENT"]
        ["API_KEY"]
        ["INTERNAL_IP"]
    """
    dfa = DeterministicFiniteAutomaton()

    q_start = State("violation_start")
    q_secret_seen = State("violation_secret_seen")
    q_violation = State("violation_ok")
    q_non_violation = State("violation_no")

    dfa.add_start_state(q_start)
    dfa.add_final_state(q_violation)

    # Start state
    dfa.add_transition(q_start, Symbol("API_KEY"), q_secret_seen)
    dfa.add_transition(q_start, Symbol("HARDCODED_PASSWORD"), q_secret_seen)
    dfa.add_transition(q_start, Symbol("AWS_API_KEY"), q_violation)

    for token in {"PRINT_SENSITIVE", "TODO_COMMENT", "SUSPICIOUS_URL", "INTERNAL_IP", "OTHER"}:
        dfa.add_transition(q_start, Symbol(token), q_non_violation)

    # Secret has been seen
    dfa.add_transition(q_secret_seen, Symbol("PRINT_SENSITIVE"), q_violation)
    dfa.add_transition(q_secret_seen, Symbol("AWS_API_KEY"), q_violation)
    dfa.add_transition(q_secret_seen, Symbol("API_KEY"), q_secret_seen)
    dfa.add_transition(q_secret_seen, Symbol("HARDCODED_PASSWORD"), q_secret_seen)
    dfa.add_transition(q_secret_seen, Symbol("TODO_COMMENT"), q_secret_seen)
    dfa.add_transition(q_secret_seen, Symbol("SUSPICIOUS_URL"), q_secret_seen)
    dfa.add_transition(q_secret_seen, Symbol("INTERNAL_IP"), q_secret_seen)
    dfa.add_transition(q_secret_seen, Symbol("OTHER"), q_secret_seen)

    # Once violation is confirmed, stay there
    for token in SIGMA:
        dfa.add_transition(q_violation, Symbol(token), q_violation)

    # Non-violation path can still become a violation later
    dfa.add_transition(q_non_violation, Symbol("API_KEY"), q_secret_seen)
    dfa.add_transition(q_non_violation, Symbol("HARDCODED_PASSWORD"), q_secret_seen)
    dfa.add_transition(q_non_violation, Symbol("AWS_API_KEY"), q_violation)

    for token in {"PRINT_SENSITIVE", "TODO_COMMENT", "SUSPICIOUS_URL", "INTERNAL_IP", "OTHER"}:
        dfa.add_transition(q_non_violation, Symbol(token), q_non_violation)

    return dfa


def run_security_violation_dfa(tokens):
    if not tokens:
        return False

    dfa = build_security_violation_dfa()
    current_state = State("violation_start")

    for token in tokens:
        symbol = Symbol(normalize_token(token))
        next_state = dfa._transition_function(current_state, symbol)

        if isinstance(next_state, (list, set, tuple)):
            current_state = next(iter(next_state))
        else:
            current_state = next_state

    return current_state.value  == "violation_ok"


# =========================================================
# ORCHESTRATOR
# =========================================================
def classify_tokens_detailed(tokens):
    normalized_tokens = [normalize_token(token) for token in tokens]

    if run_safe_dfa(normalized_tokens):
        return {
            "classification": "Safe",
            "accepted_by": "SafeClassifier",
            "final_state": "safe_ok",
            "tokens": normalized_tokens,
        }

    if run_needs_review_dfa(normalized_tokens):
        return {
            "classification": "Needs Review",
            "accepted_by": "NeedsReviewClassifier",
            "final_state": "review_ok",
            "tokens": normalized_tokens,
        }

    if run_security_violation_dfa(normalized_tokens):
        return {
            "classification": "Security Violation",
            "accepted_by": "SecurityViolationClassifier",
            "final_state": "violation_ok",
            "tokens": normalized_tokens,
        }

    # Defensive fallback
    return {
        "classification": "Needs Review",
        "accepted_by": "FallbackRule",
        "final_state": "review_fallback",
        "tokens": normalized_tokens,
    }


def classify_tokens(tokens):
    return classify_tokens_detailed(tokens)["classification"]