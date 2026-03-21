#!/usr/bin/env python3
"""Generate C++ .h/.cpp from all .east files in src/runtime/generated/.

This replaces the old gen_runtime_from_manifest.py for the simple case
of generating test-time C++ from pre-compiled .east files.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from toolchain.emit.cpp.emitter import transpile_to_cpp
from toolchain.emit.cpp.emitter.header_builder import build_cpp_header_from_east


def main() -> int:
    generated_dir = ROOT / "src" / "runtime" / "generated"
    east_files = sorted(generated_dir.rglob("*.east"))
    count = 0
    for east_path in east_files:
        east = json.loads(east_path.read_text(encoding="utf-8"))
        out_base = east_path.with_suffix("")
        cpp = transpile_to_cpp(east)
        # Strip main() from generated .cpp — these are library modules, not executables.
        import re
        cpp = re.sub(r'\nint main\(int argc, char\*\* argv\) \{.*', '', cpp, flags=re.DOTALL)
        header = build_cpp_header_from_east(east, east_path, out_base.with_suffix(".h"), cpp_text=cpp)
        out_base.with_suffix(".cpp").write_text(cpp, encoding="utf-8")
        out_base.with_suffix(".h").write_text(header, encoding="utf-8")
        count += 1
    print(f"generated {count} .east → .h + .cpp pairs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
