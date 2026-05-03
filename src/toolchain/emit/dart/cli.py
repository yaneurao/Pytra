"""Dart backend CLI: manifest.json → Dart multi-file output."""
from __future__ import annotations

from pathlib import Path

from toolchain.emit.common.cli_runner import run_emit_cli
from toolchain.emit.dart.emitter import emit_dart_module


def _copy_dart_runtime(output_dir: Path) -> None:
    """Copy Dart runtime files into the emit directory."""
    output_dir = Path(str(output_dir))
    runtime_root = Path(__file__).resolve().parents[3] / "runtime" / "dart"
    if not runtime_root.exists():
        return
    for bucket in ("built_in", "std"):
        bucket_dir = runtime_root / bucket
        if not bucket_dir.exists():
            continue
        for dart_file in bucket_dir.glob("*.dart"):
            dst = output_dir / bucket / dart_file.name
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(dart_file.read_text(encoding="utf-8"), encoding="utf-8")


def main() -> int:
    import sys
    return run_emit_cli(
        emit_dart_module,
        sys.argv[1:],
        default_ext=".dart",
        post_emit=_copy_dart_runtime,
        module_path_style=True,
    )


if __name__ == "__main__":
    raise SystemExit(main())
