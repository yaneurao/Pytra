"""Helpers for staging the JS runtime bundle next to transpiled outputs."""

from __future__ import annotations

from pathlib import Path as NativePath
import shutil

from pytra.std.pathlib import Path


_ROOT = NativePath(__file__).resolve().parents[3]
_JS_RUNTIME_SRC_ROOT = _ROOT / "src" / "runtime" / "js"
_JS_RUNTIME_STAGE_ROOTS = ("generated", "native")


def write_js_runtime_shims(output_dir: Path) -> None:
    """Stage the JS runtime bundle expected by JS/TS transpiled imports.

    Generated JS/TS imports runtime modules under `./runtime/js/...`.
    Copy the checked-in generated/native runtime tree into the output bundle so
    transpiled programs do not direct-load repo-owned files.
    """
    stage_root = NativePath(str(output_dir)) / "runtime" / "js"
    stage_root.mkdir(parents=True, exist_ok=True)
    for root_name in _JS_RUNTIME_STAGE_ROOTS:
        src_root = _JS_RUNTIME_SRC_ROOT / root_name
        if not src_root.exists():
            raise RuntimeError("missing JS runtime stage root: " + str(src_root))
        dst_root = stage_root / root_name
        if dst_root.exists():
            shutil.rmtree(dst_root)
        shutil.copytree(src_root, dst_root)
