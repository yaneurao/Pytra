"""Java backend CLI: manifest.json → Java multi-file output."""
from __future__ import annotations

from toolchain2.emit.common.cli_runner import run_emit_cli
from toolchain2.emit.java.emitter import emit_java_module


def main() -> int:
    import sys
    return run_emit_cli(emit_java_module, sys.argv[1:], default_ext=".java")


if __name__ == "__main__":
    raise SystemExit(main())
