"""py2lua (EAST based) smoke tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.py2lua import load_east, load_lua_profile, transpile_to_lua, transpile_to_lua_native
from src.pytra.compiler.east_parts.core import convert_path
from comment_fidelity import assert_no_generated_comments


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

    def test_transpile_add_fixture_uses_native_output(self) -> None:
        fixture = find_fixture_case("add")
        east = load_east(fixture, parser_backend="self_hosted")
        lua = transpile_to_lua(east)
        assert_no_generated_comments(self, lua)
        self.assertIn("function add(a, b)", lua)
        self.assertIn("print(add(3, 4))", lua)
        self.assertNotIn("node ", lua)

    def test_transpile_if_else_fixture_contains_lua_if(self) -> None:
        fixture = find_fixture_case("if_else")
        east = load_east(fixture, parser_backend="self_hosted")
        lua = transpile_to_lua_native(east)
        self.assertIn("function abs_like(n)", lua)
        self.assertIn("if (n < 0) then", lua)
        self.assertIn("return (-n)", lua)
        self.assertIn("else", lua)

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

    def test_transpile_for_range_fixture_contains_static_for(self) -> None:
        fixture = find_fixture_case("for_range")
        east = load_east(fixture, parser_backend="self_hosted")
        lua = transpile_to_lua_native(east)
        self.assertIn("function sum_range_29(n)", lua)
        self.assertIn("local total = 0", lua)
        self.assertIn("for i = 0, (n) - 1, 1 do", lua)
        self.assertIn("total = total + i", lua)

    def test_transpile_downcount_range_fixture_uses_descending_upper_bound(self) -> None:
        fixture = find_fixture_case("range_downcount_len_minus1")
        east = load_east(fixture, parser_backend="self_hosted")
        lua = transpile_to_lua_native(east)
        self.assertIn("for i = (#(xs) - 1), ((-1)) + 1, (-1) do", lua)
        self.assertNotIn("for i = (#(xs) - 1), ((-1)) - 1, (-1) do", lua)

    def test_load_east_from_json(self) -> None:
        fixture = find_fixture_case("add")
        east = convert_path(fixture)
        with tempfile.TemporaryDirectory() as td:
            east_json = Path(td) / "case.east.json"
            east_json.write_text(json.dumps(east), encoding="utf-8")
            loaded = load_east(east_json)
            lua = transpile_to_lua_native(loaded)
        self.assertIn("function add(a, b)", lua)

    def test_load_east_defaults_to_stage3_entry_and_returns_east3_shape(self) -> None:
        fixture = find_fixture_case("for_range")
        loaded = load_east(fixture, parser_backend="self_hosted")
        self.assertIsInstance(loaded, dict)
        self.assertEqual(loaded.get("kind"), "Module")
        self.assertEqual(loaded.get("east_stage"), 3)

    def test_cli_smoke_defaults_to_native_without_sidecar(self) -> None:
        fixture = find_fixture_case("if_else")
        with tempfile.TemporaryDirectory() as td:
            out_lua = Path(td) / "if_else.lua"
            out_js = Path(td) / "if_else.js"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/py2lua.py", str(fixture), "-o", str(out_lua)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            self.assertTrue(out_lua.exists())
            self.assertFalse(out_js.exists())
            txt = out_lua.read_text(encoding="utf-8")
            self.assertNotIn("Auto-generated Pytra Lua native source from EAST3.", txt)

    def test_cli_rejects_stage2_compat_mode(self) -> None:
        fixture = find_fixture_case("if_else")
        with tempfile.TemporaryDirectory() as td:
            out_lua = Path(td) / "if_else.lua"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/py2lua.py", str(fixture), "-o", str(out_lua), "--east-stage", "2"],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            self.assertIn("--east-stage 2 is no longer supported; use EAST3 (default).", proc.stderr)

    def test_py2lua_does_not_import_src_common(self) -> None:
        src = (ROOT / "src" / "py2lua.py").read_text(encoding="utf-8")
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
        self.assertIn('return (d["x"] + a[(1) + 1])', lua)

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
        self.assertIn("y = ((flag) and (x) or (0))", lua)
        self.assertIn("z = math.sqrt(9)", lua)
        self.assertIn('return ("v=" .. tostring(y) .. ":" .. tostring(z))', lua)

    def test_lowering_supports_class_constructor_and_method_dispatch(self) -> None:
        fixture = find_fixture_case("inheritance")
        east = load_east(fixture, parser_backend="self_hosted")
        lua = transpile_to_lua_native(east)
        self.assertIn("Animal = {}", lua)
        self.assertIn("Dog = setmetatable({}, { __index = Animal })", lua)
        self.assertIn("function Dog.new()", lua)
        self.assertIn("d = Dog.new()", lua)
        self.assertIn("return (self:sound() + \"-bark\")", lua)
        self.assertIn("print(d:bark())", lua)

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
            "from time import perf_counter\n"
            "from pytra.utils import png\n"
            "def f() -> None:\n"
            "    _ = perf_counter()\n"
            "    png.write_rgb_png('x.png', 1, 1, b'')\n"
            "def g() -> None:\n"
            "    print(py_assert_stdout(['ok'], f))\n"
        )
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "imports_png.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py, parser_backend="self_hosted")
            lua = transpile_to_lua_native(east)
        self.assertIn("local py_assert_stdout = function(expected, fn) fn(); return true end", lua)
        self.assertIn("local function __pytra_perf_counter()", lua)
        self.assertIn("local perf_counter = __pytra_perf_counter", lua)
        self.assertIn("local function __pytra_write_rgb_png(path, width, height, pixels)", lua)
        self.assertIn("local png = __pytra_png_module()", lua)
        self.assertIn('png.write_rgb_png("x.png", 1, 1, "")', lua)
        self.assertNotIn("write_rgb_png = function(...) end", lua)
        self.assertNotIn("not yet mapped", lua)

    def test_sample01_uses_runtime_mapped_perf_counter_and_png(self) -> None:
        sample = ROOT / "sample" / "py" / "01_mandelbrot.py"
        east = load_east(sample, parser_backend="self_hosted")
        lua = transpile_to_lua_native(east)
        self.assertIn("local function __pytra_perf_counter()", lua)
        self.assertIn("local perf_counter = __pytra_perf_counter", lua)
        self.assertIn("local png = __pytra_png_module()", lua)
        self.assertNotIn("write_rgb_png = function(...) end", lua)
        self.assertNotIn("from time import perf_counter", lua)

    def test_import_lowering_fails_closed_for_unmapped_pytra_gif(self) -> None:
        src = (
            "from pytra.runtime import gif\n"
            "def f() -> None:\n"
            "    _ = gif\n"
        )
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "imports_gif_unmapped.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py, parser_backend="self_hosted")
            with self.assertRaises(RuntimeError):
                _ = transpile_to_lua_native(east)


if __name__ == "__main__":
    unittest.main()
