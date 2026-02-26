from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))


TYPE_ID_COMPARE_RE = re.compile(r"type_id\(\)\s*(==|!=|<=|>=|<|>)")
TYPE_ID_SWITCH_RE = re.compile(r"switch\s*\([^)]*type_id\(")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


class SelfhostVirtualDispatchRegressionTest(unittest.TestCase):
    def test_sample_cpp_has_no_type_id_dispatch_conditionals(self) -> None:
        sample_cpp_dir = ROOT / "sample" / "cpp"
        self.assertTrue(sample_cpp_dir.is_dir(), f"missing dir: {sample_cpp_dir}")
        for cpp_path in sorted(sample_cpp_dir.glob("*.cpp")):
            text = _read_text(cpp_path)
            self.assertIsNone(
                TYPE_ID_COMPARE_RE.search(text),
                f"type_id compare conditional found in {cpp_path}",
            )
            self.assertIsNone(
                TYPE_ID_SWITCH_RE.search(text),
                f"type_id switch dispatch found in {cpp_path}",
            )

    def test_pytra_gen_has_no_type_id_dispatch_conditionals_except_registry(self) -> None:
        gen_dir = ROOT / "src" / "runtime" / "cpp" / "pytra-gen"
        self.assertTrue(gen_dir.is_dir(), f"missing dir: {gen_dir}")
        allow_registry = (gen_dir / "built_in" / "type_id.cpp").resolve()
        for cpp_path in sorted(gen_dir.rglob("*.cpp")):
            if cpp_path.resolve() == allow_registry:
                continue
            text = _read_text(cpp_path)
            self.assertIsNone(
                TYPE_ID_COMPARE_RE.search(text),
                f"type_id compare conditional found in {cpp_path}",
            )
            self.assertIsNone(
                TYPE_ID_SWITCH_RE.search(text),
                f"type_id switch dispatch found in {cpp_path}",
            )

    def test_verify_selfhost_end_to_end_two_cases_skip_build(self) -> None:
        verify = ROOT / "tools" / "verify_selfhost_end_to_end.py"
        selfhost_bin = ROOT / "selfhost" / "py2cpp.out"
        if not selfhost_bin.exists():
            self.skipTest(f"missing selfhost binary: {selfhost_bin}")
        cmd = [
            "python3",
            str(verify),
            "--skip-build",
            "--selfhost-bin",
            str(selfhost_bin),
            "--cases",
            "test/fixtures/core/fib.py",
            "sample/py/17_monte_carlo_pi.py",
        ]
        cp = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
        combined = (cp.stdout or "") + (cp.stderr or "")
        self.assertEqual(cp.returncode, 0, combined)
        self.assertIn("[OK] test/fixtures/core/fib.py", combined)
        self.assertIn("[OK] sample/py/17_monte_carlo_pi.py", combined)


if __name__ == "__main__":
    unittest.main()
