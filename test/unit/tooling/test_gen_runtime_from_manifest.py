from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import gen_runtime_from_manifest as gen_mod


class GenRuntimeFromManifestTest(unittest.TestCase):
    def test_load_manifest_items_contains_png_cpp_rs_and_cs_built_in_std(self) -> None:
        items = gen_mod.load_manifest_items(ROOT / "tools" / "runtime_generation_manifest.json")
        pairs = {(item.item_id, item.target, item.output_rel) for item in items}
        self.assertIn(("utils/png", "cpp", "src/runtime/cpp/generated/utils/png.cpp"), pairs)
        self.assertIn(("utils/png", "rs", "src/runtime/rs/generated/utils/png.rs"), pairs)
        self.assertIn(("built_in/type_id", "rs", "src/runtime/rs/generated/built_in/type_id.rs"), pairs)
        self.assertIn(("built_in/type_id", "cs", "src/runtime/cs/generated/built_in/type_id.cs"), pairs)
        self.assertIn(("built_in/contains", "go", "src/runtime/go/generated/built_in/contains.go"), pairs)
        self.assertIn(("built_in/contains", "java", "src/runtime/java/generated/built_in/contains.java"), pairs)
        self.assertIn(("built_in/type_id", "js", "src/runtime/js/generated/built_in/type_id.js"), pairs)
        self.assertIn(("built_in/type_id", "ts", "src/runtime/ts/generated/built_in/type_id.ts"), pairs)
        self.assertIn(("built_in/type_id", "php", "src/runtime/php/generated/built_in/type_id.php"), pairs)
        self.assertIn(("std/pathlib", "cs", "src/runtime/cs/generated/std/pathlib.cs"), pairs)
        self.assertIn(("std/pathlib", "js", "src/runtime/js/generated/std/pathlib.js"), pairs)
        self.assertIn(("std/pathlib", "ts", "src/runtime/ts/generated/std/pathlib.ts"), pairs)
        self.assertIn(("std/pathlib", "php", "src/runtime/php/generated/std/pathlib.php"), pairs)
        self.assertIn(("std/math", "js", "src/runtime/js/generated/std/math.js"), pairs)
        self.assertIn(("std/math", "ts", "src/runtime/ts/generated/std/math.ts"), pairs)
        self.assertIn(("std/math", "php", "src/runtime/php/generated/std/math.php"), pairs)
        self.assertIn(("std/json", "js", "src/runtime/js/generated/std/json.js"), pairs)
        self.assertIn(("std/json", "ts", "src/runtime/ts/generated/std/json.ts"), pairs)
        self.assertIn(("std/json", "php", "src/runtime/php/generated/std/json.php"), pairs)
        self.assertIn(("std/time", "java", "src/runtime/java/generated/std/time.java"), pairs)
        self.assertIn(("std/time", "js", "src/runtime/js/generated/std/time.js"), pairs)
        self.assertIn(("std/time", "ts", "src/runtime/ts/generated/std/time.ts"), pairs)
        self.assertIn(("std/time", "php", "src/runtime/php/generated/std/time.php"), pairs)

    def test_built_in_manifest_covers_compare_targets_for_all_sot_modules(self) -> None:
        items = gen_mod.load_manifest_items(ROOT / "tools" / "runtime_generation_manifest.json")
        by_pair = {(item.item_id, item.target): item.output_rel for item in items}
        module_names = sorted(
            p.stem
            for p in (ROOT / "src" / "pytra" / "built_in").glob("*.py")
            if p.name != "__init__.py"
        )
        self.assertEqual(
            module_names,
            [
                "contains",
                "io_ops",
                "iter_ops",
                "numeric_ops",
                "predicates",
                "scalar_ops",
                "sequence",
                "string_ops",
                "type_id",
                "zip_ops",
            ],
        )
        go_java_supported = {
            "contains",
            "io_ops",
            "iter_ops",
            "numeric_ops",
            "scalar_ops",
            "zip_ops",
        }
        for module_name in module_names:
            item_id = f"built_in/{module_name}"
            self.assertEqual(
                by_pair[(item_id, "rs")],
                f"src/runtime/rs/generated/built_in/{module_name}.rs",
            )
            self.assertEqual(
                by_pair[(item_id, "cs")],
                f"src/runtime/cs/generated/built_in/{module_name}.cs",
            )
            self.assertEqual(
                by_pair[(item_id, "js")],
                f"src/runtime/js/generated/built_in/{module_name}.js",
            )
            self.assertEqual(
                by_pair[(item_id, "ts")],
                f"src/runtime/ts/generated/built_in/{module_name}.ts",
            )
            self.assertEqual(
                by_pair[(item_id, "php")],
                f"src/runtime/php/generated/built_in/{module_name}.php",
            )
            if module_name in go_java_supported:
                self.assertEqual(
                    by_pair[(item_id, "go")],
                    f"src/runtime/go/generated/built_in/{module_name}.go",
                )
                self.assertEqual(
                    by_pair[(item_id, "java")],
                    f"src/runtime/java/generated/built_in/{module_name}.java",
                )
            else:
                self.assertNotIn((item_id, "go"), by_pair)
                self.assertNotIn((item_id, "java"), by_pair)

    def test_resolve_targets_all_contains_cpp_and_swift(self) -> None:
        items = gen_mod.load_manifest_items(ROOT / "tools" / "runtime_generation_manifest.json")
        targets = gen_mod.resolve_targets("all", items)
        self.assertIn("cpp", targets)
        self.assertIn("swift", targets)

    def test_inject_generated_header_for_php_keeps_php_open_tag(self) -> None:
        src = "<?php\necho 'x';\n"
        out = gen_mod.inject_generated_header(src, "php", "src/pytra/utils/png.py")
        self.assertTrue(out.startswith("<?php\n"))
        self.assertIn("// source: src/pytra/utils/png.py", out)
        self.assertIn("// generated-by: tools/gen_runtime_from_manifest.py", out)

    def test_rewrite_cs_program_to_helper_renames_program_class(self) -> None:
        src = "\n".join(
            [
                "using System;",
                "public static class Program",
                "{",
                "    public static int f() { return 1; }",
                "}",
            ]
        )
        out = gen_mod.rewrite_cs_program_to_helper(src, "png_helper")
        self.assertIn("public static class png_helper", out)
        self.assertNotIn("public static class Program", out)

    def test_rewrite_cs_std_time_live_wrapper_targets_time_native(self) -> None:
        src = "\n".join(
            [
                "using Pytra.CsModule;",
                "public static class Program",
                "{",
                "    public static double perf_counter() { return __t.perf_counter(); }",
                "}",
            ]
        )
        out = gen_mod.rewrite_cs_std_time_live_wrapper(src)
        self.assertIn("namespace Pytra.CsModule", out)
        self.assertIn("public static class time", out)
        self.assertIn("return time_native.perf_counter();", out)
        self.assertNotIn("return __t.perf_counter();", out)

    def test_rewrite_java_std_time_live_wrapper_inlines_system_nanotime(self) -> None:
        src = "\n".join(
            [
                "public final class time {",
                "    public static double perf_counter() {",
                "        return __t.perf_counter();",
                "    }",
                "}",
            ]
        )
        out = gen_mod.rewrite_java_std_time_live_wrapper(src)
        self.assertIn("System.nanoTime()", out)
        self.assertNotIn("__t.perf_counter()", out)

    def test_rewrite_java_std_math_live_wrapper_inlines_java_math(self) -> None:
        src = "\n".join(
            [
                "public final class math {",
                "    public static double pi = extern(math.pi);",
                "    public static double fabs(double x) { return math.fabs(x); }",
                "    public static double pow(double x, double y) { return math.pow(x, y); }",
                "}",
            ]
        )
        out = gen_mod.rewrite_java_std_math_live_wrapper(src)
        self.assertIn("public static double pi = Math.PI;", out)
        self.assertIn("return Math.abs(x);", out)
        self.assertIn("return Math.pow(x, y);", out)
        self.assertNotIn("extern(math.pi)", out)

    def test_rewrite_js_std_math_live_wrapper_inlines_math_and_exports_constants(self) -> None:
        src = "\n".join(
            [
                'import { extern } from "./pytra/std.js";',
                "",
                "function sin(x) {",
                "    return __m.sin(x);",
                "}",
                "function pow(x, y) {",
                "    return __m.pow(x, y);",
                "}",
                "",
                '"pytra.std.math: extern-marked math API with Python runtime fallback.";',
                "let pi = extern(__m.pi);",
                "let e = extern(__m.e);",
            ]
        )
        out = gen_mod.rewrite_js_std_math_live_wrapper(src)
        self.assertIn("const pi = Math.PI;", out)
        self.assertIn("const e = Math.E;", out)
        self.assertIn("return Math.sin(x);", out)
        self.assertIn("return Math.pow(x, y);", out)
        self.assertIn("module.exports = { pi, e, sin, cos, tan, sqrt, exp, log, log10, fabs, floor, ceil, pow };", out)
        self.assertNotIn("__m.", out)
        self.assertNotIn("extern(", out)

    def test_rewrite_js_ts_built_in_cjs_module_rehomes_runtime_import(self) -> None:
        src = "\n".join(
            [
                'import { pyStr, pyLen } from "./pytra/py_runtime.js";',
                "",
                "function py_contains_str_object(values, key) {",
                "    return pyLen(values) > pyStr(key).length;",
                "}",
            ]
        )
        out = gen_mod.rewrite_js_ts_built_in_cjs_module(src)
        self.assertIn('require("../../native/built_in/py_runtime.js")', out)
        self.assertIn("function py_contains_str_object(values, key) {", out)
        self.assertIn("module.exports = {py_contains_str_object};", out)
        self.assertNotIn("./pytra/py_runtime.js", out)

    def test_rewrite_ts_std_math_live_wrapper_exports_typed_symbols(self) -> None:
        src = "\n".join(
            [
                'import { extern } from "./pytra/std.js";',
                "",
                "function sin(x) {",
                "    return __m.sin(x);",
                "}",
                "function pow(x, y) {",
                "    return __m.pow(x, y);",
                "}",
                "",
                '"pytra.std.math: extern-marked math API with Python runtime fallback.";',
                "let pi = extern(__m.pi);",
                "let e = extern(__m.e);",
            ]
        )
        out = gen_mod.rewrite_ts_std_math_live_wrapper(src)
        self.assertIn("export const pi: number = Math.PI;", out)
        self.assertIn("export const e: number = Math.E;", out)
        self.assertIn("export function sin(x: number): number {", out)
        self.assertIn("return Math.sin(x);", out)
        self.assertIn("export function pow(x: number, y: number): number {", out)
        self.assertIn("return Math.pow(x, y);", out)
        self.assertNotIn("__m.", out)
        self.assertNotIn("extern(", out)

    def test_rewrite_js_std_time_live_wrapper_inlines_hrtime_and_alias(self) -> None:
        src = "\n".join(
            [
                "function perf_counter() {",
                "    return __t.perf_counter();",
                "}",
                "",
                "\"pytra.std.time: extern-marked time API with Python runtime fallback.\";",
            ]
        )
        out = gen_mod.rewrite_js_std_time_live_wrapper(src)
        self.assertIn("process.hrtime.bigint()", out)
        self.assertIn("const perfCounter = perf_counter;", out)
        self.assertIn("module.exports = {perf_counter, perfCounter};", out)
        self.assertNotIn("__t.perf_counter()", out)

    def test_rewrite_js_std_pathlib_live_wrapper_exports_factory_with_property_getters(self) -> None:
        src = "\n".join(
            [
                "class Path {",
                "    __truediv__(rhs) { return new Path(rhs); }",
                "    parent() { return new Path('.'); }",
                "    parents() { return []; }",
                "    name() { return 'n'; }",
                "    suffix() { return '.txt'; }",
                "    stem() { return 'n'; }",
                "    resolve() { return new Path('.'); }",
                "    exists() { return true; }",
                "    mkdir(parents, exist_ok) { }",
                "    read_text(encoding) { return ''; }",
                "    write_text(text, encoding) { return 0; }",
                "    glob(pattern) { return []; }",
                "    cwd() { return new Path('.'); }",
                "}",
            ]
        )
        out = gen_mod.rewrite_js_std_pathlib_live_wrapper(src)
        self.assertIn("class PathValue {", out)
        self.assertIn("function Path(value = \"\") {", out)
        self.assertIn("Path.cwd = function() {", out)
        self.assertIn('Object.defineProperty(obj, "parent"', out)
        self.assertIn("module.exports = { Path, pathJoin };", out)

    def test_rewrite_js_std_json_live_wrapper_exports_json_facade(self) -> None:
        src = "\n".join(
            [
                "class JsonObj {",
                "}",
                "class JsonArr {",
                "}",
                "class JsonValue {",
                "}",
                "function loads(text) { return text; }",
                "function loads_obj(text) { return text; }",
                "function loads_arr(text) { return text; }",
                "function dumps(obj) { return obj; }",
            ]
        )
        out = gen_mod.rewrite_js_std_json_live_wrapper(src)
        self.assertIn('require("../../native/built_in/py_runtime.js")', out)
        self.assertIn("class JsonObj {", out)
        self.assertIn("function loads(text) {", out)
        self.assertIn("return JSON.parse(String(text));", out)
        self.assertIn("module.exports = { JsonObj, JsonArr, JsonValue, loads, loads_obj, loads_arr, dumps };", out)

    def test_rewrite_ts_std_time_live_wrapper_exports_perf_counter(self) -> None:
        src = "\n".join(
            [
                "function perf_counter() {",
                "    return __t.perf_counter();",
                "}",
                "",
                "\"pytra.std.time: extern-marked time API with Python runtime fallback.\";",
            ]
        )
        out = gen_mod.rewrite_ts_std_time_live_wrapper(src)
        self.assertIn("export function perf_counter(): number {", out)
        self.assertIn("process.hrtime.bigint()", out)
        self.assertIn("export const perfCounter = perf_counter;", out)
        self.assertNotIn("__t.perf_counter()", out)

    def test_rewrite_ts_std_pathlib_live_wrapper_exports_factory_with_property_getters(self) -> None:
        src = "\n".join(
            [
                "class Path {",
                "    __truediv__(rhs) { return new Path(rhs); }",
                "    parent() { return new Path('.'); }",
                "    parents() { return []; }",
                "    name() { return 'n'; }",
                "    suffix() { return '.txt'; }",
                "    stem() { return 'n'; }",
                "    resolve() { return new Path('.'); }",
                "    exists() { return true; }",
                "    mkdir(parents, exist_ok) { }",
                "    read_text(encoding) { return ''; }",
                "    write_text(text, encoding) { return 0; }",
                "    glob(pattern) { return []; }",
                "    cwd() { return new Path('.'); }",
                "}",
            ]
        )
        out = gen_mod.rewrite_ts_std_pathlib_live_wrapper(src)
        self.assertIn("export class PathValue {", out)
        self.assertIn("export const Path: ((value?: unknown) => PathValue) & { cwd(): PathValue }", out)
        self.assertIn('Object.defineProperty(obj, "parent"', out)
        self.assertIn("export function pathJoin(base: unknown, child: unknown): PathValue {", out)

    def test_rewrite_ts_std_json_live_wrapper_exports_json_facade(self) -> None:
        src = "\n".join(
            [
                "class JsonObj {",
                "}",
                "class JsonArr {",
                "}",
                "class JsonValue {",
                "}",
                "function loads(text) { return text; }",
                "function loads_obj(text) { return text; }",
                "function loads_arr(text) { return text; }",
                "function dumps(obj) { return obj; }",
            ]
        )
        out = gen_mod.rewrite_ts_std_json_live_wrapper(src)
        self.assertIn('from "../../native/built_in/py_runtime"', out)
        self.assertIn("export class JsonObj {", out)
        self.assertIn("export function loads(text: string): unknown {", out)
        self.assertIn("return JSON.parse(String(text));", out)
        self.assertIn("export function dumps(", out)

    def test_rewrite_php_std_time_live_wrapper_inlines_microtime(self) -> None:
        src = "\n".join(
            [
                "<?php",
                "declare(strict_types=1);",
                "",
                "require_once __DIR__ . '/pytra/py_runtime.php';",
                "",
                "function perf_counter() {",
                "    return $__t->perf_counter();",
                "}",
                "",
                "function __pytra_main(): void {",
                "}",
                "",
                "__pytra_main();",
            ]
        )
        out = gen_mod.rewrite_php_std_time_live_wrapper(src)
        self.assertIn("function perf_counter(): float {", out)
        self.assertIn("return microtime(true);", out)
        self.assertNotIn("/pytra/py_runtime.php", out)
        self.assertNotIn("__pytra_main();", out)

    def test_rewrite_php_program_to_library_prefers_packaged_root_and_falls_back_to_repo_native(self) -> None:
        src = "\n".join(
            [
                "<?php",
                "declare(strict_types=1);",
                "",
                "require_once __DIR__ . '/pytra/py_runtime.php';",
                "",
                "function helper() {",
                "    return __pytra_len([]);",
                "}",
                "",
                "function __pytra_main(): void {",
                "}",
                "",
                "__pytra_main();",
            ]
        )
        out = gen_mod.rewrite_php_program_to_library(src)
        self.assertIn("dirname(__DIR__) . '/py_runtime.php'", out)
        self.assertIn("dirname(__DIR__, 2) . '/native/built_in/py_runtime.php'", out)
        self.assertIn("function_exists('__pytra_len')", out)
        self.assertNotIn("__pytra_main();", out)

    def test_rewrite_php_std_math_live_wrapper_exports_pi_and_e(self) -> None:
        src = "\n".join(
            [
                "<?php",
                "declare(strict_types=1);",
                "",
                "require_once __DIR__ . '/pytra/py_runtime.php';",
                "",
                "function sqrt($x) {",
                "    return pyMathSqrt($x);",
                "}",
                "",
                "function pow($x, $y) {",
                "    return pyMathPow($x, $y);",
                "}",
                "",
                "function __pytra_main(): void {",
                "}",
                "",
                "__pytra_main();",
            ]
        )
        out = gen_mod.rewrite_php_std_math_live_wrapper(src)
        self.assertIn("dirname(__DIR__) . '/py_runtime.php'", out)
        self.assertIn("dirname(__DIR__, 2) . '/native/built_in/py_runtime.php'", out)
        self.assertIn("$pi = pyMathPi();", out)
        self.assertIn("$e = pyMathE();", out)
        self.assertIn("function sqrt($x): float {", out)
        self.assertIn("function pow($x, $y): float {", out)
        self.assertNotIn("__pytra_main", out)

    def test_rewrite_php_std_pathlib_live_wrapper_guards_path_redefinition(self) -> None:
        src = "\n".join(
            [
                "<?php",
                "declare(strict_types=1);",
                "",
                "require_once __DIR__ . '/pytra/py_runtime.php';",
                "",
                "class Path {",
                "    public function __truediv__($rhs) { return new Path($rhs); }",
                "    public function parent() { return new Path('.'); }",
                "    public function name() { return 'n'; }",
                "    public function stem() { return 'n'; }",
                "    public function resolve() { return new Path('.'); }",
                "    public function exists() { return true; }",
                "    public function mkdir($parents, $exist_ok) { }",
                "    public function read_text($encoding) { return ''; }",
                "    public function write_text($text, $encoding) { return 0; }",
                "    public function glob($pattern) { return []; }",
                "    public function cwd() { return new Path('.'); }",
                "}",
            ]
        )
        out = gen_mod.rewrite_php_std_pathlib_live_wrapper(src)
        self.assertIn("dirname(__DIR__) . '/py_runtime.php'", out)
        self.assertIn("dirname(__DIR__, 2) . '/native/built_in/py_runtime.php'", out)
        self.assertIn("if (!class_exists('Path', false)) {", out)
        self.assertIn("public string $suffix;", out)
        self.assertIn("public static function cwd(): Path {", out)

    def test_rewrite_php_std_json_live_wrapper_exports_json_facade(self) -> None:
        src = "\n".join(
            [
                "<?php",
                "declare(strict_types=1);",
                "",
                "class JsonObj {",
                "}",
                "class JsonArr {",
                "}",
                "class JsonValue {",
                "}",
                "function loads($text) { return $text; }",
                "function loads_obj($text) { return $text; }",
                "function loads_arr($text) { return $text; }",
                "function dumps($obj) { return $obj; }",
            ]
        )
        out = gen_mod.rewrite_php_std_json_live_wrapper(src)
        self.assertIn("dirname(__DIR__) . '/py_runtime.php'", out)
        self.assertIn("dirname(__DIR__, 2) . '/native/built_in/py_runtime.php'", out)
        self.assertIn("class JsonObj {", out)
        self.assertIn("function loads(string $text)", out)
        self.assertIn("return json_decode((string)$text, false, 512, JSON_THROW_ON_ERROR);", out)
        self.assertIn("function dumps($obj, bool $ensure_ascii = true, $indent = null, $separators = null): string {", out)
        self.assertIn("JSON_PRESERVE_ZERO_FRACTION", out)

    def test_run_py2x_raises_when_backend_emits_no_text_and_no_file(self) -> None:
        with (
            patch.object(gen_mod, "get_backend_spec", return_value={}),
            patch.object(gen_mod, "load_east3_document", return_value={}),
            patch.object(gen_mod, "resolve_layer_options", return_value={}),
            patch.object(gen_mod, "lower_ir", return_value={}),
            patch.object(gen_mod, "optimize_ir", return_value={}),
            patch.object(gen_mod, "emit_source", return_value=""),
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "runtime generation backend emitted no inline text and wrote no file: "
                "nim -> src/runtime/nim/generated/utils/png_helper.nim",
            ):
                gen_mod.run_py2x(
                    "nim",
                    "src/pytra/utils/png.py",
                    "src/runtime/nim/generated/utils/png_helper.nim",
                )

    def test_run_py2x_nim_png_helper_lowers_try_finally(self) -> None:
        out = gen_mod.run_py2x(
            "nim",
            "src/pytra/utils/png.py",
            "src/runtime/nim/generated/utils/png_helper.nim",
        )
        self.assertIn("f.write(png)", out)
        self.assertIn("f.close()", out)
        self.assertNotIn("# unsupported stmt: Try", out)

    def test_run_py2x_lua_gif_helper_ignores_compile_time_std_imports(self) -> None:
        out = gen_mod.run_py2x(
            "lua",
            "src/pytra/utils/gif.py",
            "src/runtime/lua/generated/utils/gif_helper.lua",
        )
        self.assertIn("function grayscale_palette()", out)
        self.assertIn("function save_gif(", out)
        self.assertNotIn("pytra.std.abi", out)

    def test_wave_b_runtime_regeneration_check_passes(self) -> None:
        items = gen_mod.load_manifest_items(ROOT / "tools" / "runtime_generation_manifest.json")
        targets = gen_mod.resolve_targets("js,ts,lua,ruby,php", items)
        item_ids = gen_mod.resolve_item_ids("all", items)
        plan = gen_mod.build_generation_plan(items, targets, item_ids)
        checked, updated = gen_mod.generate(plan, check=True, dry_run=False)
        self.assertEqual(checked, 52)
        self.assertEqual(updated, 0)


if __name__ == "__main__":
    unittest.main()
