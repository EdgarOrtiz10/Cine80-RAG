---
name: n8n-qa
description: Orquestador del sistema QA multiagente de n8n (F1 detección + F2 corrección). Úsalo cuando el usuario pida "QA", "barrido QA", "auditar/revisar bugs de n8n", "QA <workflowId>", "corrige los bugs QA" / "QA fix <bug_id>", o cuando lo dispare la Routine diaria.
---

# Orquestador QA n8n — F1 (detección) + F2 (corrección)

El barrido (F1) **solo detecta y registra**. La corrección (F2) solo ocurre cuando el usuario la
pide y **nunca publica**: deja el parche en el borrador para revisión humana (F3).

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

## Corrección (F2) — solo a petición del usuario
Ciclo por bug o grupo de bugs del mismo workflow, en este orden:
1. **Triage** (`n8n-qa-triage`): causa raíz con evidencia, bugs hermanos, caso golden.
2. **Tester — reproducir** (`n8n-qa-tester`): el caso nuevo debe FALLAR en el borrador actual.
   Si pasa, no demuestra el bug: vuelve a Triage.
3. **Fixer** (`n8n-qa-fixer`): parche mínimo en el borrador, rollback anotado.
4. **Tester — verificar**: TODOS los casos golden del workflow (regresión), no solo el nuevo.
   Si algo falla: rollback con el versionId anotado **pidiendo confirmación al usuario**, o
   nueva iteración del Fixer.
5. **Linter** sobre el borrador parchado: no debe aparecer ningún hallazgo nuevo.
6. Actualiza `state/bug_registry.json` (status `fix_pending_publish`, `fix_version_id`,
   `root_cause`) y las Data Tables `bug_registry` / `golden_cases`; commit y push.
7. Reporta: qué se corrigió, evidencia (executionIds), lo no verificable con pin data, y que
   **publicar es decisión del usuario**.

Estados del registro: open → fix_pending_publish → published (lo marca el humano al publicar)
→ regression (si reaparece). `wontfix` y `LIM-*` (limitaciones de plataforma) no bloquean.

## Reglas de seguridad
- Prohibido en el barrido F1: `update_workflow`, `publish_workflow`, `unpublish_workflow`,
  `archive_workflow`, `restore_workflow_version`, `execute_workflow`, `test_workflow`.
- Prohibido SIEMPRE: `publish_workflow`, `unpublish_workflow`, `archive_workflow`.
- Si un workflow tiene VD-01 (borrador ≠ publicado) con cambios que no son parches QA
  registrados, el Fixer no lo toca hasta que se revise y registre ese diff.
- No inventes hallazgos. Solo cuenta lo que devolvieron los scripts; las observaciones
  no verificadas van aparte y marcadas como tales.
- El MCP de n8n no puede leer filas de Data Tables: la fuente de verdad del registro es
  `n8n-qa/state/bug_registry.json`. Nunca asumas el contenido de una Data Table.
