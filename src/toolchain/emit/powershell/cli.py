"""PowerShell backend CLI: manifest.json → PowerShell multi-file output."""
from __future__ import annotations

from pathlib import Path

from toolchain.emit.common.cli_runner import run_emit_cli
from toolchain.emit.powershell.emitter import emit_ps1_module


def _copy_powershell_runtime(output_dir: Path) -> None:
    """Copy PowerShell runtime files into the emit directory."""
    runtime_root = Path(__file__).resolve().parents[3] / "runtime" / "powershell"
    if not runtime_root.exists():
        return
    for bucket in ("built_in", "std", "utils"):
        bucket_dir = runtime_root / bucket
        if not bucket_dir.exists():
            continue
        for runtime_file in bucket_dir.glob("*.ps1"):
            dst = output_dir / bucket / runtime_file.name
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(runtime_file.read_text(encoding="utf-8"), encoding="utf-8")


def main() -> int:
    import sys
    return run_emit_cli(
        emit_ps1_module,
        sys.argv[1:],
        default_ext=".ps1",
        post_emit=_copy_powershell_runtime,
    )


if __name__ == "__main__":
    raise SystemExit(main())
