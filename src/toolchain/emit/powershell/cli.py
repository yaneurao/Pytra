"""PowerShell backend CLI: manifest.json → PowerShell multi-file output."""
from __future__ import annotations

from pytra.std.pathlib import Path

from toolchain.emit.common.cli_runner import run_emit_cli
from toolchain.emit.powershell.emitter import emit_ps1_module


def _copy_powershell_runtime(output_dir: Path) -> None:
    """Copy PowerShell runtime files needed by emitted modules."""
    runtime_root = Path("src").joinpath("runtime").joinpath("powershell")
    for bucket in ["built_in", "std", "utils"]:
        source_dir = runtime_root.joinpath(bucket)
        if not source_dir.exists():
            continue
        target_dir = output_dir.joinpath(bucket)
        target_dir.mkdir(parents=True, exist_ok=True)
        for runtime_file in source_dir.glob("*.ps1"):
            target_dir.joinpath(runtime_file.name).write_text(runtime_file.read_text(encoding="utf-8"), encoding="utf-8")


def main() -> int:
    import sys
    cli_argv: list[str] = sys.argv[1:]
    return run_emit_cli(emit_ps1_module, cli_argv, default_ext=".ps1", post_emit=_copy_powershell_runtime)


if __name__ == "__main__":
    raise SystemExit(main())
