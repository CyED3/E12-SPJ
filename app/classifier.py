from pyformlang.finite_automaton import DeterministicFiniteAutomaton, State, Symbol

Q0 = State("q0") # Safe so far
Q1 = State("q1") # Secret detected
Q2 = State("q2") # Suspicious but not a definite leak
Q3 = State("q3") # Confirmed security violation

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

def build_security_dfa():
    dfa = DeterministicFiniteAutomaton()

    dfa.add_start_state(Q0)

    dfa.add_final_state(Q0)
    dfa.add_final_state(Q1)
    dfa.add_final_state(Q2)
    dfa.add_final_state(Q3)

    # q0
    dfa.add_transition(Q0, Symbol("API_KEY"), Q1)
    dfa.add_transition(Q0, Symbol("HARDCODED_PASSWORD"), Q1)
    dfa.add_transition(Q0, Symbol("PRINT_SENSITIVE"), Q2)
    dfa.add_transition(Q0, Symbol("TODO_COMMENT"), Q2)
    dfa.add_transition(Q0, Symbol("SUSPICIOUS_URL"), Q2)
    dfa.add_transition(Q0, Symbol("AWS_API_KEY"), Q3)
    dfa.add_transition(Q0, Symbol("INTERNAL_IP"), Q2)
    dfa.add_transition(Q0, Symbol("OTHER"), Q0)

    # q1
    dfa.add_transition(Q1, Symbol("API_KEY"), Q1)
    dfa.add_transition(Q1, Symbol("HARDCODED_PASSWORD"), Q1)
    dfa.add_transition(Q1, Symbol("PRINT_SENSITIVE"), Q3)
    dfa.add_transition(Q1, Symbol("TODO_COMMENT"), Q1)
    dfa.add_transition(Q1, Symbol("SUSPICIOUS_URL"), Q1)
    dfa.add_transition(Q1, Symbol("AWS_API_KEY"), Q3)
    dfa.add_transition(Q1, Symbol("INTERNAL_IP"), Q1)
    dfa.add_transition(Q1, Symbol("OTHER"), Q1)

    # q2
    dfa.add_transition(Q2, Symbol("API_KEY"), Q1)
    dfa.add_transition(Q2, Symbol("HARDCODED_PASSWORD"), Q1)
    dfa.add_transition(Q2, Symbol("PRINT_SENSITIVE"), Q2)
    dfa.add_transition(Q2, Symbol("TODO_COMMENT"), Q2)
    dfa.add_transition(Q2, Symbol("SUSPICIOUS_URL"), Q2)
    dfa.add_transition(Q2, Symbol("AWS_API_KEY"), Q3)
    dfa.add_transition(Q2, Symbol("INTERNAL_IP"), Q2)
    dfa.add_transition(Q2, Symbol("OTHER"), Q2)

    # q3
    for token in SIGMA:
        dfa.add_transition(Q3, Symbol(token), Q3)

    return dfa


def run_dfa(tokens):
    dfa = build_security_dfa()
    current_state = Q0

    for token in tokens:
        symbol = Symbol(token if token in SIGMA else "OTHER")
        next_state = dfa._transition_function(current_state, symbol)

        if isinstance(next_state, (list, set, tuple)):
            current_state = next(iter(next_state))
        else:
            current_state = next_state

    return current_state


def classify_tokens(tokens):
    final_state = run_dfa(tokens)

    if final_state == Q0:
        return "Safe"
    elif final_state == Q1 or final_state == Q2:
        return "Needs Review"
    else:
        return "Security Violation"