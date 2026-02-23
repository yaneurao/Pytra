"""Regression tests that verify major py2cpp compatibility features at runtime."""

from __future__ import annotations

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

# Subprocess timeouts for py2cpp feature tests.
# Override with env vars when longer runs are needed on slower machines.
PYTRA_TEST_COMPILE_TIMEOUT_SEC = float(os.environ.get("PYTRA_TEST_COMPILE_TIMEOUT_SEC", "120"))
PYTRA_TEST_RUN_TIMEOUT_SEC = float(os.environ.get("PYTRA_TEST_RUN_TIMEOUT_SEC", "2"))
PYTRA_TEST_TOOL_TIMEOUT_SEC = float(os.environ.get("PYTRA_TEST_TOOL_TIMEOUT_SEC", "120"))

from src.pytra.compiler.transpile_cli import append_unique_non_empty, assign_targets, collect_import_modules, collect_store_names_from_target, collect_symbols_from_stmt, collect_symbols_from_stmt_list, count_text_lines, dict_any_get, dict_any_get_str, dict_any_get_list, dict_any_get_dict, dict_any_get_dict_list, dict_any_get_str_list, dict_any_kind, dict_str_get, dump_codegen_options_text, extract_function_arg_types_from_python_source, extract_function_signatures_from_python_source, first_import_detail_line, format_graph_list_section, graph_cycle_dfs, inject_after_includes_block, is_known_non_user_import, is_pytra_module_name, join_str_list, local_binding_name, looks_like_runtime_function_name, make_user_error, meta_import_bindings, meta_qualified_symbol_refs, mkdirs_for_cli, module_analyze_metrics, module_id_from_east_for_graph, module_name_from_path_for_graph, module_parse_metrics, module_rel_label, name_target_id, normalize_param_annotation, parse_py2cpp_argv, parse_guard_limit_or_raise, guard_profile_base_limits, parse_user_error, path_key_for_graph, path_parent_text, python_module_exists_under, rel_disp_for_graph, replace_first, resolve_codegen_options, resolve_module_name_for_graph, resolve_user_module_path_for_graph, sanitize_module_label, select_guard_module_map, set_import_module_binding, set_import_symbol_binding, set_import_symbol_binding_and_module_set, sort_str_list_copy, split_graph_issue_entry, split_infix_once, split_top_level_csv, split_top_level_union, split_type_args, split_ws_tokens, stmt_assigned_names, stmt_child_stmt_lists, stmt_list_parse_metrics, stmt_list_scope_depth, stmt_target_name, write_text_file
from src.py2cpp import (
    _analyze_import_graph,
    _runtime_module_tail_from_source_path,
    _runtime_namespace_for_tail,
    _runtime_output_rel_tail,
    build_module_east_map,
    build_module_symbol_index,
    build_module_type_schema,
    dump_deps_text,
    dump_deps_graph_text,
    load_cpp_module_attr_call_map,
    load_east,
    resolve_module_name,
    transpile_to_cpp,
)

CPP_RUNTIME_SRCS = [
    "src/runtime/cpp/pytra/built_in/gc.cpp",
    "src/runtime/cpp/pytra/std/pathlib.cpp",
    "src/runtime/cpp/pytra/std/time.cpp",
    "src/runtime/cpp/pytra/std/time-impl.cpp",
    "src/runtime/cpp/pytra/std/math.cpp",
    "src/runtime/cpp/pytra/std/math-impl.cpp",
    "src/runtime/cpp/pytra/std/random.cpp",
    "src/runtime/cpp/pytra/std/dataclasses.cpp",
    "src/runtime/cpp/pytra/std/glob.cpp",
    "src/runtime/cpp/pytra/std/json.cpp",
    "src/runtime/cpp/pytra/std/re.cpp",
    "src/runtime/cpp/pytra/std/sys.cpp",
    "src/runtime/cpp/pytra/std/timeit.cpp",
    "src/runtime/cpp/pytra/std/traceback.cpp",
    "src/runtime/cpp/pytra/std/typing.cpp",
    "src/runtime/cpp/pytra/built_in/io.cpp",
    "src/runtime/cpp/pytra/built_in/bytes_util.cpp",
    "src/runtime/cpp/pytra/utils/png.cpp",
    "src/runtime/cpp/pytra/utils/gif.cpp",
    "src/runtime/cpp/pytra/utils/assertions.cpp",
]

def find_fixture_case(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixtures").rglob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(f"missing fixture: {stem}")
    return matches[0]


def transpile(input_py: Path, output_cpp: Path) -> None:
    east = load_east(input_py)
    cpp = transpile_to_cpp(east)
    output_cpp.write_text(cpp, encoding="utf-8")


class Py2CppFeatureTest(unittest.TestCase):
    _selected_test_methods: list[str] = []
    _progress_total: int = 0
    _progress_index: int = 0

    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        if methodName.startswith("test_"):
            self.__class__._selected_test_methods.append(methodName)

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        seen: set[str] = set()
        deduped: list[str] = []
        for name in cls._selected_test_methods:
            if name not in seen:
                seen.add(name)
                deduped.append(name)
        cls._selected_test_methods = deduped
        cls._progress_total = len(deduped)
        cls._progress_index = 0

    def setUp(self) -> None:
        super().setUp()
        cls = self.__class__
        cls._progress_index += 1
        total_txt = str(cls._progress_total) if cls._progress_total > 0 else "?"
        print(f"[{cls._progress_index}/{total_txt}] {self.id()}", flush=True)

    def _run_subprocess_with_timeout(
        self,
        args: list[str],
        *,
        cwd: Path,
        timeout_sec: float,
        label: str,
    ) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout_sec)
        except subprocess.TimeoutExpired as ex:
            out_obj = ex.stdout
            err_obj = ex.stderr
            out_txt = out_obj if isinstance(out_obj, str) else ""
            err_txt = err_obj if isinstance(err_obj, str) else ""
            self.fail(
                f"{label} timed out after {timeout_sec:.1f}s: {' '.join(args)}\n"
                f"stdout:\n{out_txt}\n"
                f"stderr:\n{err_txt}"
            )
            raise AssertionError("unreachable")

    def test_runtime_module_tail_and_namespace_support_compiler_tree(self) -> None:
        self.assertEqual(_runtime_module_tail_from_source_path(Path("src/pytra/std/math.py")), "std/math")
        self.assertEqual(_runtime_module_tail_from_source_path(Path("src/pytra/utils/png.py")), "png")
        self.assertEqual(
            _runtime_module_tail_from_source_path(Path("src/pytra/compiler/east_parts/core.py")),
            "compiler/east_parts/core",
        )
        self.assertEqual(_runtime_module_tail_from_source_path(Path("sample/py/01_mandelbrot.py")), "")

        self.assertEqual(_runtime_output_rel_tail("std/math_impl"), "std/math-impl")
        self.assertEqual(_runtime_output_rel_tail("json"), "utils/json")
        self.assertEqual(_runtime_output_rel_tail("compiler/east_parts/core_impl"), "compiler/east_parts/core-impl")

        self.assertEqual(_runtime_namespace_for_tail("std/math"), "pytra::std::math")
        self.assertEqual(_runtime_namespace_for_tail("json"), "pytra::utils::json")
        self.assertEqual(_runtime_namespace_for_tail("compiler/east_parts/core"), "pytra::compiler::east_parts::core")

    def test_preset_resolution_and_override(self) -> None:
        neg, bnd, fdiv, mod, iw, sidx, ssli, opt = resolve_codegen_options("native", "", "", "", "", "", "", "", "")
        self.assertEqual((neg, bnd, fdiv, mod, iw, sidx, ssli, opt), ("off", "off", "native", "native", "64", "native", "byte", "3"))

        neg, bnd, fdiv, mod, iw, sidx, ssli, opt = resolve_codegen_options("balanced", "", "", "", "", "", "", "", "")
        self.assertEqual((neg, bnd, fdiv, mod, iw, sidx, ssli, opt), ("const_only", "debug", "python", "python", "64", "byte", "byte", "2"))

        neg, bnd, fdiv, mod, iw, sidx, ssli, opt = resolve_codegen_options("python", "", "", "", "", "", "", "", "")
        self.assertEqual((neg, bnd, fdiv, mod, iw, sidx, ssli, opt), ("always", "always", "python", "python", "bigint", "codepoint", "codepoint", "0"))

        neg, bnd, fdiv, mod, iw, sidx, ssli, opt = resolve_codegen_options("native", "", "", "python", "", "32", "byte", "byte", "")
        self.assertEqual((neg, bnd, fdiv, mod, iw, sidx, ssli, opt), ("off", "off", "python", "native", "32", "byte", "byte", "3"))

    def test_dump_options_text_contains_resolved_values(self) -> None:
        txt = dump_codegen_options_text("balanced", "const_only", "debug", "python", "python", "64", "byte", "byte", "2")
        self.assertIn("preset: balanced", txt)
        self.assertIn("negative-index-mode: const_only", txt)
        self.assertIn("bounds-check-mode: debug", txt)
        self.assertIn("floor-div-mode: python", txt)
        self.assertIn("mod-mode: python", txt)
        self.assertIn("int-width: 64", txt)
        self.assertIn("str-index-mode: byte", txt)
        self.assertIn("str-slice-mode: byte", txt)
        self.assertIn("opt-level: 2", txt)

    def test_sort_str_list_copy_returns_sorted_copy(self) -> None:
        items = ["z", "b", "a", "b"]
        sorted_items = sort_str_list_copy(items)
        self.assertEqual(sorted_items, ["a", "b", "b", "z"])
        self.assertEqual(items, ["z", "b", "a", "b"])

    def test_join_str_list_joins_items(self) -> None:
        self.assertEqual(join_str_list(" / ", ["a", "b", "c"]), "a / b / c")
        self.assertEqual(join_str_list("", []), "")

    def test_split_infix_once_splits_first_match(self) -> None:
        left, right, ok = split_infix_once("a:b:c", ":")
        self.assertTrue(ok)
        self.assertEqual(left, "a")
        self.assertEqual(right, "b:c")
        left2, right2, ok2 = split_infix_once("abc", ":")
        self.assertFalse(ok2)
        self.assertEqual(left2, "")
        self.assertEqual(right2, "")

    def test_replace_first_replaces_single_match(self) -> None:
        self.assertEqual(replace_first("aaab", "a", "x"), "xaab")
        self.assertEqual(replace_first("hello", "z", "x"), "hello")

    def test_inject_after_includes_block(self) -> None:
        src = "#include <a>\n#include <b>\n\nint main(){}\n"
        injected = inject_after_includes_block(src, "namespace x {}\n")
        self.assertIn("#include <b>\n\nnamespace x {}\n\nint main(){}", injected)
        self.assertEqual(inject_after_includes_block("int main(){}\n", ""), "int main(){}\n")

    def test_make_and_parse_user_error_roundtrip(self) -> None:
        err = make_user_error("input_invalid", "bad input", ["line 1", "line 2"])
        parsed = parse_user_error(str(err))
        self.assertEqual(parsed["category"], "input_invalid")
        self.assertEqual(parsed["summary"], "bad input")
        self.assertEqual(parsed["details"], ["line 1", "line 2"])

    def test_parse_user_error_non_tagged_text(self) -> None:
        parsed = parse_user_error("plain runtime error")
        self.assertEqual(parsed["category"], "")
        self.assertEqual(parsed["summary"], "")
        self.assertEqual(parsed["details"], [])

    def test_first_import_detail_line_extracts_wildcard_and_relative(self) -> None:
        src = (
            "# comment\n"
            "from pkg.mod import *\n"
            "from .local import name\n"
        )
        self.assertEqual(first_import_detail_line(src, "wildcard"), "from pkg.mod import *")
        self.assertEqual(first_import_detail_line(src, "relative"), "from .local import name")

    def test_first_import_detail_line_fallback(self) -> None:
        src = "print('x')\n"
        self.assertEqual(first_import_detail_line(src, "wildcard"), "from ... import *")
        self.assertEqual(first_import_detail_line(src, "relative"), "from .module import symbol")

    def test_split_ws_tokens_splits_ascii_whitespace(self) -> None:
        self.assertEqual(split_ws_tokens("a b\tc"), ["a", "b", "c"])
        self.assertEqual(split_ws_tokens("  a   b  "), ["a", "b"])
        self.assertEqual(split_ws_tokens(""), [])

    def test_split_top_level_csv_splits_only_top_level_commas(self) -> None:
        self.assertEqual(split_top_level_csv("a,b,(c,d),e"), ["a", "b", "(c,d)", "e"])
        self.assertEqual(split_top_level_csv("list[int], dict[str, int]"), ["list[int]", "dict[str, int]"])
        self.assertEqual(split_top_level_csv(""), [])

    def test_split_type_args_splits_bracket_nested_commas(self) -> None:
        self.assertEqual(split_type_args("A,B[C,D],E"), ["A", "B[C,D]", "E"])
        self.assertEqual(split_type_args(""), [])

    def test_split_top_level_union_splits_only_top_level_pipe(self) -> None:
        self.assertEqual(split_top_level_union("A|B[list[C|D]]"), ["A", "B[list[C|D]]"])
        self.assertEqual(split_top_level_union("A|B|C"), ["A", "B", "C"])
        self.assertEqual(split_top_level_union(""), [])

    def test_path_parent_text_returns_parent_dir(self) -> None:
        self.assertEqual(path_parent_text(Path("a/b/c.txt")), "a/b")
        self.assertEqual(path_parent_text(Path("file.txt")), ".")

    def test_python_module_exists_under_detects_py_and_package(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "pkg").mkdir(parents=True)
            (root / "pkg" / "__init__.py").write_text("", encoding="utf-8")
            (root / "mod.py").write_text("# test\n", encoding="utf-8")
            self.assertTrue(python_module_exists_under(root, "pkg"))
            self.assertTrue(python_module_exists_under(root, "mod"))
            self.assertFalse(python_module_exists_under(root, "missing"))
            self.assertFalse(python_module_exists_under(root, ""))

    def test_graph_path_helpers(self) -> None:
        self.assertEqual(path_key_for_graph(Path("a/b.py")), "a/b.py")
        self.assertEqual(rel_disp_for_graph(Path("a"), Path("a/b/c.py")), "b/c.py")
        self.assertEqual(rel_disp_for_graph(Path("a"), Path("a")), ".")
        self.assertEqual(rel_disp_for_graph(Path("a"), Path("x/y.py")), "x/y.py")

    def test_module_name_from_path_for_graph(self) -> None:
        self.assertEqual(
            module_name_from_path_for_graph(Path("pkg"), Path("pkg/sub/mod.py")),
            "sub.mod",
        )
        self.assertEqual(
            module_name_from_path_for_graph(Path("pkg"), Path("pkg/sub/__init__.py")),
            "sub",
        )
        self.assertEqual(
            module_name_from_path_for_graph(Path("pkg"), Path("/tmp/other.py")),
            "other",
        )

    def test_sanitize_module_label(self) -> None:
        self.assertEqual(sanitize_module_label("a/b-c"), "a_b_c")
        self.assertEqual(sanitize_module_label(""), "module")
        self.assertEqual(sanitize_module_label("9abc"), "_9abc")

    def test_module_rel_label(self) -> None:
        self.assertEqual(
            module_rel_label(Path("pkg"), Path("pkg/sub/mod.py")),
            "sub__mod",
        )
        self.assertEqual(
            module_rel_label(Path("pkg"), Path("/tmp/other.py")),
            "__tmp__other",
        )

    def test_module_id_from_east_for_graph(self) -> None:
        self.assertEqual(
            module_id_from_east_for_graph(
                Path("pkg"),
                Path("pkg/sub/mod.py"),
                {"meta": {"module_id": "m.sub.mod"}},
            ),
            "m.sub.mod",
        )
        self.assertEqual(
            module_id_from_east_for_graph(
                Path("pkg"),
                Path("pkg/sub/mod.py"),
                {"meta": {}},
            ),
            "sub.mod",
        )

    def test_collect_import_modules(self) -> None:
        east_module: dict[str, object] = {
            "body": [
                {"kind": "Import", "names": [{"name": "os"}, {"name": "os"}]},
                {"kind": "ImportFrom", "module": "pkg.mod", "names": [{"name": "X"}]},
                {"kind": "Expr"},
            ]
        }
        self.assertEqual(collect_import_modules(east_module), ["os", "pkg.mod"])

    def test_is_known_non_user_import(self) -> None:
        self.assertTrue(
            is_known_non_user_import("__future__", Path("/tmp/missing_std"), Path("/tmp/missing_utils"))
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            std_root = root / "std"
            utils_root = root / "utils"
            std_root.mkdir(parents=True)
            utils_root.mkdir(parents=True)
            (std_root / "pkg").mkdir(parents=True)
            (std_root / "pkg" / "__init__.py").write_text("", encoding="utf-8")
            (utils_root / "mod.py").write_text("", encoding="utf-8")
            self.assertTrue(is_known_non_user_import("pkg", std_root, utils_root))
            self.assertTrue(is_known_non_user_import("mod", std_root, utils_root))
            self.assertFalse(is_known_non_user_import("missing_mod", std_root, utils_root))

    def test_resolve_module_name_for_graph(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            std_root = root / "std"
            utils_root = root / "utils"
            std_root.mkdir(parents=True)
            utils_root.mkdir(parents=True)
            (utils_root / "known.py").write_text("", encoding="utf-8")
            user_pkg = root / "pkg"
            user_pkg.mkdir(parents=True)
            (user_pkg / "__init__.py").write_text("", encoding="utf-8")
            self.assertEqual(
                resolve_module_name_for_graph(".rel", root, std_root, utils_root)["status"],
                "relative",
            )
            self.assertEqual(
                resolve_module_name_for_graph("pytra.std.math", root, std_root, utils_root)["status"],
                "pytra",
            )
            user_resolved = resolve_module_name_for_graph("pkg", root, std_root, utils_root)
            self.assertEqual(user_resolved["status"], "user")
            self.assertNotEqual(user_resolved["path"], "")
            self.assertEqual(
                resolve_module_name_for_graph("known", root, std_root, utils_root)["status"],
                "known",
            )
            self.assertEqual(
                resolve_module_name_for_graph("missing_mod", root, std_root, utils_root)["status"],
                "missing",
            )

    def test_graph_cycle_dfs_collects_cycle(self) -> None:
        graph_adj = {"a": ["b"], "b": ["a"]}
        key_to_disp = {"a": "a.py", "b": "b.py"}
        color: dict[str, int] = {}
        stack: list[str] = []
        cycles: list[str] = []
        cycle_seen: set[str] = set()
        graph_cycle_dfs("a", graph_adj, key_to_disp, color, stack, cycles, cycle_seen)
        self.assertEqual(cycles, ["a.py -> b.py -> a.py"])
        self.assertEqual(color.get("a"), 2)
        self.assertEqual(color.get("b"), 2)
        self.assertEqual(stack, [])

    def test_resolve_user_module_path_for_graph_prefers_package_init(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            search_root = root / "app" / "nested"
            search_root.mkdir(parents=True)
            pkg_init = root / "pkg" / "__init__.py"
            pkg_init.parent.mkdir(parents=True)
            pkg_init.write_text("", encoding="utf-8")
            (root / "pkg.py").write_text("", encoding="utf-8")
            resolved = resolve_user_module_path_for_graph("pkg", search_root)
            self.assertEqual(str(resolved), str(pkg_init))
            self.assertEqual(
                str(resolve_user_module_path_for_graph("missing_mod", search_root)),
                "",
            )

    def test_format_graph_list_section(self) -> None:
        self.assertEqual(
            format_graph_list_section("graph:\n", "cycles", ["a -> b"]),
            "graph:\ncycles:\n  - a -> b\n",
        )
        self.assertEqual(
            format_graph_list_section("graph:\n", "missing", []),
            "graph:\nmissing:\n  (none)\n",
        )

    def test_append_unique_non_empty_appends_once(self) -> None:
        items = ["a"]
        seen = {"a"}
        append_unique_non_empty(items, seen, "a")
        append_unique_non_empty(items, seen, "")
        append_unique_non_empty(items, seen, "b")
        self.assertEqual(items, ["a", "b"])
        self.assertEqual(seen, {"a", "b"})

    def test_mkdirs_for_cli_creates_directory(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "nested" / "dir"
            self.assertFalse(target.exists())
            mkdirs_for_cli(str(target))
            self.assertTrue(target.exists())
            self.assertTrue(target.is_dir())
            mkdirs_for_cli("")

    def test_write_text_file_writes_text(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "out.txt"
            write_text_file(out, "abc")
            self.assertEqual(out.read_text(encoding="utf-8"), "abc")

    def test_count_text_lines_counts_newlines(self) -> None:
        self.assertEqual(count_text_lines(""), 0)
        self.assertEqual(count_text_lines("a"), 1)
        self.assertEqual(count_text_lines("a\nb"), 2)
        self.assertEqual(count_text_lines("a\n"), 2)

    def test_dict_any_get_str_returns_default_for_non_str(self) -> None:
        data: dict[str, object] = {"a": "x", "b": 1}
        self.assertEqual(dict_any_get_str(data, "a", ""), "x")
        self.assertEqual(dict_any_get_str(data, "b", "d"), "d")
        self.assertEqual(dict_any_get_str(data, "missing", "d"), "d")

    def test_dict_any_get_returns_none_for_missing(self) -> None:
        data: dict[str, object] = {"a": "x", "b": 1}
        self.assertEqual(dict_any_get(data, "a"), "x")
        self.assertEqual(dict_any_get(data, "b"), 1)
        self.assertIsNone(dict_any_get(data, "missing"))

    def test_dict_any_kind(self) -> None:
        self.assertEqual(dict_any_kind({"kind": "Name"}), "Name")
        self.assertEqual(dict_any_kind({"kind": 1}), "")
        self.assertEqual(dict_any_kind({}), "")

    def test_name_target_id_returns_name_only(self) -> None:
        self.assertEqual(name_target_id({"kind": "Name", "id": "x"}), "x")
        self.assertEqual(name_target_id({"kind": "Attribute", "id": "x"}), "")
        self.assertEqual(name_target_id({"kind": "Name", "id": 1}), "")

    def test_stmt_target_name_reads_target_field(self) -> None:
        self.assertEqual(stmt_target_name({"target": {"kind": "Name", "id": "x"}}), "x")
        self.assertEqual(stmt_target_name({"target": {"kind": "Attribute", "id": "x"}}), "")
        self.assertEqual(stmt_target_name({"target": "bad"}), "")

    def test_stmt_assigned_names_collects_assign_and_annassign(self) -> None:
        assign_stmt: dict[str, object] = {
            "kind": "Assign",
            "targets": [{"kind": "Name", "id": "x"}, {"kind": "Attribute", "id": "y"}],
        }
        annassign_stmt: dict[str, object] = {
            "kind": "AnnAssign",
            "target": {"kind": "Name", "id": "z"},
        }
        expr_stmt: dict[str, object] = {"kind": "Expr"}
        self.assertEqual(stmt_assigned_names(assign_stmt), ["x"])
        self.assertEqual(stmt_assigned_names(annassign_stmt), ["z"])
        self.assertEqual(stmt_assigned_names(expr_stmt), [])

    def test_stmt_child_stmt_lists_extracts_nested_blocks(self) -> None:
        stmt: dict[str, object] = {
            "body": [{"kind": "Expr"}],
            "orelse": [{"kind": "Pass"}],
            "finalbody": [{"kind": "Expr"}],
            "handlers": [{"body": [{"kind": "ExceptHandler"}]}, {"body": "bad"}],
            "cases": [{"body": [{"kind": "MatchCase"}]}, {"body": "bad"}],
        }
        out = stmt_child_stmt_lists(stmt)
        self.assertEqual(len(out), 5)
        self.assertEqual(out[0], [{"kind": "Expr"}])
        self.assertEqual(out[1], [{"kind": "Pass"}])
        self.assertEqual(out[2], [{"kind": "Expr"}])
        self.assertEqual(out[3], [{"kind": "ExceptHandler"}])
        self.assertEqual(out[4], [{"kind": "MatchCase"}])
        self.assertEqual(stmt_child_stmt_lists({}), [])

    def test_collect_store_names_from_target_extracts_nested_names(self) -> None:
        out: set[str] = set()
        collect_store_names_from_target({"kind": "Name", "id": "x"}, out)
        self.assertEqual(out, {"x"})

        out2: set[str] = set()
        collect_store_names_from_target(
            {
                "kind": "Tuple",
                "elements": [
                    {"kind": "Name", "id": "a"},
                    {"kind": "List", "elements": [{"kind": "Name", "id": "b"}, {"kind": "Attribute", "id": "c"}]},
                ],
            },
            out2,
        )
        self.assertEqual(out2, {"a", "b"})

        out3: set[str] = set()
        collect_store_names_from_target({"kind": "Name", "id": 1}, out3)
        self.assertEqual(out3, set())

    def test_stmt_list_parse_metrics_counts_nodes_and_depth(self) -> None:
        body: list[dict[str, object]] = [
            {
                "kind": "If",
                "body": [{"kind": "Expr"}],
                "orelse": [{"kind": "Pass"}],
            },
            {"kind": "Expr"},
        ]
        nodes, depth = stmt_list_parse_metrics(body, 1)
        self.assertEqual(nodes, 4)
        self.assertEqual(depth, 2)
        self.assertEqual(stmt_list_parse_metrics([], 1), (0, 0))

    def test_stmt_list_scope_depth_counts_nesting(self) -> None:
        body: list[dict[str, object]] = [
            {
                "kind": "FunctionDef",
                "body": [
                    {
                        "kind": "If",
                        "body": [
                            {
                                "kind": "For",
                                "body": [{"kind": "Expr"}],
                            },
                        ],
                    },
                ],
            },
            {"kind": "Expr"},
        ]
        scope_kinds = {"FunctionDef", "If", "For"}
        self.assertEqual(stmt_list_scope_depth(body, 0, scope_kinds), 3)
        self.assertEqual(stmt_list_scope_depth([], 0, scope_kinds), 0)

    def test_module_parse_metrics_counts_nodes_and_depth(self) -> None:
        module: dict[str, object] = {
            "body": [
                {"kind": "Expr"},
                {"kind": "If", "body": [{"kind": "Expr"}], "orelse": []},
            ],
        }
        self.assertEqual(module_parse_metrics(module), {"max_ast_depth": 2, "parse_nodes": 4})
        self.assertEqual(module_parse_metrics({}), {"max_ast_depth": 1, "parse_nodes": 1})

    def test_collect_symbols_from_stmt_handles_major_kinds(self) -> None:
        self.assertEqual(
            collect_symbols_from_stmt(
                {
                    "kind": "FunctionDef",
                    "name": "f",
                    "arg_order": ["x", "y", 1],
                },
            ),
            {"f", "x", "y"},
        )
        self.assertEqual(
            collect_symbols_from_stmt(
                {
                    "kind": "With",
                    "items": [
                        {"optional_vars": {"kind": "Name", "id": "a"}},
                        {"optional_vars": {"kind": "Tuple", "elements": [{"kind": "Name", "id": "b"}]}},
                    ],
                },
            ),
            {"a", "b"},
        )
        self.assertEqual(
            collect_symbols_from_stmt(
                {"kind": "ImportFrom", "names": [{"name": "v", "asname": "u"}, {"name": "*"}]},
            ),
            {"u"},
        )

    def test_collect_symbols_from_stmt_list_walks_nested_blocks(self) -> None:
        body: list[dict[str, object]] = [
            {
                "kind": "FunctionDef",
                "name": "f",
                "arg_order": ["x"],
                "body": [
                    {"kind": "Assign", "targets": [{"kind": "Name", "id": "y"}]},
                    {"kind": "For", "target": {"kind": "Name", "id": "i"}, "body": [{"kind": "Expr"}]},
                ],
            },
            {"kind": "ImportFrom", "names": [{"name": "v", "asname": "u"}]},
        ]
        self.assertEqual(collect_symbols_from_stmt_list(body), {"f", "x", "y", "i", "u"})
        self.assertEqual(collect_symbols_from_stmt_list([]), set())

    def test_module_analyze_metrics_counts_symbols_and_scope(self) -> None:
        module: dict[str, object] = {
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "f",
                    "arg_order": ["x"],
                    "body": [
                        {
                            "kind": "For",
                            "target": {"kind": "Name", "id": "i"},
                            "body": [{"kind": "Assign", "targets": [{"kind": "Name", "id": "y"}]}],
                        },
                    ],
                },
            ],
        }
        scope_kinds = {"FunctionDef", "For"}
        self.assertEqual(module_analyze_metrics(module, scope_kinds), {"symbols": 4, "scope_depth": 2})
        self.assertEqual(module_analyze_metrics({}, scope_kinds), {"symbols": 0, "scope_depth": 0})

    def test_select_guard_module_map_uses_cache_then_input_key(self) -> None:
        cached: dict[str, dict[str, object]] = {"a.py": {"kind": "Module"}}
        self.assertEqual(select_guard_module_map("in.py", {"kind": "Module"}, cached), cached)
        self.assertEqual(select_guard_module_map("in.py", {"kind": "Module"}, {}), {"in.py": {"kind": "Module"}})
        self.assertEqual(select_guard_module_map("", {"kind": "Module"}, {}), {"<input>": {"kind": "Module"}})

    def test_set_import_binding_helpers(self) -> None:
        import_modules: dict[str, str] = {}
        set_import_module_binding(import_modules, "m", "")
        set_import_module_binding(import_modules, "m", "pkg.mod")
        self.assertEqual(import_modules, {"m": "pkg.mod"})

        import_symbols: dict[str, dict[str, str]] = {}
        set_import_symbol_binding(import_symbols, "x", "", "name")
        set_import_symbol_binding(import_symbols, "x", "pkg.mod", "name")
        self.assertEqual(import_symbols, {"x": {"module": "pkg.mod", "name": "name"}})

        import_symbol_modules: set[str] = set()
        set_import_symbol_binding_and_module_set(import_symbols, import_symbol_modules, "y", "pkg2.mod", "item")
        self.assertEqual(import_symbols["y"], {"module": "pkg2.mod", "name": "item"})
        self.assertEqual(import_symbol_modules, {"pkg2.mod"})

    def test_normalize_param_annotation_coarse_types(self) -> None:
        self.assertEqual(normalize_param_annotation(""), "unknown")
        self.assertEqual(normalize_param_annotation(" Any "), "Any")
        self.assertEqual(normalize_param_annotation("object"), "object")
        self.assertEqual(normalize_param_annotation("int"), "int")
        self.assertEqual(normalize_param_annotation("list[str]"), "list[str]")
        self.assertEqual(normalize_param_annotation("CustomType"), "CustomType")

    def test_extract_function_signatures_from_python_source_parses_defs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "sig_src.py"
            src.write_text(
                "def f(a: int, b: str = 'x'):\n"
                "    return a\n"
                "\n"
                "def g(\n"
                "    x: list[int],\n"
                "    y,\n"
                "):\n"
                "    return x\n",
                encoding="utf-8",
            )
            sigs = extract_function_signatures_from_python_source(src)
            self.assertEqual(sigs["f"]["arg_types"], ["int", "str"])
            self.assertEqual(sigs["f"]["arg_defaults"], ["", "'x'"])
            self.assertEqual(sigs["g"]["arg_types"], ["list[int]", "unknown"])

    def test_extract_function_arg_types_from_python_source(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "sig_src.py"
            src.write_text(
                "def f(a: int, b: Any):\n"
                "    return a\n",
                encoding="utf-8",
            )
            arg_types = extract_function_arg_types_from_python_source(src)
            self.assertEqual(arg_types, {"f": ["int", "Any"]})

    def test_dict_any_get_str_list_filters_non_str(self) -> None:
        data: dict[str, object] = {"xs": ["a", 1, "b"], "ys": "abc"}
        self.assertEqual(dict_any_get_str_list(data, "xs"), ["a", "b"])
        self.assertEqual(dict_any_get_str_list(data, "ys"), [])
        self.assertEqual(dict_any_get_str_list(data, "missing"), [])

    def test_dict_any_get_list_returns_empty_for_non_list(self) -> None:
        data: dict[str, object] = {"xs": ["a", 1, "b"], "ys": "abc"}
        self.assertEqual(dict_any_get_list(data, "xs"), ["a", 1, "b"])
        self.assertEqual(dict_any_get_list(data, "ys"), [])
        self.assertEqual(dict_any_get_list(data, "missing"), [])

    def test_dict_any_get_dict_returns_empty_for_non_dict(self) -> None:
        data: dict[str, object] = {"xs": {"a": 1}, "ys": "abc"}
        self.assertEqual(dict_any_get_dict(data, "xs"), {"a": 1})
        self.assertEqual(dict_any_get_dict(data, "ys"), {})
        self.assertEqual(dict_any_get_dict(data, "missing"), {})

    def test_dict_any_get_dict_list_filters_non_dict(self) -> None:
        data: dict[str, object] = {"xs": [{"a": 1}, "x", {"b": 2}], "ys": {"a": 1}}
        self.assertEqual(dict_any_get_dict_list(data, "xs"), [{"a": 1}, {"b": 2}])
        self.assertEqual(dict_any_get_dict_list(data, "ys"), [])
        self.assertEqual(dict_any_get_dict_list(data, "missing"), [])

    def test_assign_targets_prefers_targets_then_target(self) -> None:
        stmt_targets: dict[str, object] = {"targets": [{"id": "x"}, "bad"], "target": {"id": "y"}}
        stmt_target_only: dict[str, object] = {"target": {"id": "y"}}
        stmt_empty: dict[str, object] = {"targets": "bad", "target": "bad"}
        self.assertEqual(assign_targets(stmt_targets), [{"id": "x"}])
        self.assertEqual(assign_targets(stmt_target_only), [{"id": "y"}])
        self.assertEqual(assign_targets(stmt_empty), [])

    def test_dict_str_get_returns_default_when_missing(self) -> None:
        data = {"a": "x"}
        self.assertEqual(dict_str_get(data, "a", ""), "x")
        self.assertEqual(dict_str_get(data, "b", "d"), "d")

    def test_looks_like_runtime_function_name(self) -> None:
        self.assertTrue(looks_like_runtime_function_name("py_len"))
        self.assertTrue(looks_like_runtime_function_name("pytra::std::math::exp"))
        self.assertFalse(looks_like_runtime_function_name(""))
        self.assertFalse(looks_like_runtime_function_name("user_func"))

    def test_is_pytra_module_name(self) -> None:
        self.assertTrue(is_pytra_module_name("pytra"))
        self.assertTrue(is_pytra_module_name("pytra.std"))
        self.assertFalse(is_pytra_module_name("pytraa"))
        self.assertFalse(is_pytra_module_name("os"))

    def test_local_binding_name_prefers_alias(self) -> None:
        self.assertEqual(local_binding_name("a.b", "x"), "x")
        self.assertEqual(local_binding_name("a.b", ""), "a")
        self.assertEqual(local_binding_name("mod", ""), "mod")

    def test_split_graph_issue_entry(self) -> None:
        self.assertEqual(split_graph_issue_entry("a.py: pkg.mod"), ("a.py", "pkg.mod"))
        self.assertEqual(split_graph_issue_entry("raw"), ("raw", "raw"))

    def test_guard_profile_base_limits(self) -> None:
        self.assertEqual(
            guard_profile_base_limits("off"),
            {
                "max_ast_depth": 0,
                "max_parse_nodes": 0,
                "max_symbols_per_module": 0,
                "max_scope_depth": 0,
                "max_import_graph_nodes": 0,
                "max_import_graph_edges": 0,
                "max_generated_lines": 0,
            },
        )
        self.assertEqual(guard_profile_base_limits("default")["max_ast_depth"], 800)
        self.assertEqual(guard_profile_base_limits("strict")["max_generated_lines"], 300000)
        with self.assertRaisesRegex(ValueError, "invalid --guard-profile: bad"):
            guard_profile_base_limits("bad")

    def test_parse_guard_limit_or_raise(self) -> None:
        self.assertEqual(parse_guard_limit_or_raise("", "max-ast-depth"), -1)
        self.assertEqual(parse_guard_limit_or_raise("10", "max-ast-depth"), 10)
        with self.assertRaisesRegex(ValueError, "invalid value for --max-ast-depth: x"):
            parse_guard_limit_or_raise("x", "max-ast-depth")
        with self.assertRaisesRegex(ValueError, "invalid value for --max-ast-depth: must be > 0"):
            parse_guard_limit_or_raise("0", "max-ast-depth")

    def test_parse_py2cpp_argv(self) -> None:
        parsed = parse_py2cpp_argv(
            [
                "input.py",
                "-o",
                "out.cpp",
                "--preset",
                "balanced",
                "--mod-mode",
                "native",
                "--dump-options",
            ]
        )
        err = str(parsed.get("__error", ""))
        self.assertEqual(err, "")
        self.assertEqual(parsed.get("input"), "input.py")
        self.assertEqual(parsed.get("output"), "out.cpp")
        self.assertEqual(parsed.get("preset"), "balanced")
        self.assertEqual(parsed.get("mod_mode_opt"), "native")
        self.assertEqual(parsed.get("dump_options"), "1")

    def test_parse_py2cpp_argv_accepts_positional_output(self) -> None:
        parsed = parse_py2cpp_argv(["input.py", "out.cpp", "-O2"])
        err = str(parsed.get("__error", ""))
        self.assertEqual(err, "")
        self.assertEqual(parsed.get("input"), "input.py")
        self.assertEqual(parsed.get("output"), "out.cpp")
        self.assertEqual(parsed.get("opt_level_opt"), "2")

    def test_parse_py2cpp_argv_multi_file_flags(self) -> None:
        parsed = parse_py2cpp_argv(["input.py", "--multi-file", "--output-dir", "out"])
        err = str(parsed.get("__error", ""))
        self.assertEqual(err, "")
        self.assertEqual(parsed.get("single_file"), "0")
        self.assertEqual(parsed.get("output_dir"), "out")
        self.assertEqual(parsed.get("output_mode_explicit"), "1")
        parsed2 = parse_py2cpp_argv(["input.py", "--single-file"])
        err2 = str(parsed2.get("__error", ""))
        self.assertEqual(err2, "")
        self.assertEqual(parsed2.get("single_file"), "1")
        self.assertEqual(parsed2.get("output_mode_explicit"), "1")
        parsed3 = parse_py2cpp_argv(["input.py"])
        err3 = str(parsed3.get("__error", ""))
        self.assertEqual(err3, "")
        self.assertEqual(parsed3.get("single_file"), "0")
        self.assertEqual(parsed3.get("output_mode_explicit"), "0")

    def test_parse_py2cpp_argv_header_output(self) -> None:
        parsed = parse_py2cpp_argv(["input.py", "--header-output", "out.h", "-o", "out.cpp"])
        err = str(parsed.get("__error", ""))
        self.assertEqual(err, "")
        self.assertEqual(parsed.get("header_output"), "out.h")
        self.assertEqual(parsed.get("output"), "out.cpp")

    def test_parse_py2cpp_argv_emit_runtime_cpp(self) -> None:
        parsed = parse_py2cpp_argv(["src/pytra/std/math.py", "--emit-runtime-cpp"])
        err = str(parsed.get("__error", ""))
        self.assertEqual(err, "")
        self.assertEqual(parsed.get("emit_runtime_cpp"), "1")

    def test_parse_py2cpp_argv_guard_options(self) -> None:
        parsed = parse_py2cpp_argv(
            [
                "input.py",
                "--guard-profile",
                "strict",
                "--max-ast-depth",
                "10",
                "--max-parse-nodes",
                "20",
                "--max-symbols-per-module",
                "30",
                "--max-scope-depth",
                "40",
                "--max-import-graph-nodes",
                "50",
                "--max-import-graph-edges",
                "60",
                "--max-generated-lines",
                "70",
            ]
        )
        err = str(parsed.get("__error", ""))
        self.assertEqual(err, "")
        self.assertEqual(parsed.get("guard_profile"), "strict")
        self.assertEqual(parsed.get("max_ast_depth"), "10")
        self.assertEqual(parsed.get("max_parse_nodes"), "20")
        self.assertEqual(parsed.get("max_symbols_per_module"), "30")
        self.assertEqual(parsed.get("max_scope_depth"), "40")
        self.assertEqual(parsed.get("max_import_graph_nodes"), "50")
        self.assertEqual(parsed.get("max_import_graph_edges"), "60")
        self.assertEqual(parsed.get("max_generated_lines"), "70")

    def test_guard_limit_exceeded_in_parse_stage(self) -> None:
        src = "x: int = 1\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "guard_parse.py"
            out_cpp = Path(tmpdir) / "guard_parse.cpp"
            src_py.write_text(src, encoding="utf-8")
            cp = self._run_subprocess_with_timeout(
                [
                    "python3",
                    "src/py2cpp.py",
                    str(src_py),
                    "-o",
                    str(out_cpp),
                    "--max-parse-nodes",
                    "1",
                ],
                cwd=ROOT,
                timeout_sec=PYTRA_TEST_TOOL_TIMEOUT_SEC,
                label="py2cpp parse guard",
            )
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("[input_invalid]", cp.stderr)
        self.assertIn("kind=limit_exceeded stage=parse limit=max-parse-nodes", cp.stderr)

    def test_guard_limit_exceeded_in_analyze_stage(self) -> None:
        main_src = "import dep\nx: int = dep.value\n"
        dep_src = "value: int = 1\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "main.py"
            dep_py = Path(tmpdir) / "dep.py"
            out_cpp = Path(tmpdir) / "guard_analyze.cpp"
            src_py.write_text(main_src, encoding="utf-8")
            dep_py.write_text(dep_src, encoding="utf-8")
            cp = self._run_subprocess_with_timeout(
                [
                    "python3",
                    "src/py2cpp.py",
                    str(src_py),
                    "-o",
                    str(out_cpp),
                    "--max-import-graph-nodes",
                    "1",
                ],
                cwd=ROOT,
                timeout_sec=PYTRA_TEST_TOOL_TIMEOUT_SEC,
                label="py2cpp analyze guard",
            )
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("[input_invalid]", cp.stderr)
        self.assertIn("kind=limit_exceeded stage=analyze limit=max-import-graph-nodes", cp.stderr)

    def test_guard_limit_exceeded_in_emit_stage(self) -> None:
        src = "x: int = 1\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "guard_emit.py"
            out_cpp = Path(tmpdir) / "guard_emit.cpp"
            src_py.write_text(src, encoding="utf-8")
            cp = self._run_subprocess_with_timeout(
                [
                    "python3",
                    "src/py2cpp.py",
                    str(src_py),
                    "-o",
                    str(out_cpp),
                    "--max-generated-lines",
                    "1",
                ],
                cwd=ROOT,
                timeout_sec=PYTRA_TEST_TOOL_TIMEOUT_SEC,
                label="py2cpp emit guard",
            )
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("[input_invalid]", cp.stderr)
        self.assertIn("kind=limit_exceeded stage=emit limit=max-generated-lines", cp.stderr)

    def test_list_pop_emits_method_call(self) -> None:
        src = """def pop_last() -> int:
    xs: list[int] = [1, 2, 3]
    return xs.pop()
"""
        with tempfile.TemporaryDirectory() as td:
            py_path = Path(td) / "case.py"
            py_path.write_text(src, encoding="utf-8")
            east = load_east(py_path)
            cpp = transpile_to_cpp(east)
        self.assertIn("xs.pop()", cpp)
        self.assertNotIn("py_pop(", cpp)

    def test_reserved_identifier_is_renamed_by_profile_rule(self) -> None:
        src = """def main() -> None:
    auto: int = 1
    print(auto)

if __name__ == "__main__":
    main()
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "reserved_name.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east)
        self.assertIn("int64 py_auto = 1;", cpp)
        self.assertIn("py_print(py_auto);", cpp)

    def test_runtime_call_map_for_math_is_not_hardcoded(self) -> None:
        mp = load_cpp_module_attr_call_map()
        self.assertNotIn("math", mp)
        self.assertNotIn("pytra.std.math", mp)

    def test_math_module_call_uses_runtime_call_map(self) -> None:
        src = """import math

def main() -> None:
    x: float = math.sqrt(9.0)
    print(x)

if __name__ == "__main__":
    main()
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "math_call.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east)
        self.assertIn("pytra::std::math::sqrt(9.0)", cpp)

    def test_os_path_calls_use_runtime_helpers(self) -> None:
        src = """from pytra.std import os

def main() -> None:
    p: str = os.path.join("a", "b.txt")
    root, ext = os.path.splitext(p)
    print(root, ext)

if __name__ == "__main__":
    main()
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "os_path_calls.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east)
        self.assertIn("py_os_path_join(", cpp)
        self.assertIn("py_os_path_splitext(", cpp)
        self.assertNotIn("pytra::std::os::path::join(", cpp)
        self.assertNotIn("pytra::std::os::path::splitext(", cpp)

    def test_from_import_symbol_uses_runtime_call_map(self) -> None:
        src = """from math import sqrt as msqrt

def main() -> None:
    x: float = msqrt(9.0)
    print(x)

if __name__ == "__main__":
    main()
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "from_math_call.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east)
        self.assertIn("pytra::std::math::sqrt(9.0)", cpp)

    def test_import_module_alias_uses_runtime_call_map(self) -> None:
        src = """import math as m

def main() -> None:
    x: float = m.sqrt(9.0)
    print(x)

if __name__ == "__main__":
    main()
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "math_alias_call.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east)
        self.assertIn("pytra::std::math::sqrt(9.0)", cpp)

    def test_pytra_std_import_emits_one_to_one_include(self) -> None:
        src = """import pytra.std.math as math

def main() -> None:
    print(math.sqrt(9.0))

if __name__ == "__main__":
    main()
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "pytra_std_import.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east)
        self.assertIn('#include "pytra/std/math.h"', cpp)
        self.assertIn("pytra::std::math::sqrt(9.0)", cpp)

    def test_pytra_runtime_import_emits_one_to_one_include(self) -> None:
        src = """import pytra.utils.png as png

def main() -> None:
    pixels: bytearray = bytearray(3)
    png.write_rgb_png("x.png", 1, 1, pixels)

if __name__ == "__main__":
    main()
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "pytra_runtime_import.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east)
        self.assertIn('#include "pytra/utils/png.h"', cpp)
        self.assertIn("pytra::utils::png::write_rgb_png(", cpp)

    def test_import_includes_are_deduped_and_sorted(self) -> None:
        src = """import pytra.utils.png as png
from pytra.utils import gif
from pytra.utils.png import write_rgb_png

def main() -> None:
    frames: list[bytearray] = []
    gif.save_gif("x.gif", 1, 1, frames)
    pixels: bytearray = bytearray(3)
    write_rgb_png("x.png", 1, 1, pixels)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "include_sort.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east)
        gif_inc = '#include "pytra/utils/gif.h"'
        png_inc = '#include "pytra/utils/png.h"'
        self.assertEqual(cpp.count(gif_inc), 1)
        self.assertEqual(cpp.count(png_inc), 1)
        self.assertLess(cpp.find(gif_inc), cpp.find(png_inc))

    def test_from_pytra_runtime_import_png_emits_one_to_one_include(self) -> None:
        src = """from pytra.utils import png

def main() -> None:
    pixels: bytearray = bytearray(3)
    png.write_rgb_png("x.png", 1, 1, pixels)

if __name__ == "__main__":
    main()
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "from_pytra_runtime_import_png.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east)
        self.assertIn('#include "pytra/utils/png.h"', cpp)
        self.assertIn("pytra::utils::png::write_rgb_png(", cpp)

    def test_from_pytra_runtime_import_gif_emits_one_to_one_include(self) -> None:
        src = """from pytra.utils import gif

def main() -> None:
    frames: list[bytearray] = []
    gif.save_gif("x.gif", 1, 1, frames)

if __name__ == "__main__":
    main()
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "from_pytra_runtime_import_gif.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east)
        self.assertIn('#include "pytra/utils/gif.h"', cpp)
        self.assertIn("pytra::utils::gif::save_gif(", cpp)

    def test_from_pytra_std_time_import_perf_counter_resolves(self) -> None:
        src = """from pytra.std.time import perf_counter

def main() -> None:
    t0: float = perf_counter()
    print(t0 >= 0.0)

if __name__ == "__main__":
    main()
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "from_pytra_std_time_perf_counter.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east)
        self.assertIn('#include "pytra/std/time.h"', cpp)
        self.assertIn("pytra::std::time::perf_counter()", cpp)

    def test_from_pytra_std_pathlib_import_path_resolves(self) -> None:
        src = """from pytra.std.pathlib import Path

def main() -> None:
    p: Path = Path("a")
    print(p.name)

if __name__ == "__main__":
    main()
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "from_pytra_std_pathlib_path.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east)
        self.assertIn('#include "pytra/std/pathlib.h"', cpp)
        self.assertIn("Path(\"a\")", cpp)

    def test_dump_deps_text_lists_modules_and_symbols(self) -> None:
        src = """import math
from pytra.std.json import loads as json_loads, dumps
from pytra.utils.png import write_rgb_png

def main() -> None:
    print(math.sqrt(4.0))
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "deps_case.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            txt = dump_deps_text(east)
        self.assertIn("modules:", txt)
        self.assertIn("  - math", txt)
        self.assertIn("  - pytra.std.json", txt)
        self.assertIn("  - pytra.utils.png", txt)
        self.assertIn("symbols:", txt)
        self.assertIn("  - pytra.std.json.loads as json_loads", txt)
        self.assertIn("  - pytra.std.json.dumps", txt)
        self.assertIn("  - pytra.utils.png.write_rgb_png", txt)

    def test_east_meta_import_bindings_is_emitted(self) -> None:
        src = """import math as m
from pytra.std.json import loads as json_loads
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "import_bindings.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
        meta_obj = east.get("meta")
        meta = meta_obj if isinstance(meta_obj, dict) else {}
        bindings_obj = meta.get("import_bindings")
        bindings = bindings_obj if isinstance(bindings_obj, list) else []
        self.assertGreaterEqual(len(bindings), 2)
        self.assertIn(
            {
                "module_id": "math",
                "export_name": "",
                "local_name": "m",
                "binding_kind": "module",
                "source_file": str(src_py),
                "source_line": 1,
            },
            bindings,
        )
        self.assertIn(
            {
                "module_id": "pytra.std.json",
                "export_name": "loads",
                "local_name": "json_loads",
                "binding_kind": "symbol",
                "source_file": str(src_py),
                "source_line": 2,
            },
            bindings,
        )
        bindings_norm = meta_import_bindings(east)
        self.assertIn(
            {
                "module_id": "math",
                "export_name": "",
                "local_name": "m",
                "binding_kind": "module",
            },
            bindings_norm,
        )
        refs = meta_qualified_symbol_refs(east)
        self.assertIn(
            {
                "module_id": "pytra.std.json",
                "symbol": "loads",
                "local_name": "json_loads",
            },
            refs,
        )

    def test_cli_dump_deps_includes_user_module_graph(self) -> None:
        src_main = """import helper

def main() -> None:
    print(helper.f())
"""
        src_helper = """def f() -> int:
    return 1
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            main_py = root / "main.py"
            helper_py = root / "helper.py"
            main_py.write_text(src_main, encoding="utf-8")
            helper_py.write_text(src_helper, encoding="utf-8")
            proc = subprocess.run(
                ["python3", "src/py2cpp.py", str(main_py), "--dump-deps"],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        self.assertIn("graph:", proc.stdout)
        self.assertIn("main.py -> helper.py", proc.stdout)

    def test_dump_deps_graph_and_build_map_are_consistent(self) -> None:
        src_main = """import helper

def main() -> None:
    print(helper.f())
"""
        src_helper = """def f() -> int:
    return 1
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            main_py = root / "main.py"
            helper_py = root / "helper.py"
            main_py.write_text(src_main, encoding="utf-8")
            helper_py.write_text(src_helper, encoding="utf-8")
            deps_txt = dump_deps_graph_text(main_py)
            module_map = build_module_east_map(main_py)
        self.assertIn("main.py -> helper.py", deps_txt)
        self.assertEqual(set(module_map.keys()), {str(main_py), str(helper_py)})

    def test_multi_file_from_import_alias_uses_fully_qualified_symbol(self) -> None:
        src_main = """from helper import add as plus

def main() -> None:
    print(plus(1, 2))
"""
        src_helper = """def add(a: int, b: int) -> int:
    return a + b
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            main_py = root / "main.py"
            helper_py = root / "helper.py"
            out_dir = root / "out"
            main_py.write_text(src_main, encoding="utf-8")
            helper_py.write_text(src_helper, encoding="utf-8")
            proc = subprocess.run(
                ["python3", "src/py2cpp.py", str(main_py), "--multi-file", "--output-dir", str(out_dir)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            main_cpp = (out_dir / "src" / "main.cpp").read_text(encoding="utf-8")
        self.assertIn("namespace pytra_mod_helper {", main_cpp)
        self.assertIn("pytra_mod_helper::add(1, 2)", main_cpp)

    def test_cli_reports_input_invalid_for_missing_user_module(self) -> None:
        src_main = """import missing_mod

def main() -> None:
    print(1)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            main_py = root / "main.py"
            out_cpp = root / "out.cpp"
            main_py.write_text(src_main, encoding="utf-8")
            proc = subprocess.run(
                ["python3", "src/py2cpp.py", str(main_py), "-o", str(out_cpp)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("[input_invalid]", proc.stderr)
        self.assertIn("kind=missing_module", proc.stderr)
        self.assertIn("file=main.py", proc.stderr)
        self.assertIn("import=missing_mod", proc.stderr)

    def test_cli_reports_input_invalid_for_import_cycle(self) -> None:
        src_main = """import helper

def main() -> None:
    print(1)
"""
        src_helper = """import main

def f() -> int:
    return 1
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            main_py = root / "main.py"
            helper_py = root / "helper.py"
            out_cpp = root / "out.cpp"
            main_py.write_text(src_main, encoding="utf-8")
            helper_py.write_text(src_helper, encoding="utf-8")
            proc = subprocess.run(
                ["python3", "src/py2cpp.py", str(main_py), "-o", str(out_cpp)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("[input_invalid]", proc.stderr)
        self.assertIn("kind=import_cycle", proc.stderr)
        self.assertIn("main.py -> helper.py -> main.py", proc.stderr)

    def test_cli_reports_input_invalid_for_relative_import(self) -> None:
        src_main = """from .helper import f

def main() -> None:
    print(f())
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            main_py = root / "main.py"
            out_cpp = root / "out.cpp"
            main_py.write_text(src_main, encoding="utf-8")
            proc = subprocess.run(
                ["python3", "src/py2cpp.py", str(main_py), "-o", str(out_cpp)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("[input_invalid]", proc.stderr)
        self.assertIn("kind=unsupported_import_form", proc.stderr)
        self.assertIn("import=from .helper import f", proc.stderr)

    def test_cli_reports_input_invalid_for_from_import_star(self) -> None:
        src_main = """from helper import *

def main() -> None:
    print(1)
"""
        src_helper = """def f() -> int:
    return 1
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            main_py = root / "main.py"
            helper_py = root / "helper.py"
            out_cpp = root / "out.cpp"
            main_py.write_text(src_main, encoding="utf-8")
            helper_py.write_text(src_helper, encoding="utf-8")
            proc = subprocess.run(
                ["python3", "src/py2cpp.py", str(main_py), "-o", str(out_cpp)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("[input_invalid]", proc.stderr)
        self.assertIn("kind=unsupported_import_form", proc.stderr)
        self.assertIn("import=from helper import *", proc.stderr)

    def test_cli_reports_input_invalid_for_duplicate_import_binding(self) -> None:
        src_main = """from a import x
from b import x

def main() -> None:
    print(x)
"""
        src_a = """x: int = 1
"""
        src_b = """x: int = 2
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            main_py = root / "main.py"
            a_py = root / "a.py"
            b_py = root / "b.py"
            out_cpp = root / "out.cpp"
            main_py.write_text(src_main, encoding="utf-8")
            a_py.write_text(src_a, encoding="utf-8")
            b_py.write_text(src_b, encoding="utf-8")
            proc = subprocess.run(
                ["python3", "src/py2cpp.py", str(main_py), "-o", str(out_cpp)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("[input_invalid]", proc.stderr)
        self.assertIn("kind=duplicate_binding", proc.stderr)

    def test_cli_reports_input_invalid_for_duplicate_import_binding_mixed(self) -> None:
        src_main = """import a as m
from b import x as m

def main() -> None:
    print(1)
"""
        src_a = """x: int = 1
"""
        src_b = """x: int = 2
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            main_py = root / "main.py"
            a_py = root / "a.py"
            b_py = root / "b.py"
            out_cpp = root / "out.cpp"
            main_py.write_text(src_main, encoding="utf-8")
            a_py.write_text(src_a, encoding="utf-8")
            b_py.write_text(src_b, encoding="utf-8")
            proc = subprocess.run(
                ["python3", "src/py2cpp.py", str(main_py), "-o", str(out_cpp)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("[input_invalid]", proc.stderr)
        self.assertIn("kind=duplicate_binding", proc.stderr)

    def test_cli_reports_input_invalid_for_missing_import_symbol(self) -> None:
        src_main = """from helper import missing_symbol

def main() -> None:
    print(1)
"""
        src_helper = """def present() -> int:
    return 1
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            main_py = root / "main.py"
            helper_py = root / "helper.py"
            out_cpp = root / "out.cpp"
            main_py.write_text(src_main, encoding="utf-8")
            helper_py.write_text(src_helper, encoding="utf-8")
            proc = subprocess.run(
                ["python3", "src/py2cpp.py", str(main_py), "-o", str(out_cpp)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("[input_invalid]", proc.stderr)
        self.assertIn("kind=missing_symbol", proc.stderr)
        self.assertIn("import=from helper import missing_symbol", proc.stderr)

    def test_cli_reports_input_invalid_for_unbound_module_after_from_import(self) -> None:
        src_main = """from helper import f

def main() -> None:
    print(helper.g())
"""
        src_helper = """def f() -> int:
    return 1
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            main_py = root / "main.py"
            helper_py = root / "helper.py"
            out_cpp = root / "out.cpp"
            main_py.write_text(src_main, encoding="utf-8")
            helper_py.write_text(src_helper, encoding="utf-8")
            proc = subprocess.run(
                ["python3", "src/py2cpp.py", str(main_py), "-o", str(out_cpp)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("[input_invalid]", proc.stderr)
        self.assertIn("kind=missing_symbol", proc.stderr)
        self.assertIn("import=helper.g", proc.stderr)

    def test_name_resolution_prefers_local_over_import_symbol(self) -> None:
        src = """from pytra.std.math import sqrt as calc

def main() -> None:
    calc: int = 3
    print(calc)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "local_over_import_symbol.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east)
        self.assertIn("int64 calc = 3;", cpp)
        self.assertIn("py_print(calc);", cpp)
        self.assertNotIn("math::sqrt", cpp)

    def test_name_resolution_prefers_arg_over_import_module(self) -> None:
        src = """import pytra.std.math as m

def f(m: int) -> int:
    return m + 1
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "arg_over_import_module.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)
        self.assertIn("int64 f(int64 m)", cpp)
        self.assertIn("return m + 1;", cpp)
        self.assertNotIn("pytra::std::math::", cpp)

    def test_build_module_east_map_collects_entry_and_user_deps(self) -> None:
        src_main = """import helper

def main() -> None:
    print(helper.f())
"""
        src_helper = """def f() -> int:
    return 1
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            main_py = root / "main.py"
            helper_py = root / "helper.py"
            main_py.write_text(src_main, encoding="utf-8")
            helper_py.write_text(src_helper, encoding="utf-8")
            mp = build_module_east_map(main_py)
        self.assertIn(str(main_py), mp)
        self.assertIn(str(helper_py), mp)
        self.assertEqual(mp[str(main_py)].get("kind"), "Module")
        self.assertEqual(mp[str(helper_py)].get("kind"), "Module")

    def test_build_module_symbol_index_contains_defs_and_import_aliases(self) -> None:
        src_main = """import helper as hp
from helper import C as HC

def run() -> int:
    return hp.f()
"""
        src_helper = """class C:
    x: int = 1

def f() -> int:
    return 1
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            main_py = root / "main.py"
            helper_py = root / "helper.py"
            main_py.write_text(src_main, encoding="utf-8")
            helper_py.write_text(src_helper, encoding="utf-8")
            mp = build_module_east_map(main_py)
            idx = build_module_symbol_index(mp)
        self.assertIn(str(main_py), idx)
        self.assertIn(str(helper_py), idx)
        self.assertIn("run", idx[str(main_py)]["functions"])
        self.assertIn("f", idx[str(helper_py)]["functions"])
        self.assertIn("C", idx[str(helper_py)]["classes"])
        self.assertEqual(idx[str(main_py)]["import_modules"].get("hp"), "helper")
        self.assertIn("HC", idx[str(main_py)]["import_symbols"])

    def test_resolve_module_name_classifies_user_pytra_and_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "helper.py").write_text("x: int = 1\n", encoding="utf-8")
            user_res = resolve_module_name("helper", root)
            pytra_res = resolve_module_name("pytra.std.math", root)
            miss_res = resolve_module_name("no_such_module", root)
            rel_res = resolve_module_name(".helper", root)
        self.assertEqual(user_res.get("status"), "user")
        self.assertEqual(pytra_res.get("status"), "pytra")
        self.assertEqual(miss_res.get("status"), "missing")
        self.assertEqual(rel_res.get("status"), "relative")

    def test_resolve_module_name_prefers_named_package_module_over_local_flat_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            docs_dir = root / "docs" / "scene"
            docs_dir.mkdir(parents=True, exist_ok=True)
            (docs_dir / "yanesdk.py").write_text("x: int = 1\n", encoding="utf-8")
            pkg_dir = root / "yanesdk"
            pkg_dir.mkdir(parents=True, exist_ok=True)
            canonical = pkg_dir / "yanesdk.py"
            canonical.write_text("y: int = 2\n", encoding="utf-8")
            res = resolve_module_name("yanesdk", docs_dir)
        self.assertEqual(res.get("status"), "user")
        self.assertEqual(Path(str(res.get("path", ""))).name, "yanesdk.py")
        self.assertIn("/yanesdk/yanesdk.py", str(res.get("path", "")).replace("\\", "/"))

    def test_resolve_module_name_recognizes_std_and_utils_shims(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            random_res = resolve_module_name("random", root)
            timeit_res = resolve_module_name("timeit", root)
            traceback_res = resolve_module_name("traceback", root)
            browser_res = resolve_module_name("browser", root)
            browser_dialog_res = resolve_module_name("browser.widgets.dialog", root)
        self.assertEqual(random_res.get("status"), "known")
        self.assertEqual(timeit_res.get("status"), "known")
        self.assertEqual(traceback_res.get("status"), "known")
        self.assertEqual(browser_res.get("status"), "known")
        self.assertEqual(browser_dialog_res.get("status"), "known")

    def test_analyze_import_graph_resolves_from_importer_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            docs_dir = root / "docs" / "scene"
            docs_dir.mkdir(parents=True, exist_ok=True)
            main_py = docs_dir / "main.py"
            pkg_dir = root / "yanesdk"
            pkg_dir.mkdir(parents=True, exist_ok=True)
            (pkg_dir / "yanesdk.py").write_text("import browser\n", encoding="utf-8")
            (pkg_dir / "browser.py").write_text("x: int = 1\n", encoding="utf-8")
            main_py.write_text("import yanesdk\n", encoding="utf-8")
            graph = _analyze_import_graph(main_py)
        missing = graph.get("missing_modules")
        self.assertEqual([], missing)
        module_id_map_obj = graph.get("module_id_map")
        module_id_map = module_id_map_obj if isinstance(module_id_map_obj, dict) else {}
        yanesdk_key = str(pkg_dir / "yanesdk.py")
        browser_key = str(pkg_dir / "browser.py")
        self.assertEqual(module_id_map.get(yanesdk_key), "yanesdk")
        self.assertEqual(module_id_map.get(browser_key), "browser")

    def test_build_module_east_map_sets_module_id_from_import_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            docs_dir = root / "docs" / "scene"
            docs_dir.mkdir(parents=True, exist_ok=True)
            main_py = docs_dir / "main.py"
            pkg_dir = root / "yanesdk"
            pkg_dir.mkdir(parents=True, exist_ok=True)
            dep_py = pkg_dir / "yanesdk.py"
            dep_py.write_text("x: int = 1\n", encoding="utf-8")
            main_py.write_text("import yanesdk\n", encoding="utf-8")
            mp = build_module_east_map(main_py)
        dep_east = mp.get(str(dep_py))
        self.assertIsInstance(dep_east, dict)
        meta = dep_east.get("meta") if isinstance(dep_east, dict) else {}
        self.assertIsInstance(meta, dict)
        self.assertEqual(meta.get("module_id"), "yanesdk")

    def test_from_import_symbol_accepts_assign_target_form_exports(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            main_py = root / "main.py"
            helper_py = root / "helper.py"
            helper_py.write_text("X = 1\n", encoding="utf-8")
            main_py.write_text("from helper import X\n", encoding="utf-8")
            mp = build_module_east_map(main_py)
        self.assertIn(str(main_py), mp)
        self.assertIn(str(helper_py), mp)

    def test_build_module_type_schema_contains_function_and_class_types(self) -> None:
        src_main = """def run(v: int) -> int:
    return v + 1
"""
        src_helper = """class C:
    x: int = 1

def f(a: int, b: int) -> int:
    return a + b
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            main_py = root / "main.py"
            helper_py = root / "helper.py"
            main_py.write_text(src_main, encoding="utf-8")
            helper_py.write_text(src_helper, encoding="utf-8")
            mp = {
                str(main_py): load_east(main_py),
                str(helper_py): load_east(helper_py),
            }
            schema = build_module_type_schema(mp)
        self.assertEqual(schema[str(main_py)]["functions"]["run"]["return_type"], "int64")
        self.assertEqual(schema[str(helper_py)]["functions"]["f"]["arg_types"]["a"], "int64")
        self.assertEqual(schema[str(helper_py)]["classes"]["C"]["field_types"]["x"], "int64")

    def test_floor_div_mode_native_and_python(self) -> None:
        src = """def main() -> None:
    a: int = 7
    b: int = 3
    c: int = a // b
    a //= b
    print(c, a)

if __name__ == "__main__":
    main()
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "floor_div_mode.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp_native = transpile_to_cpp(east, floor_div_mode="native")
            cpp_python = transpile_to_cpp(east, floor_div_mode="python")
        self.assertIn("a / b", cpp_native)
        self.assertIn("a /= b;", cpp_native)
        self.assertNotIn("py_floordiv(", cpp_native)
        self.assertIn("py_floordiv(a, b)", cpp_python)
        self.assertIn("a = py_floordiv(a, b);", cpp_python)

    def test_mod_mode_native_and_python(self) -> None:
        src = """def main() -> None:
    a: int = 7
    b: int = 3
    c: int = a % b
    a %= b
    print(c, a)

if __name__ == "__main__":
    main()
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "mod_mode.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp_native = transpile_to_cpp(east, mod_mode="native")
            cpp_python = transpile_to_cpp(east, mod_mode="python")
        self.assertIn("a % b", cpp_native)
        self.assertIn("a %= b;", cpp_native)
        self.assertNotIn("py_mod(", cpp_native)
        self.assertIn("py_mod(a, b)", cpp_python)
        self.assertIn("a = py_mod(a, b);", cpp_python)

    def test_bounds_check_mode_off_always_debug(self) -> None:
        src = """def main() -> None:
    xs: list[int] = [1, 2, 3]
    i: int = 1
    s: str = "ABC"
    print(xs[i], s[i])

if __name__ == "__main__":
    main()
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "bounds_mode.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp_off = transpile_to_cpp(east, bounds_check_mode="off")
            cpp_always = transpile_to_cpp(east, bounds_check_mode="always")
            cpp_debug = transpile_to_cpp(east, bounds_check_mode="debug")
        self.assertIn("xs[i]", cpp_off)
        self.assertIn("s[i]", cpp_off)
        self.assertNotIn("py_at_bounds(", cpp_off)
        self.assertIn("py_at_bounds(xs, i)", cpp_always)
        self.assertIn("py_at_bounds(s, i)", cpp_always)
        self.assertIn("py_at_bounds_debug(xs, i)", cpp_debug)
        self.assertIn("py_at_bounds_debug(s, i)", cpp_debug)

    def test_int_width_32_and_64(self) -> None:
        src = """def main() -> None:
    x: int = 1
    y: int = x + 2
    print(y)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "int_width.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp64 = transpile_to_cpp(east, int_width="64")
            cpp32 = transpile_to_cpp(east, int_width="32")
        self.assertIn("int64 x = 1;", cpp64)
        self.assertIn("int32 x = 1;", cpp32)

    def test_ifexp_renders_cpp_ternary(self) -> None:
        src = """def pick(v: int) -> int:
    return 1 if v > 0 else 2
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "ifexp.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)
        self.assertIn("? 1 : 2", cpp)

    def test_east_builtin_call_normalization(self) -> None:
        src = """from pathlib import Path

def main() -> None:
    s: str = "  x  "
    xs: list[int] = []
    d: dict[str, int] = {"a": 1}
    p: Path = Path("tmp")
    xs.append(1)
    _ = s.strip()
    _ = d.get("a", 0)
    _ = p.exists()
    print(len(xs))

if __name__ == "__main__":
    main()
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "norm.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
        runtime_calls: set[str] = set()
        stack: list[object] = [east]
        while stack:
            cur = stack.pop()
            if isinstance(cur, dict):
                if cur.get("kind") == "Call" and cur.get("lowered_kind") == "BuiltinCall":
                    rc = cur.get("runtime_call")
                    if isinstance(rc, str):
                        runtime_calls.add(rc)
                for v in cur.values():
                    stack.append(v)
            elif isinstance(cur, list):
                for it in cur:
                    stack.append(it)
        self.assertIn("list.append", runtime_calls)
        self.assertIn("py_strip", runtime_calls)
        self.assertIn("dict.get", runtime_calls)
        self.assertIn("std::filesystem::exists", runtime_calls)
        self.assertIn("py_len", runtime_calls)
        self.assertIn("py_print", runtime_calls)

    def _compile_and_run_fixture(self, stem: str) -> str:
        leaked_png = ROOT / f"{stem}.png"
        if leaked_png.exists():
            leaked_png.unlink()
        with tempfile.TemporaryDirectory() as tmpdir:
            work = Path(tmpdir)
            src_py = find_fixture_case(stem)
            out_cpp = work / f"{stem}.cpp"
            out_exe = work / f"{stem}.out"
            try:
                print(f"  [fixture:{stem}] transpile", flush=True)
                transpile(src_py, out_cpp)
                print(f"  [fixture:{stem}] compile", flush=True)
                comp = self._run_subprocess_with_timeout(
                    [
                        "g++",
                        "-std=c++20",
                        "-O2",
                        "-I",
                        "src",
                        "-I",
                        "src/runtime/cpp",
                        str(out_cpp),
                        *CPP_RUNTIME_SRCS,
                        "-o",
                        str(out_exe),
                    ],
                    cwd=ROOT,
                    timeout_sec=PYTRA_TEST_COMPILE_TIMEOUT_SEC,
                    label=f"compile fixture {stem}",
                )
                self.assertEqual(comp.returncode, 0, msg=comp.stderr)
                # Keep repository root clean even if a fixture writes images with relative paths,
                # by fixing runtime cwd to a temporary directory.
                print(f"  [fixture:{stem}] run", flush=True)
                run = self._run_subprocess_with_timeout(
                    [str(out_exe)],
                    cwd=work,
                    timeout_sec=PYTRA_TEST_RUN_TIMEOUT_SEC,
                    label=f"run fixture {stem}",
                )
                self.assertEqual(run.returncode, 0, msg=run.stderr)
                self.assertFalse(
                    leaked_png.exists(),
                    msg=f"fixture {stem} leaked {leaked_png.name} to repository root",
                )
                return run.stdout.replace("\r\n", "\n")
            finally:
                if leaked_png.exists():
                    leaked_png.unlink()

    def _transpile_and_syntax_check_fixture(self, stem: str) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            work = Path(tmpdir)
            src_py = find_fixture_case(stem)
            out_cpp = work / f"{stem}.cpp"
            print(f"  [fixture:{stem}] transpile", flush=True)
            transpile(src_py, out_cpp)
            print(f"  [fixture:{stem}] syntax-check", flush=True)
            comp = self._run_subprocess_with_timeout(
                [
                    "g++",
                    "-std=c++20",
                    "-O2",
                    "-I",
                    "src",
                    "-I",
                    "src/runtime/cpp",
                    "-fsyntax-only",
                    str(out_cpp),
                ],
                cwd=ROOT,
                timeout_sec=PYTRA_TEST_COMPILE_TIMEOUT_SEC,
                label=f"syntax-check fixture {stem}",
            )
            self.assertEqual(comp.returncode, 0, msg=comp.stderr)

    def test_cli_reports_user_syntax_error_category(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_py = Path(tmpdir) / "bad.py"
            bad_py.write_text("def main(:\n    pass\n", encoding="utf-8")
            out_cpp = Path(tmpdir) / "bad.cpp"
            proc = subprocess.run(
                ["python3", "src/py2cpp.py", str(bad_py), "-o", str(out_cpp)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("[user_syntax_error]", proc.stderr)

    def test_cli_multi_file_generates_out_include_src(self) -> None:
        src_main = """import helper

def main() -> None:
    print(helper.f())
"""
        src_helper = """def f() -> int:
    return 1
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            out_dir = root / "out"
            main_py = root / "main.py"
            helper_py = root / "helper.py"
            main_py.write_text(src_main, encoding="utf-8")
            helper_py.write_text(src_helper, encoding="utf-8")
            proc = subprocess.run(
                ["python3", "src/py2cpp.py", str(main_py), "--multi-file", "--output-dir", str(out_dir)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            self.assertTrue((out_dir / "include").exists())
            self.assertTrue((out_dir / "src").exists())
            self.assertTrue((out_dir / "manifest.json").exists())
            self.assertTrue((out_dir / "include" / "pytra_multi_prelude.h").exists())
            manifest_txt = (out_dir / "manifest.json").read_text(encoding="utf-8")
            self.assertIn("main.py", manifest_txt)
            self.assertIn("helper.py", manifest_txt)
            src_txt = (out_dir / "src" / "main.cpp").read_text(encoding="utf-8")
            self.assertIn('#include "pytra_multi_prelude.h"', src_txt)
            self.assertNotIn('#include "runtime/cpp/py_runtime.h"', src_txt)

    def test_cli_default_mode_is_multi_file(self) -> None:
        src_main = """def main() -> None:
    print(1)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            out_dir = root / "out"
            main_py = root / "main.py"
            main_py.write_text(src_main, encoding="utf-8")
            proc = subprocess.run(
                ["python3", "src/py2cpp.py", str(main_py), "--output-dir", str(out_dir)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            self.assertTrue((out_dir / "manifest.json").exists())

    def test_cli_multi_file_user_import_build_and_run(self) -> None:
        src_main = """import helper

def main() -> None:
    print(helper.f())

if __name__ == "__main__":
    main()
"""
        src_helper = """def f() -> int:
    return 1
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            out_dir = root / "out"
            main_py = root / "main.py"
            helper_py = root / "helper.py"
            exe = out_dir / "app.out"
            main_py.write_text(src_main, encoding="utf-8")
            helper_py.write_text(src_helper, encoding="utf-8")
            tr = self._run_subprocess_with_timeout(
                ["python3", "src/py2cpp.py", str(main_py), "--multi-file", "--output-dir", str(out_dir)],
                cwd=ROOT,
                timeout_sec=PYTRA_TEST_TOOL_TIMEOUT_SEC,
                label="transpile multi-file sample",
            )
            self.assertEqual(tr.returncode, 0, msg=tr.stderr)
            bd = self._run_subprocess_with_timeout(
                ["python3", "tools/build_multi_cpp.py", str(out_dir / "manifest.json"), "-o", str(exe)],
                cwd=ROOT,
                timeout_sec=PYTRA_TEST_COMPILE_TIMEOUT_SEC,
                label="build multi-file sample",
            )
            self.assertEqual(bd.returncode, 0, msg=bd.stderr)
            rn = self._run_subprocess_with_timeout(
                [str(exe)],
                cwd=ROOT,
                timeout_sec=PYTRA_TEST_RUN_TIMEOUT_SEC,
                label="run multi-file sample",
            )
            self.assertEqual(rn.returncode, 0, msg=rn.stderr)
            self.assertIn("1", rn.stdout)

    def test_cli_reports_input_invalid_category(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_json = Path(tmpdir) / "bad.json"
            bad_json.write_text("[1,2,3]", encoding="utf-8")
            out_cpp = Path(tmpdir) / "bad.cpp"
            proc = subprocess.run(
                ["python3", "src/py2cpp.py", str(bad_json), "-o", str(out_cpp)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("[input_invalid]", proc.stderr)

    def test_cli_dump_options_allows_planned_bigint_preset(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "ok.py"
            src_py.write_text("print(1)\n", encoding="utf-8")
            proc = subprocess.run(
                ["python3", "src/py2cpp.py", str(src_py), "--preset", "python", "--dump-options"],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            self.assertIn("preset: python", proc.stdout)
            self.assertIn("int-width: bigint", proc.stdout)
            self.assertIn("str-index-mode: codepoint", proc.stdout)
            self.assertIn("str-slice-mode: codepoint", proc.stdout)

    def test_cli_rejects_codepoint_modes_without_dump_options(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "ok.py"
            src_py.write_text("print(1)\n", encoding="utf-8")
            proc = subprocess.run(
                ["python3", "src/py2cpp.py", str(src_py), "--str-index-mode", "codepoint"],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("--str-index-mode=codepoint is not implemented yet", proc.stderr)

    def test_class_storage_strategy_case15_case34(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            work = Path(tmpdir)

            case15_py = find_fixture_case("class_member")
            case15_cpp = work / "case15.cpp"
            transpile(case15_py, case15_cpp)
            case15_txt = case15_cpp.read_text(encoding="utf-8")
            self.assertIn("struct Counter {", case15_txt)
            self.assertIn("Counter c = Counter();", case15_txt)
            self.assertNotIn("rc<Counter>", case15_txt)

            case34_py = find_fixture_case("gc_reassign")
            case34_cpp = work / "case34.cpp"
            transpile(case34_py, case34_cpp)
            case34_txt = case34_cpp.read_text(encoding="utf-8")
            self.assertIn("struct Tracked : public PyObj {", case34_txt)
            self.assertIn("rc<Tracked> a = ", case34_txt)
            self.assertIn("rc_new<Tracked>(\"A\")", case34_txt)
            self.assertIn("a = b;", case34_txt)

    def test_dict_get_items_runtime(self) -> None:
        out = self._compile_and_run_fixture("dict_get_items")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_dict_wrapper_methods_runtime(self) -> None:
        out = self._compile_and_run_fixture("dict_wrapper_methods")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_set_wrapper_methods_runtime(self) -> None:
        out = self._compile_and_run_fixture("set_wrapper_methods")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_boolop_value_select_runtime(self) -> None:
        out = self._compile_and_run_fixture("boolop_value_select")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_bytes_basic_runtime(self) -> None:
        out = self._compile_and_run_fixture("bytes_basic")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_bytearray_basic_runtime(self) -> None:
        out = self._compile_and_run_fixture("bytearray_basic")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_comprehension_filter_runtime(self) -> None:
        out = self._compile_and_run_fixture("comprehension_filter")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_lambda_basic_runtime(self) -> None:
        out = self._compile_and_run_fixture("lambda_basic")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_any_basic_runtime(self) -> None:
        out = self._compile_and_run_fixture("any_basic")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_any_none_runtime(self) -> None:
        out = self._compile_and_run_fixture("any_none")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_any_dict_items_runtime(self) -> None:
        out = self._compile_and_run_fixture("any_dict_items")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_from_import_symbols_runtime(self) -> None:
        out = self._compile_and_run_fixture("from_import_symbols")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_any_list_mixed_runtime(self) -> None:
        out = self._compile_and_run_fixture("any_list_mixed")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_comprehension_nested_runtime(self) -> None:
        out = self._compile_and_run_fixture("comprehension_nested")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_comprehension_if_chain_runtime(self) -> None:
        out = self._compile_and_run_fixture("comprehension_if_chain")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_comprehension_dict_set_runtime(self) -> None:
        out = self._compile_and_run_fixture("comprehension_dict_set")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_comprehension_ifexp_runtime(self) -> None:
        out = self._compile_and_run_fixture("comprehension_ifexp")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_comprehension_range_step_like_runtime(self) -> None:
        out = self._compile_and_run_fixture("comprehension_range_step_like")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_comprehension_range_step_runtime(self) -> None:
        out = self._compile_and_run_fixture("comprehension_range_step")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_lambda_ifexp_runtime(self) -> None:
        out = self._compile_and_run_fixture("lambda_ifexp")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_lambda_capture_multiargs_runtime(self) -> None:
        out = self._compile_and_run_fixture("lambda_capture_multiargs")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_lambda_local_state_runtime(self) -> None:
        out = self._compile_and_run_fixture("lambda_local_state")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_lambda_as_arg_runtime(self) -> None:
        out = self._compile_and_run_fixture("lambda_as_arg")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_lambda_immediate_runtime(self) -> None:
        out = self._compile_and_run_fixture("lambda_immediate")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_pass_through_comment_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            work = Path(tmpdir)
            src_py = find_fixture_case("pass_through_comment")
            out_cpp = work / "pass_through_comment.cpp"
            transpile(src_py, out_cpp)
            txt = out_cpp.read_text(encoding="utf-8")
            self.assertIn("int injected = x;", txt)
            self.assertIn("injected += 1;", txt)
            self.assertIn("int temp = x;", txt)
            self.assertIn("temp += 1;", txt)
            self.assertNotIn("// Pytra::cpp", txt)
            self.assertNotIn("// Pytra::pass", txt)
        out = self._compile_and_run_fixture("pass_through_comment")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_super_init_runtime(self) -> None:
        out = self._compile_and_run_fixture("super_init")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_import_math_module_runtime(self) -> None:
        out = self._compile_and_run_fixture("import_math_module")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_import_time_from_runtime(self) -> None:
        out = self._compile_and_run_fixture("import_time_from")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_import_pylib_png_runtime(self) -> None:
        out = self._compile_and_run_fixture("import_pylib_png")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_import_pytra_runtime_png_runtime(self) -> None:
        out = self._compile_and_run_fixture("import_pytra_runtime_png")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_from_pytra_std_import_math_runtime(self) -> None:
        out = self._compile_and_run_fixture("from_pytra_std_import_math")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_str_index_char_compare_optimized_and_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            work = Path(tmpdir)
            src_py = find_fixture_case("str_index_char_compare")
            out_cpp = work / "str_index_char_compare.cpp"
            transpile(src_py, out_cpp)
            txt = out_cpp.read_text(encoding="utf-8")
            self.assertTrue(("s.at(i) == 'B'" in txt) or ('s[i] == "B"' in txt))
            self.assertTrue(("s.at(0) != 'B'" in txt) or ('s[0] != "B"' in txt))
        out = self._compile_and_run_fixture("str_index_char_compare")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_str_for_each_runtime(self) -> None:
        out = self._compile_and_run_fixture("str_for_each")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_str_slice_runtime(self) -> None:
        out = self._compile_and_run_fixture("str_slice")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_enumerate_basic_runtime(self) -> None:
        out = self._compile_and_run_fixture("enumerate_basic")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_in_membership_runtime(self) -> None:
        out = self._compile_and_run_fixture("in_membership")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_enum_basic_runtime(self) -> None:
        out = self._compile_and_run_fixture("enum_basic")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_intenum_basic_runtime(self) -> None:
        out = self._compile_and_run_fixture("intenum_basic")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_intflag_basic_runtime(self) -> None:
        out = self._compile_and_run_fixture("intflag_basic")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_math_extended_runtime(self) -> None:
        out = self._compile_and_run_fixture("math_extended")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_pathlib_extended_runtime(self) -> None:
        out = self._compile_and_run_fixture("pathlib_extended")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_os_glob_extended_runtime(self) -> None:
        out = self._compile_and_run_fixture("os_glob_extended")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_json_extended_runtime(self) -> None:
        out = self._compile_and_run_fixture("json_extended")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_argparse_extended_runtime(self) -> None:
        out = self._compile_and_run_fixture("argparse_extended")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_sys_extended_runtime(self) -> None:
        out = self._compile_and_run_fixture("sys_extended")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_typing_extended_runtime(self) -> None:
        out = self._compile_and_run_fixture("typing_extended")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_re_extended_runtime(self) -> None:
        out = self._compile_and_run_fixture("re_extended")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_dataclasses_extended_runtime(self) -> None:
        out = self._compile_and_run_fixture("dataclasses_extended")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_enum_extended_runtime(self) -> None:
        out = self._compile_and_run_fixture("enum_extended")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_random_timeit_traceback_extended_runtime(self) -> None:
        out = self._compile_and_run_fixture("random_timeit_traceback_extended")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_random_choices_range_call_lowers_to_py_range(self) -> None:
        src = """from pytra.std import random

def main() -> None:
    weights: list[float] = [1.0, 2.0, 3.0]
    picks: list[int] = random.choices(range(3), weights=weights, k=1)
    print(picks[0])
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "random_choices_range.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east)
        self.assertIn("py_range(0, 3, 1)", cpp)

    def test_lambda_default_arg_emits_cpp_default(self) -> None:
        src = """matrix = lambda nout, nin, std=0.08: nout + nin * std
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "lambda_default.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east)
        self.assertIn("float64 std = 0.08", cpp)

    def test_zip_tuple_unpack_does_not_force_object_receiver(self) -> None:
        src = """class Value:
    def __init__(self, children=(), local_grads=()):
        self.grad = 0
        self._children = children
        self._local_grads = local_grads

    def backward(self) -> None:
        for child, local_grad in zip(self._children, self._local_grads):
            child.grad += local_grad
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "zip_unpack.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east)
        self.assertIn("for (auto __it", cpp)
        self.assertIn("::std::get<0>(__it", cpp)
        self.assertNotIn("object receiver method call", cpp)

    def test_microgpt_compat_min_syntax_check(self) -> None:
        self._transpile_and_syntax_check_fixture("microgpt_compat_min")

    def test_emit_guard_rejects_object_receiver_call(self) -> None:
        east = {
            "kind": "Module",
            "body": [
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "func": {
                            "kind": "Attribute",
                            "value": {"kind": "Name", "id": "x", "resolved_type": "object"},
                            "attr": "bit_length",
                        },
                        "args": [],
                        "keywords": [],
                        "resolved_type": "unknown",
                    },
                }
            ],
        }
        with self.assertRaisesRegex(RuntimeError, "object receiver method call"):
            transpile_to_cpp(east)


if __name__ == "__main__":
    unittest.main()
