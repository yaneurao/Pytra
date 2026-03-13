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
        self.assertIn(("utils/png", "ruby", "src/runtime/ruby/generated/utils/png.rb"), pairs)
        self.assertIn(("utils/gif", "ruby", "src/runtime/ruby/generated/utils/gif.rb"), pairs)
        self.assertIn(("built_in/type_id", "rs", "src/runtime/rs/generated/built_in/type_id.rs"), pairs)
        self.assertIn(("built_in/type_id", "cs", "src/runtime/cs/generated/built_in/type_id.cs"), pairs)
        self.assertIn(("built_in/contains", "ruby", "src/runtime/ruby/generated/built_in/contains.rb"), pairs)
        self.assertIn(("built_in/contains", "go", "src/runtime/go/generated/built_in/contains.go"), pairs)
        self.assertIn(("built_in/contains", "java", "src/runtime/java/generated/built_in/contains.java"), pairs)
        self.assertIn(("built_in/contains", "kotlin", "src/runtime/kotlin/generated/built_in/contains.kt"), pairs)
        self.assertIn(("built_in/contains", "scala", "src/runtime/scala/generated/built_in/contains.scala"), pairs)
        self.assertIn(("built_in/contains", "swift", "src/runtime/swift/generated/built_in/contains.swift"), pairs)
        self.assertIn(("built_in/contains", "nim", "src/runtime/nim/generated/built_in/contains.nim"), pairs)
        self.assertIn(("built_in/type_id", "js", "src/runtime/js/generated/built_in/type_id.js"), pairs)
        self.assertIn(("built_in/type_id", "ts", "src/runtime/ts/generated/built_in/type_id.ts"), pairs)
        self.assertIn(("built_in/type_id", "ruby", "src/runtime/ruby/generated/built_in/type_id.rb"), pairs)
        self.assertIn(("built_in/type_id", "php", "src/runtime/php/generated/built_in/type_id.php"), pairs)
        self.assertIn(("std/pathlib", "cs", "src/runtime/cs/generated/std/pathlib.cs"), pairs)
        self.assertIn(("std/pathlib", "js", "src/runtime/js/generated/std/pathlib.js"), pairs)
        self.assertIn(("std/pathlib", "ts", "src/runtime/ts/generated/std/pathlib.ts"), pairs)
        self.assertIn(("std/pathlib", "ruby", "src/runtime/ruby/generated/std/pathlib.rb"), pairs)
        self.assertIn(("std/pathlib", "php", "src/runtime/php/generated/std/pathlib.php"), pairs)
        self.assertIn(("std/math", "js", "src/runtime/js/generated/std/math.js"), pairs)
        self.assertIn(("std/math", "ts", "src/runtime/ts/generated/std/math.ts"), pairs)
        self.assertIn(("std/math", "ruby", "src/runtime/ruby/generated/std/math.rb"), pairs)
        self.assertIn(("std/math", "php", "src/runtime/php/generated/std/math.php"), pairs)
        self.assertIn(("std/json", "rs", "src/runtime/rs/generated/std/json.rs"), pairs)
        self.assertIn(("std/json", "cs", "src/runtime/cs/generated/std/json.cs"), pairs)
        self.assertIn(("std/json", "js", "src/runtime/js/generated/std/json.js"), pairs)
        self.assertIn(("std/json", "ts", "src/runtime/ts/generated/std/json.ts"), pairs)
        self.assertIn(("std/json", "ruby", "src/runtime/ruby/generated/std/json.rb"), pairs)
        self.assertIn(("std/json", "php", "src/runtime/php/generated/std/json.php"), pairs)
        self.assertIn(("std/time", "java", "src/runtime/java/generated/std/time.java"), pairs)
        self.assertIn(("std/time", "kotlin", "src/runtime/kotlin/generated/std/time.kt"), pairs)
        self.assertIn(("std/time", "scala", "src/runtime/scala/generated/std/time.scala"), pairs)
        self.assertIn(("std/time", "swift", "src/runtime/swift/generated/std/time.swift"), pairs)
        self.assertIn(("std/time", "nim", "src/runtime/nim/generated/std/time.nim"), pairs)
        self.assertIn(("std/time", "js", "src/runtime/js/generated/std/time.js"), pairs)
        self.assertIn(("std/time", "ts", "src/runtime/ts/generated/std/time.ts"), pairs)
        self.assertIn(("std/time", "ruby", "src/runtime/ruby/generated/std/time.rb"), pairs)
        self.assertIn(("std/time", "php", "src/runtime/php/generated/std/time.php"), pairs)
        self.assertIn(("std/argparse", "rs", "src/runtime/rs/generated/std/argparse.rs"), pairs)
        self.assertIn(("std/argparse", "cs", "src/runtime/cs/generated/std/argparse.cs"), pairs)
        self.assertIn(("std/argparse", "go", "src/runtime/go/generated/std/argparse.go"), pairs)
        self.assertIn(("std/argparse", "java", "src/runtime/java/generated/std/argparse.java"), pairs)
        self.assertIn(("std/argparse", "kotlin", "src/runtime/kotlin/generated/std/argparse.kt"), pairs)
        self.assertIn(("std/argparse", "scala", "src/runtime/scala/generated/std/argparse.scala"), pairs)
        self.assertIn(("std/argparse", "swift", "src/runtime/swift/generated/std/argparse.swift"), pairs)
        self.assertIn(("std/argparse", "nim", "src/runtime/nim/generated/std/argparse.nim"), pairs)
        self.assertIn(("std/argparse", "js", "src/runtime/js/generated/std/argparse.js"), pairs)
        self.assertIn(("std/argparse", "ts", "src/runtime/ts/generated/std/argparse.ts"), pairs)
        self.assertIn(("std/argparse", "ruby", "src/runtime/ruby/generated/std/argparse.rb"), pairs)
        self.assertIn(("std/argparse", "php", "src/runtime/php/generated/std/argparse.php"), pairs)
        self.assertIn(("std/glob", "go", "src/runtime/go/generated/std/glob.go"), pairs)
        self.assertIn(("std/glob", "java", "src/runtime/java/generated/std/glob.java"), pairs)
        self.assertIn(("std/glob", "kotlin", "src/runtime/kotlin/generated/std/glob.kt"), pairs)
        self.assertIn(("std/glob", "scala", "src/runtime/scala/generated/std/glob.scala"), pairs)
        self.assertIn(("std/glob", "swift", "src/runtime/swift/generated/std/glob.swift"), pairs)
        self.assertIn(("std/glob", "nim", "src/runtime/nim/generated/std/glob.nim"), pairs)
        self.assertIn(("std/glob", "js", "src/runtime/js/generated/std/glob.js"), pairs)
        self.assertIn(("std/glob", "ts", "src/runtime/ts/generated/std/glob.ts"), pairs)
        self.assertIn(("std/glob", "ruby", "src/runtime/ruby/generated/std/glob.rb"), pairs)
        self.assertIn(("std/glob", "php", "src/runtime/php/generated/std/glob.php"), pairs)
        self.assertIn(("std/json", "go", "src/runtime/go/generated/std/json.go"), pairs)
        self.assertIn(("std/json", "kotlin", "src/runtime/kotlin/generated/std/json.kt"), pairs)
        self.assertIn(("std/json", "scala", "src/runtime/scala/generated/std/json.scala"), pairs)
        self.assertIn(("std/json", "swift", "src/runtime/swift/generated/std/json.swift"), pairs)
        self.assertIn(("std/json", "nim", "src/runtime/nim/generated/std/json.nim"), pairs)
        self.assertIn(("std/math", "go", "src/runtime/go/generated/std/math.go"), pairs)
        self.assertIn(("std/math", "kotlin", "src/runtime/kotlin/generated/std/math.kt"), pairs)
        self.assertIn(("std/math", "scala", "src/runtime/scala/generated/std/math.scala"), pairs)
        self.assertIn(("std/math", "swift", "src/runtime/swift/generated/std/math.swift"), pairs)
        self.assertIn(("std/math", "nim", "src/runtime/nim/generated/std/math.nim"), pairs)
        self.assertIn(("std/os", "go", "src/runtime/go/generated/std/os.go"), pairs)
        self.assertIn(("std/os", "java", "src/runtime/java/generated/std/os.java"), pairs)
        self.assertIn(("std/os", "kotlin", "src/runtime/kotlin/generated/std/os.kt"), pairs)
        self.assertIn(("std/os", "scala", "src/runtime/scala/generated/std/os.scala"), pairs)
        self.assertIn(("std/os", "swift", "src/runtime/swift/generated/std/os.swift"), pairs)
        self.assertIn(("std/os", "nim", "src/runtime/nim/generated/std/os.nim"), pairs)
        self.assertIn(("std/os", "js", "src/runtime/js/generated/std/os.js"), pairs)
        self.assertIn(("std/os", "ts", "src/runtime/ts/generated/std/os.ts"), pairs)
        self.assertIn(("std/os", "ruby", "src/runtime/ruby/generated/std/os.rb"), pairs)
        self.assertIn(("std/os", "php", "src/runtime/php/generated/std/os.php"), pairs)
        self.assertIn(("std/os_path", "go", "src/runtime/go/generated/std/os_path.go"), pairs)
        self.assertIn(("std/os_path", "java", "src/runtime/java/generated/std/os_path.java"), pairs)
        self.assertIn(("std/os_path", "kotlin", "src/runtime/kotlin/generated/std/os_path.kt"), pairs)
        self.assertIn(("std/os_path", "scala", "src/runtime/scala/generated/std/os_path.scala"), pairs)
        self.assertIn(("std/os_path", "swift", "src/runtime/swift/generated/std/os_path.swift"), pairs)
        self.assertIn(("std/os_path", "nim", "src/runtime/nim/generated/std/os_path.nim"), pairs)
        self.assertIn(("std/os_path", "js", "src/runtime/js/generated/std/os_path.js"), pairs)
        self.assertIn(("std/os_path", "ts", "src/runtime/ts/generated/std/os_path.ts"), pairs)
        self.assertIn(("std/os_path", "ruby", "src/runtime/ruby/generated/std/os_path.rb"), pairs)
        self.assertIn(("std/os_path", "php", "src/runtime/php/generated/std/os_path.php"), pairs)
        self.assertIn(("std/pathlib", "go", "src/runtime/go/generated/std/pathlib.go"), pairs)
        self.assertIn(("std/pathlib", "kotlin", "src/runtime/kotlin/generated/std/pathlib.kt"), pairs)
        self.assertIn(("std/pathlib", "scala", "src/runtime/scala/generated/std/pathlib.scala"), pairs)
        self.assertIn(("std/pathlib", "swift", "src/runtime/swift/generated/std/pathlib.swift"), pairs)
        self.assertIn(("std/pathlib", "nim", "src/runtime/nim/generated/std/pathlib.nim"), pairs)
        self.assertIn(("std/random", "rs", "src/runtime/rs/generated/std/random.rs"), pairs)
        self.assertIn(("std/random", "cs", "src/runtime/cs/generated/std/random.cs"), pairs)
        self.assertIn(("std/random", "go", "src/runtime/go/generated/std/random.go"), pairs)
        self.assertIn(("std/random", "java", "src/runtime/java/generated/std/random.java"), pairs)
        self.assertIn(("std/random", "kotlin", "src/runtime/kotlin/generated/std/random.kt"), pairs)
        self.assertIn(("std/random", "scala", "src/runtime/scala/generated/std/random.scala"), pairs)
        self.assertIn(("std/random", "swift", "src/runtime/swift/generated/std/random.swift"), pairs)
        self.assertIn(("std/random", "nim", "src/runtime/nim/generated/std/random.nim"), pairs)
        self.assertIn(("std/random", "js", "src/runtime/js/generated/std/random.js"), pairs)
        self.assertIn(("std/random", "ts", "src/runtime/ts/generated/std/random.ts"), pairs)
        self.assertIn(("std/random", "ruby", "src/runtime/ruby/generated/std/random.rb"), pairs)
        self.assertIn(("std/random", "php", "src/runtime/php/generated/std/random.php"), pairs)
        self.assertIn(("std/re", "rs", "src/runtime/rs/generated/std/re.rs"), pairs)
        self.assertIn(("std/re", "cs", "src/runtime/cs/generated/std/re.cs"), pairs)
        self.assertIn(("std/re", "go", "src/runtime/go/generated/std/re.go"), pairs)
        self.assertIn(("std/re", "java", "src/runtime/java/generated/std/re.java"), pairs)
        self.assertIn(("std/re", "kotlin", "src/runtime/kotlin/generated/std/re.kt"), pairs)
        self.assertIn(("std/re", "scala", "src/runtime/scala/generated/std/re.scala"), pairs)
        self.assertIn(("std/re", "swift", "src/runtime/swift/generated/std/re.swift"), pairs)
        self.assertIn(("std/re", "nim", "src/runtime/nim/generated/std/re.nim"), pairs)
        self.assertIn(("std/re", "js", "src/runtime/js/generated/std/re.js"), pairs)
        self.assertIn(("std/re", "ts", "src/runtime/ts/generated/std/re.ts"), pairs)
        self.assertIn(("std/re", "ruby", "src/runtime/ruby/generated/std/re.rb"), pairs)
        self.assertIn(("std/re", "php", "src/runtime/php/generated/std/re.php"), pairs)
        self.assertIn(("std/sys", "rs", "src/runtime/rs/generated/std/sys.rs"), pairs)
        self.assertIn(("std/sys", "cs", "src/runtime/cs/generated/std/sys.cs"), pairs)
        self.assertIn(("std/sys", "go", "src/runtime/go/generated/std/sys.go"), pairs)
        self.assertIn(("std/sys", "java", "src/runtime/java/generated/std/sys.java"), pairs)
        self.assertIn(("std/sys", "kotlin", "src/runtime/kotlin/generated/std/sys.kt"), pairs)
        self.assertIn(("std/sys", "scala", "src/runtime/scala/generated/std/sys.scala"), pairs)
        self.assertIn(("std/sys", "swift", "src/runtime/swift/generated/std/sys.swift"), pairs)
        self.assertIn(("std/sys", "nim", "src/runtime/nim/generated/std/sys.nim"), pairs)
        self.assertIn(("std/sys", "js", "src/runtime/js/generated/std/sys.js"), pairs)
        self.assertIn(("std/sys", "ts", "src/runtime/ts/generated/std/sys.ts"), pairs)
        self.assertIn(("std/sys", "ruby", "src/runtime/ruby/generated/std/sys.rb"), pairs)
        self.assertIn(("std/sys", "php", "src/runtime/php/generated/std/sys.php"), pairs)
        self.assertIn(("std/time", "go", "src/runtime/go/generated/std/time.go"), pairs)
        self.assertIn(("std/timeit", "rs", "src/runtime/rs/generated/std/timeit.rs"), pairs)
        self.assertIn(("std/timeit", "cs", "src/runtime/cs/generated/std/timeit.cs"), pairs)
        self.assertIn(("std/timeit", "go", "src/runtime/go/generated/std/timeit.go"), pairs)
        self.assertIn(("std/timeit", "java", "src/runtime/java/generated/std/timeit.java"), pairs)
        self.assertIn(("std/timeit", "kotlin", "src/runtime/kotlin/generated/std/timeit.kt"), pairs)
        self.assertIn(("std/timeit", "scala", "src/runtime/scala/generated/std/timeit.scala"), pairs)
        self.assertIn(("std/timeit", "swift", "src/runtime/swift/generated/std/timeit.swift"), pairs)
        self.assertIn(("std/timeit", "nim", "src/runtime/nim/generated/std/timeit.nim"), pairs)
        self.assertIn(("std/timeit", "js", "src/runtime/js/generated/std/timeit.js"), pairs)
        self.assertIn(("std/timeit", "ts", "src/runtime/ts/generated/std/timeit.ts"), pairs)
        self.assertIn(("std/timeit", "ruby", "src/runtime/ruby/generated/std/timeit.rb"), pairs)
        self.assertIn(("std/timeit", "php", "src/runtime/php/generated/std/timeit.php"), pairs)
        self.assertIn(("utils/assertions", "go", "src/runtime/go/generated/utils/assertions.go"), pairs)
        self.assertIn(("utils/assertions", "rs", "src/runtime/rs/generated/utils/assertions.rs"), pairs)
        self.assertIn(("utils/assertions", "cs", "src/runtime/cs/generated/utils/assertions.cs"), pairs)
        self.assertIn(("utils/assertions", "java", "src/runtime/java/generated/utils/assertions.java"), pairs)
        self.assertIn(("utils/assertions", "kotlin", "src/runtime/kotlin/generated/utils/assertions.kt"), pairs)
        self.assertIn(("utils/assertions", "scala", "src/runtime/scala/generated/utils/assertions.scala"), pairs)
        self.assertIn(("utils/assertions", "swift", "src/runtime/swift/generated/utils/assertions.swift"), pairs)
        self.assertIn(("utils/assertions", "nim", "src/runtime/nim/generated/utils/assertions.nim"), pairs)
        self.assertIn(("utils/assertions", "js", "src/runtime/js/generated/utils/assertions.js"), pairs)
        self.assertIn(("utils/assertions", "ts", "src/runtime/ts/generated/utils/assertions.ts"), pairs)
        self.assertIn(("utils/assertions", "ruby", "src/runtime/ruby/generated/utils/assertions.rb"), pairs)
        self.assertIn(("utils/assertions", "php", "src/runtime/php/generated/utils/assertions.php"), pairs)
        self.assertIn(("built_in/predicates", "go", "src/runtime/go/generated/built_in/predicates.go"), pairs)
        self.assertIn(("built_in/predicates", "java", "src/runtime/java/generated/built_in/predicates.java"), pairs)
        self.assertIn(("built_in/sequence", "go", "src/runtime/go/generated/built_in/sequence.go"), pairs)
        self.assertIn(("built_in/sequence", "java", "src/runtime/java/generated/built_in/sequence.java"), pairs)
        self.assertIn(("built_in/scalar_ops", "swift", "src/runtime/swift/generated/built_in/scalar_ops.swift"), pairs)
        self.assertIn(("built_in/scalar_ops", "nim", "src/runtime/nim/generated/built_in/scalar_ops.nim"), pairs)
        self.assertIn(("built_in/string_ops", "go", "src/runtime/go/generated/built_in/string_ops.go"), pairs)
        self.assertIn(("built_in/string_ops", "java", "src/runtime/java/generated/built_in/string_ops.java"), pairs)
        self.assertIn(("built_in/string_ops", "swift", "src/runtime/swift/generated/built_in/string_ops.swift"), pairs)
        self.assertIn(("built_in/string_ops", "nim", "src/runtime/nim/generated/built_in/string_ops.nim"), pairs)
        self.assertIn(("built_in/numeric_ops", "swift", "src/runtime/swift/generated/built_in/numeric_ops.swift"), pairs)
        self.assertIn(("built_in/type_id", "go", "src/runtime/go/generated/built_in/type_id.go"), pairs)
        self.assertIn(("built_in/type_id", "java", "src/runtime/java/generated/built_in/type_id.java"), pairs)
        self.assertIn(("built_in/type_id", "swift", "src/runtime/swift/generated/built_in/type_id.swift"), pairs)
        self.assertIn(("built_in/type_id", "nim", "src/runtime/nim/generated/built_in/type_id.nim"), pairs)

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
        supported_by_target = {
            "go": {"contains", "io_ops", "iter_ops", "numeric_ops", "predicates", "scalar_ops", "sequence", "string_ops", "type_id", "zip_ops"},
            "java": {"contains", "io_ops", "iter_ops", "numeric_ops", "predicates", "scalar_ops", "sequence", "string_ops", "type_id", "zip_ops"},
            "kotlin": {"contains", "io_ops", "iter_ops", "numeric_ops", "predicates", "scalar_ops", "sequence", "string_ops", "type_id", "zip_ops"},
            "scala": {"contains", "io_ops", "iter_ops", "numeric_ops", "predicates", "scalar_ops", "sequence", "string_ops", "type_id", "zip_ops"},
            "swift": {"contains", "io_ops", "iter_ops", "numeric_ops", "predicates", "scalar_ops", "sequence", "string_ops", "type_id", "zip_ops"},
            "nim": {"contains", "io_ops", "iter_ops", "numeric_ops", "predicates", "scalar_ops", "sequence", "string_ops", "type_id", "zip_ops"},
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
            for target, supported in supported_by_target.items():
                suffix = {
                    "go": "go",
                    "java": "java",
                    "kotlin": "kt",
                    "scala": "scala",
                    "swift": "swift",
                    "nim": "nim",
                }[target]
                if module_name in supported:
                    self.assertEqual(
                        by_pair[(item_id, target)],
                        f"src/runtime/{target}/generated/built_in/{module_name}.{suffix}",
                    )
                else:
                    self.assertNotIn((item_id, target), by_pair)

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

    def test_rewrite_cs_std_native_owner_wrapper_targets_time_native(self) -> None:
        src = "\n".join(
            [
                "using Pytra.CsModule;",
                "public static class Program",
                "{",
                "    public static double perf_counter() { return __t.perf_counter(); }",
                "}",
            ]
        )
        out = gen_mod.rewrite_cs_std_native_owner_wrapper(src, "time")
        self.assertIn("namespace Pytra.CsModule", out)
        self.assertIn("public static class time", out)
        self.assertIn("return time_native.perf_counter();", out)
        self.assertNotIn("return __t.perf_counter();", out)

    def test_rewrite_cs_std_math_live_wrapper_delegates_to_math_native(self) -> None:
        src = "\n".join(
            [
                "using Pytra.CsModule;",
                "public static class Program",
                "{",
                "    public static double sqrt(double x) { return __m.sqrt(x); }",
                "    public static double ceil(double x) { return __m.ceil(x); }",
                "    public static void Main(string[] args) { double pi = System.Convert.ToDouble(py_extern(__m.pi)); }",
                "}",
            ]
        )
        out = gen_mod.rewrite_cs_std_math_live_wrapper(src)
        self.assertIn("namespace Pytra.CsModule", out)
        self.assertIn("public static class math", out)
        self.assertIn("public static double pi { get { return math_native.pi; } }", out)
        self.assertIn("public static double e { get { return math_native.e; } }", out)
        self.assertIn("return math_native.sqrt(x);", out)
        self.assertIn("return math_native.ceil(x);", out)
        self.assertNotIn("__m.", out)
        self.assertNotIn("py_extern(", out)
        self.assertNotIn("Math.", out)

    def test_rewrite_cs_std_json_live_wrapper_exports_json_facade(self) -> None:
        src = "\n".join(
            [
                "using Pytra.CsModule;",
                "public static class Program",
                "{",
                "    public class JsonObj { }",
                "    public class JsonArr { }",
                "    public class JsonValue { }",
                "    public static object loads(string text) { return text; }",
                "    public static JsonObj loads_obj(string text) { return null; }",
                "    public static JsonArr loads_arr(string text) { return null; }",
                "    public static string dumps(object obj) { return obj.ToString(); }",
                "}",
            ]
        )
        out = gen_mod.rewrite_cs_std_json_live_wrapper(src)
        self.assertIn("namespace Pytra.CsModule", out)
        self.assertIn("public class JsonObj", out)
        self.assertIn("public class JsonArr", out)
        self.assertIn("public class JsonValue", out)
        self.assertIn("public static class json", out)
        self.assertIn("public static object loads(string text)", out)
        self.assertIn("public static JsonObj loads_obj(string text)", out)
        self.assertIn("public static JsonArr loads_arr(string text)", out)
        self.assertIn("public static string dumps(object obj)", out)
        self.assertNotIn("public static class Program", out)

    def test_rewrite_cs_std_pathlib_live_wrapper_exports_py_path_facade(self) -> None:
        src = "\n".join(
            [
                "using Pytra.CsModule;",
                "public class Path",
                "{",
                "    public Path __truediv__(string rhs) { return new Path(); }",
                "    public Path parent() { return new Path(); }",
                "    public string name() { return \"n\"; }",
                "    public string stem() { return \"s\"; }",
                "    public Path resolve() { return new Path(); }",
                "    public bool exists() { return true; }",
                "    public string read_text(string encoding = \"utf-8\") { return \"\"; }",
                "    public long write_text(string text, string encoding = \"utf-8\") { return 0; }",
                "    public System.Collections.Generic.List<Path> glob(string pattern) { return null; }",
                "    public static Path cwd() { return new Path(); }",
                "}",
            ]
        )
        out = gen_mod.rewrite_cs_std_pathlib_live_wrapper(src)
        self.assertIn("namespace Pytra.CsModule", out)
        self.assertIn("public class py_path", out)
        self.assertIn("public static py_path operator /", out)
        self.assertIn("public py_path parent()", out)
        self.assertIn("public string name()", out)
        self.assertIn("public string stem()", out)
        self.assertIn('public string read_text(string encoding = "utf-8")', out)
        self.assertIn('public long write_text(string text, string encoding = "utf-8")', out)
        self.assertIn("public static py_path cwd()", out)
        self.assertNotIn("public static class Program", out)

    def test_rewrite_rs_std_time_live_wrapper_targets_runtime_perf_counter(self) -> None:
        src = "\n".join(
            [
                "// AUTO-GENERATED FILE. DO NOT EDIT.",
                "// source: src/pytra/std/time.py",
                "// generated-by: tools/gen_runtime_from_manifest.py",
                "",
                "fn perf_counter() -> f64 {",
                "    return __t.perf_counter();",
                "}",
            ]
        )
        out = gen_mod.rewrite_rs_std_time_live_wrapper(src)
        self.assertIn("pub fn perf_counter() -> f64 {", out)
        self.assertIn("crate::py_runtime::perf_counter()", out)
        self.assertNotIn("__t.perf_counter()", out)

    def test_rewrite_rs_std_math_live_wrapper_exports_std_math_facade(self) -> None:
        src = "\n".join(
            [
                "// AUTO-GENERATED FILE. DO NOT EDIT.",
                "// source: src/pytra/std/math.py",
                "// generated-by: tools/gen_runtime_from_manifest.py",
                "",
                "fn sqrt(x: f64) -> f64 {",
                "    return __m.sqrt(x);",
                "}",
            ]
        )
        out = gen_mod.rewrite_rs_std_math_live_wrapper(src)
        self.assertIn("pub const pi: f64 = ::std::f64::consts::PI;", out)
        self.assertIn("pub const e: f64 = ::std::f64::consts::E;", out)
        self.assertIn("pub trait ToF64 {", out)
        self.assertIn("pub fn sqrt<T: ToF64>(v: T) -> f64 {", out)
        self.assertIn("pub fn pow(a: f64, b: f64) -> f64 {", out)
        self.assertNotIn("__m.", out)

    def test_rewrite_kotlin_program_to_library_removes_empty_main(self) -> None:
        src = "\n".join(
            [
                "fun py_contains_str_object(values: Any?, key: Any?): Boolean {",
                "    return true",
                "}",
                "",
                "fun main(args: Array<String>) {",
                "}",
            ]
        )
        out = gen_mod.rewrite_kotlin_program_to_library(src)
        self.assertIn("fun py_contains_str_object(values: Any?, key: Any?): Boolean {", out)
        self.assertNotIn("fun main(args: Array<String>) {", out)

    def test_rewrite_scala_program_to_library_removes_empty_main(self) -> None:
        src = "\n".join(
            [
                "def py_contains_str_object(values: Any, key: Any): Boolean = {",
                "    true",
                "}",
                "",
                "def main(args: Array[String]): Unit = {",
                "}",
            ]
        )
        out = gen_mod.rewrite_scala_program_to_library(src)
        self.assertIn("def py_contains_str_object(values: Any, key: Any): Boolean = {", out)
        self.assertNotIn("def main(args: Array[String]): Unit = {", out)

    def test_rewrite_swift_program_to_library_removes_empty_main(self) -> None:
        src = "\n".join(
            [
                "func py_contains_str_object(_ values: Any, _ key: Any) -> Bool {",
                "    true",
                "}",
                "",
                "@main",
                "struct Main {",
                "    static func main() {",
                "    }",
                "}",
            ]
        )
        out = gen_mod.rewrite_swift_program_to_library(src)
        self.assertIn("func py_contains_str_object(_ values: Any, _ key: Any) -> Bool {", out)
        self.assertNotIn("@main", out)

    def test_render_item_round_trip_preserves_embedded_carriage_return_literals(self) -> None:
        items = gen_mod.load_manifest_items(ROOT / "tools" / "runtime_generation_manifest.json")
        item = next(i for i in items if i.item_id == "built_in/string_ops" and i.target == "nim")
        rendered = gen_mod.render_item(item)
        with (ROOT / item.output_rel).open("r", encoding="utf-8", newline="") as handle:
            current = handle.read()
        self.assertEqual(current, rendered)
        self.assertIn("\r", current)

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
                "nim -> src/runtime/nim/generated/utils/png.nim",
            ):
                gen_mod.run_py2x(
                    "nim",
                    "src/pytra/utils/png.py",
                    "src/runtime/nim/generated/utils/png.nim",
                )

    def test_run_py2x_nim_png_lowers_try_finally(self) -> None:
        out = gen_mod.run_py2x(
            "nim",
            "src/pytra/utils/png.py",
            "src/runtime/nim/generated/utils/png.nim",
        )
        self.assertIn("f.write(png)", out)
        self.assertIn("f.close()", out)
        self.assertNotIn("# unsupported stmt: Try", out)

    def test_run_py2x_lua_gif_canonical_name_ignores_compile_time_std_imports(self) -> None:
        out = gen_mod.run_py2x(
            "lua",
            "src/pytra/utils/gif.py",
            "src/runtime/lua/generated/utils/gif.lua",
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
        self.assertEqual(checked, 125)
        self.assertEqual(updated, 0)


if __name__ == "__main__":
    unittest.main()
