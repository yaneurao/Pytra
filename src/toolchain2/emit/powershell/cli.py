"""PowerShell backend CLI: manifest.json → PowerShell multi-file output."""
from __future__ import annotations

from toolchain2.emit.common.cli_runner import run_emit_cli
from toolchain2.emit.powershell.emitter import emit_ps


def main() -> int:
    import sys
    return run_emit_cli(emit_ps, sys.argv[1:], default_ext=".ps1")


if __name__ == "__main__":
    raise SystemExit(main())
