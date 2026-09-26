# n8n-qa — Sistema QA multiagente para workflows n8n

Detecta, registra (y en fases posteriores corrige y audita) bugs en los workflows de la
instancia n8n `n8n.eortiz-dev.com`. Estado actual: **F0 + F1 (detección) + F2 (corrección en borrador) + F3 (auditoría; la publicación es manual)**.

## Arquitectura

| Capa | Componente | Dónde vive | Qué hace |
|---|---|---|---|
| 0 | `QA - Error Collector` (`MQH3MoijkHW4iwnI`) | n8n | Error Trigger → fila en `qa_events` + alerta Telegram al admin |
| 1 | Orquestador | `.claude/skills/n8n-qa/SKILL.md` | Reparte trabajo, consolida, persiste, reporta |
| 1 | A1 Linter | `.claude/agents/n8n-qa-linter.md` + `qa/lint_workflow.py` | Análisis estático |
| 1 | A2 Forense | `.claude/agents/n8n-qa-forense.md` + `qa/check_execution.py` | Aserciones sobre ejecuciones |
| 1 | Registro | `qa/registry.py` + `state/bug_registry.json` | Deduplicación por fingerprint, detección de regresiones |
| 2 | A3 Triage | `.claude/agents/n8n-qa-triage.md` | Causa raíz, bugs hermanos, caso golden |
| 2 | A4 Fixer | `.claude/agents/n8n-qa-fixer.md` + `fixes/*.json` | Parche mínimo en borrador, nunca publica |
| 3 | A6 Auditor | `.claude/agents/n8n-qa-auditor.md` + `qa/audit.py` + `audits/` | Diff publicado↔borrador, atribución de cada cambio, veredicto |
| 2 | A5 Tester | `.claude/agents/n8n-qa-tester.md` + `qa/golden.py` + `golden/` | Reproduce antes y verifica después con pin data |

## Catálogo de reglas

| ID | Sev. | Detecta | Origen |
|---|---|---|---|
| DF-01 | high | `$json` leído tras un nodo con efecto secundario (Telegram, escritura Sheets); atraviesa IF/Switch/Filter | Bug Append Gastos 25-09-2026 |
| SD-02 | high | Pendiente de `staticData` recuperado como `null` y esparcido (`...datos`) sin guardia | `Recuperar y Detectar Acción` |
| VD-01 | high | Workflow activo con borrador ≠ versión publicada | Autosave `1692898c` sin publicar |
| SF-01 | high | *(runtime)* Nodo terminó OK con campos obligatorios vacíos | Ejecución #441 |
| EX-01 | high | *(runtime)* Ejecución con status=error | — |
| SF-02 | medium | Mensaje de éxito alcanzable tras una escritura sin guardia de validación | "✅ Gasto registrado" con fila vacía |
| TG-01 | medium | Texto dinámico con `parse_mode` explícito, sin escapar y sin fallback a texto plano en la salida de error | `Send Respuesta` |
| AG-01 | medium | *(runtime)* Agente respondió "sin datos" tras una sola tool vacía sin probar las demás | Ejecución #442 |
| NR-01 | high | *(triage/golden)* Code que devuelve 0 items corta el flujo antes del mensaje al usuario | Gasto por texto/voz sin productos (ejecución #445) |
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

## Casos golden (F2)

`golden/<workflowId>/_base.json` simula **todos** los nodos con credenciales (Telegram, Sheets,
OpenAI), así que las pruebas no escriben en la hoja ni envían mensajes. Cada `gc*.json` define
el mensaje, pins extra (p. ej. un gasto pendiente) y aserciones `node_ran` / `node_not_run`.
Usuario ficticio `999000111`; la allowlist y el guardrail se simulan.

```bash
python3 -m qa.golden list <wf>
python3 -m qa.golden build <wf> <caso>          # pinData para mcp__n8n__test_workflow
python3 -m qa.golden check <wf> <caso> <execution.json>
```

Si añades un nodo con credenciales al workflow, añádelo a `_base.json` o correrá de verdad.

## Auditoría (F3)

```bash
python3 -m qa.audit <publicado.json> <borrador.json> --policy assertions/<wf>.json --out audits/<fecha>_<wf>
```

Todo cambio debe estar atribuido a un parche (`fixes/*.json`) o a un diff revisado por un humano
(`fixes/reviewed/*.json`); si no, **RECHAZADO**. También rechaza nodos de riesgo nuevos
(HTTP, comandos, API de n8n), código con `fetch`/`require`/`eval`, cambios en nodos de seguridad
(`audit_policy.sensitive_nodes`) y cualquier regresión del linter. Credenciales y settings no se
pueden verificar vía API: el informe lo dice explícitamente.

La publicación **no está automatizada**: la hace el humano desde el historial de versiones de n8n,
publicando la versión exacta auditada.

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
| `qa_approvals` | `KfIvB24Ocj14PeVd` | Reservada para un gate de aprobación (sin usar) |

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

- **F4** Bibliotecario: cada bug corregido genera regla nueva + golden case.
