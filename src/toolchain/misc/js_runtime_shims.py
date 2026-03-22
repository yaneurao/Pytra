"""Helpers for staging the JS runtime bundle next to transpiled outputs."""

from __future__ import annotations

from pathlib import Path as NativePath
import shutil

from pytra.std.pathlib import Path


_ROOT = NativePath(__file__).resolve().parents[3]
_JS_RUNTIME_SRC_ROOT = _ROOT / "src" / "runtime" / "js"

# Maps src/runtime/js/<src_subdir> → <output>/<dst_subdir>
_JS_RUNTIME_COPY_MAP: tuple[tuple[str, str], ...] = (
    ("built_in", "built_in"),
    ("std", "std"),
)


def write_js_runtime_shims(output_dir: Path) -> None:
    """Stage the JS runtime files next to transpiled outputs.

    Copy the runtime files from src/runtime/js/{built_in,std} into
    <output_dir>/{built_in,std} so transpiled programs can resolve
    runtime imports locally. No generated/ or native/ subdirectories.
    """
    stage_root = NativePath(str(output_dir))
    stage_root.mkdir(parents=True, exist_ok=True)
    for src_name, dst_name in _JS_RUNTIME_COPY_MAP:
        src_root = _JS_RUNTIME_SRC_ROOT / src_name
        if not src_root.exists():
            continue
        dst_root = stage_root / dst_name
        if dst_root.exists():
            shutil.rmtree(dst_root)
        dst_root.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_root, dst_root)
