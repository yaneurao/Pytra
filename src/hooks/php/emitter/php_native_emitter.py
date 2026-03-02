"""EAST3 -> PHP native emitter (skeleton)."""

from __future__ import annotations

from pytra.std.typing import Any


def _module_leading_comment_lines(east_doc: dict[str, Any], prefix: str) -> list[str]:
    trivia_any = east_doc.get("module_leading_trivia")
    trivia = trivia_any if isinstance(trivia_any, list) else []
    out: list[str] = []
    for item_any in trivia:
        if not isinstance(item_any, dict):
            continue
        kind = item_any.get("kind")
        if kind == "comment":
            text = item_any.get("text")
            if isinstance(text, str):
                out.append(prefix + text)
            continue
        if kind == "blank":
            count = item_any.get("count")
            n = count if isinstance(count, int) and count > 0 else 1
            i = 0
            while i < n:
                out.append("")
                i += 1
    while len(out) > 0 and out[-1] == "":
        out.pop()
    return out


def transpile_to_php_native(east_doc: dict[str, Any]) -> str:
    """Emit PHP native source from EAST3 Module."""
    if not isinstance(east_doc, dict):
        raise RuntimeError("php native emitter: east_doc must be dict")
    if east_doc.get("kind") != "Module":
        raise RuntimeError("php native emitter: root kind must be Module")
    body_any = east_doc.get("body")
    if not isinstance(body_any, list):
        raise RuntimeError("php native emitter: Module.body must be list")

    lines: list[str] = [
        "<?php",
        "declare(strict_types=1);",
        "",
        "require_once __DIR__ . '/pytra/py_runtime.php';",
        "",
    ]
    module_comments = _module_leading_comment_lines(east_doc, "// ")
    if len(module_comments) > 0:
        lines.extend(module_comments)
        lines.append("")

    lines.extend(
        [
            "function __pytra_main(): void {",
            "}",
            "",
            "__pytra_main();",
        ]
    )
    return "\n".join(lines) + "\n"
