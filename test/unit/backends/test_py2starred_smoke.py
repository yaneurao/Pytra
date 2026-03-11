"""All-target smoke for representative starred tuple call lowering."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))


TARGET_EXT: dict[str, str] = {
    "cpp": ".cpp",
    "rs": ".rs",
    "cs": ".cs",
    "js": ".js",
    "ts": ".ts",
    "go": ".go",
    "java": ".java",
    "swift": ".swift",
    "kotlin": ".kt",
    "ruby": ".rb",
    "lua": ".lua",
    "scala": ".scala",
    "php": ".php",
    "nim": ".nim",
}


def find_fixture_case(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixtures").rglob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(f"missing fixture: {stem}")
    return matches[0]


def run_py2x(target: str, fixture: Path, output_path: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    py_path = str(ROOT / "src")
    old = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
    cmd = [sys.executable, "src/py2x.py", "--target", target, str(fixture), "-o", str(output_path)]
    return subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True)


class Py2StarredSmokeTest(unittest.TestCase):
    def test_starred_call_tuple_fixture_transpiles_for_all_targets(self) -> None:
        fixture = find_fixture_case("starred_call_tuple_basic")
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            for target, ext in TARGET_EXT.items():
                with self.subTest(target=target):
                    out = base / f"starred_call_tuple_basic_{target}{ext}"
                    proc = run_py2x(target, fixture, out)
                    self.assertEqual(proc.returncode, 0, msg=f"{target}\n{proc.stdout}\n{proc.stderr}")
                    text = out.read_text(encoding="utf-8")
                    self.assertNotIn("*rgb", text, msg=target)
                    if text.strip() != "":
                        self.assertIn("mix_rgb", text, msg=target)


if __name__ == "__main__":
    unittest.main()
