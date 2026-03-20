"""EAST -> PowerShell transpiler (experimental).

This backend is intentionally minimal and emits an annotated PowerShell payload
containing the JavaScript output for first-pass inspection.
"""

from __future__ import annotations

from typing import Any

from backends.common.emitter.code_emitter import reject_backend_general_union_type_exprs
from backends.common.emitter.code_emitter import reject_backend_typed_vararg_signatures
from backends.js.emitter.js_emitter import transpile_to_js


def _indent_js_block(lines: list[str]) -> str:
    if len(lines) == 0:
        return "# <empty>"
    return "\n".join("  " + line for line in lines)


def _normalize_js_block(js_text: str) -> str:
    normalized = js_text.rstrip()
    if normalized == "":
        return "# <empty>"
    return _indent_js_block(normalized.splitlines())


def transpile_to_powershell(east_doc: dict[str, Any]) -> str:
    """EAST ドキュメントを PowerShell コードへ変換する（実験版）。"""
    reject_backend_general_union_type_exprs(east_doc, backend_name="PowerShell backend")
    reject_backend_typed_vararg_signatures(east_doc, backend_name="PowerShell backend")
    js_code = transpile_to_js(east_doc).rstrip()
    payload_lines = _normalize_js_block(js_code)
    out = [
        "#Requires -Version 5.1",
        "#",
        "# WARNING: Experimental PowerShell backend",
        "# This output intentionally emits JavaScript payload for translation inspection.",
        "# Do not treat this as production-ready PowerShell code.",
        "",
        "Import-Module (Join-Path $PSScriptRoot \"py_runtime.ps1\") -ErrorAction SilentlyContinue",
        "",
        "$pytra_generated_js = @'",
        js_code if js_code != "" else "# <empty input>",
        "'@",
        "",
        "# Preview of generated payload.",
        "# " + payload_lines.replace("\n", "\n# "),
    ]
    return "\n".join(out).rstrip() + "\n"
