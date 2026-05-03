"""Zig backend CLI: manifest.json → Zig multi-file output."""
from __future__ import annotations

from pathlib import Path

from toolchain.emit.common.cli_runner import run_emit_cli
from toolchain.emit.zig.emitter import emit_zig_module


def _copy_zig_runtime(output_dir: Path) -> None:
    """Copy Zig runtime files into the emit directory."""
    output_dir = Path(str(output_dir))
    runtime_root = Path(__file__).resolve().parents[3] / "runtime" / "zig"
    if not runtime_root.exists():
        return
    for bucket in ("built_in", "std"):
        bucket_dir = runtime_root / bucket
        if not bucket_dir.exists():
            continue
        for zig_file in bucket_dir.glob("*.zig"):
            dst = output_dir / bucket / zig_file.name
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(zig_file.read_text(encoding="utf-8"), encoding="utf-8")
    built_in_runtime = runtime_root / "built_in" / "py_runtime.zig"
    if built_in_runtime.exists():
        core_dst = output_dir / "core" / "py_runtime.zig"
        core_dst.parent.mkdir(parents=True, exist_ok=True)
        core_dst.write_text(built_in_runtime.read_text(encoding="utf-8"), encoding="utf-8")
    entry_candidate: Path | None = None
    entry_count = 0
    for candidate in output_dir.glob("**/cli.zig"):
        if candidate.name != "cli.zig":
            continue
        entry_candidate = candidate
        entry_count += 1
    if entry_candidate is not None and entry_count == 1:
        output_text = str(output_dir)
        entry_text = str(entry_candidate)
        rel = entry_text
        prefix = output_text + "/"
        if entry_text.startswith(prefix):
            rel = entry_text[len(prefix) :]
        main_path = output_dir / "main.zig"
        main_path.write_text(
            "pub fn main() void {\n    @import(\"" + rel + "\").main();\n}\n",
            encoding="utf-8",
        )


def main() -> int:
    import sys
    return run_emit_cli(
        emit_zig_module,
        sys.argv[1:],
        default_ext=".zig",
        post_emit=_copy_zig_runtime,
        module_path_style=True,
    )


if __name__ == "__main__":
    raise SystemExit(main())
