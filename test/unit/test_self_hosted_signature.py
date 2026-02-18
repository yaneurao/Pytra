import subprocess
import tempfile
import unittest
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
EAST = ROOT / "src" / "common" / "east.py"
SIG_DIR = ROOT / "test" / "fixtures" / "signature"


class SelfHostedSignatureTest(unittest.TestCase):
    def _run_east(self, src: Path) -> tuple[subprocess.CompletedProcess[str], dict]:
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "out.east.json"
            cp = subprocess.run(
                [
                    "python3",
                    str(EAST),
                    str(src),
                    "-o",
                    str(out),
                    "--parser-backend",
                    "self_hosted",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            payload: dict = {}
            if out.exists():
                payload = json.loads(out.read_text(encoding="utf-8"))
            return cp, payload

    def test_accept_kwonly_marker(self) -> None:
        cp, payload = self._run_east(SIG_DIR / "ok_kwonly.py")
        self.assertEqual(cp.returncode, 0, msg=cp.stderr)
        self.assertEqual(payload.get("ok"), True)

    def test_reject_posonly_marker(self) -> None:
        cp, payload = self._run_east(SIG_DIR / "ng_posonly.py")
        self.assertNotEqual(cp.returncode, 0)
        self.assertEqual(payload.get("ok"), False)
        err = payload.get("error", {})
        self.assertEqual(err.get("kind"), "unsupported_syntax")

    def test_reject_varargs(self) -> None:
        cp, payload = self._run_east(SIG_DIR / "ng_varargs.py")
        self.assertNotEqual(cp.returncode, 0)
        self.assertEqual(payload.get("ok"), False)
        err = payload.get("error", {})
        self.assertEqual(err.get("kind"), "unsupported_syntax")

    def test_reject_kwargs(self) -> None:
        cp, payload = self._run_east(SIG_DIR / "ng_kwargs.py")
        self.assertNotEqual(cp.returncode, 0)
        self.assertEqual(payload.get("ok"), False)
        err = payload.get("error", {})
        self.assertEqual(err.get("kind"), "unsupported_syntax")


if __name__ == "__main__":
    unittest.main()
