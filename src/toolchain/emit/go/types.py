"""Go type mapping from EAST3 resolved types.

§5 準拠: Any/object 禁止, pytra.std.* のみ, selfhost 対象。
"""

from __future__ import annotations

# EAST3 resolved_type → Go type
# Includes cross-module aliases such as parse.py.nodes union helper names.
_GO_TYPE_MAP: dict[str, str] = {
    "int": "int64",
    "int8": "int8",
    "int16": "int16",
    "int32": "int32",
    "int64": "int64",
    "uint8": "uint8",
    "uint16": "uint16",
    "uint32": "uint32",
    "uint64": "uint64",
    "float": "float64",
    "float32": "float32",
    "float64": "float64",
    "bool": "bool",
    "str": "string",
    "None": "",
    "none": "",
    "bytes": "[]byte",
    "bytearray": "[]byte",
    "list": "[]any",
    "dict": "map[string]any",
    "set": "map[any]struct{}",
    "tuple": "[]any",
    "object": "any",
    "Obj": "any",
    "Any": "any",
    "any": "any",
    "JsonVal": "any",
    "Node": "map[string]any",
    "TypeExpr": "any",
    "TriviaNode": "any",
    "Expr": "any",
    "Stmt": "any",
    "Callable": "any",
    "callable": "any",
    "T": "any",
    "K": "any",
    "V": "any",
    "Exception": "*PytraErrorCarrier",
    "BaseException": "*PytraErrorCarrier",
    "RuntimeError": "*PytraErrorCarrier",
    "ValueError": "*PytraErrorCarrier",
    "TypeError": "*PytraErrorCarrier",
    "IndexError": "*PytraErrorCarrier",
    "KeyError": "*PytraErrorCarrier",
}


def _parse_callable_signature(resolved_type: str) -> tuple[list[str], str]:
    has_callable_prefix = False
    if resolved_type.startswith("callable["):
        has_callable_prefix = True
    if resolved_type.startswith("Callable["):
        has_callable_prefix = True
    if not has_callable_prefix:
        empty_params: list[str] = []
        return (empty_params, "unknown")
    if not resolved_type.endswith("]"):
        empty_params: list[str] = []
        return (empty_params, "unknown")
    prefix_len: int = len("callable[")
    if resolved_type.startswith("Callable["):
        prefix_len = len("Callable[")
    inner = resolved_type[prefix_len:-1].strip()
    if inner == "":
        empty_params2: list[str] = []
        return (empty_params2, "unknown")
    if inner.startswith("["):
        depth = 0
        close_idx = -1
        i = 0
        while i < len(inner):
            ch = inner[i]
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    close_idx = i
                    break
            i += 1
        if close_idx >= 0 and close_idx + 1 < len(inner) and inner[close_idx + 1] == ",":
            params_text = inner[1:close_idx].strip()
            ret_text = inner[close_idx + 2:].strip()
            params: list[str] = []
            if params_text != "":
                params = _split_generic_args(params_text)
            return (params, ret_text if ret_text != "" else "unknown")
    arrow_idx = inner.find("->")
    if arrow_idx >= 0:
        params_text2 = inner[:arrow_idx].strip()
        ret_text2 = inner[arrow_idx + 2:].strip()
        params2: list[str] = []
        if params_text2 != "":
            for part in params_text2.split(","):
                item = part.strip()
                if item != "":
                    params2.append(item)
        return (params2, ret_text2 if ret_text2 != "" else "unknown")
    empty_params3: list[str] = []
    return (empty_params3, inner)


def go_type(resolved_type: str) -> str:
    """Convert an EAST3 resolved_type to a Go type string."""
    if resolved_type == "" or resolved_type == "unknown":
        return "any"

    if (resolved_type.startswith("callable[") or resolved_type.startswith("Callable[")) and resolved_type.endswith("]"):
        params, ret = _parse_callable_signature(resolved_type)
        param_gts: list[str] = []
        param_idx = 0
        while param_idx < len(params):
            param_gts.append(go_type(params[param_idx]))
            param_idx += 1
        ret_gt = go_type(ret)
        if ret_gt == "":
            return "func(" + ", ".join(param_gts) + ")"
        return "func(" + ", ".join(param_gts) + ") " + ret_gt

    if resolved_type.startswith("multi_return[") and resolved_type.endswith("]"):
        inner = resolved_type[len("multi_return["):-1]
        parts = _split_generic_args(inner)
        mapped_parts: list[str] = []
        part_idx = 0
        while part_idx < len(parts):
            mapped_parts.append(go_type(parts[part_idx]))
            part_idx += 1
        return "(" + ", ".join(mapped_parts) + ")"

    # Direct mapping
    mapped = _GO_TYPE_MAP.get(resolved_type, "")
    if resolved_type in _GO_TYPE_MAP:
        return mapped

    # list[T] → []T
    if resolved_type.startswith("list[") and resolved_type.endswith("]"):
        inner = resolved_type[5:-1]
        return "[]" + go_type(inner)

    # dict[K, V] → map[K]V
    if resolved_type.startswith("dict[") and resolved_type.endswith("]"):
        inner = resolved_type[5:-1]
        parts = _split_generic_args(inner)
        if len(parts) == 2:
            return "map[" + go_type(parts[0]) + "]" + go_type(parts[1])

    # set[T] → map[T]struct{}
    if resolved_type.startswith("set[") and resolved_type.endswith("]"):
        inner = resolved_type[4:-1]
        return "map[" + go_type(inner) + "]struct{}"

    # tuple[A, B, ...] — box as []any in Go
    if resolved_type.startswith("tuple[") and resolved_type.endswith("]"):
        return "PyTuple"

    # Optional[T] / T | None → *T (pointer for nilability)
    if resolved_type.endswith(" | None") or resolved_type.endswith("|None"):
        inner = resolved_type[: -7] if resolved_type.endswith(" | None") else resolved_type[: -5]
        gt = go_type(inner)
        if gt == "any":
            return gt
        if gt.startswith("*") or gt.startswith("[]") or gt.startswith("map[") or gt.startswith("func("):
            return gt
        return "*" + gt

    # Union type (A | B, A|B) → any
    if "|" in resolved_type:
        parts: list[str] = []
        for part in resolved_type.split("|"):
            stripped_part = part.strip()
            if stripped_part != "":
                parts.append(stripped_part)
        if len(parts) > 1:
            return "any"

    # User class → *ClassName (pointer for reference semantics)
    return "*" + _safe_go_ident(resolved_type)


def go_zero_value(resolved_type: str) -> str:
    """Return the Go zero value for a type."""
    gt = go_type(resolved_type)
    if gt in ("int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64"):
        return "0"
    if gt in ("float32", "float64"):
        return "0.0"
    if gt == "bool":
        return "false"
    if gt == "string":
        return "\"\""
    return "nil"


def _safe_go_ident(name: str) -> str:
    """Make a string safe as a Go identifier."""
    _GO_KEYWORDS = {
        "break", "case", "chan", "const", "continue", "default", "defer",
        "else", "fallthrough", "for", "func", "go", "goto", "if", "import",
        "interface", "map", "package", "range", "return", "select", "struct",
        "switch", "type", "var",
    }
    chars: list[str] = []
    for ch in name:
        if ch.isalnum() or ch == "_":
            chars.append(ch)
        else:
            chars.append("_")
    out = "".join(chars)
    if out == "":
        return "_unnamed"
    if out[0].isdigit():
        out = "_" + out
    if out in _GO_KEYWORDS:
        out = out + "_"
    return out


def _split_generic_args(s: str) -> list[str]:
    """Split comma-separated generic type args respecting brackets."""
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for ch in s:
        if ch == "[":
            depth += 1
            current.append(ch)
        elif ch == "]":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    tail = "".join(current).strip()
    if tail != "":
        parts.append(tail)
    return parts
