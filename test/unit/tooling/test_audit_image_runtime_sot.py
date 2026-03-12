from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import audit_image_runtime_sot as audit_mod


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class AuditImageRuntimeSotTest(unittest.TestCase):
    def _scan_single_lang(
        self,
        runtime_root: Path,
        *,
        core_text: str,
        gen_text: str,
        compat_text: str = "",
    ) -> dict[str, object]:
        _write_text(runtime_root / "native" / "built_in" / "py_runtime.fake", core_text)
        _write_text(runtime_root / "generated" / "utils" / "image_runtime.fake", gen_text)
        if compat_text != "":
            _write_text(runtime_root / "pytra" / "compat.fake", compat_text)

        root = runtime_root.parents[2]
        fake_specs = {
            "demo": audit_mod.LangSpec(target="demo", runtime_root="src/runtime/demo"),
        }
        with patch.object(audit_mod, "ROOT", root), patch.object(audit_mod, "LANG_SPECS", fake_specs):
            return audit_mod.run_audit(probe_transpile=False)

    def test_guardrail_accepts_valid_core_and_gen(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            runtime_root = Path(td) / "src" / "runtime" / "demo"
            report = self._scan_single_lang(
                runtime_root,
                core_text="def py_truthy(v):\n    return bool(v)\n",
                gen_text=(
                    "// source: src/pytra/utils/png.py\n"
                    "// generated-by: tools/gen_runtime_from_manifest.py\n"
                    "def __pytra_write_rgb_png():\n"
                    "    pass\n"
                ),
            )
            failures = audit_mod.collect_guardrail_failures(
                report,
                fail_on_core_mix=True,
                fail_on_gen_markers=True,
                fail_on_non_compliant=False,
            )
            self.assertEqual(failures["core_mix"], [])
            self.assertEqual(failures["gen_markers"], [])

    def test_guardrail_detects_core_mix_symbol(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            runtime_root = Path(td) / "src" / "runtime" / "demo"
            report = self._scan_single_lang(
                runtime_root,
                core_text="int png_crc32 = 0;\n",
                gen_text=(
                    "// source: src/pytra/utils/gif.py\n"
                    "// generated-by: tools/gen_runtime_from_manifest.py\n"
                    "def __pytra_save_gif():\n"
                    "    pass\n"
                ),
            )
            failures = audit_mod.collect_guardrail_failures(
                report,
                fail_on_core_mix=True,
                fail_on_gen_markers=True,
                fail_on_non_compliant=False,
            )
            self.assertEqual(failures["core_mix"], ["demo"])

    def test_guardrail_detects_missing_source_marker(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            runtime_root = Path(td) / "src" / "runtime" / "demo"
            report = self._scan_single_lang(
                runtime_root,
                core_text="def py_truthy(v):\n    return bool(v)\n",
                gen_text=(
                    "// generated-by: tools/gen_runtime_from_manifest.py\n"
                    "def __pytra_write_rgb_png():\n"
                    "    pass\n"
                ),
            )
            failures = audit_mod.collect_guardrail_failures(
                report,
                fail_on_core_mix=False,
                fail_on_gen_markers=True,
                fail_on_non_compliant=False,
            )
            self.assertEqual(failures["gen_markers"], ["demo"])

    def test_guardrail_detects_missing_generated_by_marker(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            runtime_root = Path(td) / "src" / "runtime" / "demo"
            report = self._scan_single_lang(
                runtime_root,
                core_text="def py_truthy(v):\n    return bool(v)\n",
                gen_text=(
                    "// source: src/pytra/utils/gif.py\n"
                    "def __pytra_save_gif():\n"
                    "    pass\n"
                ),
            )
            failures = audit_mod.collect_guardrail_failures(
                report,
                fail_on_core_mix=False,
                fail_on_gen_markers=True,
                fail_on_non_compliant=False,
            )
            self.assertEqual(failures["gen_markers"], ["demo"])


if __name__ == "__main__":
    unittest.main()
