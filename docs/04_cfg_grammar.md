
# 4. Context-Free Grammar for Secure Configuration Validation

## Objective

This grammar defines a small secure configuration language for the structural validation phase of the project. It supports:

- well-formed key-value assignments,
- hierarchical sections,
- recursive nesting,
- balanced braces,
- and secure references to environment variables.

The grammar validates the **structure** of configuration files, while the validator enforces the policy that sensitive keys must use environment variable references.

---

## Formal grammar definition

We define the grammar as:

G = (V, $\Sigma$, P, S)

---

## Non-terminals


V = {
Config, Element, Section, Assignment, SensitiveAssignment, RegularAssignment, Key, SensitiveKey, Value, EnvReference, Boolean, BareWord
}


---

## Terminals

$\Sigma$ = {
ID, STRING, INT, '{', '}', '=', '.', '${', 'true', 'false'
}
Descriptions:

- `ID` = identifier  
- `STRING` = quoted string literal  
- `INT` = integer literal  
- `{`, `}` = block delimiters  
- `=` = assignment operator  
- `.` = key separator for compound keys  
- `${` and `}` = environment reference delimiters  
- `true`, `false` = boolean literals  

---

## Start symbol

S = Config

---

## Production rules (EBNF)

```ebnf
Config              ::= Element*

Element             ::= Section | Assignment

Section             ::= Key "{" Element* "}"

Assignment          ::= SensitiveAssignment | RegularAssignment

SensitiveAssignment ::= SensitiveKey "=" EnvReference

RegularAssignment   ::= Key "=" Value

Key                 ::= ID ("." ID)*

SensitiveKey        ::= "DB_PASSWORD"
                      | "API_KEY"
                      | "SECRET_KEY"
                      | "AWS_ACCESS_KEY_ID"
                      | "APP_PASSWORD"
                      | "APP_API_KEY"
                      | "APP_BASE_URL"

Value               ::= STRING | INT | Boolean | EnvReference | BareWord

EnvReference        ::= "${" ID "}"

Boolean             ::= "true" | "false"

BareWord            ::= letter_or_digit_or_symbol+
````

---

## Examples

### Valid secure assignments

```text
DB_PASSWORD=${APP_PASSWORD}
API_KEY=${APP_API_KEY}
APP_BASE_URL=${APP_BASE_URL}
```

### Invalid insecure assignments

```text
DB_PASSWORD=admin123
API_KEY="local-dev-key"
APP_BASE_URL=http://internal.company.local/api
```

### Valid nested configuration

```text
app {
    database {
        credentials {
            DB_PASSWORD=${APP_PASSWORD}
        }
    }
}
```

### Valid dotted keys

```text
service.url=${APP_BASE_URL}
security.api.enabled=true
```

---

## Why this language is not regular

This language is **not regular** because it allows **arbitrarily nested sections with balanced braces**.

For example:

```text
app {
    database {
        credentials {
            DB_PASSWORD=${APP_PASSWORD}
        }
    }
}
```

To recognize whether every opening brace `{` has a matching closing brace `}` at arbitrary depth, the parser must keep track of nested structure. A finite automaton cannot do this in the general case because it has only finite memory and no stack.

Balanced delimiters are a classical example of a non-regular language.

---

## Why a context-free grammar is required

A context-free grammar is required because:

1. **Recursive nesting**

   * A `Section` contains `Element*`
   * Each `Element` may again be a `Section`
   * This creates recursive hierarchical structure

2. **Balanced braces**

   * The grammar must enforce properly matched `{` and `}`
   * This cannot be done by regex or DFA for arbitrary depth

3. **Hierarchical syntax**

   * The language is tree-structured rather than flat
   * CFGs are the appropriate formal model for such syntax

Therefore, a CFG is necessary for the structural validation phase of the secure configuration language.

---

## Relation to the implementation

This grammar is implemented using **textX** and used to validate configuration files after the previous stages of the pipeline:

```text
Detection (Regex)
→ Classification (DFA)
→ Transformation (FST)
→ Validation (CFG with textX)
```

The CFG ensures that transformed configuration files remain structurally valid and conform to the secure configuration language.

