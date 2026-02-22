"""Regression tests for JS/TS runtime type-id dispatch contracts."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class JsTsRuntimeDispatchTest(unittest.TestCase):
    def _run_node(self, script: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "runtime_dispatch_check.js"
            path.write_text(script, encoding="utf-8")
            return subprocess.run(
                ["node", str(path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=30,
            )

    def test_runtime_sources_do_not_use_name_dispatch(self) -> None:
        js_src = (ROOT / "src" / "js_module" / "py_runtime.js").read_text(encoding="utf-8")
        ts_src = (ROOT / "src" / "ts_module" / "py_runtime.ts").read_text(encoding="utf-8")
        self.assertNotIn("constructor.name", js_src)
        self.assertNotIn("constructor.name", ts_src)
        self.assertIn("function pyTypeId", js_src)
        self.assertIn("export function pyTypeId", ts_src)
        self.assertIn("PYTRA_TYPE_ID", js_src)
        self.assertIn("PYTRA_TYPE_ID", ts_src)

    def test_js_runtime_type_id_dispatch_and_hooks(self) -> None:
        script = r"""
const assert = require("assert");
const rt = require(process.cwd() + "/src/js_module/py_runtime.js");

const custom = {
  [rt.PYTRA_TYPE_ID]: 7001,
  [rt.PYTRA_TRUTHY]: () => false,
  [rt.PYTRA_TRY_LEN]: () => 7,
  [rt.PYTRA_STR]: () => "custom",
};

assert.equal(rt.pyTypeId(custom), 7001);
assert.equal(rt.pyBool(custom), false);
assert.equal(rt.pyLen(custom), 7);
assert.equal(rt.pyToString(custom), "custom");

assert.equal(rt.pyBool([]), false);
assert.equal(rt.pyLen({ a: 1, b: 2 }), 2);
assert.equal(rt.pyTypeId("x"), rt.PY_TYPE_STRING);
assert.equal(rt.pyTypeId(1), rt.PY_TYPE_NUMBER);

let threw = false;
try {
  rt.pyLen(123);
} catch (e) {
  threw = true;
}
assert.equal(threw, true);
console.log("ok");
"""
        proc = self._run_node(script)
        self.assertEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
        self.assertIn("ok", proc.stdout)

    def test_ts_runtime_exports_type_id_dispatch_apis(self) -> None:
        src = (ROOT / "src" / "ts_module" / "py_runtime.ts").read_text(encoding="utf-8")
        self.assertIn("export const PYTRA_TYPE_ID", src)
        self.assertIn("export const PYTRA_TRUTHY", src)
        self.assertIn("export const PYTRA_TRY_LEN", src)
        self.assertIn("export const PYTRA_STR", src)
        self.assertIn("export function pyTypeId", src)
        self.assertIn("export function pyTruthy", src)
        self.assertIn("export function pyTryLen", src)
        self.assertIn("export function pyStr", src)
        self.assertIn("switch (typeId)", src)


if __name__ == "__main__":
    unittest.main()
