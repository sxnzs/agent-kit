# Neutral Latin American Spanish

Read when drafting, rewriting, or reviewing Spanish prose for humans (explainers, docs, guides, messages, or scripts). Use neutral Latin American Spanish (Mexico-friendly, *tú*).

## Concrete patterns to avoid

### 1. Lexicon (use LatAm neutral, drop Spain-only words)

- Use: `computadora`, `celular`, `carpeta`, `archivo`, `carro`, `rentar`, `platicar`, `lentes`, `manejar`.
- Avoid: `ordenador`, `móvil` (prefer `celular` for phones), `fichero`, `coche`, `ascensor`, `vale` (as filler; `vale la pena` is fine), `tío`, `guay`, `mola`, `coger`.

### 2. English calques and AI-Spanish tells

| Avoid | Use instead |
|---|---|
| `hace sentido` | `tiene sentido` |
| `en orden de` | `para` |
| `accesar` | `acceder` or `entrar` |
| `aplicar` (to a job/program) | `postularse` |
| `asumir` (to guess/suppose) | `suponer` |
| `en esencia` / `en última instancia` | cut it and state the claim directly |
| `cabe destacar` / `es importante señalar` | cut it; lead with the fact |
| `jugar un papel clave` | name the exact verb (`decide`, `bloquea`, `controla`) |
| `a través de la utilización de` / `a través de` | `con` or `por` |
| `impulsar` / `fomentar` / `aprovechar al máximo` | concrete action verb |
| `realizar la ejecución / verificación` | `ejecutar` / `verificar` |
| `no es X, sino Y` / `no solo X, sino Y` | state what it is directly |
| `lo cual permite` (chained subordinates) | end the sentence and start a clean second one |

### 3. Rhythm and syntax

- Put the actor and concrete verb first: `"El compilador rechaza el cambio"`, not `"Se procede a rechazar el cambio por parte del compilador"`.
- Keep sentences short and varied (aim for 8 to 20 words; split anything past 30 words).
- Use periods and commas. Never use em-dashes (`—`) or en-dashes (`–`) in prose.
- Keep one Spanish or technical term per concept. Do not rotate synonyms for the same thing.
- Cut chatty filler openings (`Claro, con gusto`, `Por supuesto`, `Excelente pregunta`) and stock endings (`En resumen`, `En conclusión`).

## Before and after examples

Copy the concrete shift shown in each pair: direct subject, short clauses, zero calques.

### Technical explainer

- **Before**: "En esencia, el modelo no es un agente autónomo, sino un predictor de texto que, a través de la utilización de un harness, logra interactuar con el sistema de archivos, lo cual permite realizar la ejecución de comandos."
- **After**: "El modelo solo predice texto. No toca tus archivos ni corre comandos por su cuenta. El harness es el programa alrededor que recibe esa salida, ejecuta la herramienta y le devuelve el resultado."

### Developer documentation

- **Before**: "Es importante señalar que esta configuración juega un papel clave en orden de evitar que el caché se corrompa cuando múltiples procesos accesan el mismo fichero."
- **After**: "Esta configuración evita que el caché se corrompa cuando varios procesos leen y escriben el mismo archivo al mismo tiempo."

### Direct reply to a human

- **Before**: "¡Claro, con gusto! Hace sentido que el test falle de manera intermitente; cabe destacar que ambos casos comparten la misma carpeta temporal, lo cual genera una condición de carrera."
- **After**: "El test falla de forma intermitente porque los dos casos escriben en la misma carpeta temporal. Si cada test crea su propio directorio temporal único, el fallo desaparece."

### Spoken or narrative prose

- **Before**: "A diferencia de las herramientas tradicionales, esta arquitectura aprovecha al máximo el contexto disponible para impulsar un flujo de trabajo más fluido."
- **After**: "En lugar de releer todo el repositorio en cada paso, guardas el primer ejemplo en la sesión y el modelo rápido sigue ese mismo molde."

## Deterministic check

Run the prose checker before returning any Spanish draft:

```sh
python3 ~/.agents/skills/writing/scripts/check_prose.py --lang es <file>
```

Use `--strict` to also fail on warnings. If the repo has a stricter domain linter, run that too.
