from __future__ import annotations

from pytra.std.pathlib import Path

from toolchain.compiler.transpile_cli import join_str_list
from toolchain.frontends.runtime_symbol_index import canonical_runtime_module_id
from toolchain.frontends.runtime_symbol_index import lookup_target_module_primary_header
from toolchain.frontends.runtime_symbol_index import runtime_module_exists


RUNTIME_CPP_CORE_ROOT: Path = Path("src/runtime/cpp/core")
RUNTIME_CPP_ROOT: Path = Path("src/runtime/cpp")
# Legacy name kept as alias while callers are being updated.
RUNTIME_CPP_COMPAT_ROOT: Path = RUNTIME_CPP_CORE_ROOT
TOOLCHAIN_COMPILER_PREFIX = "toolchain.compiler."
TOOLCHAIN_COMPILER_PREFIX_LEN = len(TOOLCHAIN_COMPILER_PREFIX)


def module_tail_to_cpp_header_path(module_tail: str) -> str:
    """`a.b.c` を `a/b/c.gen.h` へ変換する。"""
    return module_tail.replace(".", "/") + ".gen.h"


def module_tail_to_cpp_public_header_path(module_tail: str) -> str:
    """runtime module tail を public include 用 `pytra/.../*.h` へ変換する。"""
    rel = join_str_list("/", module_tail.split("/"))
    if rel == "":
        return ""
    if rel.startswith("std/"):
        return "pytra/std/" + rel[4:] + ".h"
    if rel.startswith("built_in/"):
        return "pytra/built_in/" + rel[9:] + ".h"
    if rel.startswith("compiler/"):
        return "pytra/compiler/" + rel[9:] + ".h"
    if rel == "std":
        return "pytra/std.h"
    if rel == "built_in":
        return "pytra/built_in.h"
    if rel == "compiler":
        return "pytra/compiler.h"
    return "pytra/utils/" + rel + ".h"


def join_runtime_path(base_dir: Path, rel_path: str) -> Path:
    """selfhost-safe な Path 連結（`/` 演算子依存を避ける）。"""
    base_txt = str(base_dir)
    if base_txt.endswith("/"):
        return Path(base_txt + rel_path)
    return Path(base_txt + "/" + rel_path)


def runtime_cpp_header_exists_for_module(module_name_norm: str) -> bool:
    """`pytra.*` モジュールの runtime C++ ヘッダ実在有無を返す。"""
    module_id = canonical_runtime_module_id(module_name_norm)
    return lookup_target_module_primary_header("cpp", module_id) != ""


def runtime_module_tail_from_source_path(input_path: Path) -> str:
    """`src/pytra/std|utils|built_in` と `src/toolchain/compiler` から runtime tail を返す。"""
    src = str(input_path)
    rel = ""
    std_prefix = "src/pytra/std/"
    utils_prefix = "src/pytra/utils/"
    compiler_prefix = "src/toolchain/compiler/"
    built_in_prefix = "src/pytra/built_in/"
    if src.startswith(std_prefix):
        rel = "std/" + src[len(std_prefix) :]
    elif src.startswith(utils_prefix):
        rel = src[len(utils_prefix) :]
    elif src.startswith(compiler_prefix):
        rel = "compiler/" + src[len(compiler_prefix) :]
    elif src.startswith(built_in_prefix):
        rel = "built_in/" + src[len(built_in_prefix) :]
    else:
        return ""
    if rel.endswith(".py"):
        rel = rel[: len(rel) - 3]
    if rel.endswith("/__init__"):
        rel = rel[: len(rel) - 9]
    return rel


def prepend_generated_cpp_banner(cpp_text: str, source_path: Path) -> str:
    """生成 C++ ソースへ AUTO-GENERATED バナーを先頭付与する。"""
    marker = "// AUTO-GENERATED FILE. DO NOT EDIT."
    if cpp_text.startswith(marker):
        return cpp_text
    lines = [
        marker,
        "// source: " + str(source_path),
        "// generated-by: src/backends/cpp/cli.py",
        "",
    ]
    return join_str_list("\n", lines) + cpp_text


def is_runtime_emit_input_path(input_path: Path) -> bool:
    """`--emit-runtime-cpp` 対象パスかを判定する。"""
    return runtime_module_tail_from_source_path(input_path) != ""


def runtime_output_rel_tail(module_tail: str) -> str:
    """module tail を runtime/cpp 相対パス tail へ写像する。"""
    rel = join_str_list("/", module_tail.split("/"))
    if rel == "std" or rel.startswith("std/"):
        return rel
    if rel == "compiler" or rel.startswith("compiler/"):
        return rel
    if rel == "built_in" or rel.startswith("built_in/"):
        return rel
    return "utils/" + rel


def runtime_namespace_for_tail(module_tail: str) -> str:
    """runtime source tail から C++ namespace を導出する。"""
    if module_tail == "":
        return ""
    if module_tail.startswith("std/"):
        rest: str = module_tail[4:].replace("/", "::")
        return "pytra::std::" + rest
    if module_tail == "std":
        return "pytra::std"
    if module_tail.startswith("compiler/"):
        rest = module_tail[9:].replace("/", "::")
        return "pytra::compiler::" + rest
    if module_tail == "compiler":
        return "pytra::compiler"
    if module_tail.startswith("built_in/"):
        return ""
    if module_tail == "built_in":
        return ""
    return "pytra::utils::" + module_tail.replace("/", "::")


def module_name_to_cpp_include(module_name_norm: str) -> str:
    """`pytra.std|utils|compiler|built_in` 名を C++ include 形式へ変換する。"""
    module_id = canonical_runtime_module_id(module_name_norm)
    indexed = lookup_target_module_primary_header("cpp", module_id)
    if indexed != "":
        if indexed.startswith("src/runtime/cpp/"):
            return indexed[len("src/runtime/cpp/") :]
        if indexed.startswith("src/"):
            return indexed[4:]
        return indexed
    if module_id.startswith(TOOLCHAIN_COMPILER_PREFIX):
        rel_hdr = "compiler/" + module_tail_to_cpp_header_path(module_id[TOOLCHAIN_COMPILER_PREFIX_LEN:])
        return "runtime/cpp/" + rel_hdr
    return ""


def runtime_module_has_header(module_name_norm: str) -> bool:
    """`pytra.std|utils|compiler|built_in` の runtime ヘッダを持つか判定する。"""
    module_id = canonical_runtime_module_id(module_name_norm)
    if module_id.startswith("pytra.") and runtime_module_exists(module_id):
        return runtime_cpp_header_exists_for_module(module_id)
    if module_id.startswith(TOOLCHAIN_COMPILER_PREFIX):
        return runtime_cpp_header_exists_for_module(module_id)
    return False
