"""py2lua (EAST based) smoke tests."""

# Language-specific smoke suite.
# Shared py2x target-parameterized checks live in test_py2x_smoke_common.py.

from __future__ import annotations

import json
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
if str(ROOT / "test" / "unit") not in sys.path:
    sys.path.insert(0, str(ROOT / "test" / "unit"))
if str(ROOT / "test" / "unit" / "backends") not in sys.path:
    sys.path.insert(0, str(ROOT / "test" / "unit" / "backends"))

from toolchain.emit.lua.emitter import load_lua_profile, transpile_to_lua, transpile_to_lua_native
from toolchain.misc.transpile_cli import load_east3_document
from src.toolchain.compile.core_entrypoints import convert_path
from comment_fidelity import assert_no_generated_comments
from relative_import_longtail_smoke_support import (
    relative_import_longtail_expected_rewrite,
    relative_import_longtail_scenarios,
    transpile_relative_import_longtail_via_module_graph,
    transpile_relative_import_longtail_project,
    transpile_relative_import_longtail_expect_failure,
)


LUA_RELATIVE_IMPORT_REWRITE_MARKER = "helper.f()"
LUA_RELATIVE_IMPORT_MODULE_ALIAS_FORBIDDEN = "h.f()"
LUA_RELATIVE_IMPORT_SYMBOL_ALIAS_FORBIDDEN = "g()"


def load_east(
    input_path: Path,
    parser_backend: str = "self_hosted",
    east_stage: str = "3",
    object_dispatch_mode: str = "native",
    east3_opt_level: str = "1",
    east3_opt_pass: str = "",
    dump_east3_before_opt: str = "",
    dump_east3_after_opt: str = "",
    dump_east3_opt_trace: str = "",
):
    if east_stage != "3":
        raise RuntimeError("unsupported east_stage: " + east_stage)
    doc3 = load_east3_document(
        input_path,
        parser_backend=parser_backend,
        object_dispatch_mode=object_dispatch_mode,
        east3_opt_level=east3_opt_level,
        east3_opt_pass=east3_opt_pass,
        dump_east3_before_opt=dump_east3_before_opt,
        dump_east3_after_opt=dump_east3_after_opt,
        dump_east3_opt_trace=dump_east3_opt_trace,
        target_lang="lua",
    )
    return doc3 if isinstance(doc3, dict) else {}


def find_fixture_case(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixtures").rglob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(f"missing fixture: {stem}")
    return matches[0]


class Py2LuaSmokeTest(unittest.TestCase):
    def test_load_lua_profile_contains_core_sections(self) -> None:
        profile = load_lua_profile()
        self.assertIn("types", profile)
        self.assertIn("operators", profile)
        self.assertIn("syntax", profile)
        self.assertIn("runtime_calls", profile)

    def test_lua_runtime_source_path_is_migrated(self) -> None:
        runtime_path = ROOT / "src" / "runtime" / "lua" / "native" / "built_in" / "py_runtime.lua"
        image_runtime = ROOT / "src" / "runtime" / "lua" / "generated" / "utils" / "image_runtime.lua"
        delete_target_path = ROOT / "src" / "runtime" / "lua" / "pytra"
        legacy_path = ROOT / "src" / "runtime" / "lua" / "pytra-core"
        self.assertTrue(runtime_path.exists())
        self.assertTrue(image_runtime.exists())
        self.assertFalse(delete_target_path.exists())
        self.assertFalse(legacy_path.exists())

    def test_lua_generated_std_baseline_source_guard_materializes_new_compare_modules(self) -> None:
        runtime_root = ROOT / "src" / "runtime" / "lua" / "generated"
        guarded_targets = {
            runtime_root / "built_in" / "type_id.lua": ("function py_tid_runtime_type_id(",),
            runtime_root / "std" / "argparse.lua": ("ArgumentParser = {}", "function ArgumentParser:parse_args("),
            runtime_root / "std" / "re.lua": ("function match(", "function sub("),
            runtime_root / "utils" / "assertions.lua": ("function py_assert_true(", "function py_assert_eq("),
            runtime_root / "utils" / "gif.lua": ("function save_gif(",),
            runtime_root / "utils" / "png.lua": ("function write_rgb_png(",),
        }
        for path, needles in guarded_targets.items():
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                text = path.read_text(encoding="utf-8")
                self.assertIn("AUTO-GENERATED FILE. DO NOT EDIT.", text)
                for needle in needles:
                    self.assertIn(needle, text)
        self.assertFalse((runtime_root / "utils" / "gif_helper.lua").exists())
        self.assertFalse((runtime_root / "utils" / "png_helper.lua").exists())
        for lint_path in (
            runtime_root / "built_in" / "type_id.lua",
            runtime_root / "std" / "argparse.lua",
            runtime_root / "std" / "re.lua",
            runtime_root / "utils" / "assertions.lua",
        ):
            with self.subTest(lint_path=lint_path.relative_to(ROOT).as_posix()):
                proc = subprocess.run(
                    ["luac", "-p", str(lint_path)],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_lua_cli_staged_runtime_lane_resolves_runtime_helpers(self) -> None:
        fixture = find_fixture_case("add")
        with tempfile.TemporaryDirectory() as td:
            out_lua = Path(td) / "add.lua"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/pytra-cli.py", "--target", "lua", str(fixture), "-o", str(out_lua)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            staged_runtime = (Path(td) / "py_runtime.lua").resolve()
            self.assertTrue(staged_runtime.exists())
            code = "\n".join(
                [
                    f"dofile({staged_runtime.as_posix()!r})",
                    "io.write((__pytra_truthy({1}) and 'lua-ok' or 'lua-missing') .. '\\n')",
                ]
            )
            proc = subprocess.run(
                ["lua", "-"],
                cwd=ROOT,
                input=code,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(proc.stdout, "lua-ok\n")

    def test_transpile_if_else_fixture_contains_lua_if(self) -> None:
        fixture = find_fixture_case("if_else")
        east = load_east(fixture, parser_backend="self_hosted")
        lua = transpile_to_lua_native(east)
        self.assertIn("function abs_like(n)", lua)
        self.assertIn("if (n < 0) then", lua)
        self.assertIn("return (-n)", lua)
        self.assertIn("else", lua)

    def test_lambda_fixture_renders_function_for_lua(self) -> None:
        fixture = find_fixture_case("lambda_basic")
        east = load_east(fixture, parser_backend="self_hosted")
        lua = transpile_to_lua_native(east)
        self.assertIn("function(x) return (x + base) end", lua)
        self.assertIn("function() return true end", lua)

    def test_longtail_bundle_representative_fixtures_transpile_for_lua(self) -> None:
        for stem in (
            "tuple_assign",
            "lambda_basic",
            "comprehension",
            "try_raise",
            "enumerate_basic",
            "json_extended",
            "pathlib_extended",
            "enum_extended",
            "argparse_extended",
            "pytra_std_import_math",
            "re_extended",
        ):
            with self.subTest(stem=stem):
                fixture = find_fixture_case(stem)
                east = load_east(fixture, parser_backend="self_hosted")
                lua = transpile_to_lua_native(east)
                self.assertTrue(lua.strip())

    def test_import_lowering_maps_math_runtime_via_generic_extern_metadata(self) -> None:
        src = (
            "import math\n"
            "from math import pi, sqrt\n"
            "def f() -> float:\n"
            "    return sqrt(pi)\n"
            "def g() -> float:\n"
            "    return math.sin(pi)\n"
        )
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "imports_math.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py, parser_backend="self_hosted")
            lua = transpile_to_lua_native(east)
        self.assertIn("local math = { ", lua)
        self.assertIn("pi = pyMathPi()", lua)
        self.assertIn("sin = pyMathSin", lua)
        self.assertIn("sqrt = pyMathSqrt", lua)
        self.assertIn("return sqrt(pi)", lua)
        self.assertIn("return math.sin(pi)", lua)
        self.assertNotIn("__pytra_math_module()", lua)

    def test_import_lowering_maps_os_sys_glob_runtime_via_generic_extern_metadata(self) -> None:
        src = (
            "import os\n"
            "from os_path import join\n"
            "from sys import write_stdout\n"
            "from glob import glob\n"
            "def f() -> None:\n"
            "    _ = os.getcwd()\n"
            "    _ = join('a', 'b')\n"
            "    _ = glob('*.png')\n"
            "    write_stdout('ok')\n"
        )
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "imports_os_sys_glob.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py, parser_backend="self_hosted")
            lua = transpile_to_lua_native(east)
        self.assertIn("local os = { ", lua)
        self.assertIn("getcwd = function() return '.' end", lua)
        self.assertIn("local join = function(a, b) return tostring(a) .. '/' .. tostring(b) end", lua)
        self.assertIn("local write_stdout = function(text) io.write(text) end", lua)
        self.assertIn("local glob = function(_pattern) return {} end", lua)
        self.assertNotIn('mod == "pytra.std.os"', lua)

    def test_representative_property_method_call_fixture_transpiles(self) -> None:
        try:
            from test.unit.backends.representative_contract_support import (
                assert_no_representative_escape,
            )
        except ModuleNotFoundError:
            from representative_contract_support import assert_no_representative_escape

        fixture = find_fixture_case("property_method_call")
        east = load_east(fixture, parser_backend="self_hosted")
        lua = transpile_to_lua_native(east)
        assert_no_representative_escape(self, lua, backend="lua", fixture="property_method_call")

    def test_representative_list_bool_index_fixture_transpiles(self) -> None:
        try:
            from test.unit.backends.representative_contract_support import (
                assert_no_representative_escape,
            )
        except ModuleNotFoundError:
            from representative_contract_support import assert_no_representative_escape

        fixture = find_fixture_case("list_bool_index")
        east = load_east(fixture, parser_backend="self_hosted")
        lua = transpile_to_lua_native(east)
        assert_no_representative_escape(self, lua, backend="lua", fixture="list_bool_index")

    def test_cli_relative_import_support_rollout_scenarios_transpile_for_lua(self) -> None:
        for scenario_id in ("parent_module_alias", "parent_symbol_alias"):
            with self.subTest(scenario_id=scenario_id):
                lua = transpile_relative_import_longtail_project("lua", scenario_id)
                positive, forbidden = relative_import_longtail_expected_rewrite(scenario_id)
                self.assertEqual(positive, LUA_RELATIVE_IMPORT_REWRITE_MARKER)
                if scenario_id == "parent_module_alias":
                    self.assertEqual(forbidden, LUA_RELATIVE_IMPORT_MODULE_ALIAS_FORBIDDEN)
                    self.assertIn("helper.f()", lua)
                    self.assertNotIn("h.f()", lua)
                else:
                    self.assertEqual(forbidden, LUA_RELATIVE_IMPORT_SYMBOL_ALIAS_FORBIDDEN)
                    self.assertIn("helper.f()", lua)
                    self.assertNotIn("g()", lua)
                self.assertNotIn("(not yet mapped)", lua)

    def test_cli_relative_import_support_rollout_fail_closed_for_wildcard_on_lua(self) -> None:
        err = transpile_relative_import_longtail_expect_failure(
            "lua",
            "from ..helper import *",
            "f()",
        )
        self.assertIn("unsupported relative import form: wildcard import", err)
        self.assertIn("lua native emitter", err)

    def test_cli_relative_import_support_rollout_module_graph_wildcard_for_lua(self) -> None:
        lua = transpile_relative_import_longtail_via_module_graph(
            target="lua",
            import_form="from ..helper import *",
            body_text="def call() -> int:\n    return f()\n",
        )
        self.assertIn("helper.f()", lua)
        self.assertNotIn("unsupported relative import form: wildcard import", lua)

    def test_module_leading_comments_are_emitted(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "leading_comment.lua_case.py"
            src_py.write_text(
                "# leading comment 1\n"
                "# leading comment 2\n"
                "def f() -> int:\n"
                "    return 1\n"
                "if __name__ == '__main__':\n"
                "    print(f())\n",
                encoding="utf-8",
            )
            east = load_east(src_py, parser_backend="self_hosted")
            lua = transpile_to_lua_native(east)
        assert_no_generated_comments(self, lua)
        self.assertIn("-- leading comment 1", lua)
        self.assertIn("-- leading comment 2", lua)

    def test_main_guard_calls_renamed_pytra_main_function(self) -> None:
        src = (
            "def main() -> None:\n"
            "    print(1)\n"
            "if __name__ == '__main__':\n"
            "    main()\n"
        )
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "main_guard.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py, parser_backend="self_hosted")
            lua = transpile_to_lua_native(east)
        self.assertIn("function __pytra_main()", lua)
        self.assertIn("__pytra_main()", lua)
        self.assertNotIn("\nmain()\n", lua)

    def test_transpile_for_range_fixture_contains_static_for(self) -> None:
        fixture = find_fixture_case("for_range")
        east = load_east(fixture, parser_backend="self_hosted")
        lua = transpile_to_lua_native(east)
        self.assertIn("function sum_range_29(n)", lua)
        self.assertIn("local total = 0", lua)
        self.assertIn("for i = 0, n - 1 do", lua)
        self.assertIn("total = total + i", lua)

    def test_append_chain_is_compacted_with_table_move(self) -> None:
        src = (
            "def f() -> list[int]:\n"
            "    xs: list[int] = []\n"
            "    xs.append(1)\n"
            "    xs.append(2)\n"
            "    xs.append(3)\n"
            "    return xs\n"
        )
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "append_chain.lua_case.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py, parser_backend="self_hosted")
            lua = transpile_to_lua_native(east)
        self.assertIn("table.move({1, 2, 3}, 1, 3, #(xs) + 1, xs)", lua)

    def test_inheritance_virtual_dispatch_lowers_super_to_base_method_call(self) -> None:
        fixture = find_fixture_case("inheritance_virtual_dispatch_multilang")
        east = load_east(fixture, parser_backend="self_hosted")
        lua = transpile_to_lua_native(east)
        self.assertIn("Dog.speak(self)", lua)
        self.assertNotIn("super()", lua)

    def test_lua_native_emitter_fail_closed_on_unresolved_stdlib_runtime_call(self) -> None:
        east = {
            "kind": "Module",
            "east_stage": 3,
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "_case_main",
                    "arg_order": [],
                    "arg_types": {},
                    "return_type": "None",
                    "body": [
                        {
                            "kind": "Expr",
                            "value": {
                                "kind": "Call",
                                "func": {"kind": "Name", "id": "save_gif"},
                                "args": [],
                                "keywords": [],
                                "semantic_tag": "stdlib.fn.save_gif",
                            },
                        }
                    ],
                }
            ],
            "main_guard_body": [],
            "meta": {},
        }
        with self.assertRaises(RuntimeError) as cm:
            transpile_to_lua_native(east)
        self.assertIn("unresolved stdlib runtime call", str(cm.exception))

    def test_transpile_downcount_range_fixture_uses_descending_upper_bound(self) -> None:
        fixture = find_fixture_case("range_downcount_len_minus1")
        east = load_east(fixture, parser_backend="self_hosted")
        lua = transpile_to_lua_native(east)
        self.assertIn("for i = (#(xs) - 1), ((-1)) + 1, (-1) do", lua)
        self.assertNotIn("for i = (#(xs) - 1), ((-1)) - 1, (-1) do", lua)

    def test_py2lua_does_not_import_src_common(self) -> None:
        src = (ROOT / "src" / "pytra-cli.py").read_text(encoding="utf-8")
        self.assertNotIn("src.common", src)
        self.assertNotIn("from common.", src)

    def test_lowering_supports_while_loop_and_augassign(self) -> None:
        src = (
            "def f(n: int) -> int:\n"
            "    i: int = 0\n"
            "    s: int = 0\n"
            "    while i < n:\n"
            "        s += i\n"
            "        i += 1\n"
            "    return s\n"
        )
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "while_loop.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py, parser_backend="self_hosted")
            lua = transpile_to_lua_native(east)
        self.assertIn("while (i < n) do", lua)
        self.assertIn("s = s + i", lua)
        self.assertIn("i = i + 1", lua)

    def test_lowering_supports_dict_and_subscript(self) -> None:
        src = (
            "def f() -> int:\n"
            "    d = {'x': 7}\n"
            "    a = [10, 20, 30]\n"
            "    return d['x'] + a[1]\n"
        )
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "dict_subscript.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py, parser_backend="self_hosted")
            lua = transpile_to_lua_native(east)
        self.assertIn('d = { ["x"] = 7 }', lua)
        self.assertIn('return (d["x"] + a[2])', lua)

    def test_lowering_supports_negative_subscript(self) -> None:
        src = (
            "def f(xs: list[int]) -> int:\n"
            "    return xs[-1]\n"
        )
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "negative_subscript.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py, parser_backend="self_hosted")
            lua = transpile_to_lua_native(east)
        self.assertIn("return xs[(#(xs) + (-1) + 1)]", lua)

    def test_lowering_supports_dict_get_and_str_predicates(self) -> None:
        src = (
            "def f(d: dict[str, int], s: str) -> bool:\n"
            "    x = d.get(s, 0)\n"
            "    return s.isdigit() or (s.isalpha() and x >= 0)\n"
        )
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "dict_get_str_pred.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py, parser_backend="self_hosted")
            lua = transpile_to_lua_native(east)
        self.assertIn("(function(__tbl, __key, __default) local __val = __tbl[__key]; if __val == nil then return __default end; return __val end)(d, s, 0)", lua)
        self.assertIn("__pytra_str_isdigit(s)", lua)
        self.assertIn("__pytra_str_isalpha(s)", lua)

    def test_ref_container_args_materialize_value_path_with_table_copy(self) -> None:
        src = (
            "def f(xs: list[int], ys: dict[str, int]) -> int:\n"
            "    a: list[int] = xs\n"
            "    b: dict[str, int] = ys\n"
            "    a.append(1)\n"
            "    b['k'] = 2\n"
            "    return len(a) + len(b)\n"
        )
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "ref_materialize.lua_case.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py, parser_backend="self_hosted")
            lua = transpile_to_lua_native(east)
        self.assertIn(
            "local a = (function(__src) local __out = {}; for __i = 1, #__src do __out[__i] = __src[__i] end; return __out end)(xs)",
            lua,
        )
        self.assertIn(
            "local b = (function(__src) local __out = {}; for __k, __v in pairs(__src) do __out[__k] = __v end; return __out end)(ys)",
            lua,
        )

    def test_lowering_supports_in_notin_via_contains_helper(self) -> None:
        src = (
            "def f(d: dict[str, int], xs: list[int], k: str, v: int) -> bool:\n"
            "    return (k in d) and (v in xs) and (k not in 'abc')\n"
        )
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "contains_ops.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py, parser_backend="self_hosted")
            lua = transpile_to_lua_native(east)
        self.assertIn("__pytra_contains(d, k)", lua)
        self.assertIn("__pytra_contains(xs, v)", lua)
        self.assertIn("(not __pytra_contains(\"abc\", k))", lua)

    def test_while_on_typed_list_uses_python_truthiness(self) -> None:
        src = (
            "def f(xs: list[int]) -> int:\n"
            "    c = 0\n"
            "    while xs:\n"
            "        xs.pop()\n"
            "        c += 1\n"
            "    return c\n"
        )
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "while_truthy_list.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py, parser_backend="self_hosted")
            lua = transpile_to_lua_native(east)
        self.assertIn("while __pytra_truthy(xs) do", lua)

    def test_lowering_supports_bytes_constructor(self) -> None:
        src = (
            "def f() -> int:\n"
            "    b = bytes([1, 2, 3])\n"
            "    return len(b)\n"
        )
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "bytes_ctor.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py, parser_backend="self_hosted")
            lua = transpile_to_lua_native(east)
        self.assertIn("__pytra_bytes({ 1, 2, 3 })", lua)
        self.assertNotIn("string.byte(__v, __i)", lua)

    def test_sample01_prefers_runtime_numeric_and_bytearray_helpers(self) -> None:
        sample = ROOT / "sample" / "py" / "01_mandelbrot.py"
        east = load_east(sample, parser_backend="self_hosted")
        lua = transpile_to_lua_native(east)
        self.assertIn("local pixels = __pytra_bytearray()", lua)
        self.assertIn("local __hoisted_cast_1 = __pytra_float((height - 1))", lua)
        self.assertIn("local __hoisted_cast_2 = __pytra_float((width - 1))", lua)
        self.assertIn("local __hoisted_cast_3 = __pytra_float(max_iter)", lua)
        self.assertIn("local r = __pytra_int((255.0 * (t * t)))", lua)
        self.assertIn("local g = __pytra_int((255.0 * t))", lua)
        self.assertIn("local b = __pytra_int((255.0 * (1.0 - t)))", lua)
        self.assertNotIn("math.floor(tonumber((255.0 * (t * t))) or 0)", lua)
        self.assertIn("local r", lua)
        self.assertIn("local g", lua)
        self.assertIn("local b", lua)
        self.assertNotIn("local r = nil", lua)
        self.assertNotIn("local g = nil", lua)
        self.assertNotIn("local b = nil", lua)
        self.assertIn("for i = 0, max_iter - 1 do", lua)
        self.assertIn("for y = 0, height - 1 do", lua)
        self.assertIn("for x = 0, width - 1 do", lua)
        self.assertNotIn("::__pytra_continue_", lua)

    def test_lowering_supports_sequence_repeat(self) -> None:
        src = (
            "def f(n: int) -> list[int]:\n"
            "    return [0] * n\n"
        )
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "seq_repeat.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py, parser_backend="self_hosted")
            lua = transpile_to_lua_native(east)
        self.assertIn("__pytra_repeat_seq({ 0 }, n)", lua)

    def test_lowering_supports_enumerate_and_max(self) -> None:
        src = (
            "def f(xs: list[int]) -> int:\n"
            "    best = 0\n"
            "    for i, v in enumerate(xs):\n"
            "        best = max(best, i + v)\n"
            "    return best\n"
        )
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "enumerate_max.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py, parser_backend="self_hosted")
            lua = transpile_to_lua_native(east)
        self.assertIn("ipairs((function(__v) local __out = {}; for __i = 1, #__v do table.insert(__out, { __i - 1, __v[__i] }) end; return __out end)(xs))", lua)
        self.assertIn("local i = __it_", lua)
        self.assertIn("local v = __it_", lua)
        self.assertIn("best = _G.math.max(best, (i + v))", lua)

    def test_objbool_on_typed_list_checks_emptiness(self) -> None:
        src = (
            "def f() -> bool:\n"
            "    xs: list[int] = []\n"
            "    return bool(xs)\n"
        )
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "objbool_list.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py, parser_backend="self_hosted")
            lua = transpile_to_lua_native(east)
        self.assertIn("return __pytra_truthy(xs)", lua)

    def test_lowering_supports_ifexp_joinedstr_and_attribute_call(self) -> None:
        src = (
            "import math\n"
            "def f(flag: bool, x: int) -> str:\n"
            "    y = x if flag else 0\n"
            "    z = math.sqrt(9)\n"
            "    return f'v={y}:{z}'\n"
        )
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "ifexp_joinedstr_attr.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py, parser_backend="self_hosted")
            lua = transpile_to_lua_native(east)
        self.assertIn(
            "local y = (function() if __pytra_truthy(flag) then return (x) else return (0) end end)()",
            lua,
        )
        self.assertIn("z = math.sqrt(9)", lua)
        self.assertIn('return ("v=" .. tostring(y) .. ":" .. tostring(z))', lua)

    def test_string_add_uses_lua_concat_operator(self) -> None:
        src = (
            "def f(a: str, b: str) -> str:\n"
            "    return a + b\n"
        )
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "str_add.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py, parser_backend="self_hosted")
            lua = transpile_to_lua_native(east)
        self.assertIn("return (a .. b)", lua)

    def test_lowering_supports_class_constructor_and_method_dispatch(self) -> None:
        fixture = find_fixture_case("inheritance")
        east = load_east(fixture, parser_backend="self_hosted")
        lua = transpile_to_lua_native(east)
        self.assertIn("Animal = {}", lua)
        self.assertIn("Dog = setmetatable({}, { __index = Animal })", lua)
        self.assertIn("function Dog.new()", lua)
        self.assertIn("d = Dog.new()", lua)
        self.assertIn("return (self:sound() .. \"-bark\")", lua)
        self.assertIn("print(d:bark())", lua)

    def test_dataclass_default_constructor_assigns_fields(self) -> None:
        src = (
            "from dataclasses import dataclass\n"
            "@dataclass\n"
            "class Pair:\n"
            "    x: int\n"
            "    y: int\n"
            "def f() -> int:\n"
            "    p = Pair(3, 4)\n"
            "    return p.x + p.y\n"
        )
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "dataclass_pair.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py, parser_backend="self_hosted")
            lua = transpile_to_lua_native(east)
        self.assertIn("function Pair.new(x, y)", lua)
        self.assertIn("self.x = x", lua)
        self.assertIn("self.y = y", lua)

    def test_annassign_on_attribute_inside_init_is_not_local(self) -> None:
        src = (
            "class C:\n"
            "    def __init__(self, x: int):\n"
            "        self.value: int = x\n"
            "def f() -> int:\n"
            "    c = C(7)\n"
            "    return c.value\n"
        )
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "annassign_attr.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py, parser_backend="self_hosted")
            lua = transpile_to_lua_native(east)
        self.assertIn("self.value = x", lua)
        self.assertNotIn("local self.value = x", lua)

    def test_lowering_supports_isinstance_node_for_classes(self) -> None:
        fixture = find_fixture_case("is_instance")
        east = load_east(fixture, parser_backend="self_hosted")
        lua = transpile_to_lua_native(east)
        self.assertIn("local function __pytra_isinstance(obj, class_tbl)", lua)
        self.assertIn("__pytra_isinstance(cat, Dog)", lua)
        self.assertIn("__pytra_isinstance(cat, Animal)", lua)

    def test_import_lowering_maps_assertions_perf_counter_and_png_runtime(self) -> None:
        src = (
            "from pytra.utils.assertions import py_assert_stdout\n"
            "from pytra.utils.assertions import py_assert_eq, py_assert_true, py_assert_all\n"
            "from time import perf_counter\n"
            "from pytra.utils import png\n"
            "def f() -> None:\n"
            "    _ = perf_counter()\n"
            "    png.write_rgb_png('x.png', 1, 1, b'')\n"
            "def g() -> None:\n"
            "    checks = [py_assert_eq(1, 1), py_assert_true(True)]\n"
            "    print(py_assert_all(checks, 'case'))\n"
            "    print(py_assert_stdout(['ok'], f))\n"
        )
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "imports_png.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py, parser_backend="self_hosted")
            lua = transpile_to_lua_native(east)
        self.assertIn("dofile((debug.getinfo(1, \"S\").source:sub(2):match(\"^(.*[\\\\/])\") or \"\") .. \"py_runtime.lua\")", lua)
        self.assertIn("local py_assert_stdout = function(", lua)
        self.assertIn("local py_assert_eq = function(a, b, _label) return a == b end", lua)
        self.assertIn("local py_assert_true = function(v, _label) return not not v end", lua)
        self.assertIn("local py_assert_all = function(checks, _label)", lua)
        self.assertIn("local perf_counter = __pytra_perf_counter", lua)
        self.assertIn("local png = __pytra_png_module()", lua)
        self.assertIn('png.write_rgb_png("x.png", 1, 1, "")', lua)
        self.assertNotIn("write_rgb_png = function(...) end", lua)
        self.assertNotIn("not yet mapped", lua)

    def test_sample01_uses_runtime_mapped_perf_counter_and_png(self) -> None:
        sample = ROOT / "sample" / "py" / "01_mandelbrot.py"
        east = load_east(sample, parser_backend="self_hosted")
        lua = transpile_to_lua_native(east)
        self.assertIn("dofile((debug.getinfo(1, \"S\").source:sub(2):match(\"^(.*[\\\\/])\") or \"\") .. \"py_runtime.lua\")", lua)
        self.assertIn("local perf_counter = __pytra_perf_counter", lua)
        self.assertIn("local png = __pytra_png_module()", lua)
        self.assertNotIn("write_rgb_png = function(...) end", lua)
        self.assertNotIn("from time import perf_counter", lua)

    def test_import_lowering_maps_pytra_gif_runtime(self) -> None:
        src = (
            "from pytra.utils import gif\n"
            "def f() -> None:\n"
            "    _ = gif\n"
        )
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "imports_gif_unmapped.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py, parser_backend="self_hosted")
            lua = transpile_to_lua_native(east)
        self.assertIn("dofile((debug.getinfo(1, \"S\").source:sub(2):match(\"^(.*[\\\\/])\") or \"\") .. \"py_runtime.lua\")", lua)
        self.assertIn("local gif = __pytra_gif_module()", lua)

    def test_import_lowering_fails_closed_for_unknown_pytra_symbol(self) -> None:
        src = (
            "from pytra.utils import unknown_symbol\n"
            "def f() -> None:\n"
            "    _ = unknown_symbol\n"
        )
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "imports_unknown_unmapped.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py, parser_backend="self_hosted")
            with self.assertRaises(RuntimeError):
                _ = transpile_to_lua_native(east)

    def test_lua_emitter_source_has_no_source_runtime_module_special_case(self) -> None:
        src = (ROOT / "src" / "backends" / "lua" / "emitter" / "lua_native_emitter.py").read_text(encoding="utf-8")
        self.assertNotIn('mod == "math"', src)
        self.assertNotIn('mod == "time"', src)
        self.assertNotIn('mod == "pytra.std.math"', src)
        self.assertNotIn('mod == "pytra.std.time"', src)
        self.assertNotIn('mod == "pytra.std.os"', src)
        self.assertNotIn('mod == "pytra.std.os_path"', src)
        self.assertNotIn('mod == "pytra.std.sys"', src)
        self.assertNotIn('mod == "pytra.std.glob"', src)
        self.assertNotIn('mod == "pathlib"', src)
        self.assertNotIn('mod == "json"', src)
        self.assertNotIn('mod == "pytra.utils"', src)


if __name__ == "__main__":
    unittest.main()
