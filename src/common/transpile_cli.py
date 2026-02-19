"""トランスパイラ CLI の共通引数定義。"""

from __future__ import annotations

from pylib import argparse
from pylib.typing import Iterable


def add_common_transpile_args(
    parser: argparse.ArgumentParser,
    *,
    enable_negative_index_mode: bool = False,
    parser_backends: Iterable[str] | None = None,
) -> None:
    """各トランスパイラで共通利用する CLI 引数を追加する。"""
    parser.add_argument("input", help="Input .py or EAST .json")
    parser.add_argument("-o", "--output", help="Output file path")
    if enable_negative_index_mode:
        parser.add_argument(
            "--negative-index-mode",
            choices=["always", "const_only", "off"],
            help="Policy for Python-style negative indexing on list/str subscripts",
        )
    if parser_backends is not None:
        choices = list(parser_backends)
        parser.add_argument(
            "--parser-backend",
            choices=choices,
            help="EAST parser backend for .py input",
        )


def normalize_common_transpile_args(
    args: argparse.Namespace,
    *,
    default_negative_index_mode: str | None = None,
    default_parser_backend: str | None = None,
) -> argparse.Namespace:
    """共通引数の既定値を埋める。"""
    if default_negative_index_mode is not None:
        cur = getattr(args, "negative_index_mode", None)
        if not cur:
            setattr(args, "negative_index_mode", default_negative_index_mode)
    if default_parser_backend is not None:
        cur = getattr(args, "parser_backend", None)
        if not cur:
            setattr(args, "parser_backend", default_parser_backend)
    return args


def resolve_codegen_options(
    preset: str,
    negative_index_mode_opt: str,
    bounds_check_mode_opt: str,
    floor_div_mode_opt: str,
    mod_mode_opt: str,
    int_width_opt: str,
    str_index_mode_opt: str,
    str_slice_mode_opt: str,
    opt_level_opt: str,
) -> tuple[str, str, str, str, str, str, str, str]:
    """プリセットと個別指定から最終オプションを決定する。"""
    neg = "const_only"
    bnd = "off"
    fdiv = "native"
    mod = "native"
    int_width = "64"
    str_index = "native"
    str_slice = "byte"
    opt_level = "3"

    if preset != "":
        if preset == "native":
            neg = "off"
            bnd = "off"
            fdiv = "native"
            mod = "native"
            int_width = "64"
            str_index = "native"
            str_slice = "byte"
            opt_level = "3"
        elif preset == "balanced":
            neg = "const_only"
            bnd = "debug"
            fdiv = "python"
            mod = "python"
            int_width = "64"
            str_index = "byte"
            str_slice = "byte"
            opt_level = "2"
        elif preset == "python":
            neg = "always"
            bnd = "always"
            fdiv = "python"
            mod = "python"
            int_width = "bigint"
            str_index = "codepoint"
            str_slice = "codepoint"
            opt_level = "0"
        else:
            raise ValueError(f"invalid --preset: {preset}")

    if negative_index_mode_opt != "":
        neg = negative_index_mode_opt
    if bounds_check_mode_opt != "":
        bnd = bounds_check_mode_opt
    if floor_div_mode_opt != "":
        fdiv = floor_div_mode_opt
    if mod_mode_opt != "":
        mod = mod_mode_opt
    if int_width_opt != "":
        int_width = int_width_opt
    if str_index_mode_opt != "":
        str_index = str_index_mode_opt
    if str_slice_mode_opt != "":
        str_slice = str_slice_mode_opt
    if opt_level_opt != "":
        opt_level = opt_level_opt
    return neg, bnd, fdiv, mod, int_width, str_index, str_slice, opt_level


def validate_codegen_options(
    negative_index_mode: str,
    bounds_check_mode: str,
    floor_div_mode: str,
    mod_mode: str,
    int_width: str,
    str_index_mode: str,
    str_slice_mode: str,
    opt_level: str,
) -> str:
    """最終オプションの妥当性を検証し、エラーメッセージを返す。"""
    if negative_index_mode not in {"always", "const_only", "off"}:
        return f"invalid --negative-index-mode: {negative_index_mode}"
    if bounds_check_mode not in {"always", "debug", "off"}:
        return f"invalid --bounds-check-mode: {bounds_check_mode}"
    if floor_div_mode not in {"native", "python"}:
        return f"invalid --floor-div-mode: {floor_div_mode}"
    if mod_mode not in {"native", "python"}:
        return f"invalid --mod-mode: {mod_mode}"
    if int_width not in {"32", "64", "bigint"}:
        return f"invalid --int-width: {int_width}"
    if int_width == "bigint":
        return "--int-width=bigint is not implemented yet"
    if str_index_mode not in {"byte", "codepoint", "native"}:
        return f"invalid --str-index-mode: {str_index_mode}"
    if str_slice_mode not in {"byte", "codepoint"}:
        return f"invalid --str-slice-mode: {str_slice_mode}"
    if opt_level not in {"0", "1", "2", "3"}:
        return f"invalid -O level: {opt_level}"
    if str_index_mode == "codepoint":
        return "--str-index-mode=codepoint is not implemented yet"
    if str_slice_mode == "codepoint":
        return "--str-slice-mode=codepoint is not implemented yet"
    return ""


def dump_codegen_options_text(
    preset: str,
    negative_index_mode: str,
    bounds_check_mode: str,
    floor_div_mode: str,
    mod_mode: str,
    int_width: str,
    str_index_mode: str,
    str_slice_mode: str,
    opt_level: str,
) -> str:
    """解決済みオプションを人間向けテキストへ整形する。"""
    p = preset if preset != "" else "(none)"
    out = "options:\n"
    out += f"  preset: {p}\n"
    out += f"  negative-index-mode: {negative_index_mode}\n"
    out += f"  bounds-check-mode: {bounds_check_mode}\n"
    out += f"  floor-div-mode: {floor_div_mode}\n"
    out += f"  mod-mode: {mod_mode}\n"
    out += f"  int-width: {int_width}\n"
    out += f"  str-index-mode: {str_index_mode}\n"
    out += f"  str-slice-mode: {str_slice_mode}\n"
    out += f"  opt-level: {opt_level}\n"
    return out


def empty_parse_dict() -> dict[str, str]:
    out: dict[str, str] = {}
    return out


def parse_py2cpp_argv(argv: list[str]) -> tuple[dict[str, str], str]:
    """py2cpp 向け CLI 引数を解析し、値辞書またはエラー文字列を返す。"""
    out: dict[str, str] = {
        "input": "",
        "output": "",
        "negative_index_mode_opt": "",
        "bounds_check_mode_opt": "",
        "floor_div_mode_opt": "",
        "mod_mode_opt": "",
        "int_width_opt": "",
        "str_index_mode_opt": "",
        "str_slice_mode_opt": "",
        "opt_level_opt": "",
        "preset": "",
        "parser_backend": "self_hosted",
        "no_main": "0",
        "dump_deps": "0",
        "dump_options": "0",
        "help": "0",
    }
    i = 0
    while i < len(argv):
        a = str(argv[i])
        if a == "-h" or a == "--help":
            out["help"] = "1"
        elif a == "-o" or a == "--output":
            i += 1
            if i >= len(argv):
                return empty_parse_dict(), "missing value for --output"
            out["output"] = argv[i]
        elif a == "--negative-index-mode":
            i += 1
            if i >= len(argv):
                return empty_parse_dict(), "missing value for --negative-index-mode"
            out["negative_index_mode_opt"] = argv[i]
        elif a == "--bounds-check-mode":
            i += 1
            if i >= len(argv):
                return empty_parse_dict(), "missing value for --bounds-check-mode"
            out["bounds_check_mode_opt"] = argv[i]
        elif a == "--floor-div-mode":
            i += 1
            if i >= len(argv):
                return empty_parse_dict(), "missing value for --floor-div-mode"
            out["floor_div_mode_opt"] = argv[i]
        elif a == "--mod-mode":
            i += 1
            if i >= len(argv):
                return empty_parse_dict(), "missing value for --mod-mode"
            out["mod_mode_opt"] = argv[i]
        elif a == "--int-width":
            i += 1
            if i >= len(argv):
                return empty_parse_dict(), "missing value for --int-width"
            out["int_width_opt"] = argv[i]
        elif a == "--str-index-mode":
            i += 1
            if i >= len(argv):
                return empty_parse_dict(), "missing value for --str-index-mode"
            out["str_index_mode_opt"] = argv[i]
        elif a == "--str-slice-mode":
            i += 1
            if i >= len(argv):
                return empty_parse_dict(), "missing value for --str-slice-mode"
            out["str_slice_mode_opt"] = argv[i]
        elif a in {"-O0", "-O1", "-O2", "-O3"}:
            out["opt_level_opt"] = a[2:]
        elif a == "-O":
            i += 1
            if i >= len(argv):
                return empty_parse_dict(), "missing value for -O"
            out["opt_level_opt"] = argv[i]
        elif a == "--opt-level":
            i += 1
            if i >= len(argv):
                return empty_parse_dict(), "missing value for --opt-level"
            out["opt_level_opt"] = argv[i]
        elif a == "--preset":
            i += 1
            if i >= len(argv):
                return empty_parse_dict(), "missing value for --preset"
            out["preset"] = argv[i]
        elif a == "--parser-backend":
            i += 1
            if i >= len(argv):
                return empty_parse_dict(), "missing value for --parser-backend"
            out["parser_backend"] = argv[i]
        elif a == "--no-main":
            out["no_main"] = "1"
        elif a == "--dump-deps":
            out["dump_deps"] = "1"
        elif a == "--dump-options":
            out["dump_options"] = "1"
        elif a.startswith("-"):
            return empty_parse_dict(), f"unknown option: {a}"
        else:
            if out["input"] == "":
                out["input"] = a
            else:
                return empty_parse_dict(), f"unexpected extra argument: {a}"
        i += 1
    return out, ""
