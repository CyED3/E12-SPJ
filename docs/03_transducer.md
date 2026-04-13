# 3. Refactor automático con transductores (FST)

## Qué agrega esto respecto al DFA

El autómata solo **acepta o rechaza** (o te dice en qué estado caés). El **transductor** va un paso más: además de leer tokens, **emite acciones** del estilo “reemplazá esta línea por otra” o “comentá esto”. Es la parte “cirujano” del proyecto: ya sabemos que hay problema, ahora proponemos un parche.

---

## Modelo general (para el informe)

Un FST se puede escribir como:

T = (Q, Σ, Γ, δ, ω, q₀, F)

- **Σ** — lo que leés (tokens de seguridad).  
- **Γ** — lo que “escupís” como salida simbólica (acciones de rewrite).  
- **ω** — función que dice qué salida va con cada transición.

En el código de `pyformlang` armamos FST y después esas acciones las traducimos a texto Java / líneas concretas.

---

## FST 1: secretos → variable de entorno

Q = {q0, q1}  
Σ = {`HARDCODED_PASSWORD`, `API_KEY`, `AWS_API_KEY`}  
Γ = {`ENV_PASSWORD`, `ENV_API_KEY`, `ENV_AWS_KEY`}  

**Idea:** un token de secreto dispara la acción correspondiente (password → env de password, etc.).

---

## FST 2: sacar prints peligrosos

Σ = {`PRINT_SENSITIVE`}  
Γ = {`REMOVE_SENSITIVE_PRINT`}

---

## FST 3: limpiar TODOs (línea)

Σ = {`TODO_COMMENT`}  
Γ = {`DELETE_LINE`}

---

## FST 4: URL rara → algo configurable

Σ = {`SUSPICIOUS_URL`}  
Γ = {`ENV_URL`}

---

## FST 5: IP interna

Σ = {`INTERNAL_IP`}  
Γ = {`REDACT_IP`}

---

## Cómo lo bajamos a código

1. Token → acción (vía FST / tabla de transiciones).  
2. Acción → string nuevo de línea (funciones que reescriben Java o config).

---

## Por qué no alcanza “solo un DFA”

Porque acá no queremos un booleano: queremos una **función** entrada → salida (texto transformado). Eso es exactamente el rol del transductor frente al autómata clasificador.
