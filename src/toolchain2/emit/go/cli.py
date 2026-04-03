"""Go backend CLI: manifest.json → Go multi-file output."""
from __future__ import annotations

from toolchain2.emit.common.cli_runner import run_emit_cli
from toolchain2.emit.go.emitter import emit_go_module


def main() -> int:
    import sys
    return run_emit_cli(emit_go_module, sys.argv[1:], default_ext=".go")


if __name__ == "__main__":
    raise SystemExit(main())
