#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from toolchain.frontends.transpile_cli import extract_function_signatures_from_python_source


SCHEMA_VERSION = 1
DEFAULT_OUTPUT = ROOT / "tools" / "runtime_symbol_index.json"
SOURCE_ROOTS: tuple[tuple[str, str, Path], ...] = (
    ("pytra.built_in", "built_in", ROOT / "src" / "pytra" / "built_in"),
    ("pytra.std", "std", ROOT / "src" / "pytra" / "std"),
    ("pytra.utils", "utils", ROOT / "src" / "pytra" / "utils"),
)
TOP_LEVEL_CLASS_RE = re.compile(r"^class\s+([A-Za-z_][A-Za-z0-9_]*)\b")
TOP_LEVEL_ASSIGN_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=")


def _path_to_rel_txt(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _module_id_for_source(prefix: str, root: Path, path: Path) -> str:
    rel = path.relative_to(root).as_posix()
    if rel.endswith("/__init__.py"):
        tail = rel[: -len("/__init__.py")].replace("/", ".")
        if tail == "":
            return prefix
        return prefix + "." + tail
    if rel == "__init__.py":
        return prefix
    if rel.endswith(".py"):
        rel = rel[:-3]
    tail = rel.replace("/", ".")
    if tail == "":
        return prefix
    return prefix + "." + tail


def _module_tail(module_id: str, group: str) -> str:
    if group == "core" and module_id.startswith("pytra.core."):
        return module_id[len("pytra.core.") :].replace(".", "/")
    if group == "built_in" and module_id.startswith("pytra.built_in."):
        return module_id[len("pytra.built_in.") :].replace(".", "/")
    if group == "std" and module_id.startswith("pytra.std."):
        return module_id[len("pytra.std.") :].replace(".", "/")
    if group == "utils" and module_id.startswith("pytra.utils."):
        return module_id[len("pytra.utils.") :].replace(".", "/")
    return ""


def _scan_top_level_symbols(path: Path) -> dict[str, dict[str, str]]:
    fn_sigs = extract_function_signatures_from_python_source(path)
    out: dict[str, dict[str, str]] = {}
    for name in sorted(fn_sigs.keys()):
        if name == "":
            continue
        out[name] = {"kind": "function", "dispatch": "function"}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return out
    for raw_line in lines:
        if raw_line == "":
            continue
        if raw_line[:1] in {" ", "\t"}:
            continue
        stripped = raw_line.strip()
        if stripped == "" or stripped.startswith("#") or stripped.startswith("@"):
            continue
        cls_m = TOP_LEVEL_CLASS_RE.match(stripped)
        if cls_m is not None:
            name = cls_m.group(1)
            if name not in out:
                out[name] = {"kind": "class", "dispatch": "ctor"}
            continue
        if stripped.startswith("def ") or stripped.startswith("class "):
            continue
        if stripped.startswith("import ") or stripped.startswith("from "):
            continue
        assign_m = TOP_LEVEL_ASSIGN_RE.match(stripped)
        if assign_m is not None:
            name = assign_m.group(1)
            if name not in out:
                out[name] = {"kind": "const", "dispatch": "value"}
    return out


def _modern_runtime_langs() -> list[str]:
    root = ROOT / "src" / "runtime"
    out: list[str] = []
    if not root.exists():
        return out
    for ent in sorted(root.iterdir()):
        if not ent.is_dir():
            continue
        if (ent / "core").exists() or (ent / "built_in").exists() or (ent / "std").exists() or (ent / "utils").exists():
            out.append(ent.name)
    return out


def _target_module_artifacts(lang: str, group: str, tail: str) -> dict[str, Any] | None:
    if tail == "":
        return None
    base_dir = ROOT / "src" / "runtime" / lang / group
    if not base_dir.exists():
        return None
    stem = base_dir / tail
    public_headers: list[str] = []
    compile_sources: list[str] = []
    companions: list[str] = []

    gen_h = stem.with_name(stem.name + ".gen.h")
    gen_cpp = stem.with_name(stem.name + ".gen.cpp")
    ext_h = stem.with_name(stem.name + ".ext.h")
    ext_cpp = stem.with_name(stem.name + ".ext.cpp")
    public_shim = ROOT / "src" / "runtime" / lang / "pytra" / group / (tail + ".h")

    if lang == "cpp" and public_shim.exists():
        public_headers.append(_path_to_rel_txt(public_shim))
    else:
        if gen_h.exists():
            public_headers.append(_path_to_rel_txt(gen_h))
        if ext_h.exists():
            public_headers.append(_path_to_rel_txt(ext_h))
    if gen_cpp.exists():
        compile_sources.append(_path_to_rel_txt(gen_cpp))
    if ext_cpp.exists():
        compile_sources.append(_path_to_rel_txt(ext_cpp))

    if gen_h.exists() or gen_cpp.exists():
        companions.append("gen")
    if ext_h.exists() or ext_cpp.exists():
        companions.append("ext")
    if len(public_headers) == 0 and len(compile_sources) == 0:
        return None
    return {
        "public_headers": public_headers,
        "compile_sources": compile_sources,
        "companions": companions,
    }


def _iter_target_core_module_ids(lang: str) -> list[str]:
    base_dir = ROOT / "src" / "runtime" / lang / "core"
    if not base_dir.exists():
        return []
    tails: set[str] = set()
    suffixes = (".gen.h", ".gen.cpp", ".ext.h", ".ext.cpp")
    for path in sorted(base_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(base_dir).as_posix()
        tail = ""
        for suffix in suffixes:
            if rel.endswith(suffix):
                tail = rel[: -len(suffix)]
                break
        if tail != "":
            tails.add(tail)
    out: list[str] = []
    for tail in sorted(tails):
        out.append("pytra.core." + tail.replace("/", "."))
    return out


def build_runtime_symbol_index() -> dict[str, Any]:
    modules: dict[str, Any] = {}
    targets: dict[str, Any] = {}
    langs = _modern_runtime_langs()

    for prefix, group, root in SOURCE_ROOTS:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.py")):
            module_id = _module_id_for_source(prefix, root, path)
            tail = _module_tail(module_id, group)
            modules[module_id] = {
                "source_py": _path_to_rel_txt(path),
                "runtime_group": group,
                "symbols": _scan_top_level_symbols(path),
            }
            for lang in langs:
                artifact = _target_module_artifacts(lang, group, tail)
                if artifact is None:
                    continue
                lang_doc = targets.setdefault(lang, {"modules": {}})
                lang_modules = lang_doc.setdefault("modules", {})
                lang_modules[module_id] = artifact

    for lang in langs:
        for module_id in _iter_target_core_module_ids(lang):
            if module_id not in modules:
                modules[module_id] = {
                    "source_py": "",
                    "runtime_group": "core",
                    "symbols": {},
                }
            tail = _module_tail(module_id, "core")
            artifact = _target_module_artifacts(lang, "core", tail)
            if artifact is None:
                continue
            lang_doc = targets.setdefault(lang, {"modules": {}})
            lang_modules = lang_doc.setdefault("modules", {})
            lang_modules[module_id] = artifact

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_by": "tools/gen_runtime_symbol_index.py",
        "modules": modules,
        "targets": targets,
    }


def _normalized_json_bytes(doc: dict[str, Any]) -> bytes:
    return (json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _check_index(path: Path) -> int:
    if not path.exists():
        print(f"error: runtime symbol index not found: {path}", file=sys.stderr)
        return 1
    expected = _normalized_json_bytes(build_runtime_symbol_index())
    actual = path.read_bytes()
    if actual != expected:
        print(f"error: stale runtime symbol index: {path}", file=sys.stderr)
        return 1
    print(f"[OK] runtime symbol index is up to date: {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate runtime symbol index JSON from SoT and runtime layout.")
    ap.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output JSON path")
    ap.add_argument("--check", action="store_true", help="Fail if output file is stale")
    ap.add_argument("--stdout", action="store_true", help="Print JSON to stdout instead of writing file")
    args = ap.parse_args(argv)

    output = Path(args.output)
    if args.check:
        return _check_index(output)
    doc = build_runtime_symbol_index()
    data = _normalized_json_bytes(doc)
    if args.stdout:
        sys.stdout.write(data.decode("utf-8"))
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    print(f"generated: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
