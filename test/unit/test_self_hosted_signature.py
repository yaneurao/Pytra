import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.pytra.compiler.east_parts.core import EastBuildError, convert_path

SIG_DIR = ROOT / "test" / "fixtures" / "signature"


class SelfHostedSignatureTest(unittest.TestCase):
    def _run_east(self, src: Path) -> tuple[int, dict]:
        try:
            east = convert_path(src, parser_backend="self_hosted")
        except SyntaxError as exc:
            err = {
                "kind": "unsupported_syntax",
                "message": str(exc),
                "source_span": {
                    "lineno": exc.lineno,
                    "col": exc.offset,
                    "end_lineno": exc.end_lineno,
                    "end_col": exc.end_offset,
                },
                "hint": "Fix Python syntax errors before EAST conversion.",
            }
            return 1, {"ok": False, "error": err}
        except RuntimeError as exc:
            txt = str(exc)
            kind = "unsupported_syntax"
            msg = txt
            hint = ""
            ln = None
            col = None
            if ": " in txt:
                kind_head, rest = txt.split(": ", 1)
                if kind_head != "":
                    kind = kind_head
                msg = rest
            if " hint=" in msg:
                msg, hint = msg.split(" hint=", 1)
            if " at " in msg:
                msg_core, pos_txt = msg.rsplit(" at ", 1)
                msg = msg_core
                if ":" in pos_txt:
                    ln_txt, col_txt = pos_txt.split(":", 1)
                    if ln_txt.isdigit():
                        ln = int(ln_txt)
                    if col_txt.isdigit():
                        col = int(col_txt)
            err = {"kind": kind, "message": msg, "hint": hint}
            if ln is not None and col is not None:
                err["source_span"] = {"lineno": ln, "col": col}
            return 1, {"ok": False, "error": err}
        except EastBuildError as exc:
            return 1, {"ok": False, "error": exc.to_payload()}
        return 0, {"ok": True, "east": east}

    def test_accept_kwonly_marker(self) -> None:
        rc, payload = self._run_east(SIG_DIR / "ok_kwonly.py")
        self.assertEqual(rc, 0)
        self.assertEqual(payload.get("ok"), True)

    def test_reject_posonly_marker(self) -> None:
        rc, payload = self._run_east(SIG_DIR / "ng_posonly.py")
        self.assertNotEqual(rc, 0)
        self.assertEqual(payload.get("ok"), False)
        err = payload.get("error", {})
        self.assertEqual(err.get("kind"), "unsupported_syntax")

    def test_reject_varargs(self) -> None:
        rc, payload = self._run_east(SIG_DIR / "ng_varargs.py")
        self.assertNotEqual(rc, 0)
        self.assertEqual(payload.get("ok"), False)
        err = payload.get("error", {})
        self.assertEqual(err.get("kind"), "unsupported_syntax")

    def test_reject_kwargs(self) -> None:
        rc, payload = self._run_east(SIG_DIR / "ng_kwargs.py")
        self.assertNotEqual(rc, 0)
        self.assertEqual(payload.get("ok"), False)
        err = payload.get("error", {})
        self.assertEqual(err.get("kind"), "unsupported_syntax")

    def test_accept_untyped_parameter(self) -> None:
        rc, payload = self._run_east(SIG_DIR / "ok_untyped_param.py")
        self.assertEqual(rc, 0)
        self.assertEqual(payload.get("ok"), True)
        east = payload.get("east", {})
        body = east.get("body", [])
        fn = None
        for stmt in body:
            if isinstance(stmt, dict) and stmt.get("kind") == "FunctionDef" and stmt.get("name") == "twice":
                fn = stmt
                break
        self.assertIsNotNone(fn)
        self.assertEqual(fn.get("arg_types", {}).get("x"), "unknown")

    def test_accept_class_inline_method(self) -> None:
        rc, payload = self._run_east(SIG_DIR / "ok_class_inline_method.py")
        self.assertEqual(rc, 0)
        self.assertEqual(payload.get("ok"), True)
        east = payload.get("east", {})
        body = east.get("body", [])
        cls = None
        for stmt in body:
            if isinstance(stmt, dict) and stmt.get("kind") == "ClassDef" and stmt.get("name") == "Value":
                cls = stmt
                break
        self.assertIsNotNone(cls)
        cls_body = cls.get("body", [])
        method = None
        for item in cls_body:
            if isinstance(item, dict) and item.get("kind") == "FunctionDef" and item.get("name") == "__pow__":
                method = item
                break
        self.assertIsNotNone(method)
        method_body = method.get("body", [])
        self.assertGreater(len(method_body), 0)
        self.assertEqual(method_body[0].get("kind"), "Return")

    def test_reject_object_receiver_access(self) -> None:
        rc, payload = self._run_east(SIG_DIR / "ng_object_receiver.py")
        self.assertNotEqual(rc, 0)
        self.assertEqual(payload.get("ok"), False)
        err = payload.get("error", {})
        self.assertEqual(err.get("kind"), "unsupported_syntax")
        self.assertIn("object receiver", str(err.get("message", "")))


if __name__ == "__main__":
    unittest.main()
