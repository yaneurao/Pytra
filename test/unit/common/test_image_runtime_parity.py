from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())


class ImageRuntimeParityTest(unittest.TestCase):
    def test_python_canonical_and_cpp_runtime_match(self) -> None:
        cp = subprocess.run(
            ["python3", "tools/verify_image_runtime_parity.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(cp.returncode, 0, msg=cp.stderr)
        lines = [ln.strip() for ln in cp.stdout.replace("\r\n", "\n").split("\n") if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_runtime_parity_check_does_not_leak_png_to_repo_root(self) -> None:
        leaked_root = ROOT / "import_pytra_runtime_png.png"
        leaked_out = ROOT / "work" / "out" / "import_pytra_runtime_png.png"
        for leaked in (leaked_root, leaked_out):
            if leaked.exists():
                leaked.unlink()
        try:
            cp = subprocess.run(
                ["python3", "tools/runtime_parity_check.py", "import_pytra_runtime_png", "--targets", "cpp"],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(cp.returncode, 0, msg=(cp.stderr + "\n" + cp.stdout))
            self.assertFalse(leaked_root.exists())
            self.assertFalse(leaked_out.exists())
        finally:
            for leaked in (leaked_root, leaked_out):
                if leaked.exists():
                    leaked.unlink()


if __name__ == "__main__":
    unittest.main()
