"""Lua backend CLI: manifest.json → Lua multi-file output."""
from __future__ import annotations

from pathlib import Path

from toolchain.emit.common.cli_runner import run_emit_cli
from toolchain.emit.lua.emitter import emit_lua_module


def _copy_lua_runtime(output_dir: Path) -> None:
    """Copy Lua runtime files into the emit directory."""
    runtime_root = Path(__file__).resolve().parents[3] / "runtime" / "lua"
    if not runtime_root.exists():
        return
    for bucket in ("built_in", "std"):
        bucket_dir = runtime_root / bucket
        if not bucket_dir.exists():
            continue
        for runtime_file in bucket_dir.glob("*.lua"):
            dst = output_dir / bucket / runtime_file.name
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(runtime_file.read_text(encoding="utf-8"), encoding="utf-8")


def main() -> int:
    import sys
    return run_emit_cli(emit_lua_module, sys.argv[1:], default_ext=".lua", post_emit=_copy_lua_runtime)


if __name__ == "__main__":
    raise SystemExit(main())
