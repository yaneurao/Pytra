#!/usr/bin/env python3
"""Prepare selfhost/py2cpp.py as a self-contained source.

This script inlines CodeEmitter into py2cpp.py so transpiling selfhost input
no longer depends on cross-module import resolution.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_PY2CPP = ROOT / "src" / "py2cpp.py"
SRC_BASE = ROOT / "src" / "pytra" / "compiler" / "east_parts" / "code_emitter.py"
DST_SELFHOST = ROOT / "selfhost" / "py2cpp.py"
SRC_TRANSPILE_CLI = ROOT / "src" / "pytra" / "compiler" / "transpile_cli.py"


def _extract_code_emitter_class(text: str) -> str:
    marker = "class EmitterHooks:"
    i = text.find(marker)
    if i < 0:
        marker = "class CodeEmitter:"
        i = text.find(marker)
    if i < 0:
        raise RuntimeError("CodeEmitter class not found")
    return text[i:].rstrip() + "\n"


def _strip_triple_quoted_docstrings(text: str) -> str:
    out: list[str] = []
    in_doc = False
    quote = ""
    for line in text.splitlines():
        stripped = line.lstrip()
        if not in_doc:
            if stripped.startswith('"""') or stripped.startswith("'''"):
                q = stripped[:3]
                # one-line docstring
                if stripped.count(q) >= 2 and len(stripped) > 3:
                    continue
                in_doc = True
                quote = q
                continue
            out.append(line)
        else:
            if quote in stripped:
                in_doc = False
                quote = ""
            continue
    return "\n".join(out) + "\n"


def _remove_import_line(text: str) -> str:
    targets = [
        "from pytra.compiler.east_parts.code_emitter import CodeEmitter\n",
        "from pytra.compiler.transpile_cli import dump_codegen_options_text, parse_py2cpp_argv, resolve_codegen_options, validate_codegen_options\n",
        "from hooks.cpp.hooks.cpp_hooks import build_cpp_hooks\n",
    ]
    out = text
    for target in targets:
        if target in out:
            out = out.replace(target, "", 1)
    return out


def _extract_top_level_block(text: str, name: str, kind: str) -> str:
    lines = text.splitlines(keepends=True)
    marker = f"{kind} {name}"
    start = -1
    for i, line in enumerate(lines):
        if line.startswith(marker):
            start = i
            if i > 0 and lines[i - 1].startswith("@"):
                start = i - 1
            break
    if start < 0:
        raise RuntimeError(f"block not found: {kind} {name}")
    end = len(lines)
    i = start + 1
    while i < len(lines):
        line = lines[i]
        if line.startswith("def ") or line.startswith("class ") or line.startswith("@"):
            end = i
            break
        i += 1
    block = "".join(lines[start:end]).rstrip() + "\n"
    return block


def _extract_support_blocks() -> str:
    cli_text = SRC_TRANSPILE_CLI.read_text(encoding="utf-8")
    names = [
        "resolve_codegen_options",
        "validate_codegen_options",
        "dump_codegen_options_text",
        "empty_parse_dict",
        "_parse_error_dict",
        "parse_py2cpp_argv",
    ]
    parts: list[str] = []
    for name in names:
        parts.append(_extract_top_level_block(cli_text, name, "def"))
    parts.append(
        "def is_help_requested(parsed: dict[str, str], argv: list[str]) -> bool:\n"
        "    _ = parsed\n"
        "    i = 0\n"
        "    while i < len(argv):\n"
        "        if argv[i] == \"-h\" or argv[i] == \"--help\":\n"
        "            return True\n"
        "        i += 1\n"
        "    return False\n\n"
    )
    parts.append(
        "def build_cpp_hooks() -> dict[str, Any]:\n"
        "    pass\n"
        "    out: dict[str, Any] = {}\n"
        "    return out\n\n"
    )
    return "\n".join(parts)


def _insert_code_emitter(text: str, base_class_text: str, support_blocks: str) -> str:
    marker = "CPP_HEADER = "
    i = text.find(marker)
    if i < 0:
        raise RuntimeError("CPP_HEADER marker not found in py2cpp.py")
    prefix = text[:i]
    suffix = text[i:]
    return prefix.rstrip() + "\n\n" + support_blocks + "\n" + base_class_text + "\n" + suffix


def _replace_dump_options_for_selfhost(text: str) -> str:
    start_marker = "def dump_codegen_options_text("
    end_marker = "\ndef empty_parse_dict("
    i = text.find(start_marker)
    j = text.find(end_marker)
    if i < 0 or j < 0 or j <= i:
        return text
    stub = (
        "def dump_codegen_options_text(\n"
        "    preset: str,\n"
        "    negative_index_mode: str,\n"
        "    bounds_check_mode: str,\n"
        "    floor_div_mode: str,\n"
        "    mod_mode: str,\n"
        "    int_width: str,\n"
        "    str_index_mode: str,\n"
        "    str_slice_mode: str,\n"
        "    opt_level: str,\n"
        ") -> str:\n"
        "    _ = preset\n"
        "    _ = negative_index_mode\n"
        "    _ = bounds_check_mode\n"
        "    _ = floor_div_mode\n"
        "    _ = mod_mode\n"
        "    _ = int_width\n"
        "    _ = str_index_mode\n"
        "    _ = str_slice_mode\n"
        "    _ = opt_level\n"
        "    return \"options:\\n\"\n\n"
    )
    return text[:i] + stub + text[j + 1 :]


def _patch_selfhost_exception_paths(text: str) -> str:
    out = text
    old2 = (
        "    if input_txt == \"\":\n"
        "        print(\n"
        "            \"usage: py2cpp.py INPUT.py [-o OUTPUT.cpp] [--preset MODE] [--negative-index-mode MODE] [--bounds-check-mode MODE] [--floor-div-mode MODE] [--mod-mode MODE] [--int-width MODE] [--str-index-mode MODE] [--str-slice-mode MODE] [-O0|-O1|-O2|-O3] [--no-main] [--dump-deps] [--dump-options]\",\n"
        "            file=sys.stderr,\n"
        "        )\n"
        "        return 1\n"
    )
    new2 = (
        "    if is_help_requested(parsed, argv_list):\n"
        "        print(\n"
        "            \"usage: py2cpp.py INPUT.py [-o OUTPUT.cpp] [--preset MODE] [--negative-index-mode MODE] [--bounds-check-mode MODE] [--floor-div-mode MODE] [--mod-mode MODE] [--int-width MODE] [--str-index-mode MODE] [--str-slice-mode MODE] [-O0|-O1|-O2|-O3] [--no-main] [--dump-deps] [--dump-options]\",\n"
        "            file=sys.stderr,\n"
        "        )\n"
        "        return 0\n"
        "    if input_txt == \"\":\n"
        "        print(\n"
        "            \"usage: py2cpp.py INPUT.py [-o OUTPUT.cpp] [--preset MODE] [--negative-index-mode MODE] [--bounds-check-mode MODE] [--floor-div-mode MODE] [--mod-mode MODE] [--int-width MODE] [--str-index-mode MODE] [--str-slice-mode MODE] [-O0|-O1|-O2|-O3] [--no-main] [--dump-deps] [--dump-options]\",\n"
        "            file=sys.stderr,\n"
        "        )\n"
        "        return 1\n"
    )
    out = out.replace(old2, new2, 1)
    old3 = (
        "        print(\"error: internal error occurred during transpilation.\", file=sys.stderr)\n"
        "        print(\"[internal_error] this may be a bug; report it with a reproducible case.\", file=sys.stderr)\n"
        "        return 1\n"
    )
    new3 = (
        "        print(\"error: internal error occurred during transpilation.\", file=sys.stderr)\n"
        "        print(\"[internal_error] this may be a bug; report it with a reproducible case.\", file=sys.stderr)\n"
        "        print(str(ex), file=sys.stderr)\n"
        "        return 1\n"
    )
    out = out.replace(old3, new3, 1)
    return out


def _patch_main_guard_for_selfhost(text: str) -> str:
    """selfhost 用に末尾 main guard を self-host parser で安定な形へ置換する。"""
    old = 'if __name__ == "__main__":\n    sys.exit(main(list(sys.argv[1:])))\n'
    new = 'if __name__ == "__main__":\n    main(list(sys.argv[1:]))\n'
    return text.replace(old, new)


def _replace_misc_heavy_helpers_for_selfhost(text: str) -> str:
    """selfhost で型崩れしやすい重い補助関数を最小スタブへ置換する。"""
    out = text

    def repl(start_marker: str, end_marker: str, stub: str) -> None:
        nonlocal out
        i = out.find(start_marker)
        j = out.find(end_marker)
        if i >= 0 and j > i:
            out = out[:i] + stub + out[j + 1 :]

    return out


def _patch_code_emitter_hooks_for_selfhost(text: str) -> str:
    """CodeEmitter の hook 呼び出しを selfhost 用に no-op 化する。"""
    out = text

    def repl(start_marker: str, end_marker: str, stub: str) -> None:
        nonlocal out
        i = out.find(start_marker)
        j = out.find(end_marker)
        if i >= 0 and j > i:
            out = out[:i] + stub + out[j + 1 :]

    repl(
        "    def hook_on_emit_stmt(",
        "\n    def hook_on_emit_stmt_kind(",
        (
            "    def hook_on_emit_stmt(self, stmt: dict[str, Any]) -> bool | None:\n"
            "        pass\n"
            "        return None\n"
        ),
    )
    repl(
        "    def hook_on_emit_stmt_kind(",
        "\n    def hook_on_render_call(",
        (
            "    def hook_on_emit_stmt_kind(\n"
            "        self,\n"
            "        kind: str,\n"
            "        stmt: dict[str, Any],\n"
            "    ) -> bool | None:\n"
            "        pass\n"
            "        return None\n"
        ),
    )
    repl(
        "    def hook_on_render_call(",
        "\n    def hook_on_render_module_method(",
        (
            "    def hook_on_render_call(\n"
            "        self,\n"
            "        call_node: dict[str, Any],\n"
            "        func_node: dict[str, Any],\n"
            "        rendered_args: list[str],\n"
            "        rendered_kwargs: dict[str, str],\n"
            "    ) -> str:\n"
            "        pass\n"
            "        return \"\"\n"
        ),
    )
    repl(
        "    def hook_on_render_module_method(",
        "\n    def hook_on_render_object_method(",
        (
            "    def hook_on_render_module_method(\n"
            "        self,\n"
            "        module_name: str,\n"
            "        attr: str,\n"
            "        rendered_args: list[str],\n"
            "        rendered_kwargs: dict[str, str],\n"
            "        arg_nodes: list[Any],\n"
            "    ) -> str:\n"
            "        pass\n"
            "        return \"\"\n"
        ),
    )
    repl(
        "    def hook_on_render_object_method(",
        "\n    def hook_on_render_binop(",
        (
            "    def hook_on_render_object_method(\n"
            "        self,\n"
            "        owner_type: str,\n"
            "        owner_expr: str,\n"
            "        attr: str,\n"
            "        rendered_args: list[str],\n"
            "    ) -> str:\n"
            "        pass\n"
            "        return \"\"\n"
        ),
    )
    repl(
        "    def hook_on_render_binop(",
        "\n    def hook_on_render_expr_kind(",
        (
            "    def hook_on_render_binop(\n"
            "        self,\n"
            "        binop_node: dict[str, Any],\n"
            "        left: str,\n"
            "        right: str,\n"
            "    ) -> str:\n"
            "        pass\n"
            "        return \"\"\n"
        ),
    )
    repl(
        "    def hook_on_render_expr_kind(",
        "\n    def hook_on_render_expr_complex(",
        (
            "    def hook_on_render_expr_kind(\n"
            "        self,\n"
            "        kind: str,\n"
            "        expr_node: dict[str, Any],\n"
            "    ) -> str:\n"
            "        pass\n"
            "        return \"\"\n"
        ),
    )
    repl(
        "    def hook_on_render_expr_complex(",
        "\n    def syntax_text(",
        (
            "    def hook_on_render_expr_complex(\n"
            "        self,\n"
            "        expr_node: dict[str, Any],\n"
            "    ) -> str:\n"
            "        pass\n"
            "        return \"\"\n"
        ),
    )
    return out


def main() -> int:
    py2cpp_text = SRC_PY2CPP.read_text(encoding="utf-8")
    base_text = SRC_BASE.read_text(encoding="utf-8")
    support_blocks = _extract_support_blocks()

    base_class = _strip_triple_quoted_docstrings(_extract_code_emitter_class(base_text))
    py2cpp_text = _remove_import_line(py2cpp_text)
    out = _insert_code_emitter(py2cpp_text, base_class, support_blocks)
    out = _replace_dump_options_for_selfhost(out)
    out = _patch_code_emitter_hooks_for_selfhost(out)
    out = _replace_misc_heavy_helpers_for_selfhost(out)
    out = _patch_main_guard_for_selfhost(out)
    out = _patch_selfhost_exception_paths(out)

    DST_SELFHOST.parent.mkdir(parents=True, exist_ok=True)
    DST_SELFHOST.write_text(out, encoding="utf-8")
    print(str(DST_SELFHOST))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
