"""Julia backend CLI: manifest.json → Julia multi-file output."""
from __future__ import annotations

from toolchain.emit.common.cli_runner import run_emit_cli
from toolchain.emit.julia.emitter import emit_julia_module


def main() -> int:
    import sys
    cli_argv: list[str] | None = sys.argv[1:]
    return run_emit_cli(emit_julia_module, cli_argv, default_ext=".jl")


if __name__ == "__main__":
    raise SystemExit(main())
