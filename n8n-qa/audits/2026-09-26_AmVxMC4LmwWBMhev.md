# Auditoría QA — AmVxMC4LmwWBMhev

**Veredicto: 🟠 REVISAR** (script: ✅ APROBADO · revisión manual: 2 medium)

- Publicado: `340b55bc-f259-4a9b-8e4c-1ced57fc36eb`
- Borrador auditado: `2b761586-9115-4166-bc63-444c5353a862`
- Conexiones: +10 / -2

## Hallazgos del auditor

Ninguno.

## Cambios y su atribución

| Cambio | Nodo | Detalle | Atribuido a |
|---|---|---|---|
| nodo añadido | Limpiar Pendiente (Error Guardado) | n8n-nodes-base.code | 2026-09-25_f2_AmVxMC4LmwWBMhev.json, 2026-09-25_autosave_1692898c.json |
| nodo añadido | Notificar Fallo Guardado (Admin) | n8n-nodes-base.telegram | 2026-09-25_autosave_1692898c.json |
| nodo añadido | Send Error Guardado (Usuario) | n8n-nodes-base.telegram | 2026-09-25_autosave_1692898c.json |
| nodo añadido | Send Respuesta (Texto Plano) | n8n-nodes-base.telegram | 2026-09-25_f2_AmVxMC4LmwWBMhev.json |
| nodo añadido | Validar Gasto | n8n-nodes-base.code | 2026-09-25_f2_AmVxMC4LmwWBMhev.json |
| nodo añadido | Zona: ⚠️ MANEJO DE ERRORES GLOBAL | n8n-nodes-base.stickyNote | — |
| nodo añadido | Zona: ✍️ FLUJO TEXTO | n8n-nodes-base.stickyNote | — |
| nodo añadido | Zona: 🎤 FLUJO VOZ | n8n-nodes-base.stickyNote | — |
| nodo añadido | Zona: 💾 CONFIRMAR Y GUARDAR GASTO | n8n-nodes-base.stickyNote | — |
| nodo añadido | Zona: 📸 FLUJO FOTO | n8n-nodes-base.stickyNote | — |
| nodo añadido | Zona: 🔁 DETECCIÓN DE DUPLICADOS | n8n-nodes-base.stickyNote | — |
| nodo añadido | Zona: 🔐 ENTRADA, SEGURIDAD Y SESIÓN | n8n-nodes-base.stickyNote | — |
| nodo añadido | Zona: 🗑️ ELIMINAR GASTO | n8n-nodes-base.stickyNote | — |
| nodo añadido | Zona: 🤖 ASISTENTE CONVERSACIONAL (AGENTE IA) | n8n-nodes-base.stickyNote | — |
| nodo añadido | ¿Sin Items? | n8n-nodes-base.if | 2026-09-25_f2_AmVxMC4LmwWBMhev.json |
| nodo modificado | Append Gastos | parameters, onError, retryOnFail, maxTries, waitBetweenTries | 2026-09-25_df01_AmVxMC4LmwWBMhev.json, 2026-09-25_f2_AmVxMC4LmwWBMhev.json, 2026-09-25_autosave_1692898c.json |
| nodo modificado | Danieled Agent | parameters | 2026-09-25_f2_AmVxMC4LmwWBMhev.json |
| nodo modificado | Explotar Items | parameters | 2026-09-25_f2_AmVxMC4LmwWBMhev.json |
| nodo modificado | Guardar Candidatos Pendientes (Eliminar) | parameters | 2026-09-25_f2_AmVxMC4LmwWBMhev.json |
| nodo modificado | Guardar Pendiente (Eliminar) | parameters | 2026-09-25_f2_AmVxMC4LmwWBMhev.json |
| nodo modificado | Guardar Static Data | parameters | 2026-09-25_f2_AmVxMC4LmwWBMhev.json |
| nodo modificado | Guardar Static Data (Duplicado) | parameters | 2026-09-25_f2_AmVxMC4LmwWBMhev.json |
| nodo modificado | Guardar Static Data (tras Duplicado) | parameters | 2026-09-25_f2_AmVxMC4LmwWBMhev.json |
| nodo modificado | Recuperar Datos Pendiente (Duplicado) | parameters | 2026-09-25_f2_AmVxMC4LmwWBMhev.json |
| nodo modificado | Recuperar Pendiente (Eliminar) | parameters | 2026-09-25_f2_AmVxMC4LmwWBMhev.json |
| nodo modificado | Recuperar Selección de Eliminación | parameters | 2026-09-25_f2_AmVxMC4LmwWBMhev.json |
| nodo modificado | Recuperar y Detectar Acción | parameters | 2026-09-25_f2_AmVxMC4LmwWBMhev.json |
| nodo modificado | Send Respuesta | onError | 2026-09-25_f2_AmVxMC4LmwWBMhev.json |

## Hallazgos del linter que desaparecen

- DF-01 Append Gastos
- SD-01 Guardar Candidatos Pendientes (Eliminar)
- SD-01 Guardar Pendiente (Eliminar)
- SD-01 Guardar Static Data
- SD-01 Guardar Static Data (Duplicado)
- SD-01 Guardar Static Data (tras Duplicado)
- SD-02 Recuperar Datos Pendiente (Duplicado)
- SD-02 Recuperar Pendiente (Eliminar)
- SD-02 Recuperar y Detectar Acción
- SF-02 Append Gastos
- SF-02 Append Items
- TG-01 Send Respuesta

## No verificable automáticamente

- Credenciales: la API de n8n no las devuelve en versiones ni detalles; revisa en la UI que ningún nodo cambió de credencial.
- Settings del workflow (p. ej. errorWorkflow): la versión publicada no los incluye.

## Revisión manual (A6)

- **medium** — DUP_SI / DEL_SI sin pendiente terminan en silencio: el usuario no recibe respuesta. Es correcto (antes mentían), pero conviene un mensaje 'no hay nada pendiente'.
- **medium** — Append Gastos con retryOnFail (2 intentos): si el primer append escribió y solo falló la respuesta, el reintento duplica la fila. Riesgo aceptado en la revisión del autosave; mitigable deduplicando por ID.
- **low** — LIM-01: el throw de Validar Gasto llega al admin como '0 [line 8]'; se pierde el detalle de campos faltantes.
- **low** — Los pendientes guardados antes de publicar no tienen _ts y expiran de inmediato: quien tenga un botón pendiente en ese momento debe reenviar el gasto.
- **info** — Prompt del agente: solo añade 'consultar la otra herramienta antes de responder que no hay datos'. No relaja ninguna regla de seguridad (scope, prompt injection, no revelar instrucciones).
- **info** — Nodos de seguridad (allowlist, rate limit, guardrails, trigger): sin cambios.

Ningún hallazgo bloquea: el veredicto REVISAR significa que la publicación es decisión humana con estos riesgos a la vista.
