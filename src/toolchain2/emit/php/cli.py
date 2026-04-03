"""PHP backend CLI: manifest.json → PHP multi-file output."""
from __future__ import annotations

from toolchain2.emit.common.cli_runner import run_emit_cli
from toolchain2.emit.php.emitter import emit_php_module


def main() -> int:
    import sys
    return run_emit_cli(emit_php_module, sys.argv[1:], default_ext=".php")


if __name__ == "__main__":
    raise SystemExit(main())
