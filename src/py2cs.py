#!/usr/bin/env python3
"""EAST -> C# transpiler CLI."""

from __future__ import annotations

from pytra.std.typing import Any

from backends.cs.emitter.cs_emitter import load_cs_profile, transpile_to_csharp
from backends.cs.lower import lower_east3_to_cs_ir
from backends.cs.optimizer import optimize_cs_ir
from toolchain.compiler.py2x_wrapper import run_py2x_for_target
from toolchain.compiler.transpile_cli import load_east3_document
from pytra.std.pathlib import Path
from pytra.std import sys


def load_east(
    input_path: Path,
    parser_backend: str = "self_hosted",
    east_stage: str = "3",
    object_dispatch_mode: str = "native",
    east3_opt_level: str = "1",
    east3_opt_pass: str = "",
    dump_east3_before_opt: str = "",
    dump_east3_after_opt: str = "",
    dump_east3_opt_trace: str = "",
) -> dict[str, Any]:
    """`.py` / `.json` を EAST ドキュメントへ読み込む。"""
    if east_stage != "3":
        raise RuntimeError("unsupported east_stage: " + east_stage)
    doc3 = load_east3_document(
        input_path,
        parser_backend=parser_backend,
        object_dispatch_mode=object_dispatch_mode,
        east3_opt_level=east3_opt_level,
        east3_opt_pass=east3_opt_pass,
        dump_east3_before_opt=dump_east3_before_opt,
        dump_east3_after_opt=dump_east3_after_opt,
        dump_east3_opt_trace=dump_east3_opt_trace,
        target_lang="cs",
    )
    empty_doc: dict[str, Any] = {}
    return doc3 if isinstance(doc3, dict) else empty_doc


def _default_output_path(input_path: Path) -> Path:
    """入力パスから既定の `.cs` 出力先を決定する。"""
    out = str(input_path)
    if out.endswith(".py"):
        out = out[:-3] + ".cs"
    elif out.endswith(".json"):
        out = out[:-5] + ".cs"
    else:
        out = out + ".cs"
    return Path(out)


def _arg_get_str(args: dict[str, str], key: str, default_value: str = "") -> str:
    """argparse(dict) から文字列値を取り出す。"""
    if key not in args:
        return default_value
    val = args[key]
    if isinstance(val, str):
        return val
    return default_value


def _parse_py2cs_error_dict(msg: str) -> dict[str, str]:
    out: dict[str, str] = {}
    out["__error"] = msg
    return out


def parse_py2cs_argv(argv: list[str]) -> dict[str, str]:
    # static-contract marker for check_noncpp_east3_contract.py: choices=["2", "3"]
    out: dict[str, str] = {}
    out["input"] = ""
    out["output"] = ""
    out["parser_backend"] = ""
    out["east_stage"] = ""
    out["object_dispatch_mode"] = ""
    out["east3_opt_level"] = ""
    out["east3_opt_pass"] = ""
    out["dump_east3_before_opt"] = ""
    out["dump_east3_after_opt"] = ""
    out["dump_east3_opt_trace"] = ""
    out["help"] = "0"

    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "-h" or a == "--help":
            out["help"] = "1"
        elif a == "-o" or a == "--output":
            i += 1
            if i >= len(argv):
                return _parse_py2cs_error_dict("missing value for " + a)
            out["output"] = argv[i]
        elif a == "--parser-backend":
            i += 1
            if i >= len(argv):
                return _parse_py2cs_error_dict("missing value for --parser-backend")
            out["parser_backend"] = argv[i]
        elif a == "--east-stage":
            i += 1
            if i >= len(argv):
                return _parse_py2cs_error_dict("missing value for --east-stage")
            out["east_stage"] = argv[i]
        elif a == "--object-dispatch-mode":
            i += 1
            if i >= len(argv):
                return _parse_py2cs_error_dict("missing value for --object-dispatch-mode")
            out["object_dispatch_mode"] = argv[i]
        elif a == "--east3-opt-level":
            i += 1
            if i >= len(argv):
                return _parse_py2cs_error_dict("missing value for --east3-opt-level")
            out["east3_opt_level"] = argv[i]
        elif a == "--east3-opt-pass":
            i += 1
            if i >= len(argv):
                return _parse_py2cs_error_dict("missing value for --east3-opt-pass")
            out["east3_opt_pass"] = argv[i]
        elif a == "--dump-east3-before-opt":
            i += 1
            if i >= len(argv):
                return _parse_py2cs_error_dict("missing value for --dump-east3-before-opt")
            out["dump_east3_before_opt"] = argv[i]
        elif a == "--dump-east3-after-opt":
            i += 1
            if i >= len(argv):
                return _parse_py2cs_error_dict("missing value for --dump-east3-after-opt")
            out["dump_east3_after_opt"] = argv[i]
        elif a == "--dump-east3-opt-trace":
            i += 1
            if i >= len(argv):
                return _parse_py2cs_error_dict("missing value for --dump-east3-opt-trace")
            out["dump_east3_opt_trace"] = argv[i]
        elif a.startswith("-"):
            return _parse_py2cs_error_dict("unknown option: " + a)
        else:
            if out["input"] == "":
                out["input"] = a
            elif out["output"] == "":
                out["output"] = a
            else:
                return _parse_py2cs_error_dict("unexpected extra argument: " + a)
        i += 1
    return out


def main(argv: list[str] | None = None) -> int:
    """CLI 入口。互換ラッパとして py2x へ委譲する。"""
    return run_py2x_for_target("cs", argv_override=argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
