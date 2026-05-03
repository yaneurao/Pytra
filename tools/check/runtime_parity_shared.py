#!/usr/bin/env python3
"""Runtime parity check across transpiler targets."""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import signal
import shlex
import shutil
import subprocess
import sys
import time

import zlib
from dataclasses import dataclass
from pathlib import Path

if str((Path(__file__).resolve().parents[2] / "src")) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from toolchain.misc.target_profiles import get_target_profile, list_parity_targets

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = ROOT / "test" / "fixture" / "source" / "py"
SAMPLE_ROOT = ROOT / "sample" / "py"
STDLIB_ROOT = ROOT / "test" / "stdlib" / "source" / "py"
ARTIFACT_OPTIONAL_TARGETS: set[str] = set()
_LOCAL_TOOL_FALLBACKS: dict[str, tuple[Path, ...]] = {
    "go": (ROOT / "work" / "tmp" / "go-toolchain" / "bin" / "go",),
    "rustc": (Path("/usr/local/cargo/bin/rustc"),),
    "cargo": (Path("/usr/local/cargo/bin/cargo"),),
    "pwsh": (Path("/tmp/pwsh/pwsh"),),
}

# Backend-declared unsupported fixtures are tracked explicitly.
# FAIL is recorded as FAIL in .parity-results/ and shown in progress matrix.
_LANG_UNSUPPORTED_FIXTURES: dict[str, set[str]] = {}

__all__ = [
    "ROOT",
    "shutil",
    "FIXTURE_ROOT",
    "SAMPLE_ROOT",
    "STDLIB_ROOT",
    "Target",
    "CheckRecord",
    "_LANG_UNSUPPORTED_FIXTURES",
    "_LOCAL_TOOL_FALLBACKS",
    "normalize",
    "run_shell",
    "_tool_env_for_target",
    "can_run",
    "_normalize_output_for_compare",
    "_target_output_text",
    "_parse_output_path",
    "_resolve_output_path",
    "_safe_unlink",
    "_file_crc32",
    "_file_size_normalized",
    "_crc32_hex",
    "_run_cpp_emit_dir",
    "run_emitted_target",
    "build_emitted_target_artifact",
    "_purge_case_artifacts",
    "find_case_path",
    "collect_sample_case_stems",
    "collect_fixture_case_stems",
    "collect_stdlib_case_stems",
    "resolve_case_stems",
    "_save_parity_results",
    "_append_parity_changelog",
    "_maybe_refresh_selfhost_python",
    "_maybe_regenerate_progress",
]


try:
    from toolchain.emit.java.types import java_module_class_name  # type: ignore
except Exception:
    def java_module_class_name(module_id: str) -> str:
        return "".join(ch if ch.isalnum() else "_" for ch in module_id)


@dataclass
class Target:
    name: str
    transpile_cmd: str
    run_cmd: str
    needs: tuple[str, ...]
    ignore_artifacts: bool = False
    output_dir: str = ""


@dataclass
class CheckRecord:
    case_stem: str
    target: str
    category: str
    detail: str
    elapsed_sec: float | None = None


def normalize(text: str) -> str:
    lines = [ln.rstrip() for ln in text.replace("\r\n", "\n").split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def run_shell(
    cmd: str,
    cwd: Path,
    *,
    env: dict[str, str] | None = None,
    timeout_sec: int | None = None,
) -> subprocess.CompletedProcess[str]:
    proc_env = os.environ.copy()
    if env is not None:
        proc_env.update(env)
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=proc_env,
        start_new_session=True,
    )
    try:
        stdout_text, stderr_text = proc.communicate(timeout=timeout_sec)
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=int(proc.returncode or 0),
            stdout=stdout_text,
            stderr=stderr_text,
        )
    except subprocess.TimeoutExpired:
        # Kill the whole process group so compiled runners spawned by the shell
        # cannot continue running in the background.
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        stdout_text, stderr_text = proc.communicate()
        timeout_note = f"[TIMEOUT] exceeded {timeout_sec}s: {cmd}"
        if stderr_text == "":
            stderr_text = timeout_note
        else:
            stderr_text = stderr_text.rstrip() + "\n" + timeout_note
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=124,
            stdout=stdout_text,
            stderr=stderr_text,
        )


def _resolve_tool_path(tool: str) -> str:
    if tool.startswith("/"):
        if Path(tool).is_file():
            return tool
        return ""
    found = shutil.which(tool)
    if found is not None:
        return found
    for candidate in _LOCAL_TOOL_FALLBACKS.get(tool, ()):
        if candidate.is_file():
            return str(candidate)
    return ""


def _tool_env_for_target(target: Target) -> dict[str, str]:
    extra_dirs: list[str] = []
    for tool in target.needs:
        if tool.startswith("/"):
            continue
        if shutil.which(tool) is not None:
            continue
        resolved = _resolve_tool_path(tool)
        if resolved == "":
            continue
        tool_dir = str(Path(resolved).parent)
        if tool_dir not in extra_dirs:
            extra_dirs.append(tool_dir)
    if len(extra_dirs) == 0:
        return {}
    current_path = os.environ.get("PATH", "")
    path_parts = extra_dirs + ([current_path] if current_path != "" else [])
    return {"PATH": os.pathsep.join(path_parts)}


def can_run(target: Target) -> bool:
    if target.name == "cs":
        has_mono = True
        for tool in target.needs:
            if tool in ("mcs", "mono"):
                if _resolve_tool_path(tool) == "":
                    has_mono = False
        if has_mono:
            return True
        return _resolve_tool_path("dotnet") != ""
    for tool in target.needs:
        if _resolve_tool_path(tool) == "":
            return False
    return True


def _normalize_output_for_compare(stdout_text: str, target_name: str = "") -> str:
    lines: list[str] = []
    for line in stdout_text.splitlines():
        low = line.strip().lower()
        if low.startswith("elapsed_sec:") or low.startswith("elapsed:") or low.startswith("time_sec:"):
            continue
        if low.startswith("build:"):
            continue
        if low.startswith("generated:"):
            continue
        if low.startswith("emitted:"):
            continue
        if target_name == "nim" and "warning:" in low:
            continue
        # C++ build via make: filter build log lines
        if target_name == "cpp":
            if low.startswith("make:") or low.startswith("g++") or low.startswith("clang"):
                continue
        lines.append(line)
    return "\n".join(lines)


def _target_output_text(target_name: str, cp: subprocess.CompletedProcess[str]) -> str:
    out = cp.stdout or ""
    if target_name == "nim" and out.strip() == "":
        # nim `c -r` prints program stdout together with compiler diagnostics
        # to stderr; parity compare should consume that stream.
        return cp.stderr or ""
    return out


def _parse_output_path(stdout_text: str) -> str:
    m = re.search(r"^output:\s*(.+)$", stdout_text, flags=re.MULTILINE)
    if m is None:
        return ""
    return m.group(1).strip()


def _resolve_output_path(cwd: Path, output_text: str) -> Path:
    p = Path(output_text)
    if p.is_absolute():
        return p
    return cwd / p


def _safe_unlink(path: Path | None) -> None:
    if path is None:
        return
    if path.exists() and path.is_file():
        path.unlink()


def _is_text_artifact(path: Path) -> bool:
    return path.suffix.lower() in {".txt", ".csv", ".log"}


def _read_artifact_bytes(path: Path) -> bytes:
    """Read artifact bytes, normalizing CRLF to LF for text files."""
    data = path.read_bytes()
    if _is_text_artifact(path):
        data = data.replace(b"\r\n", b"\n")
    return data


def _file_crc32(path: Path) -> int:
    data = _read_artifact_bytes(path)
    return zlib.crc32(data) & 0xFFFFFFFF


def _file_size_normalized(path: Path) -> int:
    return len(_read_artifact_bytes(path))


def _crc32_hex(v: int) -> str:
    return f"0x{(v & 0xFFFFFFFF):08x}"


def _run_cpp_emit_dir(
    emit_dir: Path,
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout_sec: int | None = None,
    exe_name: str = "app.out",
) -> subprocess.CompletedProcess[str]:
    if not emit_dir.exists() or not emit_dir.is_dir():
        return subprocess.CompletedProcess(
            args=str(emit_dir),
            returncode=1,
            stdout="",
            stderr="missing emit dir: " + str(emit_dir),
        )

    cpp_files: list[str] = []
    for path in sorted(emit_dir.rglob("*.cpp")):
        cpp_files.append(str(path))
    if len(cpp_files) == 0:
        return subprocess.CompletedProcess(
            args=str(emit_dir),
            returncode=1,
            stdout="",
            stderr="no .cpp files found in " + str(emit_dir),
        )

    src_dir = ROOT / "src"
    runtime_root = src_dir / "runtime" / "cpp"
    native_sources: list[str] = [str(runtime_root / "core" / "io.cpp")]
    for bucket in ("std", "utils"):
        native_dir = runtime_root / bucket
        if not native_dir.exists():
            continue
        for cpp_path in sorted(native_dir.glob("*.cpp"), key=lambda p: str(p)):
            generated_hdr = emit_dir / bucket / cpp_path.with_suffix(".h").name
            if generated_hdr.exists():
                native_sources.append(str(cpp_path))

    exe_path = emit_dir / exe_name
    compile_cmd = [
        "g++",
        "-std=c++20",
        "-O2",
        "-I", str(emit_dir),
        "-I", str(src_dir),
        "-I", str(runtime_root),
        "-o", str(exe_path),
    ] + cpp_files + native_sources
    compile_cp = run_shell(
        " ".join(shlex.quote(part) for part in compile_cmd),
        cwd=cwd,
        env=env,
        timeout_sec=timeout_sec,
    )
    if compile_cp.returncode != 0:
        return compile_cp

    return run_shell(
        shlex.quote(str(exe_path)),
        cwd=cwd,
        env=env,
        timeout_sec=timeout_sec,
    )


def _resolve_julia_runtime_bin() -> str:
    env_bin = os.environ.get("PYTRA_JULIA_BIN", "").strip()
    if env_bin != "":
        return env_bin
    direct_candidates = [
        Path("/home/node/.julia/juliaup/julia-1.12.5+0.x64.linux.gnu/bin/julia"),
        Path.home() / ".julia" / "juliaup" / "julia-1.12.5+0.x64.linux.gnu" / "bin" / "julia",
        Path("/usr/local/bin/julia"),
    ]
    for candidate in direct_candidates:
        if candidate.exists() and candidate.is_file():
            return str(candidate)
    found = shutil.which("julia")
    return found or "julia"


def _run_cs_via_dotnet(
    emit_dir: Path,
    *,
    work_dir: Path,
    env: dict[str, str] | None,
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
        "dotnet build " + shlex.quote(str(project_path)) + " -nologo -v:q",
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


def run_emitted_target(
    target: str,
    emit_dir: Path,
    case_path: Path,
    *,
    work_dir: Path,
    env: dict[str, str] | None = None,
    timeout_sec: int = 120,
) -> subprocess.CompletedProcess[str]:
    """Compile and run already-emitted target files."""
    if target == "powershell":
        target = "ps1"

    if target == "cpp":
        return _run_cpp_emit_dir(emit_dir, cwd=work_dir, env=env, timeout_sec=timeout_sec)

    if target == "go":
        go_files = sorted(str(p) for p in emit_dir.rglob("*.go"))
        if len(go_files) == 0:
            return subprocess.CompletedProcess("", 1, "", "no .go files found")
        return run_shell("go run " + " ".join(shlex.quote(f) for f in go_files), cwd=work_dir, env=env, timeout_sec=timeout_sec)

    if target == "rs":
        entry_rs = emit_dir / (case_path.stem + ".rs")
        if not entry_rs.exists():
            return subprocess.CompletedProcess("", 1, "", f"entry file not found: {entry_rs}")
        exe_path = emit_dir / (case_path.stem + "_rs.out")
        rs_env = dict(env or {})
        rs_env["RUSTUP_HOME"] = "/usr/local/rustup"
        rs_env["CARGO_HOME"] = "/usr/local/cargo"
        current_path = rs_env.get("PATH") or os.environ.get("PATH", "")
        rs_env["PATH"] = "/usr/local/cargo/bin" + (os.pathsep + current_path if current_path != "" else "")
        build = run_shell(
            f"/usr/local/cargo/bin/rustc -O {shlex.quote(str(entry_rs))} -o {shlex.quote(str(exe_path))}",
            cwd=work_dir,
            env=rs_env,
            timeout_sec=timeout_sec,
        )
        if build.returncode != 0:
            return build
        return run_shell(shlex.quote(str(exe_path)), cwd=work_dir, env=rs_env, timeout_sec=timeout_sec)

    if target == "java":
        entry_class = java_module_class_name(case_path.stem)
        entry_java = emit_dir / (entry_class + ".java")
        if not entry_java.exists():
            return subprocess.CompletedProcess("", 1, "", f"entry file not found: {entry_java}")
        java_files = sorted(str(p) for p in emit_dir.rglob("*.java"))
        if len(java_files) == 0:
            return subprocess.CompletedProcess("", 1, "", "no .java files found")
        build = run_shell(
            "javac -sourcepath " + shlex.quote(str(emit_dir)) + " " + " ".join(shlex.quote(f) for f in java_files),
            cwd=work_dir,
            env=env,
            timeout_sec=timeout_sec,
        )
        if build.returncode != 0:
            return build
        return run_shell("java -cp " + shlex.quote(str(emit_dir)) + " " + shlex.quote(entry_class), cwd=work_dir, env=env, timeout_sec=timeout_sec)

    if target == "scala":
        scala_files = sorted(str(p) for p in emit_dir.rglob("*.scala"))
        if len(scala_files) == 0:
            return subprocess.CompletedProcess("", 1, "", "no .scala files found")
        return run_shell("scala-cli run --jvm 17 " + " ".join(shlex.quote(f) for f in scala_files), cwd=work_dir, env=env, timeout_sec=timeout_sec)

    if target == "kotlin":
        kt_files = sorted(str(p) for p in emit_dir.rglob("*.kt"))
        if len(kt_files) == 0:
            return subprocess.CompletedProcess("", 1, "", "no .kt files found")
        jar_path = work_dir / (case_path.stem + "_kotlin_run.jar")
        _safe_unlink(jar_path)
        build = run_shell(
            "kotlinc " + " ".join(shlex.quote(f) for f in kt_files) + " -include-runtime -d " + shlex.quote(str(jar_path)),
            cwd=work_dir,
            env=env,
            timeout_sec=timeout_sec,
        )
        if build.returncode != 0:
            return build
        main_class = case_path.stem
        entry_file = emit_dir / (case_path.stem + ".kt")
        if entry_file.exists():
            for raw_line in entry_file.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if line.startswith("object "):
                    object_name = line[len("object "):].split("{", 1)[0].strip()
                    if object_name != "":
                        main_class = object_name
                    break
        return run_shell("java -cp " + shlex.quote(str(jar_path)) + " " + shlex.quote(main_class), cwd=work_dir, env=env, timeout_sec=timeout_sec)

    if target == "cs":
        cs_files = sorted(str(p) for p in emit_dir.rglob("*.cs"))
        if len(cs_files) == 0:
            return subprocess.CompletedProcess("", 1, "", "no .cs files found")
        if shutil.which("mcs") is None or shutil.which("mono") is None:
            return _run_cs_via_dotnet(emit_dir, work_dir=work_dir, env=env, timeout_sec=timeout_sec)
        exe_path = emit_dir / (case_path.stem + "_cs.exe")
        build = run_shell(
            "mcs -warn:0 " + shlex.quote(f"-out:{exe_path}") + " " + " ".join(shlex.quote(f) for f in cs_files),
            cwd=work_dir,
            env=env,
            timeout_sec=timeout_sec,
        )
        if build.returncode != 0:
            return build
        return run_shell("mono " + shlex.quote(str(exe_path)), cwd=work_dir, env=env, timeout_sec=timeout_sec)

    if target == "swift":
        swift_files = sorted(str(p) for p in emit_dir.rglob("*.swift"))
        if len(swift_files) == 0:
            return subprocess.CompletedProcess("", 1, "", "no .swift files found")
        exe_path = emit_dir / (case_path.stem + "_swift.out")
        build = run_shell(
            "swiftc -O " + " ".join(shlex.quote(f) for f in swift_files) + " -o " + shlex.quote(str(exe_path)),
            cwd=work_dir,
            env=env,
            timeout_sec=timeout_sec,
        )
        if build.returncode != 0:
            return build
        return run_shell(shlex.quote(str(exe_path)), cwd=work_dir, env=env, timeout_sec=timeout_sec)

    if target == "ts":
        entry_ts = emit_dir / (case_path.stem + ".ts")
        if not entry_ts.exists():
            return subprocess.CompletedProcess("", 1, "", f"entry file not found: {entry_ts}")
        ts_files = sorted(str(p) for p in emit_dir.rglob("*.ts"))
        if len(ts_files) == 0:
            return subprocess.CompletedProcess("", 1, "", "no .ts files found")
        compile_result = run_shell(
            "tsc --target es2022 --module nodenext --moduleResolution nodenext --esModuleInterop"
            + " --outDir " + shlex.quote(str(emit_dir))
            + " " + " ".join(shlex.quote(f) for f in ts_files),
            cwd=work_dir,
            env=env,
            timeout_sec=timeout_sec,
        )
        if compile_result.returncode != 0:
            return compile_result
        entry_js = emit_dir / (case_path.stem + ".js")
        if not entry_js.exists():
            candidates = [p for p in emit_dir.glob("*.js") if not p.name.startswith("pytra_")]
            if len(candidates) == 1:
                entry_js = candidates[0]
            elif len(candidates) == 0:
                return subprocess.CompletedProcess("", 1, "", "no entry .js file found after tsc")
            else:
                for candidate in candidates:
                    if "// main" in candidate.read_text(encoding="utf-8"):
                        entry_js = candidate
                        break
                else:
                    entry_js = candidates[0]
        return run_shell(f"node {shlex.quote(str(entry_js))}", cwd=work_dir, env=env, timeout_sec=timeout_sec)

    ext_by_target = {
        "js": ".js",
        "ruby": ".rb",
        "lua": ".lua",
        "php": ".php",
        "julia": ".jl",
        "dart": ".dart",
        "ps1": ".ps1",
        "zig": ".zig",
    }
    if target in ext_by_target:
        entry = emit_dir / (case_path.stem + ext_by_target[target])
        if not entry.exists():
            return subprocess.CompletedProcess("", 1, "", f"entry file not found: {entry}")
        if target == "js":
            return run_shell(f"node {shlex.quote(str(entry))}", cwd=work_dir, env=env, timeout_sec=timeout_sec)
        if target == "ruby":
            return run_shell(f"ruby {shlex.quote(str(entry))}", cwd=work_dir, env=env, timeout_sec=timeout_sec)
        if target == "lua":
            return run_shell(f"lua {shlex.quote(str(entry))}", cwd=work_dir, env=env, timeout_sec=timeout_sec)
        if target == "php":
            return run_shell(f"php {shlex.quote(str(entry))}", cwd=work_dir, env=env, timeout_sec=timeout_sec)
        if target == "julia":
            return run_shell(f"{shlex.quote(_resolve_julia_runtime_bin())} {shlex.quote(str(entry))}", cwd=work_dir, env=env, timeout_sec=timeout_sec)
        if target == "dart":
            return run_shell(f"dart run {shlex.quote(str(entry))}", cwd=work_dir, env=env, timeout_sec=timeout_sec)
        if target == "ps1":
            return run_shell(f"pwsh -NonInteractive -File {shlex.quote(str(entry))}", cwd=work_dir, env=env, timeout_sec=timeout_sec)
        if target == "zig":
            exe_path = emit_dir / (case_path.stem + "_zig.out")
            build = run_shell(
                "zig build-exe " + shlex.quote(str(entry)) + " -O ReleaseFast -I " + shlex.quote(str(emit_dir)) + " -femit-bin=" + shlex.quote(str(exe_path)),
                cwd=work_dir,
                env=env,
                timeout_sec=timeout_sec,
            )
            if build.returncode != 0:
                return build
            return run_shell(shlex.quote(str(exe_path)), cwd=work_dir, env=env, timeout_sec=timeout_sec)

    if target == "nim":
        entry_nim = emit_dir / (case_path.stem + ".nim")
        if not entry_nim.exists():
            return subprocess.CompletedProcess("", 1, "", f"entry file not found: {entry_nim}")
        stem = case_path.stem
        if stem[:1].isdigit():
            safe_stem = "m_" + stem
            safe_entry = emit_dir / (safe_stem + ".nim")
            if not safe_entry.exists():
                shutil.copy2(entry_nim, safe_entry)
            entry_nim = safe_entry
            stem = safe_stem
        exe_path = emit_dir / (stem + "_nim.out")
        nimcache_path = emit_dir / ("nimcache_" + stem)
        return run_shell(
            "nim c --hints:off --verbosity:0 --warning[UnusedImport]:off --passC:-w "
            + shlex.quote(f"--nimcache:{nimcache_path}") + " " + shlex.quote(f"-o:{exe_path}") + " -r " + shlex.quote(str(entry_nim)),
            cwd=work_dir,
            env=env,
            timeout_sec=timeout_sec,
        )

    return subprocess.CompletedProcess("", 1, "", f"unsupported target: {target}")


def _write_runner(path: Path, command: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/usr/bin/env bash\nset -euo pipefail\n" + command + " \"$@\"\n", encoding="utf-8")
    path.chmod(0o755)


def _find_entry_file(emit_dir: Path, stems: list[str], suffix: str) -> Path | None:
    for stem in stems:
        candidate = emit_dir / (stem + suffix)
        if candidate.exists():
            return candidate
    matches = sorted(emit_dir.rglob("*" + suffix))
    if len(matches) == 1:
        return matches[0]
    for candidate in matches:
        if "pytra" in candidate.stem and "cli" in candidate.stem:
            return candidate
    return None


def build_emitted_target_artifact(
    target: str,
    emit_dir: Path,
    bin_path: Path,
    *,
    entry_stem: str,
    work_dir: Path,
    env: dict[str, str] | None = None,
    timeout_sec: int = 180,
) -> subprocess.CompletedProcess[str]:
    """Build emitted selfhost sources and leave an executable artifact at bin_path.

    For interpreted targets, the artifact is an executable wrapper script.
    """
    if target == "powershell":
        target = "ps1"
    bin_path.parent.mkdir(parents=True, exist_ok=True)
    _safe_unlink(bin_path)
    stems = [entry_stem, entry_stem.replace("-", "_"), entry_stem.replace("_", "-"), "pytra_cli", "pytra-cli"]

    if target == "go":
        go_files = sorted(str(p) for p in emit_dir.rglob("*.go"))
        if len(go_files) == 0:
            return subprocess.CompletedProcess("", 1, "", "no .go files found")
        return run_shell("go build -o " + shlex.quote(str(bin_path)) + " " + " ".join(shlex.quote(f) for f in go_files), cwd=emit_dir, env=env, timeout_sec=timeout_sec)

    if target == "rs":
        cargo_toml = emit_dir / "Cargo.toml"
        if cargo_toml.exists():
            build = run_shell("cargo build --release", cwd=emit_dir, env=env, timeout_sec=timeout_sec)
            if build.returncode != 0:
                return build
            for candidate in (emit_dir / "target" / "release").glob("*"):
                if candidate.is_file() and os.access(candidate, os.X_OK) and candidate.name not in {"build-script-build"}:
                    shutil.copy2(candidate, bin_path)
                    bin_path.chmod(0o755)
                    return subprocess.CompletedProcess("cargo build --release", 0, "", "")
            return subprocess.CompletedProcess("", 1, "", "cargo build succeeded but no executable was found")
        entry = _find_entry_file(emit_dir, stems, ".rs")
        if entry is None:
            return subprocess.CompletedProcess("", 1, "", "entry .rs file not found")
        return run_shell("rustc -O " + shlex.quote(str(entry)) + " -o " + shlex.quote(str(bin_path)), cwd=work_dir, env=env, timeout_sec=timeout_sec)

    if target == "swift":
        swift_files = sorted(str(p) for p in emit_dir.rglob("*.swift"))
        if len(swift_files) == 0:
            return subprocess.CompletedProcess("", 1, "", "no .swift files found")
        return run_shell("swiftc -O " + " ".join(shlex.quote(f) for f in swift_files) + " -o " + shlex.quote(str(bin_path)), cwd=emit_dir, env=env, timeout_sec=timeout_sec)

    if target == "cs":
        cs_files = sorted(str(p) for p in emit_dir.rglob("*.cs"))
        if len(cs_files) == 0:
            return subprocess.CompletedProcess("", 1, "", "no .cs files found")
        if shutil.which("mcs") is not None and shutil.which("mono") is not None:
            exe_path = bin_path.with_suffix(".exe")
            build = run_shell("mcs -warn:0 " + shlex.quote(f"-out:{exe_path}") + " " + " ".join(shlex.quote(f) for f in cs_files), cwd=work_dir, env=env, timeout_sec=timeout_sec)
            if build.returncode != 0:
                return build
            _write_runner(bin_path, "mono " + shlex.quote(str(exe_path)))
            return subprocess.CompletedProcess(str(bin_path), 0, "", "")
        project_path = emit_dir / "PytraSelfhost.csproj"
        project_path.write_text("\n".join(["<Project Sdk=\"Microsoft.NET.Sdk\">", "  <PropertyGroup>", "    <OutputType>Exe</OutputType>", "    <TargetFramework>net8.0</TargetFramework>", "    <ImplicitUsings>disable</ImplicitUsings>", "    <Nullable>disable</Nullable>", "    <EnableDefaultCompileItems>true</EnableDefaultCompileItems>", "    <LangVersion>latest</LangVersion>", "  </PropertyGroup>", "</Project>", ""]), encoding="utf-8")
        build = run_shell("dotnet build " + shlex.quote(str(project_path)) + " -nologo -v:q", cwd=work_dir, env=env, timeout_sec=timeout_sec)
        if build.returncode != 0:
            return build
        dll_path = emit_dir / "bin" / "Debug" / "net8.0" / "PytraSelfhost.dll"
        if not dll_path.exists():
            return subprocess.CompletedProcess("", 1, "", f"dotnet output not found: {dll_path}")
        _write_runner(bin_path, "dotnet " + shlex.quote(str(dll_path)))
        return subprocess.CompletedProcess(str(bin_path), 0, "", "")

    if target == "java":
        java_files = sorted(str(p) for p in emit_dir.rglob("*.java"))
        if len(java_files) == 0:
            return subprocess.CompletedProcess("", 1, "", "no .java files found")
        classes_dir = emit_dir / "classes"
        classes_dir.mkdir(parents=True, exist_ok=True)
        build = run_shell("javac -d " + shlex.quote(str(classes_dir)) + " " + " ".join(shlex.quote(f) for f in java_files), cwd=work_dir, env=env, timeout_sec=timeout_sec)
        if build.returncode != 0:
            return build
        main_class = java_module_class_name(entry_stem)
        _write_runner(bin_path, "java -cp " + shlex.quote(str(classes_dir)) + " " + shlex.quote(main_class))
        return subprocess.CompletedProcess(str(bin_path), 0, "", "")

    if target == "kotlin":
        kt_files = sorted(str(p) for p in emit_dir.rglob("*.kt"))
        if len(kt_files) == 0:
            return subprocess.CompletedProcess("", 1, "", "no .kt files found")
        jar_path = bin_path.with_suffix(".jar")
        build = run_shell("kotlinc " + " ".join(shlex.quote(f) for f in kt_files) + " -include-runtime -d " + shlex.quote(str(jar_path)), cwd=work_dir, env=env, timeout_sec=timeout_sec)
        if build.returncode != 0:
            return build
        _write_runner(bin_path, "java -jar " + shlex.quote(str(jar_path)))
        return subprocess.CompletedProcess(str(bin_path), 0, "", "")

    if target == "scala":
        scala_files = sorted(str(p) for p in emit_dir.rglob("*.scala"))
        if len(scala_files) == 0:
            return subprocess.CompletedProcess("", 1, "", "no .scala files found")
        _write_runner(bin_path, "scala-cli run --server=false --jvm 17 " + " ".join(shlex.quote(f) for f in scala_files) + " --")
        return subprocess.CompletedProcess(str(bin_path), 0, "", "")

    if target == "ts":
        ts_files = sorted(str(p) for p in emit_dir.rglob("*.ts"))
        if len(ts_files) == 0:
            return subprocess.CompletedProcess("", 1, "", "no .ts files found")
        build = run_shell("tsc --target es2022 --module nodenext --moduleResolution nodenext --esModuleInterop --outDir " + shlex.quote(str(emit_dir)) + " " + " ".join(shlex.quote(f) for f in ts_files), cwd=work_dir, env=env, timeout_sec=timeout_sec)
        entry = _find_entry_file(emit_dir, stems, ".js")
        if entry is None:
            if build.returncode != 0:
                return build
            return subprocess.CompletedProcess("", 1, "", "entry .js file not found after tsc")
        _write_runner(bin_path, "node " + shlex.quote(str(entry)))
        return subprocess.CompletedProcess(str(bin_path), 0, "", "")

    script_specs = {
        "js": ("node", ".js"),
        "ruby": ("ruby", ".rb"),
        "lua": ("lua", ".lua"),
        "php": ("php", ".php"),
        "julia": (_resolve_julia_runtime_bin(), ".jl"),
        "dart": ("dart run", ".dart"),
        "ps1": ("pwsh -NonInteractive -File", ".ps1"),
    }
    if target in script_specs:
        runner, suffix = script_specs[target]
        entry = _find_entry_file(emit_dir, stems, suffix)
        if entry is None:
            return subprocess.CompletedProcess("", 1, "", f"entry {suffix} file not found")
        _write_runner(bin_path, runner + " " + shlex.quote(str(entry)))
        return subprocess.CompletedProcess(str(bin_path), 0, "", "")

    if target == "nim":
        entry = _find_entry_file(emit_dir, stems, ".nim")
        if entry is None:
            return subprocess.CompletedProcess("", 1, "", "entry .nim file not found")
        return run_shell("nim c --hints:off --verbosity:0 --warning[UnusedImport]:off --passC:-w " + shlex.quote(f"--nimcache:{emit_dir / 'nimcache_selfhost'}") + " " + shlex.quote(f"-o:{bin_path}") + " " + shlex.quote(str(entry)), cwd=work_dir, env=env, timeout_sec=timeout_sec)

    if target == "zig":
        entry = _find_entry_file(emit_dir, stems, ".zig")
        if entry is None:
            return subprocess.CompletedProcess("", 1, "", "entry .zig file not found")
        return run_shell("zig build-exe " + shlex.quote(str(entry)) + " -O ReleaseFast -I " + shlex.quote(str(emit_dir)) + " -femit-bin=" + shlex.quote(str(bin_path)), cwd=work_dir, env=env, timeout_sec=timeout_sec)

    return subprocess.CompletedProcess("", 1, "", f"unsupported target: {target}")


def _purge_case_artifacts(work: Path, case_stem: str) -> None:
    # Always remove stale artifacts before each run so parity checks cannot pass
    # by reusing files left by a previous language execution.
    for out_dir in (work / "sample" / "out", work / "test" / "out", work / "out"):
        if not out_dir.exists() or not out_dir.is_dir():
            continue
        for p in sorted(out_dir.glob(f"{case_stem}.*")):
            if p.is_file():
                p.unlink()


def find_case_path(case_stem: str, case_root: str) -> Path | None:
    if case_root == "sample":
        root = SAMPLE_ROOT
    elif case_root == "stdlib":
        root = STDLIB_ROOT
    else:
        root = FIXTURE_ROOT
    matches = sorted(root.rglob(f"{case_stem}.py"))
    if not matches:
        return None
    return matches[0]


def collect_sample_case_stems() -> list[str]:
    out: list[str] = []
    for p in sorted(SAMPLE_ROOT.glob("*.py")):
        stem = p.stem
        if stem == "__init__":
            continue
        out.append(stem)
    return out


def collect_fixture_case_stems(category: str = "") -> list[str]:
    """Collect fixture case stems, excluding negative tests (ng_*) and __init__.

    If *category* is non-empty, only stems under that subdirectory are returned.
    """
    if category != "":
        cat_dir = FIXTURE_ROOT / category
        if not cat_dir.is_dir():
            return []
        search_root = cat_dir
    else:
        search_root = FIXTURE_ROOT
    seen: set[str] = set()
    for p in sorted(search_root.rglob("*.py")):
        stem = p.stem
        if stem == "__init__":
            continue
        if stem.startswith("ng_"):
            continue
        seen.add(stem)
    return sorted(seen)


def collect_stdlib_case_stems() -> list[str]:
    """Return all stdlib case stems (from test/stdlib/source/py/<module>/*.py)."""
    seen: set[str] = set()
    if not STDLIB_ROOT.exists():
        return []
    for p in sorted(STDLIB_ROOT.rglob("*.py")):
        stem = p.stem
        if stem == "__init__":
            continue
        seen.add(stem)
    return sorted(seen)


def resolve_case_stems(cases: list[str], case_root: str, all_samples: bool = False, category: str = "") -> tuple[list[str], str]:
    if category != "":
        if len(cases) > 0:
            return [], "--category cannot be combined with positional cases"
        if case_root != "fixture":
            return [], "--category requires --case-root fixture"
        stems = collect_fixture_case_stems(category)
        if len(stems) == 0:
            return [], f"no cases found in category '{category}'"
        return stems, ""
    if len(cases) > 0:
        return cases, ""
    if case_root == "sample":
        return collect_sample_case_stems(), ""
    if case_root == "fixture":
        return collect_fixture_case_stems(), ""
    if case_root == "stdlib":
        return collect_stdlib_case_stems(), ""
    return [], "no cases specified"


def _save_parity_results(records: list[CheckRecord], case_root: str, targets: set[str]) -> None:
    """Save parity check results to .parity-results/<target>_<case-root>.json.

    Existing files are merged on a per-case basis so partial runs accumulate.
    Each case entry carries a timestamp.
    """
    parity_dir = ROOT / ".parity-results"
    parity_dir.mkdir(parents=True, exist_ok=True)

    # Group records by target
    by_target: dict[str, list[CheckRecord]] = {t: [] for t in targets}
    for rec in records:
        if rec.target in by_target:
            by_target[rec.target].append(rec)

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for target, recs in by_target.items():
        out_path = parity_dir / f"{target}_{case_root}.json"

        # Load existing data for merge
        existing: dict[str, object] = {}
        if out_path.exists():
            try:
                loaded = json.loads(out_path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict) and "results" in loaded:
                    existing = loaded["results"]  # type: ignore[assignment]
            except Exception:
                pass

        prev_pass = sum(1 for v in existing.values() if isinstance(v, dict) and v.get("category") == "ok")

        results: dict[str, object] = dict(existing)
        for rec in recs:
            entry: dict[str, object] = {"category": rec.category, "timestamp": now}
            if rec.detail:
                entry["detail"] = rec.detail
            if rec.elapsed_sec is not None:
                entry["elapsed_sec"] = round(rec.elapsed_sec, 3)
            # Normalize stem: strip category prefix (e.g. "collections/reversed_basic" → "reversed_basic")
            stem_key = rec.case_stem
            if "/" in stem_key:
                stem_key = stem_key.rsplit("/", 1)[-1]
            results[stem_key] = entry

        curr_pass = sum(1 for v in results.values() if isinstance(v, dict) and v.get("category") == "ok")

        doc = {
            "target": target,
            "case_root": case_root,
            "results": results,
        }
        out_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        _append_parity_changelog(target, case_root, prev_pass, curr_pass, now)

    if case_root == "sample":
        _maybe_regenerate_benchmark()


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


_CHANGELOG_PATHS = [
    ROOT / "docs" / "ja" / "progress-preview" / "changelog.md",
    ROOT / "docs" / "en" / "progress-preview" / "changelog.md",
]

_CHANGELOG_HEADERS: dict[str, str] = {
    "ja": (
        '<a href="../../en/progress-preview/changelog.md">\n'
        '  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">\n'
        '</a>\n\n'
        "# Parity Changelog\n\n"
        "| 日時 | 言語 | case-root | 変化 | 備考 |\n"
        "|---|---|---|---|---|\n"
    ),
    "en": (
        '<a href="../../ja/progress-preview/changelog.md">\n'
        '  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">\n'
        '</a>\n\n'
        "# Parity Changelog\n\n"
        "| Date | Language | case-root | Change | Note |\n"
        "|---|---|---|---|---|\n"
    ),
}


_CHANGELOG_COOLDOWN_SEC = 120  # 2 minutes: prevent multiple agents from writing in the same window


def _append_parity_changelog(target: str, case_root: str, prev_pass: int, curr_pass: int, now: str) -> None:
    """Append a row to progress-preview/changelog.md when PASS count changes.

    changelog.md は全エージェント共有の単一ファイルのため、fcntl.flock で排他制御する。
    クールダウン判定は lock 内で行い、待機中のエージェントが続けて書き込むのを防ぐ。
    クールダウンは target+case_root 単位で管理する。
    """
    import fcntl

    diff = curr_pass - prev_pass
    if diff == 0:
        return
    sign = "+" if diff > 0 else ""
    note = "regression" if diff < 0 else ""
    ts = now[:16]  # "YYYY-MM-DDTHH:MM"
    row = f"| {ts} | {target} | {case_root} | {prev_pass}→{curr_pass} ({sign}{diff}) | {note} |"
    sep_marker = "|---|---|---|---|---|"
    lock_path = ROOT / ".parity-results" / ".changelog.lock"
    marker_path = ROOT / ".parity-results" / f".changelog_last_{target}_{case_root}"
    try:
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with open(lock_path, "w") as lf:
            fcntl.flock(lf, fcntl.LOCK_EX)
            # クールダウン判定は lock 内で行う。
            # lock 待ち中のエージェントはここで「まだ期限切れでない」と判定してスキップする。
            if marker_path.exists() and time.time() - marker_path.stat().st_mtime < _CHANGELOG_COOLDOWN_SEC:
                return
            for cl_path in _CHANGELOG_PATHS:
                lang = "en" if "/en/" in cl_path.as_posix() else "ja"
                header = _CHANGELOG_HEADERS[lang]
                try:
                    cl_path.parent.mkdir(parents=True, exist_ok=True)
                    if not cl_path.exists():
                        content = header + row + "\n"
                    else:
                        content = cl_path.read_text(encoding="utf-8")
                        idx = content.find(sep_marker)
                        if idx == -1:
                            content = content.rstrip("\n") + "\n" + row + "\n"
                        else:
                            nl_pos = content.find("\n", idx)
                            insert_after = (nl_pos + 1) if nl_pos != -1 else len(content)
                            content = content[:insert_after] + row + "\n" + content[insert_after:]
                    cl_path.write_text(content, encoding="utf-8")
                except Exception:
                    pass
            marker_path.touch()
    except Exception:
        pass


def main() -> int:
    from runtime_parity_check_fast import main as fast_main  # type: ignore

    return fast_main()


def _maybe_refresh_selfhost_python() -> None:
    """Auto-re-aggregate selfhost_python.json if >2 minutes since last update.

    Reads existing .parity-results/*.json and writes selfhost_python.json so
    that gen_backend_progress.py always has up-to-date selfhost matrix data.
    呼び出しは _maybe_regenerate_progress() の前に置くこと。
    こうすることで「今サイクルの parity 結果 → selfhost_python.json → progress summary」
    の順に反映され、1サイクル遅延なく最新状態が summary に出る。
    クールダウンは changelog 書き込みと同じ 120 秒に統一。
    """
    marker = ROOT / ".parity-results" / "selfhost_python.json"
    if marker.exists() and (time.time() - marker.stat().st_mtime) < _CHANGELOG_COOLDOWN_SEC:
        return
    run_script = ROOT / "tools" / "run" / "run_selfhost_parity.py"
    if not run_script.exists():
        return
    parity_dir = ROOT / ".parity-results"
    if not parity_dir.exists() or not any(parity_dir.glob("*_sample.json")):
        return
    try:
        subprocess.run(
            ["python3", str(run_script), "--selfhost-lang", "python"],
            cwd=str(ROOT),
            timeout=60,
            capture_output=True,
        )
    except Exception:
        pass


def _maybe_regenerate_progress() -> None:
    """Regenerate backend progress pages if parity results are newer than the last generation."""
    marker = ROOT / ".parity-results" / ".progress_generated"
    parity_dir = ROOT / ".parity-results"
    gen_script = ROOT / "tools" / "gen" / "gen_backend_progress.py"
    if not gen_script.exists():
        return
    # Skip if marker exists and no parity result file is newer than it
    if marker.exists():
        marker_mtime = marker.stat().st_mtime
        has_newer = False
        if parity_dir.exists():
            for p in parity_dir.iterdir():
                if p.name.startswith("."):
                    continue
                if p.stat().st_mtime > marker_mtime:
                    has_newer = True
                    break
        if not has_newer:
            return
    try:
        subprocess.run(
            ["python3", str(gen_script)],
            cwd=str(ROOT),
            timeout=30,
            capture_output=True,
        )
        # Update marker timestamp
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(str(time.time()), encoding="utf-8")
    except Exception:
        pass


if __name__ == "__main__":
    raise SystemExit(main())
