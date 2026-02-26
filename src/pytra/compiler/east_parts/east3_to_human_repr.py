#!/usr/bin/env python3
"""EAST3 human-representation renderer helpers."""

from __future__ import annotations

from pytra.std.typing import Any

from .east2_to_human_repr import (
    _cpp_type_name,
    _dump_json,
    _expr_repr,
    _fmt_span,
    _indent,
    _render_expr as _render_expr_east2,
    _render_stmt as _render_stmt_east2,
)


def _render_expr(expr: dict[str, Any] | None) -> str:
    """Render EAST3 expression with explicit core-node pseudo notation."""
    if expr is None:
        return "/* none */"
    kind = expr.get("kind")
    if kind == "Box":
        return f"box({_render_expr(expr.get('value'))})"
    if kind == "Unbox":
        target = str(expr.get("target", "unknown"))
        on_fail = str(expr.get("on_fail", "raise"))
        return f"unbox<{target}>({_render_expr(expr.get('value'))}, on_fail={on_fail})"
    if kind == "ObjBool":
        return f"obj_bool({_render_expr(expr.get('value'))})"
    if kind == "ObjLen":
        return f"obj_len({_render_expr(expr.get('value'))})"
    if kind == "ObjStr":
        return f"obj_str({_render_expr(expr.get('value'))})"
    if kind == "ObjIterInit":
        return f"obj_iter_init({_render_expr(expr.get('value'))})"
    if kind == "ObjIterNext":
        return f"obj_iter_next({_render_expr(expr.get('iter'))})"
    if kind == "ObjTypeId":
        return f"obj_type_id({_render_expr(expr.get('value'))})"
    if kind == "IsInstance":
        return (
            "is_instance("
            + _render_expr(expr.get("value"))
            + ", "
            + _render_expr(expr.get("expected_type_id"))
            + ")"
        )
    if kind == "IsSubclass":
        return (
            "is_subclass("
            + _render_expr(expr.get("actual_type_id"))
            + ", "
            + _render_expr(expr.get("expected_type_id"))
            + ")"
        )
    if kind == "IsSubtype":
        return (
            "is_subtype("
            + _render_expr(expr.get("actual_type_id"))
            + ", "
            + _render_expr(expr.get("expected_type_id"))
            + ")"
        )
    return _render_expr_east2(expr)


def _target_plan_name(target_plan: dict[str, Any] | None) -> str:
    if target_plan is None:
        return "__item"
    if target_plan.get("kind") == "NameTarget":
        target_id = target_plan.get("id")
        if isinstance(target_id, str) and target_id != "":
            return target_id
    return "__item"


def _target_plan_decl(target_plan: dict[str, Any] | None) -> str:
    if target_plan is None:
        return "auto __item"
    if target_plan.get("kind") == "NameTarget":
        target_id = _target_plan_name(target_plan)
        target_type = target_plan.get("target_type")
        if isinstance(target_type, str) and target_type != "":
            return f"{_cpp_type_name(target_type)} {target_id}"
        return f"auto {target_id}"
    return f"auto {_target_plan_name(target_plan)}"


def _render_forcore(stmt: dict[str, Any], level: int) -> list[str]:
    """Render EAST3 ForCore node as human-readable pseudo C++ loop."""
    sp = _fmt_span(stmt.get("source_span"))
    pad = "    " * level
    plan = stmt.get("iter_plan")
    target_plan = stmt.get("target_plan")
    target_decl = _target_plan_decl(target_plan if isinstance(target_plan, dict) else None)
    target_name = _target_plan_name(target_plan if isinstance(target_plan, dict) else None)
    lines: list[str] = [f"{pad}// [{sp}] ForCore mode={stmt.get('iter_mode', 'runtime_protocol')}"]

    if isinstance(plan, dict) and plan.get("kind") == "StaticRangeForPlan":
        start = _render_expr(plan.get("start"))
        stop = _render_expr(plan.get("stop"))
        step = _render_expr(plan.get("step"))
        mode = str(plan.get("range_mode", "dynamic"))
        if mode == "ascending":
            cond = f"{target_name} < ({stop})"
        elif mode == "descending":
            cond = f"{target_name} > ({stop})"
        else:
            cond = f"({step}) > 0 ? {target_name} < ({stop}) : {target_name} > ({stop})"
        lines.append(f"{pad}for ({target_decl} = {start}; {cond}; {target_name} += ({step})) {{")
    elif isinstance(plan, dict) and plan.get("kind") == "RuntimeIterForPlan":
        iter_expr = _render_expr(plan.get("iter_expr"))
        dispatch = str(plan.get("dispatch_mode", "native"))
        init_op = str(plan.get("init_op", "ObjIterInit"))
        next_op = str(plan.get("next_op", "ObjIterNext"))
        lines.append(
            f"{pad}for ({target_decl} : py_iter_runtime({iter_expr})) "
            f"/* dispatch={dispatch}, init={init_op}, next={next_op} */ {{"
        )
    else:
        lines.append(f"{pad}for ({target_decl} : <unknown plan>) {{")

    body = stmt.get("body")
    if isinstance(body, list):
        for child in body:
            if isinstance(child, dict):
                lines.extend(_render_stmt(child, level + 1))
    lines.append(f"{pad}}}")

    orelse = stmt.get("orelse")
    if isinstance(orelse, list) and len(orelse) > 0:
        lines.append(f"{pad}// for-else")
        lines.append(f"{pad}{{")
        for child in orelse:
            if isinstance(child, dict):
                lines.extend(_render_stmt(child, level + 1))
        lines.append(f"{pad}}}")
    return lines


def _render_stmt(stmt: dict[str, Any], level: int = 1) -> list[str]:
    """Render one EAST3 statement as C++-style pseudo source lines."""
    kind = stmt.get("kind")
    sp = _fmt_span(stmt.get("source_span"))
    pad = "    " * level

    if kind == "ForCore":
        return _render_forcore(stmt, level)
    if kind == "Return":
        value = _render_expr(stmt.get("value")) if stmt.get("value") is not None else "/* void */"
        return _indent([f"// [{sp}]", f"return {value};"], level)
    if kind == "Expr":
        return _indent([f"// [{sp}]", f"{_render_expr(stmt.get('value'))};"], level)
    if kind == "Assign":
        return _indent(
            [
                f"// [{sp}]",
                f"{_render_expr(stmt.get('target'))} = {_render_expr(stmt.get('value'))};",
            ],
            level,
        )
    if kind == "AnnAssign":
        ann = str(stmt.get("annotation", "auto"))
        return _indent(
            [
                f"// [{sp}]",
                f"{ann} {_render_expr(stmt.get('target'))} = {_render_expr(stmt.get('value'))};",
            ],
            level,
        )
    if kind == "If":
        out = [f"{pad}// [{sp}]", f"{pad}if ({_render_expr(stmt.get('test'))}) {{"] 
        body = stmt.get("body")
        if isinstance(body, list):
            for child in body:
                if isinstance(child, dict):
                    out.extend(_render_stmt(child, level + 1))
        out.append(f"{pad}}}")
        orelse = stmt.get("orelse")
        if isinstance(orelse, list) and len(orelse) > 0:
            out.append(f"{pad}else {{")
            for child in orelse:
                if isinstance(child, dict):
                    out.extend(_render_stmt(child, level + 1))
            out.append(f"{pad}}}")
        return out
    if kind == "While":
        out = [f"{pad}// [{sp}]", f"{pad}while ({_render_expr(stmt.get('test'))}) {{"] 
        body = stmt.get("body")
        if isinstance(body, list):
            for child in body:
                if isinstance(child, dict):
                    out.extend(_render_stmt(child, level + 1))
        out.append(f"{pad}}}")
        return out
    if kind == "FunctionDef":
        name = str(stmt.get("name", "fn"))
        ret = str(stmt.get("return_type", "None"))
        out = [f"{pad}// [{sp}] function original={stmt.get('original_name', name)}"]
        out.append(f"{pad}{ret} {name}(/* params omitted */) {{")
        body = stmt.get("body")
        if isinstance(body, list):
            for child in body:
                if isinstance(child, dict):
                    out.extend(_render_stmt(child, level + 1))
        out.append(f"{pad}}}")
        return out
    if kind == "ClassDef":
        name = str(stmt.get("name", "Class"))
        out = [f"{pad}// [{sp}] class original={stmt.get('original_name', name)}"]
        out.append(f"{pad}struct {name} {{")
        body = stmt.get("body")
        if isinstance(body, list):
            for child in body:
                if isinstance(child, dict):
                    out.extend(_render_stmt(child, level + 1))
        out.append(f"{pad}}};")
        return out

    return _render_stmt_east2(stmt, level)


def render_east3_to_human_repr(out_doc: dict[str, Any]) -> str:
    """Render EAST doc into EAST3-oriented human-readable representation."""
    lines: list[str] = []
    lines.append("// EAST3 Human View (C++-style pseudo source)")
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

    east = out_doc.get("east")
    if not isinstance(east, dict):
        return "// invalid east payload\n"

    lines.append(f"namespace east3_view /* source: {east.get('source_path')} */ {{")
    lines.append("")
    lines.append("    // module body")
    body = east.get("body")
    if isinstance(body, list):
        for stmt in body:
            if isinstance(stmt, dict):
                lines.extend(_render_stmt(stmt, 1))
    lines.append("")
    lines.append("    // main guard body")
    lines.append("    int64 __east_main_guard() {")
    main_body = east.get("main_guard_body")
    if isinstance(main_body, list):
        for stmt in main_body:
            if isinstance(stmt, dict):
                lines.extend(_render_stmt(stmt, 2))
    lines.append("        return 0;")
    lines.append("    }")
    lines.append("")
    lines.append("} // namespace east3_view")
    lines.append("")
    return "\n".join(lines)


def render_east_to_human_repr(out_doc: dict[str, Any]) -> str:
    """Render EAST doc with EAST3 human-representation renderer."""
    return render_east3_to_human_repr(out_doc)


# Backward compatibility aliases.
def render_east3_human_cpp(out_doc: dict[str, Any]) -> str:
    return render_east3_to_human_repr(out_doc)


def render_east_human_cpp(out_doc: dict[str, Any]) -> str:
    return render_east_to_human_repr(out_doc)
