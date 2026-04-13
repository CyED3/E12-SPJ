# Chomsky – analizador de seguridad en código

Hicimos una herramienta que revisa código y configs buscando cosas peligrosas (contraseñas sueltas, keys, etc.). Por detrás usa cosas de **lenguajes formales**: expresiones regulares para detectar, **autómatas finitos** para decidir si el archivo va en “safe / revisar / violación”, y **transductores** para proponer cambios más seguros. La parte de gramática para configs “bien formadas” está explicada en `docs/`.

---

## Dónde está cada cosa (lo que pide la tarea)

| Lo que piden | Dónde lo dejamos |
|--------------|------------------|
| Documentación en Markdown dentro de `docs/` | [docs/README.md](docs/README.md) y los archivos numerados |
| Cómo instalar, dependencias y cómo usarlo | Aquí abajo + [docs/USER_GUIDE.md](docs/USER_GUIDE.md) |
| Explicación de la gramática y los autómatas | [docs/04_cfg_grammar.md](docs/04_cfg_grammar.md), [docs/02_automata.md](docs/02_automata.md), y lo demás en `docs/` |

---

## Qué hace el proyecto (en pocas palabras)

Pasas un archivo o una carpeta y Chomsky te dice si se ve **seguro**, si **merece revisión** o si hay una **violación clara** (por ejemplo contraseña en duro y después un `println` de eso). Si le dices que sí, puede intentar arreglar cosas (por ejemplo mandar valores sensibles a variables de entorno). El flujo es: **detectar → clasificar → transformar**; la validación estructural con CFG está documentada para la parte de configuración.

---

## Dependencias

En la raíz del repo:

```bash
pip install -r requirements.txt
```

- **pyformlang**: autómatas y transductores.  
- **pandas**: armamos CSV cuando analizás un directorio completo.  

Lo demás es biblioteca estándar de Python (`re`, `os`, etc.).

---

## Cómo instalarlo

1. Clonás el repo (o el que te dieron por Classroom).  
2. Te recomendamos un entorno virtual:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

   En Linux/macOS: `source .venv/bin/activate`

3. Instalás dependencias:

   ```bash
   pip install -r requirements.txt
   ```

---

## Cómo usarlo

Desde la **carpeta raíz** del proyecto (donde está la carpeta `app/`):

```bash
python -m app.cli [ruta]
```

- **`ruta`**: opcional. Puede ser relativa a la raíz o una ruta absoluta; si no la encuentra ahí, también busca en `samples/`. Si no pasás nada, te lista `samples/` y te pide que escribas qué analizar.  
- Después te pregunta si querés **aplicar** el refactor automático (`y`/`n`). Eso conviene leerlo con calma en [docs/USER_GUIDE.md](docs/USER_GUIDE.md) antes de tocar un proyecto real.

**Ejemplos rápidos:**

```bash
python -m app.cli samples/insecure.java
python -m app.cli sample_project
```

---

## Cómo está armado el código

`detector.py` → `classifier.py` → `transformer.py`, y `cli.py` es el que orquesta todo. Los detalles formales (regex, tuplas del DFA, FST, CFG) están en `docs/` por si el profe quiere ver el diseño.

---

## Tecnologías

Python 3.10+, pyformlang, pandas.

---

## Autores

- Sebastián Romero Leon  
- Paula Andrea Piedrahita  
- Jean Carlo Ocampo  

Si el profe pide IDE o paralelo, sumalo acá en una línea.
