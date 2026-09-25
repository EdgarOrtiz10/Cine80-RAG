# n8n-qa — Sistema QA multiagente para workflows n8n

Detecta, registra (y en fases posteriores corrige y audita) bugs en los workflows de la
instancia n8n `n8n.eortiz-dev.com`. Estado actual: **F0 + F1 (detección)**.

## Arquitectura

| Capa | Componente | Dónde vive | Qué hace |
|---|---|---|---|
| 0 | `QA - Error Collector` (`MQH3MoijkHW4iwnI`) | n8n | Error Trigger → fila en `qa_events` + alerta Telegram al admin |
| 1 | Orquestador | `.claude/skills/n8n-qa/SKILL.md` | Reparte trabajo, consolida, persiste, reporta |
| 1 | A1 Linter | `.claude/agents/n8n-qa-linter.md` + `qa/lint_workflow.py` | Análisis estático |
| 1 | A2 Forense | `.claude/agents/n8n-qa-forense.md` + `qa/check_execution.py` | Aserciones sobre ejecuciones |
| 1 | Registro | `qa/registry.py` + `state/bug_registry.json` | Deduplicación por fingerprint, detección de regresiones |

## Catálogo de reglas

| ID | Sev. | Detecta | Origen |
|---|---|---|---|
| DF-01 | high | `$json` leído tras un nodo con efecto secundario (Telegram, escritura Sheets); atraviesa IF/Switch/Filter | Bug Append Gastos 25-09-2026 |
| SD-02 | high | Pendiente de `staticData` recuperado como `null` y esparcido (`...datos`) sin guardia | `Recuperar y Detectar Acción` |
| VD-01 | high | Workflow activo con borrador ≠ versión publicada | Autosave `1692898c` sin publicar |
| SF-01 | high | *(runtime)* Nodo terminó OK con campos obligatorios vacíos | Ejecución #441 |
| EX-01 | high | *(runtime)* Ejecución con status=error | — |
| SF-02 | medium | Mensaje de éxito alcanzable tras una escritura sin guardia de validación | "✅ Gasto registrado" con fila vacía |
| TG-01 | medium | Texto dinámico con `parse_mode` explícito y sin escapar | `Send Respuesta` |
| AG-01 | medium | *(runtime)* Agente respondió "sin datos" tras una sola tool vacía sin probar las demás | Ejecución #442 |
| SD-01 | low | Estado pendiente en `staticData` sin marca de tiempo (nunca expira) | — |

Suprimir un hallazgo concreto: añade `qa-ignore: <RULE_ID>` en las notas del nodo en n8n.

## Uso

```bash
cd n8n-qa
python3 -m qa.lint_workflow <workflow.json> [--format json] [--min-severity medium]
python3 -m qa.check_execution <execution.json> assertions/<workflowId>.json
python3 -m qa.registry merge <findings.json>...
python3 -m unittest discover -s tests -t .
```

`<workflow.json>` = salida de `get_workflow_details` del MCP; `<execution.json>` = salida de
`get_execution` con `includeData: true`. Solo stdlib de Python 3.11, sin dependencias.

En Claude Code: "QA" (barrido de todos los workflows activos) o "QA <workflowId>".

## Estado y Data Tables

El MCP de n8n solo puede **insertar** filas en Data Tables (no leerlas ni actualizarlas), así
que la fuente de verdad del registro es `state/bug_registry.json` (versionado en git). Las
Data Tables son una bitácora append-only visible desde n8n:

| Data Table | ID | Uso |
|---|---|---|
| `qa_events` | `ntI3GbOIPCVcHZO7` | Errores capturados por el Error Collector |
| `bug_registry` | `ZnL7Qw6OmW52TmTm` | Bugs nuevos (una fila por primera aparición) |
| `golden_cases` | `KKbMvV8pFJGgjwF6` | Casos de regresión (se llena en F2) |
| `qa_runs` | `BTmcS1dpdPlqCQtr` | Una fila por barrido |

`state/watermarks.json` guarda la última ejecución revisada por workflow.

## Añadir un workflow a la vigilancia

1. Crea `assertions/<workflowId>.json` (ver el del bot de finanzas como plantilla).
2. En n8n → Settings del workflow → **Error workflow** = `QA - Error Collector`.
   Nota: si el workflow tiene su propio Error Trigger interno, el Error workflow configurado
   tiene prioridad sobre él.

## Seguridad

En F1 ningún agente modifica, ejecuta, publica ni archiva workflows. Allowlist propuesta
para `.claude/settings.json` (debe aplicarla el propietario del repo):

```json
{
  "permissions": {
    "allow": [
      "mcp__n8n__search_workflows", "mcp__n8n__get_workflow_details",
      "mcp__n8n__get_workflow_history", "mcp__n8n__get_workflow_version",
      "mcp__n8n__search_executions", "mcp__n8n__get_execution",
      "mcp__n8n__search_data_tables", "mcp__n8n__add_data_table_rows"
    ],
    "deny": [
      "mcp__n8n__publish_workflow", "mcp__n8n__unpublish_workflow",
      "mcp__n8n__archive_workflow"
    ]
  }
}
```

## Roadmap

- **F2** Triage + Fixer (parches solo en borrador) + Tester (`test_workflow` con pin data y `golden_cases`).
- **F3** Auditor independiente + aprobación por Telegram + rollback.
- **F4** Bibliotecario: cada bug corregido genera regla nueva + golden case.
