"""Swift backend CLI: manifest.json → Swift multi-file output."""
from __future__ import annotations

from toolchain2.emit.common.cli_runner import run_emit_cli
from toolchain2.emit.swift.emitter import emit_swift_module


def main() -> int:
    import sys
    return run_emit_cli(emit_swift_module, sys.argv[1:], default_ext=".swift")


if __name__ == "__main__":
    raise SystemExit(main())
