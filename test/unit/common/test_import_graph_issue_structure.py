from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import src.toolchain.frontends.transpile_cli as transpile_cli


class ImportGraphIssueStructureTest(unittest.TestCase):
    def test_graph_issue_helper_normalizes_legacy_and_structured_carriers(self) -> None:
        self.assertEqual(
            transpile_cli.normalize_graph_issue_entry("main.py: pkg.helper"),
            {"file": "main.py", "module": "pkg.helper"},
        )
        self.assertEqual(
            transpile_cli.normalize_graph_issue_entry({"file": "main.py", "module": "pkg.helper"}),
            {"file": "main.py", "module": "pkg.helper"},
        )
        self.assertEqual(
            transpile_cli.format_graph_issue_entry({"file": "main.py", "module": "pkg.helper"}),
            "main.py: pkg.helper",
        )

    def test_graph_issue_entry_list_prefers_structured_key(self) -> None:
        analysis: dict[str, object] = {
            "missing_modules": ["stale.py: stale.mod"],
            "missing_module_entries": [{"file": "main.py", "module": "pkg.helper"}],
        }
        self.assertEqual(
            transpile_cli.dict_any_get_graph_issue_entries(
                analysis,
                "missing_modules",
                "missing_module_entries",
            ),
            [{"file": "main.py", "module": "pkg.helper"}],
        )

    def test_finalize_import_graph_analysis_preserves_legacy_text_and_structured_entries(self) -> None:
        analysis = transpile_cli.finalize_import_graph_analysis(
            {"main.py": []},
            ["main.py"],
            {"main.py": "main.py"},
            ["main.py"],
            {"main.py": Path("main.py")},
            [],
            [{"file": "main.py", "module": "pkg.helper"}],
            [{"file": "main.py", "module": ".helper"}],
            [],
            {"main.py": "main"},
        )
        self.assertEqual(
            transpile_cli.dict_any_get_graph_issue_entries(
                analysis,
                "missing_modules",
                "missing_module_entries",
            ),
            [{"file": "main.py", "module": "pkg.helper"}],
        )
        self.assertEqual(
            transpile_cli.dict_any_get_graph_issue_entries(
                analysis,
                "relative_imports",
                "relative_import_entries",
            ),
            [{"file": "main.py", "module": ".helper"}],
        )
        self.assertEqual(analysis.get("missing_modules"), ["main.py: pkg.helper"])
        self.assertEqual(analysis.get("relative_imports"), ["main.py: .helper"])

    def test_report_and_validation_accept_structured_issue_entries(self) -> None:
        analysis: dict[str, object] = {
            "edges": ["main.py -> helper.py"],
            "cycles": [],
            "missing_module_entries": [{"file": "main.py", "module": "pkg.helper"}],
            "relative_import_entries": [{"file": "main.py", "module": ".helper"}],
            "reserved_conflicts": [],
        }
        report = transpile_cli.format_import_graph_report(analysis)
        self.assertIn("missing:\n  - main.py: pkg.helper\n", report)
        self.assertIn("relative:\n  - main.py: .helper\n", report)
        with self.assertRaises(RuntimeError) as cm:
            transpile_cli.validate_import_graph_or_raise(analysis)
        parsed = transpile_cli.parse_user_error(str(cm.exception))
        details = parsed.get("details")
        self.assertTrue(isinstance(details, list))
        joined = "\n".join(str(v) for v in details) if isinstance(details, list) else ""
        self.assertIn("kind=missing_module file=main.py import=pkg.helper", joined)
        self.assertIn("kind=relative_import_escape file=main.py import=from .helper import ...", joined)

    def test_validate_from_import_symbols_accepts_package_submodule_binding(self) -> None:
        root = ROOT / "tmp-relative-root"
        module_map: dict[str, dict[str, object]] = {
            str((root / "pkg" / "__init__.py")): {
                "kind": "Module",
                "east_stage": 3,
                "schema_version": 1,
                "meta": {"module_id": "pkg", "dispatch_mode": "native", "import_bindings": []},
                "body": [],
            },
            str((root / "pkg" / "main.py")): {
                "kind": "Module",
                "east_stage": 3,
                "schema_version": 1,
                "meta": {
                    "module_id": "pkg.main",
                    "dispatch_mode": "native",
                    "import_bindings": [
                        {
                            "module_id": "pkg",
                            "export_name": "helper",
                            "local_name": "helper",
                            "binding_kind": "symbol",
                        }
                    ],
                },
                "body": [
                    {
                        "kind": "ImportFrom",
                        "module": "pkg",
                        "names": [{"name": "helper"}],
                    }
                ],
            },
            str((root / "pkg" / "helper.py")): {
                "kind": "Module",
                "east_stage": 3,
                "schema_version": 1,
                "meta": {"module_id": "pkg.helper", "dispatch_mode": "native", "import_bindings": []},
                "body": [{"kind": "FunctionDef", "name": "f", "body": []}],
            },
        }

        transpile_cli.validate_from_import_symbols_or_raise(module_map, root)

        meta = module_map[str((root / "pkg" / "main.py"))]["meta"]
        self.assertEqual(meta["import_modules"], {"helper": "pkg.helper"})
        self.assertEqual(meta["import_symbols"], {})
        bindings = meta["import_bindings"]
        self.assertEqual(len(bindings), 1)
        self.assertEqual(bindings[0]["binding_kind"], "module")
        self.assertEqual(bindings[0]["module_id"], "pkg.helper")

    def test_collect_import_modules_expands_dot_only_from_import_module_candidates(self) -> None:
        east_doc: dict[str, object] = {
            "kind": "Module",
            "body": [
                {
                    "kind": "ImportFrom",
                    "module": ".",
                    "names": [{"name": "helper"}],
                }
            ],
        }

        self.assertEqual(transpile_cli.collect_import_modules(east_doc), [".helper"])

    def test_collect_import_modules_expands_parent_dot_only_from_import_module_candidates(self) -> None:
        east_doc: dict[str, object] = {
            "kind": "Module",
            "body": [
                {
                    "kind": "ImportFrom",
                    "module": "..",
                    "names": [{"name": "helper"}],
                }
            ],
        }

        self.assertEqual(transpile_cli.collect_import_modules(east_doc), ["..helper"])

    def test_collect_import_requests_preserves_from_import_symbol_shape(self) -> None:
        east_doc: dict[str, object] = {
            "kind": "Module",
            "body": [
                {
                    "kind": "ImportFrom",
                    "module": ".",
                    "names": [{"name": "helper"}],
                },
                {
                    "kind": "Import",
                    "names": [{"name": "pkg.util"}],
                },
            ],
        }

        self.assertEqual(
            transpile_cli.collect_import_requests(east_doc),
            [
                {"kind": "from_module", "module": ".", "symbol": "helper"},
                {"kind": "import_module", "module": "pkg.util", "symbol": ""},
            ],
        )

    def test_collect_import_request_modules_expands_dot_only_from_import_module_candidates(self) -> None:
        req = {"kind": "from_module", "module": ".", "symbol": "helper"}
        self.assertEqual(transpile_cli.collect_import_request_modules(req), [".helper"])

    def test_analyze_import_graph_accepts_dot_only_from_import_via_request_carrier(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pkg = root / "pkg"
            pkg.mkdir()
            (pkg / "__init__.py").write_text("", encoding="utf-8")
            main_py = pkg / "main.py"
            helper_py = pkg / "helper.py"
            main_py.write_text("from . import helper\nprint(helper.f())\n", encoding="utf-8")
            helper_py.write_text("def f() -> int:\n    return 1\n", encoding="utf-8")

            analysis = transpile_cli.analyze_import_graph(
                main_py,
                Path("src/pytra/std"),
                Path("src/pytra/utils"),
                transpile_cli.load_east_document,
            )

        self.assertEqual([], analysis.get("missing_modules"))
        self.assertEqual([], analysis.get("relative_imports"))
        self.assertIn("main.py -> helper.py", analysis.get("edges", []))
        module_id_map_obj = analysis.get("module_id_map")
        module_id_map = module_id_map_obj if isinstance(module_id_map_obj, dict) else {}
        self.assertEqual(module_id_map.get(str(main_py)), "main")
        self.assertEqual(module_id_map.get(str(helper_py)), "helper")

    def test_analyze_import_graph_accepts_parent_dot_only_from_import_via_request_carrier(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pkg = root / "pkg"
            sub = pkg / "sub"
            sub.mkdir(parents=True)
            (pkg / "__init__.py").write_text("", encoding="utf-8")
            (sub / "__init__.py").write_text("", encoding="utf-8")
            main_py = sub / "main.py"
            helper_py = pkg / "helper.py"
            main_py.write_text("from .. import helper\nprint(helper.f())\n", encoding="utf-8")
            helper_py.write_text("def f() -> int:\n    return 11\n", encoding="utf-8")

            analysis = transpile_cli.analyze_import_graph(
                main_py,
                Path("src/pytra/std"),
                Path("src/pytra/utils"),
                transpile_cli.load_east_document,
            )

        self.assertEqual([], analysis.get("missing_modules"))
        self.assertEqual([], analysis.get("relative_imports"))
        self.assertIn("sub/main.py -> helper.py", analysis.get("edges", []))

    def test_validate_from_import_symbols_accepts_parent_dot_only_module_binding(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pkg = root / "pkg"
            sub = pkg / "sub"
            sub.mkdir(parents=True)
            (pkg / "__init__.py").write_text("", encoding="utf-8")
            (sub / "__init__.py").write_text("", encoding="utf-8")
            main_py = sub / "main.py"
            helper_py = pkg / "helper.py"
            main_py.write_text("from .. import helper\nprint(helper.f())\n", encoding="utf-8")
            helper_py.write_text("def f() -> int:\n    return 11\n", encoding="utf-8")

            module_map: dict[str, dict[str, object]] = {
                str(main_py): {
                    "kind": "Module",
                    "east_stage": 3,
                    "schema_version": 1,
                    "meta": {
                        "module_id": "sub.main",
                        "dispatch_mode": "native",
                        "import_bindings": [
                            {
                                "module_id": "..",
                                "export_name": "helper",
                                "local_name": "helper",
                                "binding_kind": "symbol",
                            }
                        ],
                        "qualified_symbol_refs": [
                            {
                                "module_id": "..",
                                "symbol": "helper",
                                "local_name": "helper",
                            }
                        ],
                    },
                    "body": [
                        {
                            "kind": "ImportFrom",
                            "module": "..",
                            "names": [{"name": "helper"}],
                        }
                    ],
                },
                str(helper_py): {
                    "kind": "Module",
                    "east_stage": 3,
                    "schema_version": 1,
                    "meta": {"module_id": "helper", "dispatch_mode": "native", "import_bindings": []},
                    "body": [{"kind": "FunctionDef", "name": "f", "body": []}],
                },
            }

            transpile_cli.validate_from_import_symbols_or_raise(module_map, sub)

            meta = module_map[str(main_py)]["meta"]
            self.assertEqual(meta["import_modules"], {"helper": "helper"})
            self.assertEqual(meta["import_symbols"], {})
            bindings = meta["import_bindings"]
            self.assertEqual(len(bindings), 1)
            self.assertEqual(bindings[0]["binding_kind"], "module")
            self.assertEqual(bindings[0]["module_id"], "helper")

    def test_validate_from_import_symbols_accepts_parent_dot_only_module_alias_binding(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pkg = root / "pkg"
            sub = pkg / "sub"
            sub.mkdir(parents=True)
            (pkg / "__init__.py").write_text("", encoding="utf-8")
            (sub / "__init__.py").write_text("", encoding="utf-8")
            main_py = sub / "main.py"
            helper_py = pkg / "helper.py"
            main_py.write_text("from .. import helper as h\nprint(h.f())\n", encoding="utf-8")
            helper_py.write_text("def f() -> int:\n    return 11\n", encoding="utf-8")

            module_map: dict[str, dict[str, object]] = {
                str(main_py): {
                    "kind": "Module",
                    "east_stage": 3,
                    "schema_version": 1,
                    "meta": {
                        "module_id": "sub.main",
                        "dispatch_mode": "native",
                        "import_bindings": [
                            {
                                "module_id": "..",
                                "export_name": "helper",
                                "local_name": "h",
                                "binding_kind": "symbol",
                            }
                        ],
                        "qualified_symbol_refs": [
                            {
                                "module_id": "..",
                                "symbol": "helper",
                                "local_name": "h",
                            }
                        ],
                    },
                    "body": [
                        {
                            "kind": "ImportFrom",
                            "module": "..",
                            "names": [{"name": "helper", "asname": "h"}],
                        }
                    ],
                },
                str(helper_py): {
                    "kind": "Module",
                    "east_stage": 3,
                    "schema_version": 1,
                    "meta": {"module_id": "helper", "dispatch_mode": "native", "import_bindings": []},
                    "body": [{"kind": "FunctionDef", "name": "f", "body": []}],
                },
            }

            transpile_cli.validate_from_import_symbols_or_raise(module_map, sub)

            meta = module_map[str(main_py)]["meta"]
            self.assertEqual(meta["import_modules"], {"h": "helper"})
            self.assertEqual(meta["import_symbols"], {})
            bindings = meta["import_bindings"]
            self.assertEqual(len(bindings), 1)
            self.assertEqual(bindings[0]["binding_kind"], "module")
            self.assertEqual(bindings[0]["module_id"], "helper")
            self.assertEqual(bindings[0]["local_name"], "h")

    def test_validate_from_import_symbols_accepts_parent_symbol_alias_binding(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pkg = root / "pkg"
            sub = pkg / "sub"
            sub.mkdir(parents=True)
            (pkg / "__init__.py").write_text("", encoding="utf-8")
            (sub / "__init__.py").write_text("", encoding="utf-8")
            main_py = sub / "main.py"
            helper_py = pkg / "helper.py"
            main_py.write_text("from ..helper import f as g\nprint(g())\n", encoding="utf-8")
            helper_py.write_text("def f() -> int:\n    return 11\n", encoding="utf-8")

            module_map: dict[str, dict[str, object]] = {
                str(main_py): {
                    "kind": "Module",
                    "east_stage": 3,
                    "schema_version": 1,
                    "meta": {
                        "module_id": "sub.main",
                        "dispatch_mode": "native",
                        "import_bindings": [
                            {
                                "module_id": "..helper",
                                "export_name": "f",
                                "local_name": "g",
                                "binding_kind": "symbol",
                            }
                        ],
                        "qualified_symbol_refs": [],
                    },
                    "body": [
                        {
                            "kind": "ImportFrom",
                            "module": "..helper",
                            "names": [{"name": "f", "asname": "g"}],
                        }
                    ],
                },
                str(helper_py): {
                    "kind": "Module",
                    "east_stage": 3,
                    "schema_version": 1,
                    "meta": {"module_id": "helper", "dispatch_mode": "native", "import_bindings": []},
                    "body": [{"kind": "FunctionDef", "name": "f", "body": []}],
                },
            }

            transpile_cli.validate_from_import_symbols_or_raise(module_map, sub)

            meta = module_map[str(main_py)]["meta"]
            self.assertEqual(meta["import_modules"], {})
            self.assertEqual(meta["import_symbols"], {"g": {"module": "helper", "name": "f"}})
            bindings = meta["import_bindings"]
            self.assertEqual(len(bindings), 1)
            self.assertEqual(bindings[0]["binding_kind"], "symbol")
            self.assertEqual(bindings[0]["module_id"], "helper")
            self.assertEqual(bindings[0]["export_name"], "f")
            self.assertEqual(bindings[0]["local_name"], "g")

    def test_validate_from_import_symbols_accepts_reexported_symbol_binding(self) -> None:
        root = ROOT / "tmp-reexport-root"
        compat_py = root / "pytra_compat.py"
        main_py = root / "main.py"
        module_map: dict[str, dict[str, object]] = {
            str(compat_py): {
                "kind": "Module",
                "east_stage": 3,
                "schema_version": 1,
                "meta": {
                    "module_id": "pytra_compat",
                    "dispatch_mode": "native",
                    "import_bindings": [
                        {
                            "module_id": "pytra.std.pathlib",
                            "export_name": "Path",
                            "local_name": "Path",
                            "binding_kind": "symbol",
                        }
                    ],
                },
                "body": [
                    {
                        "kind": "ImportFrom",
                        "module": "pytra.std.pathlib",
                        "names": [{"name": "Path"}],
                    }
                ],
            },
            str(main_py): {
                "kind": "Module",
                "east_stage": 3,
                "schema_version": 1,
                "meta": {
                    "module_id": "main",
                    "dispatch_mode": "native",
                    "import_bindings": [
                        {
                            "module_id": "pytra_compat",
                            "export_name": "Path",
                            "local_name": "Path",
                            "binding_kind": "symbol",
                        }
                    ],
                },
                "body": [
                    {
                        "kind": "ImportFrom",
                        "module": "pytra_compat",
                        "names": [{"name": "Path"}],
                    }
                ],
            },
        }

        transpile_cli.validate_from_import_symbols_or_raise(module_map, root)

        meta = module_map[str(main_py)]["meta"]
        self.assertEqual(
            meta["import_symbols"],
            {"Path": {"module": "pytra_compat", "name": "Path"}},
        )


if __name__ == "__main__":
    unittest.main()
