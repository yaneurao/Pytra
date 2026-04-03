"""Dart backend CLI: manifest.json → Dart multi-file output."""
from __future__ import annotations

from toolchain2.emit.common.cli_runner import run_emit_cli
from toolchain2.emit.dart.emitter import emit_dart_module


def main() -> int:
    import sys
    return run_emit_cli(emit_dart_module, sys.argv[1:], default_ext=".dart")


if __name__ == "__main__":
    raise SystemExit(main())
