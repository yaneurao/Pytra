"""Registry for non-user modules treated as known by frontend import resolver.

This keeps external-module policy data-driven (without requiring shim source
files under ``src/pytra/utils``).
"""

from __future__ import annotations

from typing import Any


KNOWN_MODULE_SPECS: dict[str, dict[str, Any]] = {
    "browser": {
        "source_kind": "external",
        "exports": [
            "document",
            "window",
            "DOMEvent",
            "Element",
            "CanvasRenderingContext",
            "Touch",
            "TextMetrics",
            "HtmlImage",
        ],
    },
    "browser.widgets": {
        "source_kind": "external",
        "exports": [],
    },
    "browser.widgets.dialog": {
        "source_kind": "external",
        "exports": [
            "Dialog",
            "EntryDialog",
            "InfoDialog",
        ],
    },
}


def get_known_module_spec(module_name: str) -> dict[str, Any]:
    if module_name in KNOWN_MODULE_SPECS:
        raw = KNOWN_MODULE_SPECS[module_name]
        if isinstance(raw, dict):
            return raw
    return {}


def is_known_module_name(module_name: str) -> bool:
    return len(get_known_module_spec(module_name)) > 0


def list_known_module_names() -> list[str]:
    names = list(KNOWN_MODULE_SPECS.keys())
    names.sort()
    return names

