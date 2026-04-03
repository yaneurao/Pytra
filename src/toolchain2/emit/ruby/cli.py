"""Ruby backend CLI: manifest.json → Ruby multi-file output."""
from __future__ import annotations

from toolchain2.emit.common.cli_runner import run_emit_cli
from toolchain2.emit.ruby.emitter import transpile_to_ruby


def main() -> int:
    import sys
    return run_emit_cli(transpile_to_ruby, sys.argv[1:], default_ext=".rb")


if __name__ == "__main__":
    raise SystemExit(main())
