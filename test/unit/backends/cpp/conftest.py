"""Pytest conftest for C++ backend tests.

Generates C++ headers from runtime .east files before any test runs.
The generated files are placed in a temporary directory and the
-I include path is made available via the PYTRA_GENERATED_CPP_DIR
environment variable.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
sys.path.insert(0, str(ROOT / "src"))

_GENERATED_DIR: Path | None = None


def _generate_runtime_cpp() -> Path:
    """Generate C++ .h/.cpp from runtime .east files into a temp dir."""
    global _GENERATED_DIR
    if _GENERATED_DIR is not None and _GENERATED_DIR.exists():
        return _GENERATED_DIR

    from toolchain.emit.cpp.emitter import transpile_to_cpp
    from toolchain.emit.cpp.emitter.header_builder import build_cpp_header_from_east
    from toolchain.emit.cpp.cli import _build_cpp_emit_module_without_extern_decls, _is_runtime_module_extern_only
    import re

    east_dir = ROOT / "src" / "runtime" / "east"
    # Use a stable location so it persists across test collection
    gen_dir = ROOT / "out" / "_test_generated_cpp"
    gen_dir.mkdir(parents=True, exist_ok=True)

    ns_map = {
        "built_in": "pytra::built_in",
        "std": "pytra::std",
        "utils": "pytra::utils",
    }

    for east_path in sorted(east_dir.rglob("*.east")):
        rel = east_path.relative_to(east_dir).with_suffix("")
        parts = list(rel.parts)
        bucket = parts[0] if len(parts) > 0 else ""
        ns_prefix = ns_map.get(bucket, "pytra::" + bucket)
        ns = ns_prefix + "::" + "::".join(parts[1:]) if len(parts) > 1 else ns_prefix

        east = json.loads(east_path.read_text(encoding="utf-8"))
        out_base = gen_dir / rel

        # Strip @extern declarations — their C++ implementations are hand-written
        # in the native runtime, not generated from the EAST body.
        emit_east = _build_cpp_emit_module_without_extern_decls(east)
        is_extern_only = _is_runtime_module_extern_only(east)

        cpp = transpile_to_cpp(emit_east, top_namespace=ns)
        cpp = re.sub(r'\nint main\(int argc, char\*\* argv\) \{.*', '', cpp, flags=re.DOTALL)
        # Remove trailing namespace close from cpp to avoid duplication in header
        cpp_for_header = re.sub(r'\n\}  // namespace [^\n]+\s*$', '', cpp.rstrip())
        header = build_cpp_header_from_east(east, east_path, out_base.with_suffix(".h"), cpp_text=cpp_for_header, top_namespace=ns)

        # Add using namespace before #endif
        lines = header.rstrip().split("\n")
        for idx in range(len(lines) - 1, -1, -1):
            if lines[idx].strip().startswith("#endif"):
                lines.insert(idx, f"using namespace {ns};")
                break
        header = "\n".join(lines) + "\n"

        out_base.with_suffix(".cpp").parent.mkdir(parents=True, exist_ok=True)
        # Skip .cpp for extern-only modules (implementation is in native runtime)
        if not is_extern_only:
            out_base.with_suffix(".cpp").write_text(cpp, encoding="utf-8")
        out_base.with_suffix(".h").write_text(header, encoding="utf-8")

    _GENERATED_DIR = gen_dir
    return gen_dir


@pytest.fixture(autouse=True, scope="session")
def generate_runtime_cpp():
    """Session-scoped fixture: generate runtime C++ headers once."""
    gen_dir = _generate_runtime_cpp()
    os.environ["PYTRA_GENERATED_CPP_DIR"] = str(gen_dir)
    yield
    # Don't clean up — reuse across runs for speed
