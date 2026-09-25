"""Reglas deterministas del Linter (A1). Cada regla nace de un bug real observado.

Catálogo:
  DF-01  $json consumido tras un nodo con efecto secundario (Telegram / escritura Sheets)
  SF-02  Mensaje de éxito al usuario sin guardia que valide lo escrito
  SD-01  Estado pendiente en staticData sin marca de tiempo (nunca expira)
  SD-02  Estado pendiente recuperado como null y esparcido sin guardia
  TG-01  Texto dinámico enviado con parse_mode Markdown/HTML sin escapar
  VD-01  Workflow activo con borrador distinto a la versión publicada
"""
from __future__ import annotations

import hashlib
import re
from collections import deque
from dataclasses import asdict, dataclass

from .graph import (
    PASS_THROUGH_TYPES,
    Workflow,
    is_guard,
    is_sheets_write,
    is_success_text,
    is_telegram_send,
    iter_strings,
)

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}

# Campos que sí existen en la salida de un envío de Telegram.
TELEGRAM_OUTPUT_FIELDS = {"ok", "result", "message_id", "chat"}

JSON_FIELD_RE = re.compile(r"\$json(?:\s*\.\s*([A-Za-z_$][\w$]*)|\s*\[\s*['\"]([^'\"]+)['\"]\s*\]|(?![\w.\[]))")
INPUT_FIELD_RE = re.compile(
    r"\$input\.(?:first\(\)|last\(\)|item)\.json(?:\s*\.\s*([A-Za-z_$][\w$]*)|\s*\[\s*['\"]([^'\"]+)['\"]\s*\]|(?![\w.\[]))"
)
ESCAPE_HINT_RE = re.compile(r"\.replace(All)?\(|escape", re.IGNORECASE)
TIMESTAMP_HINT_RE = re.compile(r"Date\.now\(|new Date\(|\bts\b|timestamp|expires|created_at")


@dataclass
class Finding:
    rule_id: str
    severity: str
    workflow_id: str
    node: str
    title: str
    detail: str
    fingerprint: str = ""

    def __post_init__(self) -> None:
        if not self.fingerprint:
            raw = f"{self.rule_id}|{self.workflow_id}|{self.node}|{self.title}"
            self.fingerprint = hashlib.sha1(raw.encode()).hexdigest()[:12]

    def to_dict(self) -> dict:
        return asdict(self)


def _fields_used(text: str, is_code: bool) -> set[str]:
    """Campos de `$json` que consume un texto. '*' = objeto completo."""
    fields: set[str] = set()
    patterns = [JSON_FIELD_RE, INPUT_FIELD_RE] if is_code else [JSON_FIELD_RE]
    for pattern in patterns:
        for m in pattern.finditer(text):
            fields.add(m.group(1) or m.group(2) or "*")
    return fields


def _consumed_fields(wf: Workflow, name: str) -> set[str]:
    if wf.node_type(name) == "n8n-nodes-base.code":
        return _fields_used(wf.params(name).get("jsCode") or "", is_code=True)
    fields: set[str] = set()
    for s in iter_strings(wf.params(name)):
        if s.startswith("="):
            fields |= _fields_used(s, is_code=False)
    return fields


def _side_effect_output_fields(wf: Workflow, name: str) -> set[str] | None:
    """Campos válidos que emite un nodo con efecto secundario; None si no lo es."""
    if wf.node_type(name) == "n8n-nodes-base.telegram":
        return TELEGRAM_OUTPUT_FIELDS
    if is_sheets_write(wf, name):
        columns = (wf.params(name).get("columns") or {}).get("value") or {}
        return set(columns)
    return None


def _data_producers(wf: Workflow, name: str) -> list[str]:
    """Nodos que realmente producen el `$json` de `name`, atravesando pass-through."""
    producers, seen = [], set()
    queue = deque(wf.parents.get(name, []))
    while queue:
        p = queue.popleft()
        if p in seen:
            continue
        seen.add(p)
        if wf.node_type(p) in PASS_THROUGH_TYPES:
            queue.extend(wf.parents.get(p, []))
        else:
            producers.append(p)
    return producers


def rule_df01(wf: Workflow) -> list[Finding]:
    findings = []
    for name in wf.nodes:
        if wf.ignored(name, "DF-01"):
            continue
        used = _consumed_fields(wf, name)
        if not used:
            continue
        for producer in _data_producers(wf, name):
            valid = _side_effect_output_fields(wf, producer)
            if valid is None:
                continue
            broken = sorted(f for f in used if f == "*" or f not in valid)
            if broken:
                findings.append(
                    Finding(
                        "DF-01",
                        "high",
                        wf.id,
                        name,
                        f"'{name}' lee $json de '{producer}' (nodo con efecto secundario)",
                        f"Campos afectados: {', '.join(broken)}. La salida de '{producer}' es la "
                        f"respuesta de la API, no los datos de negocio. Referencia el nodo origen "
                        f"con $('<Nodo>').first().json.<campo>.",
                    )
                )
    return findings


def rule_sf02(wf: Workflow) -> list[Finding]:
    findings = []
    for writer in wf.nodes:
        if not is_sheets_write(wf, writer) or wf.ignored(writer, "SF-02"):
            continue
        if _guarded_upstream(wf, writer):
            continue
        reached, seen = [], {writer}
        queue = deque(wf.children.get(writer, []))
        while queue:
            n = queue.popleft()
            if n in seen:
                continue
            seen.add(n)
            if is_guard(wf, n):
                continue
            if is_telegram_send(wf, n) and is_success_text(wf.params(n).get("text") or ""):
                reached.append(n)
            queue.extend(wf.children.get(n, []))
        if reached:
            findings.append(
                Finding(
                    "SF-02",
                    "medium",
                    wf.id,
                    writer,
                    f"Éxito confirmado tras '{writer}' sin validar lo escrito",
                    f"Mensajes de éxito alcanzables sin guardia: {', '.join(sorted(reached))}. "
                    f"Una escritura con campos vacíos termina 'success' igual. Añade un Code con "
                    f"`throw` si faltan campos obligatorios, antes de escribir.",
                )
            )
    return findings


def _guarded_upstream(wf: Workflow, writer: str, max_hops: int = 6) -> bool:
    """¿Hay un Code con `throw` antes de la escritura, dentro del mismo tramo de guardado?

    Sube por los padres hasta `max_hops`, sin cruzar Switch (frontera de enrutamiento). Así una
    única validación antes de la primera escritura protege también a las escrituras en cadena.
    """
    queue, seen = deque((p, 1) for p in wf.parents.get(writer, [])), set()
    while queue:
        p, hops = queue.popleft()
        if p in seen or hops > max_hops:
            continue
        seen.add(p)
        t = wf.node_type(p)
        if t == "n8n-nodes-base.code" and "throw " in (wf.params(p).get("jsCode") or ""):
            return True
        if t == "n8n-nodes-base.switch":
            continue
        queue.extend((pp, hops + 1) for pp in wf.parents.get(p, []))
    return False


STATIC_ASSIGN_RE = re.compile(r"staticData\s*\[[^\]]+\]\s*=(?!=)")
NULLABLE_VAR_RE = re.compile(r"(?:const|let|var)\s+(\w+)\s*=[^;\n]*staticData[^;\n]*\?[^;\n]*:\s*null")


def rule_sd01(wf: Workflow) -> list[Finding]:
    findings = []
    for name in wf.nodes:
        if wf.node_type(name) != "n8n-nodes-base.code" or wf.ignored(name, "SD-01"):
            continue
        code = wf.params(name).get("jsCode") or ""
        if STATIC_ASSIGN_RE.search(code) and not TIMESTAMP_HINT_RE.search(code):
            findings.append(
                Finding(
                    "SD-01",
                    "low",
                    wf.id,
                    name,
                    f"'{name}' guarda estado pendiente sin marca de tiempo",
                    "El pendiente nunca expira: un botón pulsado horas después actúa sobre datos "
                    "viejos. Guarda `ts: Date.now()` y descarta pendientes con más de N minutos.",
                )
            )
    return findings


def rule_sd02(wf: Workflow) -> list[Finding]:
    findings = []
    for name in wf.nodes:
        if wf.node_type(name) != "n8n-nodes-base.code" or wf.ignored(name, "SD-02"):
            continue
        code = wf.params(name).get("jsCode") or ""
        for m in NULLABLE_VAR_RE.finditer(code):
            var = m.group(1)
            spread = re.search(rf"\.\.\.\s*{var}\b", code)
            guard = re.search(rf"if\s*\(\s*!\s*{var}\b|{var}\s*===?\s*null|{var}\s*\?\?", code)
            if spread and not guard:
                findings.append(
                    Finding(
                        "SD-02",
                        "high",
                        wf.id,
                        name,
                        f"'{name}' continúa con `{var}` = null sin guardia",
                        f"Si no hay pendiente (expiró, se limpió o el botón se pulsó dos veces), "
                        f"`...{var}` produce un objeto vacío y el flujo sigue: escrituras en blanco "
                        f"o errores aguas abajo. Añade `if (!{var}) {{ ... }}` y ramifica.",
                    )
                )
    return findings


def rule_tg01(wf: Workflow) -> list[Finding]:
    findings = []
    for name in wf.nodes:
        if not is_telegram_send(wf, name) or wf.ignored(name, "TG-01"):
            continue
        p = wf.params(name)
        # Sin parse_mode explícito no afirmamos nada: el comportamiento por defecto
        # del nodo no está verificado.
        mode = (p.get("additionalFields") or {}).get("parse_mode")
        text = p.get("text") or ""
        if not mode or not (text.startswith("=") and "{{" in text):
            continue
        if ESCAPE_HINT_RE.search(text) or _has_plain_text_fallback(wf, name):
            continue
        findings.append(
            Finding(
                "TG-01",
                "medium",
                wf.id,
                name,
                f"'{name}' envía texto dinámico con parse_mode={mode} sin escapar",
                "Datos de OCR/LLM/usuario con `_`, `*`, `[`, `<` o `&` hacen que Telegram rechace "
                "el mensaje completo. Escapa los valores dinámicos o genera el texto en un Code.",
            )
        )
    return findings


def _has_plain_text_fallback(wf: Workflow, name: str) -> bool:
    """La salida de error reenvía el mensaje por Telegram sin parse_mode."""
    return any(
        is_telegram_send(wf, c) and not (wf.params(c).get("additionalFields") or {}).get("parse_mode")
        for c in wf.error_children.get(name, [])
    )


def rule_vd01(wf: Workflow) -> list[Finding]:
    if wf.active and wf.version_id and wf.active_version_id and wf.version_id != wf.active_version_id:
        return [
            Finding(
                "VD-01",
                "high",
                wf.id,
                "(workflow)",
                "Borrador distinto de la versión publicada",
                f"Borrador {wf.version_id} ≠ publicado {wf.active_version_id}. Revisa el diff en el "
                f"historial antes de editar o publicar: publicar enviaría cambios no revisados.",
            )
        ]
    return []


ALL_RULES = [rule_vd01, rule_df01, rule_sd02, rule_sf02, rule_tg01, rule_sd01]


def run_rules(wf: Workflow) -> list[Finding]:
    findings = [f for rule in ALL_RULES for f in rule(wf)]
    return sorted(findings, key=lambda f: (SEVERITY_ORDER[f.severity], f.rule_id, f.node))
