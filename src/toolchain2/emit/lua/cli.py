"""Lua backend CLI: manifest.json → Lua multi-file output."""
from __future__ import annotations

from toolchain2.emit.common.cli_runner import run_emit_cli
from toolchain2.emit.lua.emitter import emit_lua_module


def main() -> int:
    import sys
    return run_emit_cli(emit_lua_module, sys.argv[1:], default_ext=".lua")


if __name__ == "__main__":
    raise SystemExit(main())
