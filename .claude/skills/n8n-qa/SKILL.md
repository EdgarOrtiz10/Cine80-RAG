---
name: n8n-qa
description: Orquestador del sistema QA multiagente de n8n (F1 - detección). Úsalo cuando el usuario pida "QA", "barrido QA", "auditar/revisar bugs de n8n" o "QA <workflowId>", o cuando lo dispare la Routine diaria.
---

# Orquestador QA n8n — F1 (detección)

En F1 el sistema **solo detecta y registra**. Ningún agente modifica, ejecuta, publica ni
archiva workflows. Las correcciones llegan en F2 (Fixer/Tester) y F3 (Auditor + gate humano).

## Constantes
- Proyecto n8n: `gCyB4qYXonVTNZfF`
- Data Tables: `qa_events`=`ntI3GbOIPCVcHZO7`, `bug_registry`=`ZnL7Qw6OmW52TmTm`,
  `golden_cases`=`KKbMvV8pFJGgjwF6`, `qa_runs`=`BTmcS1dpdPlqCQtr`
- Error Collector (Capa 0): workflow `MQH3MoijkHW4iwnI`
- Código y estado: `n8n-qa/` (ver `n8n-qa/README.md`)

## Procedimiento
1. **Objetivos.** Si el usuario dio un workflowId, usa solo ese. Si no,
   `mcp__n8n__search_workflows` y quédate con `active: true` y `availableInMCP: true`.
   Excluye `MQH3MoijkHW4iwnI` (el propio collector).
2. **Detección en paralelo.** Por cada workflow lanza, en un solo mensaje, los subagentes
   `n8n-qa-linter` (workflowId) y `n8n-qa-forense` (workflowId + `last_execution_id` de
   `n8n-qa/state/watermarks.json`; si no hay entrada, usa las últimas 20 ejecuciones).
3. **Consolidar.** Guarda cada JSON de hallazgos en el scratchpad y ejecuta desde `n8n-qa/`:
   `python3 -m qa.registry merge <archivos...>`
   Esto deduplica por fingerprint contra `state/bug_registry.json` y devuelve `new` y
   `recurring` (un bug `published` que reaparece pasa a `regression`).
4. **Persistir.**
   - `new` → `mcp__n8n__add_data_table_rows` en `bug_registry` (solo las columnas de la tabla).
   - Actualiza `state/watermarks.json` con el `last_execution_id` que devolvió cada Forense.
   - Inserta una fila en `qa_runs` (run_id = timestamp ISO, trigger = manual|routine).
   - Commit de `n8n-qa/state/` y push a la rama de trabajo.
5. **Reporte al usuario** (en español, directo):
   - Bugs nuevos agrupados por severidad (🔴 high primero) con bug_id, regla, nodo y la acción
     sugerida del `detail`.
   - Regresiones, siempre destacadas.
   - Recurrentes: solo el conteo.
   - Ejecuciones que el Forense no pudo leer.

## Reglas de seguridad
- Prohibido en F1: `update_workflow`, `publish_workflow`, `unpublish_workflow`,
  `archive_workflow`, `restore_workflow_version`, `execute_workflow`, `test_workflow`.
- Si un workflow tiene VD-01 (borrador ≠ publicado), repórtalo primero: ninguna fase
  posterior puede editar ese workflow hasta que el humano revise el diff.
- No inventes hallazgos. Solo cuenta lo que devolvieron los scripts; las observaciones
  no verificadas van aparte y marcadas como tales.
- El MCP de n8n no puede leer filas de Data Tables: la fuente de verdad del registro es
  `n8n-qa/state/bug_registry.json`. Nunca asumas el contenido de una Data Table.
