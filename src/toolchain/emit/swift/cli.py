"""Swift backend CLI: manifest.json → Swift multi-file output."""
from __future__ import annotations

from pytra.std.pathlib import Path

from toolchain.emit.common.cli_runner import run_emit_cli
from toolchain.emit.swift.emitter import emit_swift_module


def _copy_swift_runtime(output_dir: Path) -> None:
    """Copy Swift runtime files needed when compiling emitted modules together."""
    runtime_root = Path("src").joinpath("runtime").joinpath("swift")
    built_in = runtime_root.joinpath("built_in").joinpath("py_runtime.swift")
    if built_in.exists():
        output_dir.joinpath("py_runtime.swift").write_text(built_in.read_text(encoding="utf-8"), encoding="utf-8")
    image_runtime = runtime_root.joinpath("image_runtime.swift")
    if image_runtime.exists():
        output_dir.joinpath("image_runtime.swift").write_text(image_runtime.read_text(encoding="utf-8"), encoding="utf-8")
    std_dir = runtime_root.joinpath("std")
    if std_dir.exists():
        for runtime_file in std_dir.glob("*.swift"):
            output_dir.joinpath(runtime_file.name).write_text(runtime_file.read_text(encoding="utf-8"), encoding="utf-8")


def main() -> int:
    import sys
    return run_emit_cli(emit_swift_module, sys.argv[1:], default_ext=".swift", post_emit=_copy_swift_runtime)


if __name__ == "__main__":
    raise SystemExit(main())
