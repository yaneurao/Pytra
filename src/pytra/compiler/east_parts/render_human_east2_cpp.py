#!/usr/bin/env python3
"""EAST2 human renderer helpers (C++-style pseudo view)."""
from __future__ import annotations

from pytra.std.typing import Any
from pytra.std import json

from .core import FLOAT_TYPES, INT_TYPES

def _dump_json(obj: dict[str, Any], *, pretty: bool) -> str:
    """Serialize output JSON in compact or pretty mode."""
    if pretty:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def _indent(lines: list[str], level: int = 1) -> list[str]:
    """Indent helper for human-readable C++-style rendering."""
    prefix = "    " * level
    return [prefix + ln if ln else "" for ln in lines]


def _fmt_span(span: dict[str, Any] | None) -> str:
    """Format source span as `line:col` for comments."""
    if not span:
        return "?:?"
    ln = span.get("lineno")
    col = span.get("col")
    if ln is None or col is None:
        return "?:?"
    return f"{ln}:{col}"


def _render_expr(expr: dict[str, Any] | None) -> str:
    """Render EAST expression as compact C++-style pseudo expression."""
    if expr is None:
        return "/* none */"
    rep = expr.get("repr")
    if rep is None:
        rep = f"<{expr.get('kind', 'Expr')}>"
    typ = expr.get("resolved_type", "unknown")
    borrow = expr.get("borrow_kind", "value")
    casts = expr.get("casts", [])
    cast_txt = ""
    if casts:
        cast_parts = []
        for c in casts:
            cast_parts.append(f"{c.get('on')}:{c.get('from')}->{c.get('to')}({c.get('reason')})")
        cast_txt = " casts=" + ",".join(cast_parts)
    return f"{rep} /* type={typ}, borrow={borrow}{cast_txt} */"


def _expr_repr(expr: dict[str, Any] | None) -> str:
    """Best-effort expression representation (without metadata suffix)."""
    if expr is None:
        return "/* none */"
    rep = expr.get("repr")
    if rep is None:
        return f"<{expr.get('kind', 'Expr')}>"
    return rep


def _cpp_type_name(east_type: str | None) -> str:
    """Map EAST type names to human-view C++-like type labels."""
    if east_type is None:
        return "auto"
    if east_type in INT_TYPES | FLOAT_TYPES | {"bool", "str", "Path", "Exception", "None"}:
        return east_type
    if east_type.startswith("list["):
        return east_type
    if east_type.startswith("dict["):
        return east_type
    if east_type.startswith("set["):
        return east_type
    if east_type.startswith("tuple["):
        return east_type
    return "auto"


def _render_stmt(stmt: dict[str, Any], level: int = 1) -> list[str]:
    """Render one EAST statement as C++-style pseudo source lines."""
    k = stmt.get("kind")
    sp = _fmt_span(stmt.get("source_span"))
    pad = "    " * level
    out: list[str] = []

    if k == "Import":
        names = ", ".join((n["name"] if n.get("asname") is None else f"{n['name']} as {n['asname']}") for n in stmt.get("names", []))
        out.append(f"// [{sp}] import {names};")
        return _indent(out, level)
    if k == "ImportFrom":
        names = ", ".join((n["name"] if n.get("asname") is None else f"{n['name']} as {n['asname']}") for n in stmt.get("names", []))
        out.append(f"// [{sp}] from {stmt.get('module')} import {names};")
        return _indent(out, level)
    if k == "Pass":
        return _indent([f"// [{sp}] pass;"], level)
    if k == "Break":
        return _indent([f"// [{sp}] break;"], level)
    if k == "Continue":
        return _indent([f"// [{sp}] continue;"], level)
    if k == "Return":
        v = _render_expr(stmt.get("value")) if stmt.get("value") is not None else "/* void */"
        return _indent([f"// [{sp}]", f"return {v};"], level)
    if k == "Expr":
        return _indent([f"// [{sp}]", f"{_render_expr(stmt.get('value'))};"], level)
    if k == "Assign":
        return _indent(
            [
                f"// [{sp}]",
                f"{_render_expr(stmt.get('target'))} = {_render_expr(stmt.get('value'))};",
            ],
            level,
        )
    if k == "Swap":
        return _indent(
            [
                f"// [{sp}]",
                f"py_swap({_render_expr(stmt.get('left'))}, {_render_expr(stmt.get('right'))});",
            ],
            level,
        )
    if k == "AnnAssign":
        ann = stmt.get("annotation", "auto")
        return _indent(
            [
                f"// [{sp}]",
                f"{ann} {_render_expr(stmt.get('target'))} = {_render_expr(stmt.get('value'))};",
            ],
            level,
        )
    if k == "AugAssign":
        op = stmt.get("op", "Op")
        return _indent(
            [
                f"// [{sp}]",
                f"{_render_expr(stmt.get('target'))} /* {op} */= {_render_expr(stmt.get('value'))};",
            ],
            level,
        )
    if k == "If":
        out.append(f"{pad}// [{sp}]")
        out.append(f"{pad}if ({_render_expr(stmt.get('test'))}) {{")
        for s in stmt.get("body", []):
            out.extend(_render_stmt(s, level + 1))
        out.append(f"{pad}}}")
        if stmt.get("orelse"):
            out.append(f"{pad}else {{")
            for s in stmt.get("orelse", []):
                out.extend(_render_stmt(s, level + 1))
            out.append(f"{pad}}}")
        return out
    if k == "For":
        tgt_expr = stmt.get("target")
        tgt = _expr_repr(tgt_expr)
        tgt_ty = _cpp_type_name((tgt_expr or {}).get("resolved_type") if isinstance(tgt_expr, dict) else None)
        out.append(f"{pad}// [{sp}]")
        out.append(f"{pad}for ({tgt_ty} {tgt} : { _render_expr(stmt.get('iter')) }) {{")
        for s in stmt.get("body", []):
            out.extend(_render_stmt(s, level + 1))
        out.append(f"{pad}}}")
        if stmt.get("orelse"):
            out.append(f"{pad}// for-else")
            out.append(f"{pad}{{")
            for s in stmt.get("orelse", []):
                out.extend(_render_stmt(s, level + 1))
            out.append(f"{pad}}}")
        return out
    if k == "ForRange":
        tgt_expr = stmt.get("target")
        tgt = _expr_repr(tgt_expr)
        tgt_ty = _cpp_type_name((tgt_expr or {}).get("resolved_type") if isinstance(tgt_expr, dict) else None)
        start = _render_expr(stmt.get("start"))
        stop = _render_expr(stmt.get("stop"))
        step = _render_expr(stmt.get("step"))
        mode = stmt.get("range_mode", "dynamic")
        if mode == "ascending":
            cond = f"({tgt}) < ({stop})"
        elif mode == "descending":
            cond = f"({tgt}) > ({stop})"
        else:
            cond = f"({step}) > 0 ? ({tgt}) < ({stop}) : ({tgt}) > ({stop})"
        out.append(f"{pad}// [{sp}]")
        out.append(f"{pad}for ({tgt_ty} {tgt} = {start}; {cond}; {tgt} += ({step})) {{")
        for s in stmt.get("body", []):
            out.extend(_render_stmt(s, level + 1))
        out.append(f"{pad}}}")
        if stmt.get("orelse"):
            out.append(f"{pad}// for-else")
            out.append(f"{pad}{{")
            for s in stmt.get("orelse", []):
                out.extend(_render_stmt(s, level + 1))
            out.append(f"{pad}}}")
        return out
    if k == "While":
        out.append(f"{pad}// [{sp}]")
        out.append(f"{pad}while ({_render_expr(stmt.get('test'))}) {{")
        for s in stmt.get("body", []):
            out.extend(_render_stmt(s, level + 1))
        out.append(f"{pad}}}")
        if stmt.get("orelse"):
            out.append(f"{pad}// while-else")
            out.append(f"{pad}{{")
            for s in stmt.get("orelse", []):
                out.extend(_render_stmt(s, level + 1))
            out.append(f"{pad}}}")
        return out
    if k == "Raise":
        return _indent([f"// [{sp}]", f"throw {_render_expr(stmt.get('exc'))};"], level)
    if k == "Try":
        out.append(f"{pad}// [{sp}]")
        out.append(f"{pad}try {{")
        for s in stmt.get("body", []):
            out.extend(_render_stmt(s, level + 1))
        out.append(f"{pad}}}")
        for h in stmt.get("handlers", []):
            ex_name = h.get("name") or "ex"
            ex_type = _render_expr(h.get("type"))
            out.append(f"{pad}catch ({ex_type} as {ex_name}) {{")
            for s in h.get("body", []):
                out.extend(_render_stmt(s, level + 1))
            out.append(f"{pad}}}")
        if stmt.get("orelse"):
            out.append(f"{pad}// try-else")
            out.append(f"{pad}{{")
            for s in stmt.get("orelse", []):
                out.extend(_render_stmt(s, level + 1))
            out.append(f"{pad}}}")
        if stmt.get("finalbody"):
            out.append(f"{pad}/* finally */ {{")
            for s in stmt.get("finalbody", []):
                out.extend(_render_stmt(s, level + 1))
            out.append(f"{pad}}}")
        return out
    if k == "FunctionDef":
        name = stmt.get("name", "fn")
        ret = stmt.get("return_type", "None")
        arg_types: dict[str, str] = stmt.get("arg_types", {})
        arg_usage: dict[str, str] = stmt.get("arg_usage", {})
        params = []
        for n, t in arg_types.items():
            usage = arg_usage.get(n, "readonly")
            params.append(f"{t} {n} /* {usage} */")
        out.append(f"{pad}// [{sp}] function original={stmt.get('original_name', name)}")
        out.append(f"{pad}{ret} {name}({', '.join(params)}) {{")
        rs = stmt.get("renamed_symbols", {})
        if rs:
            out.append(("    " * (level + 1)) + f"// renamed_symbols: {rs}")
        for s in stmt.get("body", []):
            out.extend(_render_stmt(s, level + 1))
        out.append(f"{pad}}}")
        return out
    if k == "ClassDef":
        name = stmt.get("name", "Class")
        out.append(f"{pad}// [{sp}] class original={stmt.get('original_name', name)}")
        out.append(f"{pad}struct {name} {{")
        for s in stmt.get("body", []):
            out.extend(_render_stmt(s, level + 1))
        out.append(f"{pad}}};")
        return out

    return _indent([f"// [{sp}] <unsupported stmt kind={k}>"], level)


def render_east2_human_cpp(out_doc: dict[str, Any]) -> str:
    """Render EAST doc into EAST2-oriented human-readable C++ pseudo code."""
    lines: list[str] = []
    lines.append("// EAST Human View (C++-style pseudo source)")
    lines.append("// Generated by src/east.py")
    lines.append("")
    if not out_doc.get("ok", False):
        err = out_doc.get("error", {})
        lines.append("/* EAST generation failed */")
        lines.append(f"// kind: {err.get('kind')}")
        lines.append(f"// message: {err.get('message')}")
        lines.append(f"// source_span: {err.get('source_span')}")
        lines.append(f"// hint: {err.get('hint')}")
        lines.append("")
        return "\n".join(lines) + "\n"

    east = out_doc["east"]
    lines.append(f"namespace east_view /* source: {east.get('source_path')} */ {{")
    lines.append("")
    rs = east.get("renamed_symbols", {})
    if rs:
        lines.append("    // renamed_symbols")
        for k, v in rs.items():
            lines.append(f"    //   {k} -> {v}")
        lines.append("")

    lines.append("    // module body")
    for s in east.get("body", []):
        lines.extend(_render_stmt(s, 1))
    lines.append("")

    lines.append("    // main guard body")
    lines.append("    int64 __east_main_guard() {")
    for s in east.get("main_guard_body", []):
        lines.extend(_render_stmt(s, 2))
    lines.append("        return 0;")
    lines.append("    }")
    lines.append("")
    lines.append("} // namespace east_view")
    lines.append("")
    return "\n".join(lines)


# Backward compatibility alias.
def render_east_human_cpp(out_doc: dict[str, Any]) -> str:
    """Compatibility wrapper for the old renderer symbol name."""
    east = out_doc.get("east")
    if out_doc.get("ok", False) and isinstance(east, dict) and east.get("east_stage") == 3:
        from .render_human_east3_cpp import render_east3_human_cpp

        return render_east3_human_cpp(out_doc)
    return render_east2_human_cpp(out_doc)
