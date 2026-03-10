from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
_TOOL_PATH = ROOT / "tools" / "check_east_stage_boundary.py"
_SPEC = importlib.util.spec_from_file_location("check_east_stage_boundary", _TOOL_PATH)
assert _SPEC is not None and _SPEC.loader is not None
MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(MOD)


class EastStageBoundaryGuardTest(unittest.TestCase):
    def test_east_stage_boundary_guard_passes(self) -> None:
        cp = subprocess.run(
            ["python3", "tools/check_east_stage_boundary.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(cp.returncode, 0, msg=cp.stdout + "\n" + cp.stderr)

    def test_semantic_literal_guard_rejects_east2_dispatch_mode_literal(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "east2_semantic_drift.py"
            path.write_text('META_KEY = "dispatch_mode"\n', encoding="utf-8")
            errors: list[str] = []
            MOD._check_semantic_literals(
                path,
                forbidden_literals=("dispatch_mode",),
                stage_label="EAST2 stage",
                errors=errors,
            )
            self.assertEqual(
                errors,
                [f"{path.as_posix()}:1 disallowed semantic literal in EAST2 stage: dispatch_mode"],
            )

    def test_semantic_literal_guard_rejects_code_emitter_stage_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "code_emitter_semantic_drift.py"
            path.write_text('ROOT_KEY = "linked_program_v1"\n', encoding="utf-8")
            errors: list[str] = []
            MOD._check_semantic_literals(
                path,
                forbidden_literals=("linked_program_v1",),
                stage_label="CodeEmitter base",
                errors=errors,
            )
            self.assertEqual(
                errors,
                [f"{path.as_posix()}:1 disallowed semantic literal in CodeEmitter base: linked_program_v1"],
            )


if __name__ == "__main__":
    unittest.main()
