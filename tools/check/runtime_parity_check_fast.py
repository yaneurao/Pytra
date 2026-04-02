#!/usr/bin/env python3
"""Fast runtime parity check using in-memory pipeline (no CLI subprocess for transpile).

This is the high-speed variant of runtime_parity_check.py.  The transpile stage
calls toolchain2 Python APIs directly instead of spawning ``python pytra-cli.py``
subprocesses, eliminating per-case process startup and intermediate file I/O.

Compile + run still uses subprocesses (g++, go run, etc.).

Usage:
    python3 tools/runtime_parity_check_fast.py --targets cpp --category oop
    python3 tools/runtime_parity_check_fast.py --targets go
    python3 tools/runtime_parity_check_fast.py --case-root sample --targets cpp
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
import time
import zlib
from dataclasses import dataclass
from pathlib import Path

# --- repo bootstrap ---
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

# --- toolchain2 imports (in-memory pipeline) ---
from toolchain2.common.jv import deep_copy_json  # type: ignore
from toolchain2.compile.lower import lower_east2_to_east3  # type: ignore
from toolchain2.emit.cs.emitter import emit_cs_module  # type: ignore
from toolchain2.emit.cpp.emitter import emit_cpp_module  # type: ignore
from toolchain2.emit.cpp.header_gen import build_cpp_header_from_east3  # type: ignore
from toolchain2.emit.cpp.runtime_bundle import emit_runtime_module_artifacts  # type: ignore
from toolchain2.emit.go.emitter import emit_go_module  # type: ignore
from toolchain2.emit.java.emitter import emit_java_module  # type: ignore
from toolchain2.emit.java.types import java_module_class_name  # type: ignore
from toolchain2.emit.scala.emitter import emit_scala_module  # type: ignore
from toolchain2.emit.kotlin.emitter import emit_kotlin_module  # type: ignore
from toolchain2.emit.rs.emitter import emit_rs_module  # type: ignore
from toolchain2.emit.ts.emitter import emit_ts_module  # type: ignore
from toolchain2.emit.dart.emitter import emit_dart_module  # type: ignore
from toolchain2.emit.ruby.emitter import transpile_to_ruby as emit_ruby_module  # type: ignore
from toolchain2.emit.lua.emitter import emit_lua_module  # type: ignore
from toolchain2.emit.php.emitter import emit_php_module  # type: ignore
from toolchain2.link.linker import link_modules  # type: ignore
from toolchain2.emit.cpp.runtime_paths import runtime_rel_tail_for_module  # type: ignore
from toolchain2.optimize.optimizer import optimize_east3_document  # type: ignore
from toolchain2.optimize.optimizer import optimize_east3_doc_only  # type: ignore
from toolchain2.optimize.optimizer import resolve_bounds_check_mode  # type: ignore
from toolchain2.optimize.optimizer import resolve_negative_index_mode  # type: ignore
from toolchain2.parse.py.parse_python import parse_python_file  # type: ignore
from toolchain2.resolve.py.builtin_registry import load_builtin_registry  # type: ignore
from toolchain2.resolve.py.resolver import resolve_east1_to_east2  # type: ignore

# --- reuse existing parity infrastructure ---
from runtime_parity_check import (  # type: ignore
    FIXTURE_ROOT,
    SAMPLE_ROOT,
    STDLIB_ROOT,
    CheckRecord,
    _LANG_UNSUPPORTED_FIXTURES,
    _crc32_hex,
    _file_crc32,
    _file_size_normalized,
    _normalize_output_for_compare,
    _parse_output_path,
    _purge_case_artifacts,
    _resolve_output_path,
    _run_cpp_emit_dir,
    _safe_unlink,
    _target_output_text,
    _tool_env_for_target,
    can_run,
    collect_fixture_case_stems,
    collect_sample_case_stems,
    collect_stdlib_case_stems,
    find_case_path,
    normalize,
    run_shell,
)
from toolchain.misc.pytra_cli_profiles import get_target_profile, list_parity_targets  # type: ignore


# ---------------------------------------------------------------------------
# Registry singleton (loaded once, shared across all cases)
# ---------------------------------------------------------------------------

_REGISTRY = None


def _get_registry():
    global _REGISTRY
    if _REGISTRY is not None:
        return _REGISTRY
    root = ROOT
    east1_root = root / "test" / "include" / "east1" / "py"
    builtins_path = east1_root / "built_in" / "builtins.py.east1"
    containers_path = east1_root / "built_in" / "containers.py.east1"
    stdlib_dir = east1_root / "std"
    _REGISTRY = load_builtin_registry(builtins_path, containers_path, stdlib_dir)
    return _REGISTRY


def _optimizer_debug_flags(
    opt_level: int,
    negative_index_mode: str,
    bounds_check_mode: str,
) -> dict[str, JsonVal]:
    return {
        "negative_index_mode": resolve_negative_index_mode(negative_index_mode, opt_level),
        "bounds_check_mode": resolve_bounds_check_mode(bounds_check_mode, opt_level),
    }


def _optimize_linked_runtime_modules_in_place(
    linked_modules: list[object],
    *,
    opt_level: int,
    debug_flags: dict[str, JsonVal],
) -> None:
    for module in linked_modules:
        module_kind = getattr(module, "module_kind", "")
        if module_kind not in ("runtime", "helper"):
            continue
        east_doc = getattr(module, "east_doc", None)
        if not isinstance(east_doc, dict):
            continue
        module.east_doc = optimize_east3_doc_only(
            east_doc,
            opt_level=opt_level,
            debug_flags=debug_flags,
        )


# ---------------------------------------------------------------------------
# In-memory transpile
# ---------------------------------------------------------------------------


def _transpile_in_memory(
    case_path: Path,
    target: str,
    output_dir: Path,
    opt_level: int = 1,
    negative_index_mode: str = "",
    bounds_check_mode: str = "",
) -> tuple[bool, str]:
    """Transpile a .py file to target language using in-memory pipeline.

    Returns (success, error_message).
    """
    try:
        # js is TS with strip_types=True; pipeline uses "ts" profile
        pipeline_target = "ts" if target == "js" else target
        optimizer_debug_flags = _optimizer_debug_flags(opt_level, negative_index_mode, bounds_check_mode)

        # 1. Parse
        east1_doc = parse_python_file(str(case_path))

        # 2. Resolve
        registry = _get_registry()
        east2_doc = deep_copy_json(east1_doc)
        if not isinstance(east2_doc, dict):
            return False, "invalid east1 document"
        resolve_east1_to_east2(east2_doc, registry=registry)

        # 3. Compile (lower)
        east3_doc = lower_east2_to_east3(east2_doc, target_language=pipeline_target)

        # 4. Optimize
        east3_opt, _report = optimize_east3_document(
            east3_doc,
            opt_level=opt_level,
            debug_flags=optimizer_debug_flags,
        )

        # 5. Link — write east3-opt to temp file for link_modules
        link_dir = output_dir / "_link"
        link_dir.mkdir(parents=True, exist_ok=True)
        link_path = link_dir / (case_path.stem + ".east3")
        link_path.write_text(
            json.dumps(east3_opt, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        link_result = link_modules([str(link_path)], target=pipeline_target, dispatch_mode="native")
        _optimize_linked_runtime_modules_in_place(
            link_result.linked_modules,
            opt_level=opt_level,
            debug_flags=optimizer_debug_flags,
        )

        # 6. Emit
        emit_dir = output_dir / "emit"
        emit_dir.mkdir(parents=True, exist_ok=True)

        if target == "go":
            for m in link_result.linked_modules:
                code = emit_go_module(m.east_doc)
                if code.strip() == "":
                    continue
                out_name = m.module_id.replace(".", "_") + ".go"
                emit_dir.joinpath(out_name).write_text(code, encoding="utf-8")
            _copy_go_runtime(emit_dir)
        elif target == "java":
            for m in link_result.linked_modules:
                if m.module_kind == "runtime":
                    continue
                code = emit_java_module(m.east_doc)
                if code.strip() == "":
                    continue
                out_name = java_module_class_name(m.module_id) + ".java"
                emit_dir.joinpath(out_name).write_text(code, encoding="utf-8")
            _copy_java_runtime(emit_dir)
        elif target == "scala":
            for m in link_result.linked_modules:
                code = emit_scala_module(m.east_doc)
                if code.strip() == "":
                    continue
                emit_dir.joinpath(m.module_id.replace(".", "_") + ".scala").write_text(
                    code, encoding="utf-8"
                )
            _copy_scala_runtime(emit_dir)
        elif target == "kotlin":
            for m in link_result.linked_modules:
                code = emit_kotlin_module(m.east_doc)
                if code.strip() == "":
                    continue
                emit_dir.joinpath(m.module_id.replace(".", "_") + ".kt").write_text(
                    code, encoding="utf-8"
                )
            _copy_kotlin_runtime(emit_dir)
        elif target == "rs":
            for m in link_result.linked_modules:
                code = emit_rs_module(m.east_doc)
                if code.strip() == "":
                    continue
                emit_dir.joinpath(m.module_id.replace(".", "_") + ".rs").write_text(
                    code, encoding="utf-8"
                )
            _copy_rs_runtime(emit_dir)
        elif target == "cs":
            for m in link_result.linked_modules:
                code = emit_cs_module(m.east_doc)
                if code.strip() == "":
                    continue
                emit_dir.joinpath(m.module_id.replace(".", "_") + ".cs").write_text(
                    code, encoding="utf-8"
                )
            _copy_cs_runtime(emit_dir)
        elif target == "ts":
            for m in link_result.linked_modules:
                code = emit_ts_module(m.east_doc)
                if code.strip() == "":
                    continue
                emit_dir.joinpath(m.module_id.replace(".", "_") + ".ts").write_text(
                    code, encoding="utf-8"
                )
            _copy_ts_runtime(emit_dir)
        elif target == "js":
            for m in link_result.linked_modules:
                code = emit_ts_module(m.east_doc, strip_types=True)
                if code.strip() == "":
                    continue
                emit_dir.joinpath(m.module_id.replace(".", "_") + ".js").write_text(
                    code, encoding="utf-8"
                )
            _copy_js_runtime(emit_dir)
            # ESM imports require "type": "module" in package.json for .js files
            pkg_json = emit_dir / "package.json"
            if not pkg_json.exists():
                pkg_json.write_text('{"type":"module"}\n', encoding="utf-8")
        elif target == "cpp":
            for m in link_result.linked_modules:
                if m.module_kind == "runtime":
                    emit_runtime_module_artifacts(
                        m.module_id,
                        m.east_doc,
                        output_dir=emit_dir,
                        source_path=m.source_path,
                    )
                    continue
                if m.module_kind == "helper":
                    _emit_helper_cpp(m, emit_dir)
                    continue
                code = emit_cpp_module(m.east_doc)
                if code.strip() == "":
                    continue
                emit_dir.joinpath(m.module_id.replace(".", "_") + ".cpp").write_text(
                    code, encoding="utf-8"
                )
        elif target == "ruby":
            for m in link_result.linked_modules:
                code = emit_ruby_module(m.east_doc)
                if code.strip() == "":
                    continue
                emit_dir.joinpath(m.module_id.replace(".", "_") + ".rb").write_text(
                    code, encoding="utf-8"
                )
            _copy_ruby_runtime(emit_dir)
        elif target == "lua":
            for m in link_result.linked_modules:
                code = emit_lua_module(m.east_doc)
                if code.strip() == "":
                    continue
                emit_dir.joinpath(m.module_id.replace(".", "_") + ".lua").write_text(
                    code, encoding="utf-8"
                )
            _copy_lua_runtime(emit_dir)
        elif target == "php":
            for m in link_result.linked_modules:
                code = emit_php_module(m.east_doc)
                if code.strip() == "":
                    continue
                emit_dir.joinpath(m.module_id.replace(".", "_") + ".php").write_text(
                    code, encoding="utf-8"
                )
            _copy_php_runtime(emit_dir)
        elif target == "dart":
            for m in link_result.linked_modules:
                _inject_dart_emit_context(
                    m.east_doc,
                    m.module_id,
                    is_entry=bool(getattr(m, "is_entry", False)),
                )
                code = emit_dart_module(m.east_doc)
                if code.strip() == "":
                    continue
                out_path = emit_dir / _dart_rel_output_path(m.module_id)
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(code, encoding="utf-8")
            _copy_dart_runtime(emit_dir)
        else:
            return False, f"unsupported target: {target}"

        return True, ""
    except Exception as e:
        return False, str(e)


def _copy_go_runtime(emit_dir: Path) -> None:
    """Copy Go runtime files to emit directory (flat, all in same package dir)."""
    go_runtime = ROOT / "src" / "runtime" / "go"
    if not go_runtime.exists():
        return
    for f in sorted(go_runtime.rglob("*.go")):
        dest = emit_dir / f.name
        shutil.copy2(f, dest)


def _copy_scala_runtime(emit_dir: Path) -> None:
    scala_runtime = ROOT / "src" / "runtime" / "scala"
    if not scala_runtime.exists():
        return
    for f in sorted(scala_runtime.rglob("*.scala")):
        dest = emit_dir / f.name
        shutil.copy2(f, dest)


def _copy_kotlin_runtime(emit_dir: Path) -> None:
    kotlin_runtime = ROOT / "src" / "runtime" / "kotlin"
    if not kotlin_runtime.exists():
        return
    for f in sorted(kotlin_runtime.rglob("*.kt")):
        dest = emit_dir / f.name
        shutil.copy2(f, dest)


def _dart_rel_output_path(module_id: str) -> Path:
    rel_module = module_id
    if rel_module.startswith("pytra."):
        rel_module = rel_module[len("pytra."):]
    return Path(rel_module.replace(".", "/") + ".dart")


def _inject_dart_emit_context(
    east_doc: dict[str, object],
    module_id: str,
    *,
    is_entry: bool,
) -> None:
    meta = east_doc.get("meta")
    if not isinstance(meta, dict):
        meta = {}
        east_doc["meta"] = meta
    rel_path = _dart_rel_output_path(module_id)
    depth = len(rel_path.parts) - 1
    root_rel_prefix = "../" * depth if depth > 0 else "./"
    meta["emit_context"] = {
        "module_id": module_id,
        "root_rel_prefix": root_rel_prefix,
        "is_entry": is_entry,
    }


def _copy_dart_runtime(emit_dir: Path) -> None:
    dart_runtime = ROOT / "src" / "runtime" / "dart"
    if not dart_runtime.exists():
        return
    for runtime_file in sorted(dart_runtime.rglob("*.dart")):
        rel = runtime_file.relative_to(dart_runtime)
        dest = emit_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(runtime_file, dest)


def _copy_rs_runtime(emit_dir: Path) -> None:
    """Copy Rust runtime files to emit directory (flat)."""
    rs_runtime = ROOT / "src" / "runtime" / "rs"
    for bucket in ("built_in", "std"):
        bucket_dir = rs_runtime / bucket
        if bucket_dir.exists():
            for rs_file in bucket_dir.glob("*.rs"):
                shutil.copy2(rs_file, emit_dir / rs_file.name)


def _copy_java_runtime(emit_dir: Path) -> None:
    """Copy Java runtime files to emit directory (flat)."""
    java_runtime = ROOT / "src" / "runtime" / "java"
    for bucket in ("built_in", "std"):
        bucket_dir = java_runtime / bucket
        if bucket_dir.exists():
            for java_file in bucket_dir.glob("*.java"):
                shutil.copy2(java_file, emit_dir / java_file.name)


def _copy_cs_runtime(emit_dir: Path) -> None:
    """Copy the native C# runtime files used by the toolchain2 CLI path."""
    cs_runtime = ROOT / "src" / "runtime" / "cs"
    if not cs_runtime.exists():
        return
    built_in = cs_runtime / "built_in" / "py_runtime.cs"
    if built_in.exists():
        dest = emit_dir / "built_in" / "py_runtime.cs"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(built_in, dest)
    std_dir = cs_runtime / "std"
    if std_dir.exists():
        for cs_file in sorted(std_dir.glob("*.cs")):
            dest = emit_dir / "std" / cs_file.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(cs_file, dest)


def _run_cs_via_dotnet(
    emit_dir: Path,
    case_path: Path,
    *,
    work_dir: Path,
    env: dict[str, str],
    timeout_sec: int,
) -> subprocess.CompletedProcess[str]:
    project_path = emit_dir / "PytraParity.csproj"
    if not project_path.exists():
        project_path.write_text(
            "\n".join([
                "<Project Sdk=\"Microsoft.NET.Sdk\">",
                "  <PropertyGroup>",
                "    <OutputType>Exe</OutputType>",
                "    <TargetFramework>net8.0</TargetFramework>",
                "    <ImplicitUsings>disable</ImplicitUsings>",
                "    <Nullable>disable</Nullable>",
                "    <EnableDefaultCompileItems>true</EnableDefaultCompileItems>",
                "    <LangVersion>latest</LangVersion>",
                "  </PropertyGroup>",
                "</Project>",
                "",
            ]),
            encoding="utf-8",
        )
    build = run_shell(
        "dotnet build "
        + shlex.quote(str(project_path))
        + " -nologo -v:q",
        cwd=work_dir,
        env=env,
        timeout_sec=timeout_sec,
    )
    if build.returncode != 0:
        return build
    dll_path = emit_dir / "bin" / "Debug" / "net8.0" / "PytraParity.dll"
    if not dll_path.exists():
        return subprocess.CompletedProcess("", 1, "", f"dotnet output not found: {dll_path}")
    return run_shell(
        "dotnet " + shlex.quote(str(dll_path)),
        cwd=work_dir,
        env=env,
        timeout_sec=timeout_sec,
    )


def _copy_ts_runtime(emit_dir: Path) -> None:
    """Copy TypeScript built-in runtime file to emit directory."""
    runtime_src = ROOT / "src" / "runtime" / "ts" / "built_in" / "py_runtime.ts"
    if runtime_src.exists():
        shutil.copy2(runtime_src, emit_dir / "pytra_built_in_py_runtime.ts")


def _copy_js_runtime(emit_dir: Path) -> None:
    """Copy JavaScript runtime files to emit directory.

    built_in/py_runtime.js  → pytra_built_in_py_runtime.js  (name emitter expects)
    std/*.js                → <same name>.js
    """
    js_runtime = ROOT / "src" / "runtime" / "js"
    built_in_dir = js_runtime / "built_in"
    if built_in_dir.exists():
        src = built_in_dir / "py_runtime.js"
        if src.exists():
            shutil.copy2(src, emit_dir / "pytra_built_in_py_runtime.js")
    std_dir = js_runtime / "std"
    if std_dir.exists():
        for js_file in std_dir.glob("*.js"):
            shutil.copy2(js_file, emit_dir / js_file.name)


def _copy_ruby_runtime(emit_dir: Path) -> None:
    """Copy Ruby runtime files to emit directory."""
    ruby_runtime = ROOT / "src" / "runtime" / "ruby"
    for bucket in ("built_in", "std"):
        bucket_dir = ruby_runtime / bucket
        if bucket_dir.exists():
            dest_bucket = emit_dir / bucket
            dest_bucket.mkdir(parents=True, exist_ok=True)
            for rb_file in bucket_dir.glob("*.rb"):
                shutil.copy2(rb_file, dest_bucket / rb_file.name)


def _copy_lua_runtime(emit_dir: Path) -> None:
    """Copy Lua runtime files to emit directory."""
    lua_runtime = ROOT / "src" / "runtime" / "lua"
    for bucket in ("built_in", "std"):
        bucket_dir = lua_runtime / bucket
        if bucket_dir.exists():
            dest_bucket = emit_dir / bucket
            dest_bucket.mkdir(parents=True, exist_ok=True)
            for lua_file in bucket_dir.glob("*.lua"):
                shutil.copy2(lua_file, dest_bucket / lua_file.name)


def _copy_php_runtime(emit_dir: Path) -> None:
    """Copy PHP runtime files to emit directory."""
    php_runtime = ROOT / "src" / "runtime" / "php"
    for bucket in ("built_in", "std"):
        bucket_dir = php_runtime / bucket
        if bucket_dir.exists():
            dest_bucket = emit_dir / bucket
            dest_bucket.mkdir(parents=True, exist_ok=True)
            for php_file in bucket_dir.glob("*.php"):
                shutil.copy2(php_file, dest_bucket / php_file.name)


def _emit_helper_cpp(m, emit_dir: Path) -> None:
    """Emit a C++ helper module (header + source)."""
    rel = runtime_rel_tail_for_module(m.module_id)
    if rel == "":
        rel = "/".join(m.module_id.split("."))
    cpp_path = emit_dir / (rel + ".cpp")
    h_path = emit_dir / (rel + ".h")
    cpp_path.parent.mkdir(parents=True, exist_ok=True)
    h_path.parent.mkdir(parents=True, exist_ok=True)
    cpp_path.write_text(emit_cpp_module(m.east_doc), encoding="utf-8")
    h_path.write_text(
        build_cpp_header_from_east3(m.module_id, m.east_doc, rel_header_path=rel + ".h"),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Run target (compile + execute)
# ---------------------------------------------------------------------------


def _run_target(
    target: str,
    output_dir: Path,
    case_path: Path,
    *,
    work_dir: Path,
    env: dict[str, str] | None = None,
    timeout_sec: int = 120,
) -> subprocess.CompletedProcess[str]:
    """Compile and run the emitted code.

    *work_dir* is the parity check working directory, used as cwd for all
    target executions so that relative output paths match the Python run.
    """
    emit_dir = output_dir / "emit"

    if target == "cpp":
        return _run_cpp_emit_dir(emit_dir, cwd=work_dir, env=env, timeout_sec=timeout_sec)

    if target == "go":
        go_files = sorted(str(p) for p in emit_dir.rglob("*.go"))
        if len(go_files) == 0:
            return subprocess.CompletedProcess("", 1, "", "no .go files found")
        cmd = "go run " + " ".join(shlex.quote(f) for f in go_files)
        return run_shell(cmd, cwd=work_dir, env=env, timeout_sec=timeout_sec)

    if target == "rs":
        stem = case_path.stem
        entry_rs = emit_dir / (stem + ".rs")
        if not entry_rs.exists():
            return subprocess.CompletedProcess("", 1, "", f"entry file not found: {entry_rs}")
        exe_path = emit_dir / (stem + "_rs.out")
        rs_env = dict(env or {})
        rs_env["RUSTUP_HOME"] = "/usr/local/rustup"
        rs_env["CARGO_HOME"] = "/usr/local/cargo"
        current_path = rs_env.get("PATH") or os.environ.get("PATH", "")
        rs_env["PATH"] = "/usr/local/cargo/bin" + (os.pathsep + current_path if current_path != "" else "")
        build = run_shell(
            f"/usr/local/cargo/bin/rustc -O {shlex.quote(str(entry_rs))} -o {shlex.quote(str(exe_path))}",
            cwd=work_dir, env=rs_env, timeout_sec=timeout_sec,
        )
        if build.returncode != 0:
            return build
        return run_shell(shlex.quote(str(exe_path)), cwd=work_dir, env=rs_env, timeout_sec=timeout_sec)

    if target == "java":
        stem = case_path.stem
        entry_class = java_module_class_name(stem)
        entry_java = emit_dir / (entry_class + ".java")
        if not entry_java.exists():
            return subprocess.CompletedProcess("", 1, "", f"entry file not found: {entry_java}")
        java_files = sorted(str(p) for p in emit_dir.rglob("*.java"))
        if len(java_files) == 0:
            return subprocess.CompletedProcess("", 1, "", "no .java files found")
        build = run_shell(
            "javac -sourcepath "
            + shlex.quote(str(emit_dir))
            + " "
            + " ".join(shlex.quote(f) for f in java_files),
            cwd=work_dir,
            env=env,
            timeout_sec=timeout_sec,
        )
        if build.returncode != 0:
            return build
        return run_shell(
            "java -cp " + shlex.quote(str(emit_dir)) + " " + shlex.quote(entry_class),
            cwd=work_dir,
            env=env,
            timeout_sec=timeout_sec,
        )

    if target == "scala":
        scala_files = sorted(str(p) for p in emit_dir.rglob("*.scala"))
        if len(scala_files) == 0:
            return subprocess.CompletedProcess("", 1, "", "no .scala files found")
        cmd = "scala-cli run --jvm 17 " + " ".join(shlex.quote(f) for f in scala_files)
        return run_shell(cmd, cwd=work_dir, env=env, timeout_sec=timeout_sec)

    if target == "kotlin":
        kt_files = sorted(str(p) for p in emit_dir.rglob("*.kt"))
        if len(kt_files) == 0:
            return subprocess.CompletedProcess("", 1, "", "no .kt files found")
        jar_path = emit_dir / (case_path.stem + "_kotlin.jar")
        build = run_shell(
            "kotlinc "
            + " ".join(shlex.quote(f) for f in kt_files)
            + " -include-runtime -d "
            + shlex.quote(str(jar_path)),
            cwd=work_dir,
            env=env,
            timeout_sec=timeout_sec,
        )
        if build.returncode != 0:
            return build
        return run_shell(
            "java -jar " + shlex.quote(str(jar_path)),
            cwd=work_dir,
            env=env,
            timeout_sec=timeout_sec,
        )

    if target == "cs":
        cs_files = sorted(str(p) for p in emit_dir.rglob("*.cs"))
        if len(cs_files) == 0:
            return subprocess.CompletedProcess("", 1, "", "no .cs files found")
        if shutil.which("mcs") is None or shutil.which("mono") is None:
            return _run_cs_via_dotnet(
                emit_dir,
                case_path,
                work_dir=work_dir,
                env=env,
                timeout_sec=timeout_sec,
            )
        exe_path = emit_dir / (case_path.stem + "_cs.exe")
        cmd = (
            "mcs -warn:0 "
            + shlex.quote(f"-out:{exe_path}")
            + " "
            + " ".join(shlex.quote(f) for f in cs_files)
        )
        build = run_shell(cmd, cwd=work_dir, env=env, timeout_sec=timeout_sec)
        if build.returncode != 0:
            return build
        return run_shell(
            "mono " + shlex.quote(str(exe_path)),
            cwd=work_dir,
            env=env,
            timeout_sec=timeout_sec,
        )

    if target == "ts":
        stem = case_path.stem
        entry_ts = emit_dir / (stem + ".ts")
        if not entry_ts.exists():
            return subprocess.CompletedProcess("", 1, "", f"entry file not found: {entry_ts}")
        # Compile all .ts files → .js with tsc, then run entry with node
        ts_files = sorted(str(p) for p in emit_dir.rglob("*.ts"))
        if len(ts_files) == 0:
            return subprocess.CompletedProcess("", 1, "", "no .ts files found")
        compile_cmd = (
            "tsc --target es2022 --module nodenext --moduleResolution nodenext --esModuleInterop"
            + " --outDir " + shlex.quote(str(emit_dir))
            + " " + " ".join(shlex.quote(f) for f in ts_files)
        )
        compile_result = run_shell(compile_cmd, cwd=work_dir, env=env, timeout_sec=timeout_sec)
        if compile_result.returncode != 0:
            return compile_result
        # Find entry .js — try exact stem match, then fall back to any .js with main guard
        entry_js = emit_dir / (stem + ".js")
        if not entry_js.exists():
            # Entry module may have a different name after linking
            candidates = [p for p in emit_dir.glob("*.js") if not p.name.startswith("pytra_")]
            if len(candidates) == 1:
                entry_js = candidates[0]
            elif len(candidates) == 0:
                return subprocess.CompletedProcess("", 1, "", "no entry .js file found after tsc")
            else:
                # Pick the one that contains a main guard
                for c in candidates:
                    if "// main" in c.read_text(encoding="utf-8"):
                        entry_js = c
                        break
                else:
                    entry_js = candidates[0]
        return run_shell(
            f"node {shlex.quote(str(entry_js))}",
            cwd=work_dir, env=env, timeout_sec=timeout_sec,
        )

    if target == "js":
        stem = case_path.stem
        entry_js = emit_dir / (stem + ".js")
        if not entry_js.exists():
            return subprocess.CompletedProcess("", 1, "", f"entry file not found: {entry_js}")
        return run_shell(
            f"node {shlex.quote(str(entry_js))}",
            cwd=work_dir, env=env, timeout_sec=timeout_sec,
        )

    if target == "ruby":
        stem = case_path.stem
        entry_rb = emit_dir / (stem + ".rb")
        if not entry_rb.exists():
            return subprocess.CompletedProcess("", 1, "", f"entry file not found: {entry_rb}")
        return run_shell(
            f"ruby {shlex.quote(str(entry_rb))}",
            cwd=work_dir, env=env, timeout_sec=timeout_sec,
        )

    if target == "lua":
        stem = case_path.stem
        entry_lua = emit_dir / (stem + ".lua")
        if not entry_lua.exists():
            return subprocess.CompletedProcess("", 1, "", f"entry file not found: {entry_lua}")
        return run_shell(
            f"lua {shlex.quote(str(entry_lua))}",
            cwd=work_dir, env=env, timeout_sec=timeout_sec,
        )

    if target == "php":
        stem = case_path.stem
        entry_php = emit_dir / (stem + ".php")
        if not entry_php.exists():
            return subprocess.CompletedProcess("", 1, "", f"entry file not found: {entry_php}")
        return run_shell(
            f"php {shlex.quote(str(entry_php))}",
            cwd=work_dir, env=env, timeout_sec=timeout_sec,
        )

    if target == "dart":
        stem = case_path.stem
        entry_dart = emit_dir / (stem + ".dart")
        if not entry_dart.exists():
            return subprocess.CompletedProcess("", 1, "", f"entry file not found: {entry_dart}")
        return run_shell(
            f"dart run {shlex.quote(str(entry_dart))}",
            cwd=work_dir, env=env, timeout_sec=timeout_sec,
        )

    return subprocess.CompletedProcess("", 1, "", f"unsupported target: {target}")


# ---------------------------------------------------------------------------
# Python results persistence (separate file from target results)
# ---------------------------------------------------------------------------

def _save_python_results(records: list[CheckRecord], case_root: str) -> None:
    """Save Python execution timing to .parity-results/python_<case_root>.json."""
    import datetime
    parity_dir = ROOT / ".parity-results"
    parity_dir.mkdir(parents=True, exist_ok=True)
    out_path = parity_dir / f"python_{case_root}.json"

    existing: dict[str, object] = {}
    if out_path.exists():
        try:
            loaded = json.loads(out_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict) and "results" in loaded:
                existing = loaded["results"]  # type: ignore[assignment]
        except Exception:
            pass

    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    results: dict[str, object] = dict(existing)
    for rec in records:
        if rec.target != "python" or rec.elapsed_sec is None:
            continue
        entry: dict[str, object] = {"category": rec.category, "timestamp": now,
                                     "elapsed_sec": round(rec.elapsed_sec, 3)}
        results[rec.case_stem] = entry

    doc = {"target": "python", "case_root": case_root, "results": results}
    out_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Sample auto-copy: copy PASS-verified emit files to sample-preview/<lang>/
# ---------------------------------------------------------------------------

# target_name → (sample_dir_name, file_extension)
_SAMPLE_TARGET_MAP: dict[str, tuple[str, str]] = {
    "cpp":    ("cpp",        ".cpp"),
    "go":     ("go",         ".go"),
    "rs":     ("rs",         ".rs"),
    "ts":     ("ts",         ".ts"),
    "js":     ("js",         ".js"),
    "cs":     ("cs",         ".cs"),
    "ruby":   ("ruby",       ".rb"),
    "lua":    ("lua",        ".lua"),
    "php":    ("php",        ".php"),
    "java":   ("java",       ".java"),
    "swift":  ("swift",      ".swift"),
    "kotlin": ("kotlin",     ".kt"),
    "scala":  ("scala",      ".scala"),
    "nim":    ("nim",        ".nim"),
    "dart":   ("dart",       ".dart"),
    "ps1":    ("powershell", ".ps1"),
    "zig":    ("zig",        ".zig"),
    "julia":  ("julia",      ".jl"),
}


def _copy_sample_emit(target: str, emit_dir: Path, case_stem: str) -> None:
    """Copy entry file from emit_dir to sample-preview/<lang>/ after parity PASS."""
    if target not in _SAMPLE_TARGET_MAP:
        return
    sample_dir_name, ext = _SAMPLE_TARGET_MAP[target]
    src = emit_dir / (case_stem + ext)
    if not src.exists():
        return
    dest_dir = ROOT / "sample-preview" / sample_dir_name
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest_dir / src.name)


def _acquire_gen_lock(max_age: float = 120.0) -> bool:
    """Acquire .parity-results/.gen.lock for exclusive post-run generation.

    Returns True if the lock was acquired, False if already held by another process.
    Removes stale locks older than max_age seconds.
    [P0-PROGRESS-SUMMARY-S1]
    """
    lock_path = ROOT / ".parity-results" / ".gen.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    if lock_path.exists():
        try:
            age = time.time() - lock_path.stat().st_mtime
            if age > max_age:
                lock_path.unlink(missing_ok=True)
            else:
                return False
        except Exception:
            pass
    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return True
    except (FileExistsError, OSError):
        return False


def _release_gen_lock() -> None:
    """Release .parity-results/.gen.lock."""
    try:
        (ROOT / ".parity-results" / ".gen.lock").unlink(missing_ok=True)
    except Exception:
        pass




def _maybe_regenerate_benchmark() -> None:
    """Auto-run gen_sample_benchmark.py if >3 minutes since last generation."""
    marker = ROOT / "sample-preview" / "README-ja.md"
    if marker.exists() and (time.time() - marker.stat().st_mtime) < 180:
        return
    gen_script = ROOT / "tools" / "gen" / "gen_sample_benchmark.py"
    if not gen_script.exists():
        return
    # Only run if benchmark data exists
    if not (ROOT / ".parity-results" / "python_sample.json").exists():
        return
    try:
        subprocess.run(
            ["python3", str(gen_script)],
            cwd=str(ROOT),
            timeout=30,
            capture_output=True,
        )
    except Exception:
        pass


def _maybe_run_emitter_lint() -> None:
    """Auto-run check_emitter_hardcode_lint.py if >30 minutes since last run.

    Updates emitter-hardcode-lint.md and .parity-results/emitter_lint.json.
    [P0-PROGRESS-SUMMARY-S4]
    """
    marker = ROOT / "docs" / "ja" / "progress-preview" / "emitter-hardcode-lint.md"
    if marker.exists() and (time.time() - marker.stat().st_mtime) < 1800:
        return
    lint_script = ROOT / "tools" / "check" / "check_emitter_hardcode_lint.py"
    if not lint_script.exists():
        return
    try:
        subprocess.run(
            ["python3", str(lint_script)],
            cwd=str(ROOT),
            timeout=60,
            capture_output=True,
        )
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Main check logic
# ---------------------------------------------------------------------------


def check_case(
    case_stem: str,
    enabled_targets: set[str],
    *,
    case_root: str,
    opt_level: int = 1,
    cmd_timeout_sec: int = 120,
    negative_index_mode: str = "",
    bounds_check_mode: str = "",
    records: list[CheckRecord] | None = None,
) -> int:
    do_bench = case_root == "sample"

    def _record(target: str, category: str, detail: str, elapsed_sec: float | None = None) -> None:
        if records is not None:
            records.append(CheckRecord(
                case_stem=case_stem, target=target,
                category=category, detail=detail,
                elapsed_sec=elapsed_sec,
            ))

    case_path = find_case_path(case_stem, case_root)
    if case_path is None:
        print(f"[ERROR] missing case: {case_stem}")
        _record("-", "case_missing", "missing case")
        return 1

    work = ROOT / "work" / "transpile" / "parity-fast" / (case_stem + "_" + str(os.getpid()))
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True, exist_ok=True)

    try:
        # Run Python reference
        (work / "src").symlink_to(ROOT / "src", target_is_directory=True)
        (work / "test").symlink_to(ROOT / "test", target_is_directory=True)
        (work / "out").mkdir(parents=True, exist_ok=True)
        if case_root == "sample":
            (work / "sample").mkdir(parents=True, exist_ok=True)
            (work / "sample" / "py").symlink_to(ROOT / "sample" / "py", target_is_directory=True)
            (work / "sample" / "out").mkdir(parents=True, exist_ok=True)

        _purge_case_artifacts(work, case_stem)
        py_cmd = f"python {shlex.quote(case_path.as_posix())}"
        py_env = {"PYTHONPATH": "src"}
        py_t0 = time.monotonic()
        py = run_shell(py_cmd, cwd=work, env=py_env, timeout_sec=cmd_timeout_sec)
        py_elapsed_sec: float | None = round(time.monotonic() - py_t0, 3) if do_bench else None
        if py.returncode != 0:
            print(f"[ERROR] python:{case_stem} failed")
            _record("python", "python_failed", py.stderr.strip())
            return 1

        if do_bench:
            _record("python", "ok", "", elapsed_sec=py_elapsed_sec)

        expected = _normalize_output_for_compare(py.stdout)
        expected_artifact_path: Path | None = None
        expected_artifact_size: int | None = None
        expected_artifact_crc32: int | None = None
        expected_out_txt = _parse_output_path(py.stdout)
        if expected_out_txt != "":
            expected_artifact_path = _resolve_output_path(work, expected_out_txt)
            if not expected_artifact_path.exists():
                _record("python", "python_artifact_missing", str(expected_artifact_path))
                return 1
            expected_artifact_size = _file_size_normalized(expected_artifact_path)
            expected_artifact_crc32 = _file_crc32(expected_artifact_path)

        mismatches: list[str] = []
        for target_name in sorted(enabled_targets):
            if case_stem in _LANG_UNSUPPORTED_FIXTURES.get(target_name, set()):
                print(f"[SKIP] {case_stem}:{target_name} (unsupported feature)")
                _record(target_name, "unsupported_feature", "unsupported feature")
                continue

            profile = get_target_profile(target_name)
            target_obj_needs = profile.runner_needs
            from runtime_parity_check import Target
            dummy_target = Target(name=target_name, transpile_cmd="", run_cmd="", needs=target_obj_needs)
            if not can_run(dummy_target):
                print(f"[SKIP] {case_stem}:{target_name} (missing toolchain)")
                _record(target_name, "toolchain_missing", "missing toolchain")
                continue

            target_env = _tool_env_for_target(dummy_target)

            # In-memory transpile
            out_dir = work / "transpile" / target_name
            ok, err_msg = _transpile_in_memory(
                case_path,
                target_name,
                out_dir,
                opt_level,
                negative_index_mode,
                bounds_check_mode,
            )
            if not ok:
                mismatches.append(f"{case_stem}:{target_name}: transpile failed: {err_msg}")
                _record(target_name, "transpile_failed", err_msg)
                continue

            # Compile + run (subprocess)
            _purge_case_artifacts(work, case_stem)
            _safe_unlink(expected_artifact_path)
            rr_t0 = time.monotonic()
            rr = _run_target(target_name, out_dir, case_path, work_dir=work, env=target_env, timeout_sec=cmd_timeout_sec)
            rr_elapsed: float | None = round(time.monotonic() - rr_t0, 3) if do_bench else None
            if rr.returncode != 0:
                msg = rr.stderr.strip()
                mismatches.append(f"{case_stem}:{target_name}: run failed: {msg}")
                _record(target_name, "run_failed", msg)
                continue

            raw_actual = _target_output_text(target_name, rr)
            actual = _normalize_output_for_compare(raw_actual, target_name)
            if actual != expected:
                mismatches.append(f"{case_stem}:{target_name}: output mismatch")
                _record(target_name, "output_mismatch", "stdout mismatch")
                continue

            # Record target execution time from the single run above
            target_elapsed_sec: float | None = None
            if do_bench:
                target_elapsed_sec = round(rr_elapsed, 3) if rr_elapsed is not None else None

            # Artifact check
            actual_out_txt = _parse_output_path(raw_actual)
            if expected_artifact_size is None:
                if case_root == "sample":
                    _copy_sample_emit(target_name, out_dir / "emit", case_stem)
                print(f"[OK] {case_stem}:{target_name}")
                _record(target_name, "ok", "", elapsed_sec=target_elapsed_sec)
                continue

            if actual_out_txt == "":
                mismatches.append(f"{case_stem}:{target_name}: artifact presence mismatch")
                _record(target_name, "artifact_presence_mismatch", "missing output line")
                continue

            actual_artifact_path = _resolve_output_path(work, actual_out_txt)
            if not actual_artifact_path.exists():
                mismatches.append(f"{case_stem}:{target_name}: artifact missing")
                _record(target_name, "artifact_missing", str(actual_artifact_path))
                continue

            actual_size = _file_size_normalized(actual_artifact_path)
            if actual_size != expected_artifact_size:
                mismatches.append(f"{case_stem}:{target_name}: artifact size mismatch")
                _record(target_name, "artifact_size_mismatch", "size mismatch")
                continue

            actual_crc = _file_crc32(actual_artifact_path)
            if expected_artifact_crc32 is not None and actual_crc != expected_artifact_crc32:
                mismatches.append(f"{case_stem}:{target_name}: artifact crc32 mismatch")
                _record(target_name, "artifact_crc32_mismatch", "crc32 mismatch")
                continue

            info = f"artifact_size={actual_size} artifact_crc32={_crc32_hex(actual_crc)}"
            if case_root == "sample":
                _copy_sample_emit(target_name, out_dir / "emit", case_stem)
            print(f"[OK] {case_stem}:{target_name} {info}")
            _record(target_name, "ok", info, elapsed_sec=target_elapsed_sec)

    finally:
        if work.exists():
            shutil.rmtree(work, ignore_errors=True)

    if mismatches:
        print(f"\n[FAIL] {case_stem} mismatches", flush=True)
        for m in mismatches:
            print(f"- {m}", flush=True)
        return 1

    print(f"[PASS] {case_stem}", flush=True)
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fast runtime parity check (in-memory pipeline, no CLI subprocess for transpile)"
    )
    parser.add_argument("cases", nargs="*", default=[], help="case stems (without .py)")
    parser.add_argument("--case-root", default="fixture", choices=("fixture", "sample", "stdlib"))
    parser.add_argument("--targets", default="cpp", help="comma separated targets (default: cpp)")
    parser.add_argument("--category", default="", help="fixture subdirectory (e.g. oop, control)")
    parser.add_argument("--opt-level", default=1, type=int, choices=(0, 1, 2))
    parser.add_argument("--negative-index-mode", default="", choices=("", "always", "const_only", "off"))
    parser.add_argument("--bounds-check-mode", default="", choices=("", "always", "debug", "off"))
    parser.add_argument("--cmd-timeout-sec", default=120, type=int)
    parser.add_argument("--summary-json", default="")
    args = parser.parse_args()

    enabled_targets: set[str] = set()
    for raw in args.targets.split(","):
        name = raw.strip()
        if name != "":
            enabled_targets.add(name)
    if len(enabled_targets) == 0:
        print("[ERROR] --targets must include at least one target")
        return 1

    # Resolve case stems (reuse logic from runtime_parity_check)
    from runtime_parity_check import resolve_case_stems
    stems, err = resolve_case_stems(args.cases, args.case_root, category=args.category)
    if err != "":
        print(f"[ERROR] {err}")
        return 2
    if len(stems) == 0:
        print("[ERROR] no cases resolved")
        return 2

    # Pre-load registry once
    t0 = time.monotonic()
    _get_registry()
    t_reg = time.monotonic() - t0
    print(f"[INFO] registry loaded in {t_reg:.2f}s ({len(stems)} cases, targets={args.targets})")

    exit_code = 0
    pass_cases = 0
    fail_cases = 0
    records: list[CheckRecord] = []

    t_start = time.monotonic()
    for stem in stems:
        code = check_case(
            stem,
            enabled_targets,
            case_root=args.case_root,
            opt_level=args.opt_level,
            cmd_timeout_sec=args.cmd_timeout_sec,
            negative_index_mode=args.negative_index_mode,
            bounds_check_mode=args.bounds_check_mode,
            records=records,
        )
        if code != 0:
            exit_code = code
            fail_cases += 1
        else:
            pass_cases += 1
        sys.stdout.flush()
    elapsed = time.monotonic() - t_start

    category_counts: dict[str, int] = {}
    for rec in records:
        category_counts[rec.category] = category_counts.get(rec.category, 0) + 1

    print(
        f"SUMMARY cases={len(stems)} pass={pass_cases} fail={fail_cases} "
        f"targets={','.join(sorted(enabled_targets))} "
        f"opt_level={args.opt_level} "
        f"negative_index_mode={resolve_negative_index_mode(args.negative_index_mode, args.opt_level)} "
        f"bounds_check_mode={resolve_bounds_check_mode(args.bounds_check_mode, args.opt_level)} "
        f"elapsed={elapsed:.1f}s"
    )
    if len(category_counts) > 0:
        print("SUMMARY_CATEGORIES")
        for cat in sorted(category_counts.keys()):
            print(f"- {cat}: {category_counts[cat]}")

    if args.summary_json != "":
        summary = {
            "case_root": args.case_root,
            "opt_level": args.opt_level,
            "negative_index_mode": resolve_negative_index_mode(args.negative_index_mode, args.opt_level),
            "bounds_check_mode": resolve_bounds_check_mode(args.bounds_check_mode, args.opt_level),
            "targets": sorted(enabled_targets),
            "cases": stems,
            "case_total": len(stems),
            "case_pass": pass_cases,
            "case_fail": fail_cases,
            "elapsed_sec": round(elapsed, 2),
            "category_counts": category_counts,
            "records": [
                {"case": r.case_stem, "target": r.target, "category": r.category, "detail": r.detail}
                for r in records
            ],
        }
        out_path = Path(args.summary_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    from runtime_parity_check import _save_parity_results, _maybe_refresh_selfhost_python, _maybe_regenerate_progress  # type: ignore
    _save_parity_results(records, args.case_root, enabled_targets)
    if args.case_root == "sample":
        _save_python_results(records, args.case_root)
    # Acquire exclusive lock before running generation scripts [P0-PROGRESS-SUMMARY-S1]
    if _acquire_gen_lock():
        try:
            _maybe_run_emitter_lint()
            _maybe_refresh_selfhost_python()
            _maybe_regenerate_progress()
            _maybe_regenerate_benchmark()
        finally:
            _release_gen_lock()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
