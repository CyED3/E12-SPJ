# Guía de uso — CLI de Chomsky

## Qué es esto

Chomsky recorre **un archivo** o **toda una carpeta** y te cuenta si encuentra patrones raros de seguridad. No es un antivirus: es un laboratorio de la materia, pero sirve para ver el flujo completo (detectar → clasificar → transformar) y, si querés, generar reportes en CSV.

Tipos de archivo que miramos: `.java`, `.cfg`, `.conf`, `.env`, `.txt`.

---

## Antes de empezar

- Python **3.10 o más nuevo** va bien.  
- Instalá lo de `requirements.txt` (está explicado en el README de la raíz).

---

## Cómo lo corrés

Parado en la **raíz del repo** (donde ves la carpeta `app/`):

```bash
python -m app.cli [ruta]
```

- **`ruta`** es opcional: archivo o carpeta. Si la escribís relativa, primero busca desde la raíz del proyecto; si no existe, prueba en `samples/`.  
- Si **no** ponés ruta, el programa te lista lo que hay en `samples/` y te pide que escribas el nombre a mano.

### Ejemplos que podés copiar

```bash
python -m app.cli samples/insecure.java
python -m app.cli sample_project
python -m app.cli sample_project/src/Main.java
```

### La pregunta del millón: ¿aplico el arreglo automático?

Te va a salir: **Apply automatic secure refactoring? (y/n)** (sí, está en inglés en el código).

- **`n`**: solo mirás. Te imprime hallazgos, clasificación, qué haría el transductor, etc., **sin tocar** los archivos. Es lo más seguro para practicar.  
- **`y`**: si el archivo califica como *Needs Review* o *Security Violation* y hay cambios posibles, **sí modifica** el archivo original y deja un **`.bak`** al lado. También puede tocar o crear un **`.env`** cerca del archivo cuando saca secretos a variables de entorno.

**Consejo de persona a persona:** en un proyecto de verdad, usá `git` o copia la carpeta antes de poner `y`. Acá es fácil equivocarse y pisar algo.

---

## Qué significa lo que imprime

Para cada archivo vas a ver más o menos esto:

1. **DETECTED PATTERNS** — lo que encontró el regex (tipo, línea, pedacito de texto).  
2. **TOKEN SEQUENCE** — la “traducción” a etiquetas que le entran al autómata (`HARDCODED_PASSWORD`, etc.).  
3. **CLASSIFICATION** — si quedó **Safe**, **Needs Review** o **Security Violation**, y qué DFA “ganó”.  
4. **TRANSFORMATION TRACE** — línea por línea, qué acción le aplicaría el transductor.  
5. **ENV ENTRIES** — si propone claves/valores para el `.env`.

Si le pasás una **carpeta**, al final hace un **resumen** y deja CSV en la carpeta desde la que ejecutaste el comando (normalmente la raíz del proyecto):

| Archivo | Qué trae |
|---------|----------|
| `findings_report.csv` | Todos los matches |
| `classification_report.csv` | Clasificación por archivo |
| `transformations_report.csv` | Pasos de transformación |
| `env_report.csv` | Variables de entorno sugeridas/escritas |

---

## Si querés leer el lado “formal”

- Regex → [01_regex_doc.md](01_regex_doc.md)  
- DFA → [02_automata.md](02_automata.md)  
- FST → [03_transducer.md](03_transducer.md)  
- Gramática de configs → [04_cfg_grammar.md](04_cfg_grammar.md)  

---

## Si algo falla

- **Path not found**: revisá la ruta o probá un nombre que salga en la lista de `samples/`.  
- Todo se lee como **UTF-8**.  
- Si una carpeta “no hace nada”, puede que no tenga extensiones soportadas o solo archivos ocultos / ignorados.
