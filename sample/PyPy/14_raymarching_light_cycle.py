# Auto-generated launcher to run the canonical sample/py script under PyPy.
from __future__ import annotations

from pathlib import Path
import runpy

runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "py" / "14_raymarching_light_cycle.py"),
    run_name="__main__",
)
