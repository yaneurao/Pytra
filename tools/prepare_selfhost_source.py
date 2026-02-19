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
    return "\n".join(parts)


def _insert_code_emitter(text: str, base_class_text: str, support_blocks: str) -> str:
    marker = "CPP_HEADER = "
    i = text.find(marker)
    if i < 0:
        raise RuntimeError("CPP_HEADER marker not found in py2cpp.py")
    prefix = text[:i]
    suffix = text[i:]
    return prefix.rstrip() + "\n\n" + support_blocks + "\n" + base_class_text + "\n" + suffix


def _replace_load_east_for_selfhost(text: str) -> str:
    start_marker = "def load_east("
    end_marker = "\ndef transpile_to_cpp("
    i = text.find(start_marker)
    j = text.find(end_marker)
    if i < 0 or j < 0 or j <= i:
        raise RuntimeError("load_east block not found")
    stub = (
        "def load_east(input_path: Path, parser_backend: str = \"self_hosted\") -> dict[str, Any]:\n"
        "    _ = parser_backend\n"
        "    if input_path.suffix == \".json\":\n"
        "        payload = json.loads(input_path.read_text(encoding=\"utf-8\"))\n"
        "        if isinstance(payload, dict):\n"
        "            if \"ok\" in payload and payload[\"ok\"] == True and \"east\" in payload and isinstance(payload[\"east\"], dict):\n"
        "                return payload[\"east\"]\n"
        "            if \"kind\" in payload and payload[\"kind\"] == \"Module\":\n"
        "                return payload\n"
        "        raise _make_user_error(\n"
        "            \"input_invalid\",\n"
        "            \"EAST JSON の形式が不正です。\",\n"
        "            [\"期待形式: {'ok': true, 'east': {...}} または {'kind': 'Module', ...}\"],\n"
        "        )\n"
        "    details: list[str] = [\"selfhost .py parsing is not implemented yet; use JSON bridge path\"]\n"
        "    raise _make_user_error(\n"
        "        \"not_implemented\",\n"
        "        \"selfhost load_east(.py) is not implemented yet.\",\n"
        "        details,\n"
        "    )\n\n"
    )
    return text[:i] + stub + text[j + 1 :]


def _strip_main_guard(text: str) -> str:
    marker = '\nif __name__ == "__main__":\n'
    i = text.find(marker)
    if i < 0:
        return text
    return text[:i].rstrip() + "\n"


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
        "        print(\"error: 変換中に内部エラーが発生しました。\", file=sys.stderr)\n"
        "        print(\"[internal_error] バグの可能性があります。再現コードを添えて報告してください。\", file=sys.stderr)\n"
        "        return 1\n"
    )
    new3 = (
        "        print(\"error: 変換中に内部エラーが発生しました。\", file=sys.stderr)\n"
        "        print(\"[internal_error] バグの可能性があります。再現コードを添えて報告してください。\", file=sys.stderr)\n"
        "        print(str(ex), file=sys.stderr)\n"
        "        return 1\n"
    )
    out = out.replace(old3, new3, 1)
    return out


def _patch_main_guard_for_selfhost(text: str) -> str:
    old = 'if __name__ == "__main__":\n    sys.exit(main(list(sys.argv[1:])))\n'
    new = 'if __name__ == "__main__":\n    pass\n'
    return text.replace(old, new)


def _replace_import_graph_helpers_for_selfhost(text: str) -> str:
    """selfhost parser 非対応のネスト関数を含むヘルパを簡易実装へ置換する。"""
    out = text
    start_a = "def _analyze_import_graph("
    end_a = "\ndef _format_import_graph_report("
    ia = out.find(start_a)
    ja = out.find(end_a)
    if ia >= 0 and ja > ia:
        stub_a = (
            "def _analyze_import_graph(entry_path: Path) -> dict[str, Any]:\n"
            "    \"\"\"selfhost 最小互換: 依存グラフ解析は簡易結果を返す。\"\"\"\n"
            "    out: dict[str, Any] = {}\n"
            "    out[\"edges\"] = []\n"
            "    out[\"missing_modules\"] = []\n"
            "    out[\"relative_imports\"] = []\n"
            "    out[\"reserved_conflicts\"] = []\n"
            "    out[\"cycles\"] = []\n"
            "    out[\"user_module_files\"] = [str(entry_path)]\n"
            "    return out\n\n"
        )
        out = out[:ia] + stub_a + out[ja + 1 :]

    start_b = "def _format_import_graph_report("
    end_b = "\ndef _validate_import_graph_or_raise("
    ib = out.find(start_b)
    jb = out.find(end_b)
    if ib >= 0 and jb > ib:
        stub_b = (
            "def _format_import_graph_report(analysis: dict[str, Any]) -> str:\n"
            "    \"\"\"selfhost 最小互換: --dump-deps 表示を簡易化する。\"\"\"\n"
            "    _ = analysis\n"
            "    return \"graph:\\n  (selfhost minimal mode)\\n\"\n\n"
        )
        out = out[:ib] + stub_b + out[jb + 1 :]
    return out


def _replace_multi_file_helpers_for_selfhost(text: str) -> str:
    """selfhost parser 非対応のネスト関数を含む multi-file 出力ヘルパを置換する。"""
    out = text
    start = "def _write_multi_file_cpp("
    end = "\ndef _resolve_user_module_path("
    i = out.find(start)
    j = out.find(end)
    if i >= 0 and j > i:
        stub = (
            "def _write_multi_file_cpp(\n"
            "    *,\n"
            "    entry_path: Path,\n"
            "    module_east_map: dict[str, dict[str, Any]],\n"
            "    output_dir: Path,\n"
            "    negative_index_mode: str,\n"
            "    bounds_check_mode: str,\n"
            "    floor_div_mode: str,\n"
            "    mod_mode: str,\n"
            "    int_width: str,\n"
            "    str_index_mode: str,\n"
            "    str_slice_mode: str,\n"
            "    opt_level: str,\n"
            "    top_namespace: str,\n"
            "    emit_main: bool,\n"
            ") -> dict[str, Any]:\n"
            "    _ = entry_path\n"
            "    _ = module_east_map\n"
            "    _ = output_dir\n"
            "    _ = negative_index_mode\n"
            "    _ = bounds_check_mode\n"
            "    _ = floor_div_mode\n"
            "    _ = mod_mode\n"
            "    _ = int_width\n"
            "    _ = str_index_mode\n"
            "    _ = str_slice_mode\n"
            "    _ = opt_level\n"
            "    _ = top_namespace\n"
            "    _ = emit_main\n"
            "    raise _make_user_error(\n"
            "        \"not_implemented\",\n"
            "        \"selfhost multi-file output is not implemented yet.\",\n"
            "        [\"use --single-file in selfhost mode\"],\n"
            "    )\n\n"
        )
        out = out[:i] + stub + out[j + 1 :]
    return out


def main() -> int:
    py2cpp_text = SRC_PY2CPP.read_text(encoding="utf-8")
    base_text = SRC_BASE.read_text(encoding="utf-8")
    support_blocks = _extract_support_blocks()

    base_class = _strip_triple_quoted_docstrings(_extract_code_emitter_class(base_text))
    py2cpp_text = _remove_import_line(py2cpp_text)
    out = _insert_code_emitter(py2cpp_text, base_class, support_blocks)
    out = _replace_dump_options_for_selfhost(out)
    out = _replace_load_east_for_selfhost(out)
    out = _replace_multi_file_helpers_for_selfhost(out)
    out = _replace_import_graph_helpers_for_selfhost(out)
    out = _patch_main_guard_for_selfhost(out)
    out = _strip_main_guard(out)
    out = _patch_selfhost_exception_paths(out)

    DST_SELFHOST.parent.mkdir(parents=True, exist_ok=True)
    DST_SELFHOST.write_text(out, encoding="utf-8")
    print(str(DST_SELFHOST))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
