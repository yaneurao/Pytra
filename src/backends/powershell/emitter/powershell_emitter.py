"""EAST -> PowerShell transpiler (experimental).

This backend is intentionally minimal and emits a best-effort PowerShell script
for first-pass inspection.
"""

from __future__ import annotations

import re
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


def _indent_ps_block(lines: list[str]) -> str:
    if len(lines) == 0:
        return "    # <empty>"
    return "\n".join("    " + line for line in lines)


_MATH_FN_MAP: dict[str, str] = {
    "abs": "Abs",
    "floor": "Floor",
    "ceil": "Ceiling",
    "round": "Round",
    "max": "Max",
    "min": "Min",
    "sqrt": "Sqrt",
    "pow": "Pow",
    "trunc": "Truncate",
}

_BUILTIN_FN_MAP: dict[str, str] = {
    "pow": "__pytra_pow",
    "bytearray": "__pytra_bytearray",
    "bytes": "__pytra_bytes",
    "list": "__pytra_list",
    "tuple": "__pytra_list",
    "set": "__pytra_set",
    "dict": "__pytra_dict",
    "ord": "__pytra_ord",
    "chr": "__pytra_chr",
    "Error": "__pytra_error",
    "Number": "__pytra_float",
    "String": "__pytra_str",
    "Boolean": "__pytra_bool",
    "str": "__pytra_str",
    "bool": "__pytra_bool",
    "int": "__pytra_int",
    "float": "__pytra_float",
    "range": "__pytra_range",
}

_JS_KEYWORD_CALLS: set[str] = {
    "if",
    "while",
    "for",
    "switch",
    "catch",
    "finally",
    "try",
    "else",
    "function",
    "return",
    "Error",
}

_JS_KEEP_IDENTIFIERS: set[str] = {
    "true",
    "false",
    "null",
    "undefined",
    "if",
    "else",
    "for",
    "while",
    "function",
    "return",
    "break",
    "continue",
    "try",
    "catch",
    "finally",
    "switch",
    "case",
    "new",
    "this",
    "Math",
    "console",
    "print",
    "Number",
    "String",
    "Boolean",
    "Error",
    "len",
    "__pytra_print",
    "__pytra_len",
    "main",
}


def _split_top_level(text: str, delimiter: str = ",") -> list[str]:
    if text.strip() == "":
        return []

    parts: list[str] = []
    current: list[str] = []
    depth_paren = 0
    depth_brace = 0
    depth_bracket = 0
    quote_char = ""
    escape = False

    for ch in text:
        if quote_char != "":
            current.append(ch)
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
                continue
            if ch == quote_char:
                quote_char = ""
            continue

        if ch in {"\"", "'"}:
            quote_char = ch
            current.append(ch)
            continue

        if ch == "(":
            depth_paren += 1
        elif ch == ")":
            if depth_paren > 0:
                depth_paren -= 1
        elif ch == "{":
            depth_brace += 1
        elif ch == "}":
            if depth_brace > 0:
                depth_brace -= 1
        elif ch == "[":
            depth_bracket += 1
        elif ch == "]":
            if depth_bracket > 0:
                depth_bracket -= 1

        if (
            ch == delimiter
            and depth_paren == 0
            and depth_brace == 0
            and depth_bracket == 0
        ):
            parts.append("".join(current).strip())
            current = []
            continue

        current.append(ch)

    last = "".join(current).strip()
    if last != "":
        parts.append(last)
    return parts


def _convert_js_operator_tokens(line: str) -> str:
    translated = line
    translated = translated.replace("!==", "-ne")
    translated = translated.replace("===", "-eq")
    translated = translated.replace(">=", " -ge ")
    translated = translated.replace("<=", " -le ")
    translated = translated.replace("!=", "-ne")
    translated = translated.replace("==", "-eq")
    translated = translated.replace(">", " -gt ")
    translated = translated.replace("<", " -lt ")
    translated = translated.replace("&&", "-and")
    translated = translated.replace("||", "-or")
    translated = re.sub(r"\btrue\b", "$true", translated)
    translated = re.sub(r"\bfalse\b", "$false", translated)
    translated = re.sub(r"\bnull\b", "$null", translated)
    translated = re.sub(r"\bundefined\b", "$null", translated)
    translated = translated.replace(".length", ".Length")
    translated = re.sub(r"(?<![=!<>])!(?![=])", "-not ", translated)
    return translated


def _convert_js_stmt_like(line: str) -> str:
    m_throw = re.match(r"^(\s*)throw\s+new\s+Error\s*\((.*)\)\s*;?$", line)
    if m_throw is not None:
        return f"{m_throw.group(1)}throw {m_throw.group(2).rstrip(';').strip()}"
    return line


def _convert_js_function_args(arg_text: str) -> list[str]:
    parts = _split_top_level(arg_text, ",")
    if len(parts) == 0:
        return []
    out: list[str] = []
    for part in parts:
        text = part.strip()
        if text == "":
            continue
        if text == "...":
            continue
        if "=" in text:
            text = text.split("=", 1)[0].strip()
        if text == "":
            continue
        if ":" in text:
            continue
        out.append("$" + text)
    return out


def _convert_js_static_calls(line: str) -> str:
    return re.sub(
        r"\bMath\.([A-Za-z_][A-Za-z0-9_]*)\s*\((.*)\)",
        lambda match: (
            f"[Math]::{_MATH_FN_MAP.get(match.group(1), match.group(1))}({match.group(2)})"
            if match.group(1) in _MATH_FN_MAP
            else match.group(0)
        ),
        line,
    )


def _convert_js_call(line: str) -> str:
    # Conservative conversion that only touches simple function calls such as `foo(`.
    if "(" not in line:
        return line

    def _build_call(target: str, raw_args: str, sep: str) -> str:
        args = [arg.strip() for arg in _split_top_level(raw_args, ",")]
        args = [arg for arg in args if arg != ""]
        if len(args) == 0:
            return target
        return f"{target} " + sep.join(args)

    line = re.sub(
        r"(?<![\w.])console\.log\s*\((.*)\)",
        lambda match: _build_call("__pytra_print", match.group(1), " "),
        line,
    )
    return re.sub(
        r"(?<![\w.])([A-Za-z_][A-Za-z0-9_]*)\s*\((.*?)\)",
        lambda match: (
            match.group(0)
            if match.group(1) in _JS_KEYWORD_CALLS
            else _build_call("__pytra_print", match.group(2), " ")
            if match.group(1) == "console" or match.group(1) == "print"
            else _build_call("__pytra_len", match.group(2), " ")
            if match.group(1) == "len"
            else _build_call(_BUILTIN_FN_MAP[match.group(1)], match.group(2), " ")
            if match.group(1) in _BUILTIN_FN_MAP
            else _build_call(match.group(1), match.group(2), " ")
        ),
        line,
    )


def _convert_js_container_literal(expr: str) -> str:
    text = expr.strip()
    if len(text) < 2:
        return expr

    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        if inner == "":
            return "@()"
        elements = _split_top_level(inner, ",")
        return "@(" + ", ".join(_convert_js_expr(item) for item in elements if item != "") + ")"

    if text.startswith("{") and text.endswith("}"):
        inner = text[1:-1].strip()
        if inner == "":
            return "@{}"
        pairs = _split_top_level(inner, ",")
        out_items: list[str] = []
        for pair in pairs:
            if ":" not in pair:
                continue
            key, raw_value = pair.split(":", 1)
            key_name = key.strip()
            if (key_name.startswith("\"") and key_name.endswith("\"")) or (
                key_name.startswith("'") and key_name.endswith("'")
            ):
                key_name = key_name[1:-1]
            value_text = raw_value.strip()
            out_items.append(f"{key_name} = {_convert_js_expr(value_text)}")
        return "@{" + "; ".join(out_items) + "}"

    return expr


def _convert_js_compound_assignment(line: str) -> str:
    converted = line
    converted = re.sub(
        r"(?<![\w$])\b([A-Za-z_][A-Za-z0-9_]*)\s*\+\=",
        lambda m: f"${m.group(1)} +=",
        converted,
    )
    converted = re.sub(
        r"(?<![\w$])\b([A-Za-z_][A-Za-z0-9_]*)\s*\-=",
        lambda m: f"${m.group(1)} -=",
        converted,
    )
    converted = re.sub(
        r"(?<![\w$])\b([A-Za-z_][A-Za-z0-9_]*)\s*\*=",
        lambda m: f"${m.group(1)} *=",
        converted,
    )
    converted = re.sub(
        r"(?<![\w$])\b([A-Za-z_][A-Za-z0-9_]*)\s*\/=",
        lambda m: f"${m.group(1)} /=",
        converted,
    )
    converted = re.sub(
        r"(?<![\w$])\b([A-Za-z_][A-Za-z0-9_]*)\s*\%=",
        lambda m: f"${m.group(1)} %=",
        converted,
    )
    return converted


def _convert_js_new_calls(expr: str) -> str:
    return re.sub(
        r"(?<![\w.])new\s+([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)\s*\(",
        lambda match: match.group(1) + "(",
        expr,
    )


def _convert_js_identifiers(expr: str) -> str:
    out: list[str] = []
    quote_char = ""
    escape = False
    i = 0
    n = len(expr)

    while i < n:
        ch = expr[i]
        if quote_char != "":
            out.append(ch)
            if escape:
                escape = False
                i += 1
                continue
            if ch == "\\":
                escape = True
            elif ch == quote_char:
                quote_char = ""
            i += 1
            continue

        if ch in {"\"", "'"}:
            quote_char = ch
            out.append(ch)
            i += 1
            continue

        if re.match(r"[A-Za-z_]", ch):
            j = i + 1
            while j < n and re.match(r"[A-Za-z0-9_]", expr[j]):
                j += 1
            token = expr[i:j]

            prev_char = expr[i - 1] if i > 0 else ""
            next_char_idx = j
            while next_char_idx < n and expr[next_char_idx].isspace():
                next_char_idx += 1
            next_char = expr[next_char_idx] if next_char_idx < n else ""

            if (
                token in _JS_KEEP_IDENTIFIERS
                or prev_char == "."
                or prev_char == "$"
                or next_char == ":"
                or next_char == "("
                or next_char == ")"
                or (next_char_idx < n and expr[next_char_idx - 1:next_char_idx] == ".")
            ):
                out.append(token)
            else:
                out.append("$" + token)
            i = j
            continue

        out.append(ch)
        i += 1

    return "".join(out)


def _convert_js_expr(expr: str) -> str:
    converted = _convert_js_operator_tokens(expr.strip())
    converted = _convert_js_static_calls(converted)
    converted = _convert_js_new_calls(converted)
    converted = _convert_js_increment_decrement(converted)
    converted = _convert_js_compound_assignment(converted)
    converted = _convert_js_container_literal(converted)
    converted = _convert_js_call(converted)
    converted = _convert_js_identifiers(converted)
    return converted


def _convert_js_for_loop(raw: str, indent: str) -> str | None:
    m = re.match(r"^\s*for\s*\((.*)\)\s*\{\s*$", raw)
    if m is None:
        return None

    header = m.group(1)
    parts = _split_top_level(header, ";")

    # Support `for (x in y)` and `for (x of y)` as PowerShell foreach loops.
    # This is intentionally lightweight and handles common patterns only.
    if len(parts) == 1:
        m_foreach = re.match(
            r"^(?:const|let|var)\s+([A-Za-z_][A-Za-z0-9_]*)\s+(?:in|of)\s+(.+)$",
            header.strip(),
        )
        if m_foreach is not None:
            target = m_foreach.group(1)
            iterator = _convert_js_expr(m_foreach.group(2))
            return f"{indent}foreach (${target} in {iterator}) {{"
        m_foreach_simple = re.match(
            r"^([A-Za-z_][A-Za-z0-9_]*)\s+(?:in|of)\s+(.+)$",
            header.strip(),
        )
        if m_foreach_simple is not None:
            target = m_foreach_simple.group(1)
            iterator = _convert_js_expr(m_foreach_simple.group(2))
            return f"{indent}foreach (${target} in {iterator}) {{"

    # Standard `for (init; cond; step)` style.
    if len(parts) != 3:
        converted = _convert_js_expr(header)
        return f"{indent}for ({converted}) {{"

    init = parts[0].strip()
    cond = parts[1].strip()
    step = parts[2].strip()
    if init == "" and cond == "" and step == "":
        return f"{indent}while ($true) {{"

    init_targets: list[str] = []
    init_match = re.match(r"^(?:const|let|var)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$", init)
    if init_match is not None:
        init_var = init_match.group(1)
        init_targets.append(init_var)
        init_expr = _convert_js_expr(init_match.group(2))
        init = f"${init_var} = {init_expr}"
    else:
        init_assign_match = re.match(
            r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$",
            init,
        )
        if init_assign_match is not None:
            init_var = init_assign_match.group(1)
            init_targets.append(init_var)
            init_expr = _convert_js_expr(init_assign_match.group(2))
            init = f"${init_var} = {init_expr}"
        else:
            init = _convert_js_expr(init)

    cond = _convert_js_expr(cond)
    step = _convert_js_expr(step)
    for target in init_targets:
        token = re.compile(rf"(?<![\w$\.]){re.escape(target)}(?![\w$])")
        cond = token.sub(f"${target}", cond)
        step = token.sub(f"${target}", step)

    if cond == "":
        cond = "$true"
    if step == "":
        step = f"${init_targets[0]} += 1" if len(init_targets) > 0 else "break"

    return f"{indent}for ({init}; {cond}; {step}) {{"


def _convert_js_switch_head(raw: str, indent: str) -> str | None:
    m = re.match(r"^\s*switch\s*\((.*)\)\s*\{\s*$", raw)
    if m is None:
        return None
    return f"{indent}switch ({_convert_js_expr(m.group(1).strip())}) {{"


def _convert_js_switch_case(raw: str, indent: str) -> str | None:
    m_case = re.match(r"^(\s*)case\s+(.*):\s*$", raw)
    if m_case is not None:
        expr = m_case.group(2).strip()
        if expr == "":
            return f"{m_case.group(1)}default {{"
        return f"{m_case.group(1)}{_convert_js_expr(expr)} {{"

    m_default = re.match(r"^(\s*)default\s*:\s*$", raw)
    if m_default is not None:
        return f"{m_default.group(1)}default {{"

    return None


def _convert_js_else_clause(raw: str, indent: str) -> str | None:
    m_else_if = re.match(r"^(\s*)}\s*else\s+if\s*\((.*)\)\s*\{\s*$", raw)
    if m_else_if is not None:
        return f"{m_else_if.group(1)}}} elseif ({_convert_js_expr(m_else_if.group(2).strip())}) {{"

    m_else = re.match(r"^(\s*)}\s*else\s*\{\s*$", raw)
    if m_else is not None:
        return f"{m_else.group(1)}}} else {{"

    return None


def _convert_js_increment_decrement(line: str) -> str:
    converted = re.sub(
        r"(?<![\w$])\b([A-Za-z_][A-Za-z0-9_]*)\s*\+\+",
        lambda m: f"${m.group(1)} += 1",
        line,
    )
    converted = re.sub(
        r"(?<![\w$])\b([A-Za-z_][A-Za-z0-9_]*)\s*\-\-",
        lambda m: f"${m.group(1)} -= 1",
        converted,
    )
    converted = re.sub(
        r"\+\+\s*(?<![\w$])\b([A-Za-z_][A-Za-z0-9_]*)",
        lambda m: f"${m.group(1)} += 1",
        converted,
    )
    return re.sub(
        r"--\s*(?<![\w$])\b([A-Za-z_][A-Za-z0-9_]*)",
        lambda m: f"${m.group(1)} -= 1",
        converted,
    )


def _convert_js_control_flow_head(raw: str, indent: str) -> str | None:
    keyword = None
    trimmed = raw.strip()
    if trimmed.startswith("if "):
        keyword = "if"
    elif trimmed.startswith("if("):
        keyword = "if"
    elif trimmed.startswith("while "):
        keyword = "while"
    elif trimmed.startswith("while("):
        keyword = "while"

    if keyword is None:
        return None

    m = re.match(rf"^(\s*){keyword}\s*\((.*)\)\s*\{{\s*$", raw)
    if m is None:
        return None

    condition = _convert_js_expr(m.group(2).strip())
    if condition == "":
        condition = "$true"
    return f"{indent}{keyword} ({condition}) {{"


def _convert_js_return(line: str) -> str:
    m_return = re.match(r"^(\s*)return(?:\s+(.*))?;?$", line)
    if m_return is None:
        return line
    value = (m_return.group(2) or "").strip()
    if value == "":
        return f"{m_return.group(1)}return"
    value_expr = _convert_js_expr(value)
    return f"{m_return.group(1)}return {value_expr}"


def _convert_js_throw(line: str) -> str:
    m_throw = re.match(r"^(\s*)throw\s+(.*);?$", line)
    if m_throw is None:
        return line
    value = m_throw.group(2).strip()
    if value == "":
        return f"{m_throw.group(1)}throw"
    return f"{m_throw.group(1)}throw {value}"


def _convert_js_do_while(line: str) -> str:
    m_do = re.match(r"^(\s*)\}\s*while\s*\((.*)\)\s*;?$", line)
    if m_do is None:
        return line
    cond = _convert_js_expr(m_do.group(2).strip())
    if cond == "":
        cond = "$true"
    return f"{m_do.group(1)}}} while ({cond})"


def _convert_js_catch(line: str) -> tuple[str | None, list[str]]:
    m = re.match(r"^(\s*)\}\s*catch\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)\s*\{\s*$", line)
    if m is not None:
        indent = m.group(1)
        err_name = m.group(2)
        return f"{indent}}} catch {{", [f"{indent}    ${err_name} = $_"]
    m2 = re.match(r"^(\s*)\}\s*catch\s*\([^)]*\)\s*\{\s*$", line)
    if m2 is not None:
        return f"{m2.group(1)}}} catch {{", []
    m3 = re.match(r"^(\s*)catch\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)\s*\{\s*$", line)
    if m3 is not None:
        indent = m3.group(1)
        err_name = m3.group(2)
        return f"{indent}catch {{", [f"{indent}    ${err_name} = $_"]
    m4 = re.match(r"^(\s*)catch\s*\([^)]*\)\s*\{\s*$", line)
    if m4 is not None:
        return f"{m4.group(1)}catch {{", []
    return None, []


def _convert_js_to_powerline(raw_lines: list[str]) -> list[str]:
    out: list[str] = []
    in_block_comment = False
    for raw in raw_lines:
        text = raw.rstrip()
        if text == "":
            out.append("")
            continue
        if text == "use strict;" or text == "\"use strict\";" or text == "'use strict';":
            continue
        if in_block_comment:
            out.append("#" + text)
            if "*/" in text:
                in_block_comment = False
            continue
        if text.startswith("//"):
            out.append("#" + text[2:])
            continue
        if text.startswith("/*"):
            in_block_comment = "*/" not in text
            out.append("#" + text[2:].replace("*/", "").strip())
            if "*/" in text:
                in_block_comment = False
            continue
        if "/*" in text and text.endswith("*/"):
            out.append("#" + text[2:-2].strip())
            continue

        func_match = re.match(r"^(\s*)function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\((.*?)\)\s*\{\s*$", text)
        if func_match is not None:
            indent = func_match.group(1)
            fn_name = func_match.group(2)
            args = _convert_js_function_args(func_match.group(3))
            out.append(f"{indent}function {fn_name} {{")
            if len(args) > 0:
                out.append(f"{indent}    param({', '.join(args)})")
            else:
                out.append(f"{indent}    param()")
            continue

        var_match = re.match(r"^(\s*)(?:const|let|var)\s+(.*?)\s*;\s*$", text)
        if var_match is None:
            var_match = re.match(r"^(\s*)(?:const|let|var)\s+(.*)\s*$", text)
        if var_match is not None:
            indent = var_match.group(1)
            remainder = var_match.group(2).strip()
            assignments = _split_top_level(remainder, ",")
            emitted = False
            for assignment in assignments:
                assign_match = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)\s*$", assignment)
                if assign_match is None:
                    token_match = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*$", assignment)
                    if token_match is not None:
                        out.append(f"{indent}${token_match.group(1)} = $null")
                        emitted = True
                    continue
                var_name = assign_match.group(1)
                rhs = _convert_js_expr(assign_match.group(2))
                out.append(f"{indent}${var_name} = {rhs}")
                emitted = True
            if emitted:
                continue
            only_names = _split_top_level(remainder, ",")
            all_names: list[str] = []
            for item in only_names:
                token = item.strip()
                if token == "":
                    continue
                token_match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)$", token)
                if token_match is None:
                    continue
                all_names.append(token_match.group(1))
            if len(all_names) > 0:
                for var_name in all_names:
                    out.append(f"{indent}${var_name} = $null")
                continue

        for_match = re.match(r"^(\s*)", text)
        indent = for_match.group(0) if for_match is not None else ""
        converted_for = _convert_js_for_loop(text, indent)
        if converted_for is not None:
            out.append(converted_for)
            continue

        control_match = _convert_js_control_flow_head(text, indent)
        if control_match is not None:
            out.append(control_match)
            continue

        switch_match = _convert_js_switch_head(text, indent)
        if switch_match is not None:
            out.append(switch_match)
            continue

        case_match = _convert_js_switch_case(text, indent)
        if case_match is not None:
            out.append(case_match)
            continue

        else_match = _convert_js_else_clause(text, indent)
        if else_match is not None:
            out.append(else_match)
            continue

        line = text
        if re.match(r"^\s*return(\s|;|$)", line):
            line = _convert_js_return(line)
        line = _convert_js_throw(line)
        line = _convert_js_do_while(line)
        converted_catch, catch_prefill = _convert_js_catch(line)
        if converted_catch is not None:
            out.append(converted_catch)
            for item in catch_prefill:
                out.append(item)
            continue
        if line.startswith("console.log("):
            inner = line[len("console.log(") :]
            if inner.endswith(");"):
                inner = inner[:-2]
            elif inner.endswith(")"):
                inner = inner[:-1]
            line = f"__pytra_print {inner.strip()}"
        elif line.startswith("print("):
            inner = line[len("print(") :]
            if inner.endswith(");"):
                inner = inner[:-2]
            elif inner.endswith(")"):
                inner = inner[:-1]
            line = f"__pytra_print {inner.strip()}"
        line = re.sub(r"^(\s*)\}\s*finally\s*\{\s*$", r"\1} finally {", line)
        if line.endswith(";"):
            line = line[:-1]
        line = _convert_js_stmt_like(line)
        line = _convert_js_operator_tokens(line)
        line = _convert_js_increment_decrement(line)
        line = line.replace("};", "}")
        line = _convert_js_call(line)
        out.append(line)
    return out


def transpile_to_powershell(east_doc: dict[str, Any]) -> str:
    """EAST ドキュメントを PowerShell コードへ変換する（実験版）。"""
    reject_backend_general_union_type_exprs(east_doc, backend_name="PowerShell backend")
    reject_backend_typed_vararg_signatures(east_doc, backend_name="PowerShell backend")
    js_code = transpile_to_js(east_doc).rstrip()
    js_lines = js_code.splitlines() if js_code != "" else []
    ps_lines = _convert_js_to_powerline(js_lines) if len(js_lines) > 0 else ["# <empty input>"]
    payload_lines = _normalize_js_block(js_code)
    out = [
        "#Requires -Version 5.1",
        "#",
        "# WARNING: Experimental PowerShell backend",
        "# This output intentionally emits a best-effort PowerShell preview.",
        "# Do not treat this as production-ready PowerShell code.",
        "",
        "$pytra_runtime = Join-Path $PSScriptRoot \"py_runtime.ps1\"",
        "if (Test-Path $pytra_runtime) { . $pytra_runtime }",
        "",
        "Set-StrictMode -Version Latest",
        "$ErrorActionPreference = \"Stop\"",
        "",
        "$pytra_program = @'",
        "# Preview of generated payload.",
        "# " + payload_lines.replace("\n", "\n# "),
        "@'",
        "",
        "# PowerShell preview generated from JavaScript pseudo conversion.",
        _indent_ps_block(ps_lines),
        "",
        "if (Get-Command -Name main -ErrorAction SilentlyContinue) {",
        "    main",
        "}",
    ]
    return "\n".join(out).rstrip() + "\n"
