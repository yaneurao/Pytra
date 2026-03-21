#!/usr/bin/env python3
"""Go backend: link-output.json → Go multi-file output.

Usage:
    python3 -m toolchain.emit.go LINK_OUTPUT.json --output-dir out/go/
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path as NativePath

from toolchain.emit.go.emitter import transpile_to_go
from toolchain.emit.loader import emit_all_modules

_ROOT = NativePath(__file__).resolve().parents[3]
_GO_RUNTIME_SRC = _ROOT / "sample" / "go" / "py_runtime.go"
_GO_NATIVE_STD_DIR = _ROOT / "src" / "runtime" / "go" / "std"
_RUNTIME_EAST_ROOT = _ROOT / "src" / "runtime" / "east"


def _rewrite_extern_delegates(code: str, module_stem: str) -> str:
    """Rewrite @extern delegate calls in generated Go runtime modules.

    The Go emitter generates ``math.sqrt(x)`` for @extern calls, but the
    actual native function is ``math_native_sqrt(x)``.  Also wraps like
    ``__pytra_float(math.sqrt(x))`` → ``math_native_sqrt(x)`` since the
    native already returns float64.
    """
    import re
    # Pattern: module.func(args) → module_native_func(args)
    code = re.sub(
        r'\b' + re.escape(module_stem) + r'\.(\w+)\(',
        module_stem + r'_native_\1(',
        code,
    )
    # Remove __pytra_float() wrapper around native calls (native already returns float64)
    code = re.sub(
        r'__pytra_float\((' + re.escape(module_stem) + r'_native_\w+\([^)]*\))\)',
        r'\1',
        code,
    )
    return code


def _strip_main(code: str) -> str:
    """Remove func main() block from generated Go runtime modules."""
    import re
    return re.sub(r'\nfunc main\(\)\s*\{[^}]*\}\s*', '\n', code)


def _generate_go_runtime(output_dir: str) -> None:
    """Generate Go runtime files from .east sources and copy native .go files."""
    out = NativePath(output_dir)

    # 1. Copy py_runtime.go (built_in)
    dst = out / "py_runtime.go"
    if _GO_RUNTIME_SRC.exists() and not dst.exists():
        shutil.copy2(str(_GO_RUNTIME_SRC), str(dst))

    # 2. Copy native std files (math_native.go, time_native.go)
    if _GO_NATIVE_STD_DIR.is_dir():
        for f in sorted(_GO_NATIVE_STD_DIR.iterdir()):
            if f.suffix == ".go":
                d = out / f.name
                if not d.exists():
                    shutil.copy2(str(f), str(d))

    # 3. Transpile .east runtime modules to .go (std/)
    _GENERATE_MODULES: dict[str, tuple[str, ...]] = {
        "std": ("time", "math"),
    }
    east_root = str(_RUNTIME_EAST_ROOT)
    if not os.path.isdir(east_root):
        return
    for bucket, allowed in _GENERATE_MODULES.items():
        bucket_dir = os.path.join(east_root, bucket)
        if not os.path.isdir(bucket_dir):
            continue
        for stem in allowed:
            east_file = os.path.join(bucket_dir, stem + ".east")
            if not os.path.isfile(east_file):
                continue
            dst_go = out / (stem + ".go")
            if dst_go.exists():
                continue
            try:
                east_text = open(east_file, "r", encoding="utf-8").read()
                east_doc = json.loads(east_text)
                go_text = transpile_to_go(east_doc)
                # Rewrite @extern delegate calls: math.sqrt(x) → math_native_sqrt(x)
                go_text = _rewrite_extern_delegates(go_text, stem)
                # Remove func main() from runtime modules (only entry has main)
                go_text = _strip_main(go_text)
                dst_go.write_text(go_text, encoding="utf-8")
            except Exception:
                pass


def main() -> int:
    argv = sys.argv[1:]
    if len(argv) == 0 or argv[0] in ("-h", "--help"):
        print("usage: toolchain.emit.go LINK_OUTPUT.json --output-dir DIR")
        return 0

    input_path = ""
    output_dir = "out/go"
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok == "--output-dir" and i + 1 < len(argv):
            output_dir = argv[i + 1]
            i += 2
            continue
        if not tok.startswith("-") and input_path == "":
            input_path = tok
        i += 1

    if input_path == "":
        print("error: input link-output.json is required", file=sys.stderr)
        return 1

    rc = emit_all_modules(input_path, output_dir, ".go", transpile_to_go)
    if rc != 0:
        return rc
    _generate_go_runtime(output_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
