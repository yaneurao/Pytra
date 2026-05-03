from __future__ import annotations

import unittest
from pathlib import Path

from toolchain.compile.lower import lower_east2_to_east3
from toolchain.emit.go.emitter import _is_top_level_type_assertion_expr, emit_go_module
from toolchain.emit.go.types import go_type
from toolchain.parse.py.parse_python import parse_python_file
from toolchain.resolve.py.builtin_registry import load_builtin_registry
from toolchain.resolve.py.resolver import resolve_east1_to_east2


ROOT = Path(__file__).resolve().parents[3]


def _build_east3_for(path: Path) -> dict:
    builtins_path = ROOT / "test" / "include" / "east1" / "py" / "built_in" / "builtins.py.east1"
    containers_path = ROOT / "test" / "include" / "east1" / "py" / "built_in" / "containers.py.east1"
    stdlib_dir = ROOT / "test" / "include" / "east1" / "py" / "std"
    registry = load_builtin_registry(builtins_path, containers_path, stdlib_dir)
    east1 = parse_python_file(str(path))
    resolve_east1_to_east2(east1, registry=registry)
    return lower_east2_to_east3(east1)


class GoSelfhostIfExpTypingTests(unittest.TestCase):
    def test_go_emitter_emits_type_alias_declarations(self) -> None:
        east3 = _build_east3_for(ROOT / "src" / "pytra" / "std" / "json.py")

        go_code = emit_go_module(east3)

        self.assertIn("type JsonVal = any", go_code)

    def test_selfhost_emitter_coerces_isinstance_guarded_jsonval_ternaries(self) -> None:
        east3 = _build_east3_for(ROOT / "src" / "toolchain" / "emit" / "go" / "emitter.py")

        go_code = emit_go_module(east3)

        self.assertIn("if py_truthy(py_is_str(v))", go_code)
        self.assertIn("return v.(string)", go_code)
        self.assertIn("return py_to_int64(v)", go_code)
        self.assertNotIn('func() *JsonVal { if py_is_str(a) { return a }; return "" }()', go_code)
        self.assertNotIn('func() *JsonVal { if py_is_int(v) { return v }; return 0 }()', go_code)
        self.assertNotIn('py_ternary_str(py_is_str(v), v.(string), "")', go_code)

    def test_expr_stmt_discard_only_wraps_top_level_type_assertions(self) -> None:
        self.assertTrue(_is_top_level_type_assertion_expr("value.(string)"))
        self.assertTrue(_is_top_level_type_assertion_expr("any(value).(interface{ marker() })"))
        self.assertFalse(
            _is_top_level_type_assertion_expr(
                "py_print(func() bool { _, ok := any(c).(interface{ marker() }); return ok }())"
            )
        )

    def test_typevar_names_emit_as_dynamic_values(self) -> None:
        self.assertEqual(go_type("T"), "any")
        self.assertEqual(go_type("K"), "any")
        self.assertEqual(go_type("V"), "any")


if __name__ == "__main__":
    unittest.main()
