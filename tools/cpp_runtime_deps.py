from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = ROOT / "src" / "runtime" / "cpp"
SRC_ROOT = ROOT / "src"
_INCLUDE_RE = re.compile(r'^\s*#include\s+"([^"]+)"', re.MULTILINE)


def resolve_include(current_path: Path, include_txt: str, include_dir: Path) -> Path | None:
    if include_txt.startswith("runtime/cpp/"):
        cand = SRC_ROOT / include_txt
        return cand if cand.exists() else None
    search_roots = [
        current_path.parent,
        include_dir,
        SRC_ROOT,
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
    out: list[Path] = []
    name = header.name
    if name.endswith(".gen.h"):
        out.append(header.with_name(name[:-len(".gen.h")] + ".gen.cpp"))
        out.append(header.with_name(name[:-len(".gen.h")] + ".ext.cpp"))
    elif name.endswith(".ext.h"):
        out.append(header.with_name(name[:-len(".ext.h")] + ".ext.cpp"))
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
    seed = RUNTIME_ROOT / "core" / "py_runtime.ext.h"
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
