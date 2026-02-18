# このファイルは `test/unit/test_self_transpile.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PY2CS = ROOT / "src" / "py2cs.py"
SELF_SRC = ROOT / "src" / "py2cs.py"


class SelfTranspileTest(unittest.TestCase):
    def test_can_transpile_transpiler_source(self) -> None:
        # トランスパイラ自身のソースを入力にしても変換が完走できることを検証する。
        with tempfile.TemporaryDirectory() as tmpdir:
            out_cs = Path(tmpdir) / "self_pytrans_transpiler.cs"
            run = subprocess.run(
                ["python", str(PY2CS), str(SELF_SRC), str(out_cs)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(run.returncode, 0, msg=run.stderr)
            self.assertTrue(out_cs.exists())
            self.assertGreater(out_cs.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
