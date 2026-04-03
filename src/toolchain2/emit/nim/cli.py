"""Nim backend CLI: manifest.json → Nim multi-file output."""
from __future__ import annotations

from toolchain2.emit.common.cli_runner import run_emit_cli
from toolchain2.emit.nim.emitter import emit_nim_module


def main() -> int:
    import sys
    return run_emit_cli(emit_nim_module, sys.argv[1:], default_ext=".nim")


if __name__ == "__main__":
    raise SystemExit(main())
