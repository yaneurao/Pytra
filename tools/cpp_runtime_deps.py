from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from toolchain.frontends.runtime_symbol_index import load_runtime_symbol_index


RUNTIME_ROOT = ROOT / "src" / "runtime" / "cpp"
SRC_ROOT = ROOT / "src"
_INCLUDE_RE = re.compile(r'^\s*#include\s+"([^"]+)"', re.MULTILINE)
_HEADER_SOURCE_INDEX: dict[str, list[Path]] | None = None


def resolve_include(current_path: Path, include_txt: str, include_dir: Path) -> Path | None:
    if include_txt.startswith("runtime/cpp/"):
        cand = SRC_ROOT / include_txt
        return cand if cand.exists() else None
    search_roots = [
        current_path.parent,
        include_dir,
        SRC_ROOT,
        RUNTIME_ROOT,
    ]
    for base in search_roots:
        cand = base / include_txt
        if cand.exists():
            return cand
    return None


def direct_include_targets(path: Path, include_dir: Path) -> list[Path]:
    out: list[Path] = []
    if not path.exists():
        return out
    for inc in _INCLUDE_RE.findall(path.read_text(encoding="utf-8")):
        resolved = resolve_include(path, inc, include_dir)
        if resolved is not None:
            out.append(resolved)
    return out


def runtime_cpp_candidates_from_header(header: Path) -> list[Path]:
    indexed = _runtime_cpp_sources_from_header(header)
    if len(indexed) > 0:
        return indexed
    out: list[Path] = []
    rel: Path | None = None
    try:
        rel = header.resolve().relative_to(RUNTIME_ROOT.resolve())
    except ValueError:
        rel = None
    if rel is not None:
        parts = rel.parts
        if len(parts) >= 2 and header.suffix == ".h":
            layout = parts[0]
            if layout == "core":
                tail_path = Path(*parts[1:])
                stem_path = tail_path.with_suffix("")
                out.extend(_runtime_cpp_candidates_from_core_tail(stem_path))
                return out
        if len(parts) >= 3 and header.suffix == ".h":
            layout = parts[0]
            group = parts[1]
            tail_path = Path(*parts[2:])
            stem_path = tail_path.with_suffix("")
            if layout == "pytra":
                out.extend(_runtime_cpp_candidates_from_group_tail(group, stem_path))
                return out
            if layout == "generated":
                out.extend(_runtime_cpp_candidates_from_generated_tail(group, stem_path))
                return out
            if layout == "native":
                out.extend(_runtime_cpp_candidates_from_native_tail(group, stem_path))
                return out
    name = header.name
    if name.endswith(".gen.h"):
        out.append(header.with_name(name[:-len(".gen.h")] + ".gen.cpp"))
        out.append(header.with_name(name[:-len(".gen.h")] + ".ext.cpp"))
    elif name.endswith(".ext.h"):
        out.append(header.with_name(name[:-len(".ext.h")] + ".ext.cpp"))
    return out


def _append_unique_path(out: list[Path], path: Path) -> None:
    if path not in out:
        out.append(path)


def _runtime_cpp_candidates_from_group_tail(group: str, tail: Path) -> list[Path]:
    out: list[Path] = []
    _append_unique_path(out, RUNTIME_ROOT / "generated" / group / (tail.as_posix() + ".cpp"))
    _append_unique_path(out, RUNTIME_ROOT / "native" / group / (tail.as_posix() + ".cpp"))
    return out


def _runtime_cpp_candidates_from_generated_tail(group: str, tail: Path) -> list[Path]:
    if group == "core":
        return _runtime_cpp_candidates_from_generated_core_tail(tail)
    if group == "compiler":
        out: list[Path] = []
        _append_unique_path(out, RUNTIME_ROOT / "native" / group / (tail.as_posix() + ".cpp"))
        return out
    return _runtime_cpp_candidates_from_group_tail(group, tail)


def _runtime_cpp_candidates_from_native_tail(group: str, tail: Path) -> list[Path]:
    if group == "core":
        return _runtime_cpp_candidates_from_native_core_tail(tail)
    out: list[Path] = []
    _append_unique_path(out, RUNTIME_ROOT / "native" / group / (tail.as_posix() + ".cpp"))
    return out


def _core_tail_base(tail: Path) -> str:
    tail_txt = tail.as_posix()
    base_tail = tail_txt
    if base_tail.endswith(".ext"):
        base_tail = base_tail[: -len(".ext")]
    elif base_tail.endswith(".gen"):
        base_tail = base_tail[: -len(".gen")]
    return base_tail


def _runtime_cpp_candidates_from_generated_core_tail(tail: Path) -> list[Path]:
    out: list[Path] = []
    base_tail = _core_tail_base(tail)
    for rel_tail in (base_tail + ".cpp",):
        _append_unique_path(out, RUNTIME_ROOT / "generated" / "core" / rel_tail)
    for rel_tail in (base_tail + ".cpp",):
        _append_unique_path(out, RUNTIME_ROOT / "native" / "core" / rel_tail)
    return out


def _runtime_cpp_candidates_from_native_core_tail(tail: Path) -> list[Path]:
    out: list[Path] = []
    base_tail = _core_tail_base(tail)
    for rel_tail in (base_tail + ".cpp",):
        _append_unique_path(out, RUNTIME_ROOT / "generated" / "core" / rel_tail)
    for rel_tail in (base_tail + ".cpp",):
        _append_unique_path(out, RUNTIME_ROOT / "native" / "core" / rel_tail)
    return out


def _runtime_cpp_candidates_from_core_tail(tail: Path) -> list[Path]:
    out: list[Path] = []
    for path in _runtime_cpp_candidates_from_generated_core_tail(tail):
        _append_unique_path(out, path)
    for path in _runtime_cpp_candidates_from_native_core_tail(tail):
        _append_unique_path(out, path)
    return out


def _runtime_cpp_sources_from_header(header: Path) -> list[Path]:
    index = _load_header_source_index()
    key = str(header.resolve())
    hits = index.get(key)
    if isinstance(hits, list):
        return list(hits)
    return []


def _load_header_source_index() -> dict[str, list[Path]]:
    global _HEADER_SOURCE_INDEX
    if isinstance(_HEADER_SOURCE_INDEX, dict):
        return _HEADER_SOURCE_INDEX
    out: dict[str, list[Path]] = {}
    doc = load_runtime_symbol_index()
    targets = doc.get("targets")
    if isinstance(targets, dict):
        cpp_doc = targets.get("cpp")
        if isinstance(cpp_doc, dict):
            modules = cpp_doc.get("modules")
            if isinstance(modules, dict):
                for ent in modules.values():
                    if not isinstance(ent, dict):
                        continue
                    headers_obj = ent.get("compiler_headers")
                    if not isinstance(headers_obj, list):
                        headers_obj = ent.get("public_headers")
                    sources_obj = ent.get("compile_sources")
                    if not isinstance(headers_obj, list) or not isinstance(sources_obj, list):
                        continue
                    compile_sources: list[Path] = []
                    for source_txt in sources_obj:
                        if not isinstance(source_txt, str) or source_txt == "":
                            continue
                        src_path = ROOT / source_txt
                        if src_path.exists():
                            compile_sources.append(src_path.resolve())
                    if len(compile_sources) == 0:
                        continue
                    for header_txt in headers_obj:
                        if not isinstance(header_txt, str) or header_txt == "":
                            continue
                        hdr_path = ROOT / header_txt
                        if not hdr_path.exists():
                            continue
                        out[str(hdr_path.resolve())] = list(compile_sources)
    _HEADER_SOURCE_INDEX = out
    return out


def _resolve_module_sources(module_sources: list[str]) -> list[Path]:
    out: list[Path] = []
    for source_txt in module_sources:
        source_path = Path(source_txt)
        if not source_path.is_absolute():
            source_path = ROOT / source_path
        if source_path.exists():
            out.append(source_path)
    return out


def collect_runtime_cpp_sources(module_sources: list[str], include_dir: Path) -> list[str]:
    """モジュール source から辿れる runtime `.cpp` を、forwarder header 経由も含めて返す。"""
    out: list[str] = []
    seen_nodes: set[Path] = set()
    seen_sources: set[str] = set()
    queue: list[Path] = _resolve_module_sources(module_sources)
    seed = RUNTIME_ROOT / "native" / "core" / "py_runtime.h"
    if not seed.exists():
        seed = RUNTIME_ROOT / "core" / "py_runtime.h"
    if seed.exists():
        queue.append(seed)
    while queue:
        node = queue.pop(0)
        if node in seen_nodes or not node.exists():
            continue
        seen_nodes.add(node)
        if str(node).startswith(str(RUNTIME_ROOT)):
            for cpp_path in runtime_cpp_candidates_from_header(node):
                if not cpp_path.exists():
                    continue
                rel = cpp_path.relative_to(ROOT).as_posix()
                if rel not in seen_sources:
                    seen_sources.add(rel)
                    out.append(rel)
                    queue.append(cpp_path)
        queue.extend(direct_include_targets(node, include_dir))
    return out
