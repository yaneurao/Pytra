# このファイルは `test/test_transpile_cases.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PY2CS = ROOT / "src" / "py2cs.py"
PY_DIR = ROOT / "test" / "py"
CS_DIR = ROOT / "test" / "cs"


class TranspileGoldenTest(unittest.TestCase):
    def _normalize_cs(self, text: str) -> str:
        # 先頭の説明コメント（// ...）は比較対象から除外する。
        lines = text.splitlines()
        idx = 0
        while idx < len(lines) and (lines[idx].startswith("//") or lines[idx].strip() == ""):
            idx += 1
        return "\n".join(lines[idx:]).strip() + "\n"

    def test_cases_match_expected_cs(self) -> None:
        # すべてのcase入力を再変換し、期待するC#との差分がないことを確認する。
        py_cases = sorted(PY_DIR.glob("case*.py"))
        self.assertEqual(len(py_cases), 100, "Expected exactly 100 Python test cases")

        for py_case in py_cases:
            with self.subTest(case=py_case.name):
                expected_cs = CS_DIR / f"{py_case.stem}.cs"
                self.assertTrue(expected_cs.exists(), f"Missing expected C# file: {expected_cs}")

                with tempfile.TemporaryDirectory() as tmpdir:
                    generated_cs = Path(tmpdir) / f"{py_case.stem}.cs"
                    run = subprocess.run(
                        ["python", str(PY2CS), str(py_case), str(generated_cs)],
                        cwd=ROOT,
                        capture_output=True,
                        text=True,
                    )
                    self.assertEqual(run.returncode, 0, msg=run.stderr)

                    actual = generated_cs.read_text(encoding="utf-8")
                    expected = expected_cs.read_text(encoding="utf-8")
                    self.assertEqual(self._normalize_cs(actual), self._normalize_cs(expected))


if __name__ == "__main__":
    unittest.main()
