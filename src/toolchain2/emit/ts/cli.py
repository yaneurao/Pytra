"""TypeScript backend CLI: manifest.json → TypeScript multi-file output."""
from __future__ import annotations

from toolchain2.emit.common.cli_runner import run_emit_cli
from toolchain2.emit.ts.emitter import emit_ts_module


def main() -> int:
    import sys
    return run_emit_cli(emit_ts_module, sys.argv[1:], default_ext=".ts")


if __name__ == "__main__":
    raise SystemExit(main())
