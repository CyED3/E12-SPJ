# 4. Gramática libre de contexto para configuración “segura”

## Para qué sirve esto

Imaginate un mini-lenguaje para archivos tipo `.env` o configs con secciones: que las asignaciones estén bien escritas, que se puedan anidar bloques, y que las claves sensibles **no** puedan llevar un valor plano tipo `admin123`, sino algo como `${MI_VARIABLE}`.

Eso no se puede “cerrar” bien solo con regex si querés **anidar** llaves y asegurar que cierren parejo: por eso el enunciado pide una **CFG**. Acá dejamos la gramática y la justificación en limpio.

---

## Terminales y no terminales

**Terminales** (tokens idealizados que produciría un lexer):

| Símbolo | Idea |
|---------|------|
| `LBRACE`, `RBRACE` | `{` y `}` |
| `ID` | nombre de sección o clave |
| `=` | asignación |
| `STRING`, `NUMBER` | literales |
| (referencia env) | algo como `${` + `ID` + `}` |

**No terminales:** `Config`, `Section`, `Block`, `Entry`, `Key`, `Value`, `PlainValue`.  
**Símbolo inicial:** `Config`.

---

## Reglas (estilo EBNF)

```text
Config     ::= Block*
Block      ::= Section | Entry

Section    ::= 'section' ID '{' Config '}'
           |   '{' Config '}'

Entry      ::= Key '=' Value

Key        ::= ID
Value      ::= EnvRef | PlainValue
PlainValue ::= STRING | NUMBER
EnvRef     ::= '${' ID '}'

SensitiveKey ::= 'DB_PASSWORD' | 'API_KEY' | 'AWS_SECRET' | 'PASSWORD' | 'SECRET'
```

En un validador real, la idea es: si la `Key` cae en **SensitiveKey**, el `Value` **tiene** que ser solo `EnvRef`. El resto de las claves pueden usar literal o referencia, según la política que definan.

---

## Ejemplos que entran y salen

**Bien** (secreto vía entorno):

```text
DB_PASSWORD=${SECURE_DB_PASSWORD}
```

**Mal** para una política estricta (valor en claro):

```text
DB_PASSWORD=admin123
```

**Anidado** (acá se ve la recursión `Config` dentro de `Section`):

```text
section app {
  section db {
    DB_PASSWORD=${SECURE_DB_PASSWORD}
  }
}
```

---

## Por qué esto no es un lenguaje regular

1. **Llaves balanceadas:** contar “cuántas abrí y cuántas cerré” en profundidad arbitraria es el clásico ejemplo de algo que un autómata finito no puede hacer solo con estados finitos (necesitás memoria tipo pila).

2. **Recursión:** adentro de una sección volvés a tener `Config`, que otra vez puede tener secciones… Eso es estructura de **árbol**, típica de CFG.

Las regex siguen sirviendo para **pistas** en una línea (“se parece a un password”), pero para decir “este archivo respeta la jerarquía y la política de secretos” conviene un parser con gramática (en el curso suelen mostrar **textX**; acá dejamos el diseño formal; el código del repo hoy se concentra más en la parte Java + regex + DFA + FST).

---

## Cómo se relaciona con el repo

En `app/` está cableado el pipeline **regex → DFA → FST** para los archivos que soportamos. Esta gramática es el diseño del paso de **validación estructural** que describe la tarea integradora; un `.tx` de textX sería la implementación “bonita” con mensajes de error claros.

Para ver cómo encaja la detección y los autómatas con el código, mirá [01_regex_doc.md](01_regex_doc.md), [02_automata.md](02_automata.md) y [03_transducer.md](03_transducer.md).
