# 2. Clasificación con autómatas finitos (DFA)

## Intuición

Ya tenemos una **secuencia de tokens** (no el texto crudo). Ahora queremos etiquetar el archivo en tres cajones:

- **Safe** — no hay señales fuertes de riesgo.  
- **Needs Review** — hay cosas raras, pero no armamos el combo “gravísimo”.  
- **Security Violation** — por ejemplo secreto + print, o ciertos tokens que el enunciado trata como violación directa.

Cada categoría la modelamos con un **DFA** distinto en `pyformlang`; al final el programa decide cuál aplica según las reglas que programamos.

---

## Alfabeto de tokens

Σ = {
 `API_KEY`, `HARDCODED_PASSWORD`, `PRINT_SENSITIVE`,
 `TODO_COMMENT`, `SUSPICIOUS_URL`, `AWS_API_KEY`,
 `INTERNAL_IP`, `OTHER`
}

---

## DFA 1: “¿Es safe de verdad?”

**Tipo:** DFA (determinista).

**5-tupla (resumida):**

- Q = {`safe_start`, `safe_ok`, `safe_reject`}  
- Σ = el alfabeto de arriba  
- q₀ = `safe_start`  
- F = {`safe_ok`}  

**δ en palabras:** desde el inicio, si solo ves `OTHER` llegás a “ok”. Apenas aparece **cualquier** token “picante”, vas a rechazo y te quedás ahí. Es el autómata del perfeccionista: una sola mancha y no es safe.

---

## DFA 2: “¿Va a revisión humana?”

Q = {`review_start`, `review_ok`, `review_reject`}  
q₀ = `review_start`  
F = {`review_ok`}  

**Idea:** acepta cosas sospechosas o incompletas **sin** llegar al peor caso que modelamos en el tercer DFA (por ejemplo ciertos combos con print + secreto, o AWS key según las reglas).

---

## DFA 3: “¿Esto ya es violación?”

Q = {
  `violation_start`,
  `violation_secret_seen`,
  `violation_ok`,
  `violation_no`
}

q₀ = `violation_start`  
F = {`violation_ok`}  

**Transiciones que importan (a grandes rasgos):**

- Ves password/api key → estado de “ya vi un secreto”.  
- Si después viene print sensible → violación.  
- `AWS_API_KEY` puede mandarte directo a violación según el diseño.

---

## Ejemplo que se entiende a ojo

Secuencia: `HARDCODED_PASSWORD` → `PRINT_SENSITIVE`  
**Resultado:** **Security Violation** (el cuento clásico: guardé la clave y la imprimí).

---

## Por qué nos alcanza un autómata finito

Los tokens son un **alfabeto finito** y las condiciones que modelamos son **memoria finita** (“¿ya vi un secreto?”, “¿estoy en violación?”). No necesitamos contar paréntesis infinitos acá: eso lo dejamos para la parte de gramática en configs.

Por eso un DFA es razonable; si el lenguaje de secuencias fuera más rico (tipo anidamiento arbitrario de eventos con stack), habría que subir de modelo.
