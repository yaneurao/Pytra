from __future__ import annotations

from pytra.std.pathlib import Path

from toolchain.compiler.transpile_cli import join_str_list
from toolchain.compiler.transpile_cli import python_module_exists_under


RUNTIME_CPP_CORE_ROOT: Path = Path("src/runtime/cpp/core")
RUNTIME_CPP_GEN_ROOT: Path = Path("src/runtime/cpp/gen")
# Legacy name kept as alias while callers are being updated.
RUNTIME_CPP_COMPAT_ROOT: Path = RUNTIME_CPP_CORE_ROOT
RUNTIME_STD_SOURCE_ROOT: Path = Path("src/pytra/std")
RUNTIME_UTILS_SOURCE_ROOT: Path = Path("src/pytra/utils")
RUNTIME_COMPILER_SOURCE_ROOT: Path = Path("src/toolchain/compiler")
RUNTIME_BUILT_IN_SOURCE_ROOT: Path = Path("src/pytra/built_in")
TOOLCHAIN_COMPILER_PREFIX = "toolchain.compiler."
TOOLCHAIN_COMPILER_PREFIX_LEN = len(TOOLCHAIN_COMPILER_PREFIX)


def module_tail_to_cpp_header_path(module_tail: str) -> str:
    """`a.b.c_impl` を `a/b/c-impl.h` へ変換する。"""
    path_tail = module_tail.replace(".", "/")
    parts: list[str] = path_tail.split("/")
    if len(parts) > 0:
        leaf = parts[-1]
        leaf = leaf[: len(leaf) - 5] + "-impl" if leaf.endswith("_impl") else leaf
        parts[-1] = leaf
    return join_str_list("/", parts) + ".h"


def join_runtime_path(base_dir: Path, rel_path: str) -> Path:
    """selfhost-safe な Path 連結（`/` 演算子依存を避ける）。"""
    base_txt = str(base_dir)
    if base_txt.endswith("/"):
        return Path(base_txt + rel_path)
    return Path(base_txt + "/" + rel_path)


def runtime_cpp_header_exists_for_module(module_name_norm: str) -> bool:
    """`pytra.*` モジュールの runtime C++ ヘッダ実在有無を返す。"""

    def _exists_under_runtime_roots(rel_hdr: str) -> bool:
        core_hdr = join_runtime_path(RUNTIME_CPP_CORE_ROOT, rel_hdr)
        gen_hdr = join_runtime_path(RUNTIME_CPP_GEN_ROOT, rel_hdr)
        return core_hdr.exists() or gen_hdr.exists()

    if module_name_norm.startswith("pytra.std."):
        tail = module_name_norm[10:]
        rel = module_tail_to_cpp_header_path(tail) if tail != "" else ""
        return rel != "" and _exists_under_runtime_roots("std/" + rel)
    if module_name_norm.startswith("pytra.utils."):
        tail = module_name_norm[12:]
        rel = module_tail_to_cpp_header_path(tail) if tail != "" else ""
        return rel != "" and _exists_under_runtime_roots("utils/" + rel)
    if module_name_norm.startswith(TOOLCHAIN_COMPILER_PREFIX):
        tail = module_name_norm[TOOLCHAIN_COMPILER_PREFIX_LEN:]
        rel = module_tail_to_cpp_header_path(tail) if tail != "" else ""
        return rel != "" and _exists_under_runtime_roots("compiler/" + rel)
    if module_name_norm.startswith("pytra.built_in."):
        tail = module_name_norm[15:]
        rel = module_tail_to_cpp_header_path(tail) if tail != "" else ""
        return rel != "" and _exists_under_runtime_roots("built_in/" + rel)
    return False


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
    parts: list[str] = module_tail.split("/")
    if len(parts) > 0:
        leaf = parts[-1]
        if leaf.endswith("_impl"):
            parts[-1] = leaf[: len(leaf) - 5] + "-impl"
    rel = join_str_list("/", parts)
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
    def _pick(rel_hdr: str) -> str:
        core_hdr = join_runtime_path(RUNTIME_CPP_CORE_ROOT, rel_hdr)
        gen_hdr = join_runtime_path(RUNTIME_CPP_GEN_ROOT, rel_hdr)
        if core_hdr.exists():
            return "runtime/cpp/core/" + rel_hdr
        if gen_hdr.exists():
            return "runtime/cpp/gen/" + rel_hdr
        return "runtime/cpp/gen/" + rel_hdr

    if module_name_norm.startswith("pytra.std."):
        return _pick("std/" + module_tail_to_cpp_header_path(module_name_norm[10:]))
    if module_name_norm.startswith("pytra.utils."):
        return _pick("utils/" + module_tail_to_cpp_header_path(module_name_norm[12:]))
    if module_name_norm.startswith(TOOLCHAIN_COMPILER_PREFIX):
        return _pick("compiler/" + module_tail_to_cpp_header_path(module_name_norm[TOOLCHAIN_COMPILER_PREFIX_LEN:]))
    if module_name_norm.startswith("pytra.built_in."):
        return _pick("built_in/" + module_tail_to_cpp_header_path(module_name_norm[15:]))
    return "runtime/cpp/gen/" + module_name_norm.replace(".", "/") + ".h"


def runtime_module_has_header(module_name_norm: str) -> bool:
    """`pytra.std|utils|compiler|built_in` の runtime ヘッダを持つか判定する。"""
    if not module_name_norm.startswith("pytra."):
        return False
    if module_name_norm.startswith("pytra.std.") and python_module_exists_under(RUNTIME_STD_SOURCE_ROOT, module_name_norm[10:].replace(".", "/")):
        return runtime_cpp_header_exists_for_module(module_name_norm)
    if module_name_norm.startswith("pytra.utils.") and python_module_exists_under(RUNTIME_UTILS_SOURCE_ROOT, module_name_norm[12:].replace(".", "/")):
        return runtime_cpp_header_exists_for_module(module_name_norm)
    if module_name_norm.startswith(TOOLCHAIN_COMPILER_PREFIX) and python_module_exists_under(
        RUNTIME_COMPILER_SOURCE_ROOT, module_name_norm[TOOLCHAIN_COMPILER_PREFIX_LEN:].replace(".", "/")
    ):
        return runtime_cpp_header_exists_for_module(module_name_norm)
    if module_name_norm.startswith("pytra.built_in.") and python_module_exists_under(RUNTIME_BUILT_IN_SOURCE_ROOT, module_name_norm[15:].replace(".", "/")):
        return runtime_cpp_header_exists_for_module(module_name_norm)
    return False
