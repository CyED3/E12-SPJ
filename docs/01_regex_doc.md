# 1. Detección con expresiones regulares

## Qué problema resolvemos acá

Antes de meter autómatas, el archivo es solo texto. Con **regex** buscamos patrones que suelen ir mal en repos reales (keys, passwords en duro, prints feos, etc.). La salida no es “sí/no” todavía: armamos una **lista de tokens** por línea, que después le van a entrar al clasificador.

En criollo: primero marcamos “esto parece X”, sin todavía decidir la gravedad final del archivo.

---

## Patrones que usamos y qué lenguaje aproximan

### 1. Clave de AWS

**Regex:** `AKIA[0-9A-Z]{16}`

**Lenguaje (idea):** cadenas que empiezan en `AKIA` y siguen con exactamente 16 caracteres alfanuméricos en mayúsculas/dígitos.

---

### 2. Contraseña en duro

**Regex:** `(?:String\s+)?password\s*=\s*"[^"]+"`

**Qué capturamos:** asignaciones a una variable llamada `password` con un string literal (en Java puede ir con `String` adelante o no).

**Ejemplo típico:** `password = "admin123"`

---

### 3. API key en variable

**Regex:** `(?:String\s+)?api[_-]?key\s*=\s*"[^"]+"`

**Qué capturamos:** `api_key`, `api-key`, `apikey`, etc., con string literal.

---

### 4. Print sensible

**Regex:** `^\s*System\.out\.println\s*\(\s*(?:password|api[_-]?key)\s*\)\s*;?\s*$`

**Qué capturamos:** líneas donde se imprime `password` o la api key. Eso junto con el punto anterior es lo que más nos interesa para la “violación fuerte”.

---

### 5. Comentarios TODO

**Regex:** `//\s*TODO:?.*`

**Idea:** marcamos deuda técnica; a veces es inocente, a veces es “acá falta arreglar algo peligroso”.

---

### 6. URL sospechosa

**Regex:** `https?://(?:localhost|internal|dev|staging)[^\s"']*`

**Idea:** URLs que apuntan a entornos internos o de desarrollo, que no deberían colarse en producción tal cual.

---

### 7. IP privada

**Regex:** `\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3})\b`

**Idea:** rangos IPv4 privados comunes (10.x, 192.168.x, 172.16–31.x).

---

## Dónde está en el código

- `detect_issues()` — saca los matches con contexto.  
- `extract_tokens()` — arma la secuencia de tokens del archivo.  
- `classify_line()` — decide qué etiqueta le toca a cada línea.

Si algo no matchea con ningún patrón “interesante”, en la práctica cae en algo tipo `OTHER` para el siguiente paso.
