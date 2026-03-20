from __future__ import annotations

import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import check_emitter_runtimecall_guardrails as guard_mod


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_allowlist(path: Path, keys: list[str]) -> None:
    lines = [
        "# test allowlist",
        "",
    ] + keys
    _write_text(path, "\n".join(lines) + "\n")


class CheckEmitterRuntimecallGuardrailsTest(unittest.TestCase):
    def test_collect_detects_source_module_math_branch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            emitter = root / "src" / "backends" / "scala" / "emitter" / "scala_native_emitter.py"
            _write_text(emitter, 'if module_name == "math":\n    return "x"\n')
            allowlist_path = root / "tools" / "emitter_runtimecall_guardrails_allowlist.txt"
            _write_allowlist(allowlist_path, [])
            with patch.object(guard_mod, "ROOT", root), patch.object(
                guard_mod, "BACKENDS_ROOT", root / "src" / "backends"
            ), patch.object(guard_mod, "ALLOWLIST_PATH", allowlist_path):
                findings = guard_mod._collect_findings()
        self.assertTrue(any(item.symbol == "math" and item.kind == "source_module_branch" for item in findings))

    def test_collect_detects_pymath_helper_branch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            emitter = root / "src" / "backends" / "swift" / "emitter" / "swift_native_emitter.py"
            _write_text(emitter, 'if runtime_symbol.startswith("pyMath"):\n    return "x"\n')
            allowlist_path = root / "tools" / "emitter_runtimecall_guardrails_allowlist.txt"
            _write_allowlist(allowlist_path, [])
            with patch.object(guard_mod, "ROOT", root), patch.object(
                guard_mod, "BACKENDS_ROOT", root / "src" / "backends"
            ), patch.object(guard_mod, "ALLOWLIST_PATH", allowlist_path):
                findings = guard_mod._collect_findings()
        self.assertTrue(any(item.symbol == "pyMath*" and item.kind == "helper_name_branch" for item in findings))

    def test_collect_detects_source_binding_utils_prefix_branch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            emitter = root / "src" / "backends" / "java" / "emitter" / "java_native_emitter.py"
            _write_text(emitter, 'if binding_module.startswith("pytra.utils."):\n    return "x"\n')
            allowlist_path = root / "tools" / "emitter_runtimecall_guardrails_allowlist.txt"
            _write_allowlist(allowlist_path, [])
            with patch.object(guard_mod, "ROOT", root), patch.object(
                guard_mod, "BACKENDS_ROOT", root / "src" / "backends"
            ), patch.object(guard_mod, "ALLOWLIST_PATH", allowlist_path):
                findings = guard_mod._collect_findings()
        self.assertTrue(any(item.symbol == "pytra.utils.*" and item.kind == "source_module_prefix" for item in findings))

    def test_collect_allows_canonical_runtime_module_prefix_branch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            emitter = root / "src" / "backends" / "java" / "emitter" / "java_native_emitter.py"
            _write_text(emitter, 'if runtime_module.startswith("pytra.utils."):\n    return "x"\n')
            allowlist_path = root / "tools" / "emitter_runtimecall_guardrails_allowlist.txt"
            _write_allowlist(allowlist_path, [])
            with patch.object(guard_mod, "ROOT", root), patch.object(
                guard_mod, "BACKENDS_ROOT", root / "src" / "backends"
            ), patch.object(guard_mod, "ALLOWLIST_PATH", allowlist_path):
                findings = guard_mod._collect_findings()
        self.assertEqual(findings, [])

    def test_collect_detects_multiline_dispatch_table(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            emitter = root / "src" / "backends" / "ruby" / "emitter" / "ruby_native_emitter.py"
            _write_text(
                emitter,
                "_RESOLVED_RUNTIME_HELPERS = {\n"
                '    "write_rgb_png": "PngHelper.pyWriteRGBPNG",\n'
                "}\n",
            )
            allowlist_path = root / "tools" / "emitter_runtimecall_guardrails_allowlist.txt"
            _write_allowlist(allowlist_path, [])
            with patch.object(guard_mod, "ROOT", root), patch.object(
                guard_mod, "BACKENDS_ROOT", root / "src" / "backends"
            ), patch.object(guard_mod, "ALLOWLIST_PATH", allowlist_path), patch.object(
                guard_mod, "STRICT_BACKENDS", {"java"}
            ):
                findings = guard_mod._collect_findings()
        self.assertTrue(any(item.symbol == "write_rgb_png" for item in findings))
        self.assertTrue(any(item.kind.startswith("dispatch_table:") for item in findings))

    def test_main_fails_for_strict_backend_even_when_allowlisted(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            emitter = root / "src" / "backends" / "java" / "emitter" / "java_native_emitter.py"
            _write_text(emitter, 'if module_name == "math":\n    return "x"\n')
            key = "src/toolchain/emit/java/emitter/java_native_emitter.py:1:math"
            allowlist_path = root / "tools" / "emitter_runtimecall_guardrails_allowlist.txt"
            _write_allowlist(allowlist_path, [key])

            with patch.object(guard_mod, "ROOT", root), patch.object(
                guard_mod, "BACKENDS_ROOT", root / "src" / "backends"
            ), patch.object(guard_mod, "ALLOWLIST_PATH", allowlist_path), patch.object(
                guard_mod, "STRICT_BACKENDS", {"java"}
            ), patch.object(
                sys, "argv", ["check_emitter_runtimecall_guardrails.py"]
            ), patch(
                "sys.stdout", new_callable=io.StringIO
            ):
                rc = guard_mod.main()
        self.assertEqual(rc, 1)

    def test_main_passes_when_non_strict_findings_are_allowlisted(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            emitter = root / "src" / "backends" / "ruby" / "emitter" / "ruby_native_emitter.py"
            _write_text(emitter, 'if runtime_call == "perf_counter":\n    return "x"\n')
            key = "src/toolchain/emit/ruby/emitter/ruby_native_emitter.py:1:perf_counter"
            allowlist_path = root / "tools" / "emitter_runtimecall_guardrails_allowlist.txt"
            _write_allowlist(allowlist_path, [key])

            with patch.object(guard_mod, "ROOT", root), patch.object(
                guard_mod, "BACKENDS_ROOT", root / "src" / "backends"
            ), patch.object(guard_mod, "ALLOWLIST_PATH", allowlist_path), patch.object(
                guard_mod, "STRICT_BACKENDS", {"java"}
            ), patch.object(
                sys, "argv", ["check_emitter_runtimecall_guardrails.py"]
            ), patch(
                "sys.stdout", new_callable=io.StringIO
            ):
                rc = guard_mod.main()
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
