from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import shutil


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))


from toolchain2.link.linker import LinkedModule, link_modules
from toolchain2.link.dependencies import build_all_resolved_dependencies
from toolchain2.link.dependencies import is_type_only_dependency_module_id
from toolchain2.link.expand_defaults import expand_cross_module_defaults
from toolchain2.link.manifest_loader import load_linked_output
from toolchain2.link.runtime_discovery import discover_runtime_modules
from toolchain2.link.runtime_discovery import is_runtime_internal_helper_module
from toolchain2.link.runtime_discovery import is_runtime_namespace_module
from toolchain2.link.runtime_discovery import resolve_runtime_module_rel_tail
from toolchain2.link.type_id import build_type_id_table
from toolchain2.common.jv import deep_copy_json
from toolchain2.parse.py.parse_python import parse_python_file
from toolchain2.resolve.py.builtin_registry import load_builtin_registry
from toolchain2.resolve.py.resolver import resolve_east1_to_east2
from toolchain2.compile.lower import lower_east2_to_east3
from toolchain2.optimize.optimizer import optimize_east3_document
from toolchain2.emit.go.emitter import emit_go_module
from toolchain2.emit.cpp.emitter import emit_cpp_module
from toolchain2.emit.cpp.header_gen import build_cpp_header_from_east3
from toolchain2.emit.cpp.runtime_bundle import emit_runtime_module_artifacts
from toolchain2.emit.cpp.runtime_paths import collect_cpp_dependency_module_ids
from toolchain2.emit.cpp.runtime_paths import cpp_include_for_module
from toolchain2.emit.cpp.runtime_paths import runtime_rel_tail_for_module
from toolchain2.emit.common.code_emitter import RuntimeMapping
from toolchain2.emit.common.code_emitter import load_runtime_mapping


def _module_doc(
    module_id: str,
    *,
    source_path: str = "",
    body: list[dict[str, object]] | None = None,
    meta_extra: dict[str, object] | None = None,
) -> dict[str, object]:
    meta: dict[str, object] = {
        "module_id": module_id,
        "dispatch_mode": "native",
    }
    if meta_extra:
        meta.update(meta_extra)
    return {
        "kind": "Module",
        "east_stage": 3,
        "schema_version": 1,
        "source_path": source_path,
        "meta": meta,
        "body": body if body is not None else [],
    }


def _class_def(
    name: str,
    *,
    base: str | None = None,
    bases: list[str] | None = None,
) -> dict[str, object]:
    node: dict[str, object] = {
        "kind": "ClassDef",
        "name": name,
        "body": [],
    }
    if bases is not None:
        node["bases"] = bases
    else:
        node["base"] = base
    return node


def _linked_module(module_id: str, body: list[dict[str, object]]) -> LinkedModule:
    return LinkedModule(
        module_id=module_id,
        input_path=module_id.replace(".", "/") + ".east3.json",
        source_path=module_id.replace(".", "/") + ".py",
        is_entry=True,
        east_doc=_module_doc(module_id, body=body),
        module_kind="user",
    )


def _fixture_doc(relative_path: str) -> dict[str, object]:
    fixture_path = ROOT / relative_path
    return json.loads(fixture_path.read_text(encoding="utf-8"))


def _walk_nodes(node: object) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    if isinstance(node, dict):
        out.append(node)
        for value in node.values():
            out.extend(_walk_nodes(value))
    elif isinstance(node, list):
        for item in node:
            out.extend(_walk_nodes(item))
    return out


def _build_current_selfhost_east3_paths(tmpdir: Path) -> list[str]:
    inputs: list[Path] = []
    for p in sorted((ROOT / "test" / "selfhost" / "east3-opt").rglob("*.east3")):
        data = json.loads(p.read_text(encoding="utf-8"))
        source_path = data.get("source_path", "")
        if isinstance(source_path, str) and source_path.startswith("src/toolchain2/"):
            inputs.append(ROOT / source_path)
    inputs = sorted(dict.fromkeys(inputs))

    builtins_path = ROOT / "test" / "include" / "east1" / "py" / "built_in" / "builtins.py.east1"
    containers_path = ROOT / "test" / "include" / "east1" / "py" / "built_in" / "containers.py.east1"
    stdlib_dir = ROOT / "test" / "include" / "east1" / "py" / "std"
    registry = load_builtin_registry(builtins_path, containers_path, stdlib_dir)

    outdir = tmpdir / "selfhost-e3"
    shutil.rmtree(outdir, ignore_errors=True)
    outdir.mkdir(parents=True, exist_ok=True)

    out_paths: list[str] = []
    for src in inputs:
        rel = str(src.relative_to(ROOT)).replace("\\", "/")
        east1 = parse_python_file(str(src))
        east1["source_path"] = rel
        resolve_east1_to_east2(east1, registry=registry)
        east3 = lower_east2_to_east3(east1)
        east3["source_path"] = rel
        east3, _ = optimize_east3_document(east3, opt_level=1)
        east3["source_path"] = rel
        target = outdir / (rel.replace("/", "__").replace(".py", "") + ".east3")
        target.write_text(json.dumps(east3, ensure_ascii=False), encoding="utf-8")
        out_paths.append(str(target))
    return out_paths


class Toolchain2LinkerSpecConform2Tests(unittest.TestCase):
    def test_link_modules_rejects_unresolved_user_import_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entry_path = Path(tmp) / "app.main.east3.json"
            entry_path.write_text(
                json.dumps(
                    _module_doc(
                        "app.main",
                        source_path="app/main.py",
                        meta_extra={
                            "import_bindings": [
                                {"module_id": "pkg.dep", "binding_kind": "symbol", "local_name": "dep"},
                            ]
                        },
                    ),
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(RuntimeError, "pkg\\.dep"):
                link_modules([str(entry_path)], target="go", dispatch_mode="native")

    def test_link_modules_allows_external_runtime_whitelist_import(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entry_path = Path(tmp) / "app.main.east3.json"
            entry_path.write_text(
                json.dumps(
                    _module_doc(
                        "app.main",
                        source_path="app/main.py",
                        meta_extra={
                            "import_bindings": [
                                {"module_id": "pytra.std.json", "binding_kind": "symbol", "local_name": "json"},
                            ]
                        },
                    ),
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = link_modules([str(entry_path)], target="go", dispatch_mode="native")

            self.assertEqual(result.manifest["entry_modules"], ["app.main"])

    def test_link_modules_accepts_host_only_module_binding_when_runtime_module_is_provided(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entry_path = Path(tmp) / "app.main.east3.json"
            entry_path.write_text(
                json.dumps(
                    _module_doc(
                        "app.main",
                        source_path="app/main.py",
                        meta_extra={
                            "import_bindings": [
                                {
                                    "module_id": "pathlib",
                                    "binding_kind": "module",
                                    "local_name": "pathlib",
                                    "runtime_module_id": "pytra.std.pathlib",
                                    "resolved_binding_kind": "module",
                                    "host_only": True,
                                }
                            ],
                            "import_modules": {"pathlib": "pathlib"},
                        },
                    ),
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = link_modules([str(entry_path)], target="cpp", dispatch_mode="native")

            self.assertEqual(result.manifest["entry_modules"], ["app.main"])

    def test_build_all_resolved_dependencies_skips_type_only_template_but_keeps_runtime_module_import(self) -> None:
        modules = [
            _linked_module(
                "app.main",
                body=[],
            )
        ]
        meta = modules[0].east_doc["meta"]
        assert isinstance(meta, dict)
        meta["import_bindings"] = [
            {
                "module_id": "pytra.std",
                "export_name": "template",
                "binding_kind": "symbol",
                "local_name": "template",
                "runtime_module_id": "pytra.std.template",
                "runtime_group": "std",
                "resolved_binding_kind": "module",
                "host_only": True,
            },
            {
                "module_id": "pathlib",
                "binding_kind": "module",
                "local_name": "pathlib",
                "runtime_module_id": "pytra.std.pathlib",
                "resolved_binding_kind": "module",
                "host_only": True,
            },
            {
                "module_id": "os.path",
                "binding_kind": "module",
                "local_name": "os.path",
                "runtime_module_id": "os.path",
                "resolved_binding_kind": "module",
                "host_only": True,
            },
        ]

        resolved, user_deps = build_all_resolved_dependencies(modules)

        self.assertEqual(resolved["app.main"], ["pytra.std.pathlib"])
        self.assertEqual(user_deps["app.main"], [])

    def test_discover_runtime_modules_adds_type_id_runtime_for_isinstance_nodes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entry_path = Path(tmp) / "app.main.east3.json"
            entry_doc = _module_doc(
                "app.main",
                body=[
                    {
                        "kind": "Expr",
                        "value": {
                            "kind": "IsInstance",
                            "value": {"kind": "Name", "id": "dyn", "resolved_type": "object"},
                            "expected_type_id": {"kind": "Name", "id": "PYTRA_TID_LIST", "resolved_type": "int64"},
                            "resolved_type": "bool",
                        },
                    }
                ],
            )
            entry_path.write_text(json.dumps(entry_doc, ensure_ascii=False), encoding="utf-8")

            discovered = discover_runtime_modules({str(entry_path): entry_doc})

            self.assertIn(str(ROOT / "src/runtime/east/built_in/type_id.east"), discovered)

    def test_build_all_resolved_dependencies_includes_type_id_for_type_predicates(self) -> None:
        modules = [
            _linked_module(
                "app.main",
                body=[
                    {
                        "kind": "Expr",
                        "value": {
                            "kind": "IsSubtype",
                            "actual_type_id": {"kind": "Name", "id": "actual", "resolved_type": "int64"},
                            "expected_type_id": {"kind": "Name", "id": "expected", "resolved_type": "int64"},
                            "resolved_type": "bool",
                        },
                    }
                ],
            )
        ]

        resolved, _ = build_all_resolved_dependencies(modules)

        self.assertEqual(resolved["app.main"], ["pytra.built_in.type_id"])

    def test_resolve_deep_copy_keeps_enhanced_import_bindings_in_sync(self) -> None:
        source_path = ROOT / "sample" / "py" / "17_monte_carlo_pi.py"
        east1 = parse_python_file(str(source_path))
        east2 = deep_copy_json(east1)
        assert isinstance(east2, dict)
        registry = load_builtin_registry(
            ROOT / "test" / "include" / "east1" / "py" / "built_in" / "builtins.py.east1",
            ROOT / "test" / "include" / "east1" / "py" / "built_in" / "containers.py.east1",
            ROOT / "test" / "include" / "east1" / "py" / "std",
        )

        resolve_east1_to_east2(east2, registry=registry)

        meta = east2.get("meta")
        assert isinstance(meta, dict)
        bindings = meta.get("import_bindings")
        assert isinstance(bindings, list)
        self.assertGreater(len(bindings), 0)
        first = bindings[0]
        assert isinstance(first, dict)
        self.assertEqual(first.get("runtime_module_id"), "pytra.std.pathlib")
        self.assertEqual(first.get("runtime_symbol_dispatch"), "ctor")

    def test_resolve_membership_adds_contains_builtin_dependency(self) -> None:
        source = """\
def has_key(env: dict[str, int], name: str) -> bool:
    return name in env
"""
        registry = load_builtin_registry(
            ROOT / "test" / "include" / "east1" / "py" / "built_in" / "builtins.py.east1",
            ROOT / "test" / "include" / "east1" / "py" / "built_in" / "containers.py.east1",
            ROOT / "test" / "include" / "east1" / "py" / "std",
        )
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "has_key.py"
            src.write_text(source, encoding="utf-8")
            east2 = parse_python_file(str(src))
            resolve_east1_to_east2(east2, registry=registry)

        meta = east2.get("meta")
        assert isinstance(meta, dict)
        bindings = meta.get("import_bindings")
        assert isinstance(bindings, list)
        self.assertTrue(any(isinstance(b, dict) and b.get("module_id") == "pytra.built_in.contains" for b in bindings))

    def test_link_modules_reports_missing_selfhost_transitive_modules(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _build_current_selfhost_east3_paths(Path(tmp))
            self.assertEqual(len(paths), 37)

            with self.assertRaisesRegex(RuntimeError, "toolchain2\\.compile\\.jv"):
                link_modules(paths, target="go", dispatch_mode="native")

            try:
                link_modules(paths, target="go", dispatch_mode="native")
            except RuntimeError as exc:
                msg = str(exc)
            else:
                self.fail("expected unresolved import dependency")

        self.assertIn("toolchain2.compile.jv", msg)
        self.assertIn("toolchain2.link.expand_defaults", msg)
        self.assertIn("toolchain2.optimize.passes", msg)
        self.assertIn("toolchain2.parse.py.nodes", msg)
        self.assertIn("toolchain2.parse.py.parser", msg)
        self.assertIn("toolchain2.resolve.py.builtin_registry", msg)
        self.assertIn("toolchain2.resolve.py.normalize_order", msg)

    def test_type_id_builder_accepts_single_base_from_bases_array(self) -> None:
        modules = [
            _linked_module(
                "app.main",
                [
                    _class_def("Base"),
                    _class_def("Child", bases=["Base"]),
                ],
            )
        ]

        type_id_table, type_id_base_map, type_info_table = build_type_id_table(modules)

        self.assertIn("app.main.Base", type_id_table)
        self.assertIn("app.main.Child", type_id_table)
        self.assertEqual(type_id_base_map["app.main.Child"], type_id_table["app.main.Base"])
        self.assertEqual(type_info_table["app.main.Base"]["id"], type_id_table["app.main.Base"])

    def test_type_id_builder_rejects_multiple_inheritance(self) -> None:
        modules = [
            _linked_module(
                "app.main",
                [
                    _class_def("A"),
                    _class_def("B"),
                    _class_def("C", bases=["A", "B"]),
                ],
            )
        ]

        with self.assertRaisesRegex(RuntimeError, "multiple inheritance is not supported"):
            build_type_id_table(modules)

    def test_type_id_builder_rejects_undefined_base(self) -> None:
        modules = [
            _linked_module(
                "app.main",
                [
                    _class_def("Child", bases=["Missing"]),
                ],
            )
        ]

        with self.assertRaisesRegex(RuntimeError, "undefined base class"):
            build_type_id_table(modules)

    def test_type_id_builder_rejects_inheritance_cycle(self) -> None:
        modules = [
            _linked_module(
                "app.main",
                [
                    _class_def("A", bases=["B"]),
                    _class_def("B", bases=["A"]),
                ],
            )
        ]

        with self.assertRaisesRegex(RuntimeError, "inheritance cycle"):
            build_type_id_table(modules)

    def test_type_id_builder_maps_exception_base_to_builtin_value_error(self) -> None:
        modules = [
            _linked_module(
                "app.main",
                [
                    _class_def("ParseError", base="ValueError"),
                ],
            )
        ]

        type_id_table, type_id_base_map, _ = build_type_id_table(modules)

        self.assertIn("app.main.ParseError", type_id_table)
        self.assertEqual(type_id_base_map["app.main.ParseError"], 12)

    def test_runtime_discovery_rejects_missing_explicit_runtime_module(self) -> None:
        module_map = {
            "/tmp/app.main.east3.json": _module_doc(
                "app.main",
                meta_extra={"import_bindings": [{"module_id": "pytra.std.missing"}]},
            )
        }

        with patch("toolchain2.link.runtime_discovery.resolve_runtime_east_path", return_value=""):
            with self.assertRaisesRegex(RuntimeError, "runtime EAST module not found"):
                discover_runtime_modules(module_map)

    def test_runtime_discovery_rejects_invalid_runtime_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad_runtime = Path(tmp) / "bad.east"
            bad_runtime.write_text("{bad json", encoding="utf-8")
            module_map = {
                "/tmp/app.main.east3.json": _module_doc(
                    "app.main",
                    meta_extra={"import_bindings": [{"module_id": "pytra.std.time"}]},
                )
            }

            with patch("toolchain2.link.runtime_discovery.resolve_runtime_east_path", return_value=str(bad_runtime)):
                with self.assertRaisesRegex(RuntimeError, "failed to parse runtime EAST"):
                    discover_runtime_modules(module_map)

    def test_runtime_discovery_allows_missing_speculative_runtime_submodule_probe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime_path = Path(tmp) / "assertions.east"
            runtime_path.write_text(
                json.dumps(
                    _module_doc("pytra.utils.assertions"),
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            module_map = {
                "/tmp/app.main.east3.json": _module_doc(
                    "app.main",
                    body=[
                        {
                            "kind": "ImportFrom",
                            "module": "pytra.utils.assertions",
                            "names": [{"name": "py_assert_all"}],
                        }
                    ],
                )
            }

            def _resolve(module_id: str) -> str:
                if module_id == "pytra.utils.assertions":
                    return str(runtime_path)
                if module_id == "pytra.utils.assertions.py_assert_all":
                    return ""
                return ""

            with patch("toolchain2.link.runtime_discovery.resolve_runtime_east_path", side_effect=_resolve):
                result = discover_runtime_modules(module_map)

            self.assertIn(str(runtime_path), result)

    def test_runtime_discovery_ignores_meta_binding_runtime_ids_without_ast_kind(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime_path = Path(tmp) / "sequence.east"
            runtime_path.write_text(
                json.dumps(
                    _module_doc("pytra.built_in.sequence"),
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            module_map = {
                "/tmp/app.main.east3.json": _module_doc(
                    "app.main",
                    meta_extra={
                        "import_bindings": [{"module_id": "pytra.built_in.sequence"}],
                        "import_resolution": {
                            "bindings": [
                                {
                                    "runtime_module_id": "pytra.std.template",
                                    "resolved_binding_kind": "module",
                                }
                            ]
                        },
                    },
                )
            }

            def _resolve(module_id: str) -> str:
                if module_id == "pytra.built_in.sequence":
                    return str(runtime_path)
                if module_id == "pytra.std.template":
                    return ""
                return ""

            with patch("toolchain2.link.runtime_discovery.resolve_runtime_east_path", side_effect=_resolve):
                result = discover_runtime_modules(module_map)

            self.assertIn(str(runtime_path), result)

    def test_link_dependencies_prefer_runtime_module_ids_and_skip_host_python_modules(self) -> None:
        module = LinkedModule(
            module_id="app.main",
            input_path="app/main.east3.json",
            source_path="app/main.py",
            is_entry=True,
            module_kind="user",
            east_doc=_module_doc(
                "app.main",
                body=[
                    {
                        "kind": "ImportFrom",
                        "module": "pytra.std",
                        "names": [{"name": "os_path", "asname": "path"}],
                    },
                    {
                        "kind": "Import",
                        "names": [{"name": "os.path", "asname": None}],
                    },
                ],
                meta_extra={
                    "import_bindings": [
                        {
                            "module_id": "pytra.std",
                            "export_name": "os_path",
                            "local_name": "path",
                            "binding_kind": "symbol",
                            "runtime_module_id": "pytra.std.os_path",
                            "runtime_group": "std",
                            "resolved_binding_kind": "module",
                            "host_only": True,
                        },
                        {
                            "module_id": "os.path",
                            "export_name": "",
                            "local_name": "os.path",
                            "binding_kind": "module",
                            "runtime_module_id": "os.path",
                            "runtime_group": "",
                            "host_only": True,
                        },
                    ]
                },
            ),
        )

        resolved, user_deps = build_all_resolved_dependencies([module])

        self.assertEqual(resolved["app.main"], ["pytra.std.os_path"])
        self.assertEqual(user_deps["app.main"], [])

    def test_manifest_loader_rejects_invalid_module_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema": "pytra.link_output.v1",
                        "target": "cpp",
                        "dispatch_mode": "native",
                        "entry_modules": ["app.main"],
                        "modules": [
                            {
                                "module_id": "app.main",
                                "input": "raw/app.main.east3.json",
                                "source_path": "app/main.py",
                                "is_entry": True,
                                "module_kind": "user",
                            }
                        ],
                        "global": {
                            "type_id_table": {},
                            "type_id_base_map": {},
                            "call_graph": {},
                            "sccs": [],
                            "non_escape_summary": {},
                            "container_ownership_hints_v1": {},
                        },
                        "diagnostics": {"warnings": [], "errors": []},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(RuntimeError, r"manifest\.modules\[0\]\.output must be non-empty string"):
                load_linked_output(manifest_path)

    def test_manifest_loader_rejects_missing_linked_east_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema": "pytra.link_output.v1",
                        "target": "cpp",
                        "dispatch_mode": "native",
                        "entry_modules": ["app.main"],
                        "modules": [
                            {
                                "module_id": "app.main",
                                "input": "raw/app.main.east3.json",
                                "output": "east3/app.main.east3.json",
                                "source_path": "app/main.py",
                                "is_entry": True,
                                "module_kind": "user",
                            }
                        ],
                        "global": {
                            "type_id_table": {},
                            "type_id_base_map": {},
                            "call_graph": {},
                            "sccs": [],
                            "non_escape_summary": {},
                            "container_ownership_hints_v1": {},
                        },
                        "diagnostics": {"warnings": [], "errors": []},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(RuntimeError, "linked EAST file not found"):
                load_linked_output(manifest_path)

    def test_manifest_loader_rejects_invalid_linked_east_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            east_path = Path(tmp) / "east3" / "app.main.east3.json"
            east_path.parent.mkdir(parents=True, exist_ok=True)
            east_path.write_text("{bad json", encoding="utf-8")
            manifest_path = Path(tmp) / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema": "pytra.link_output.v1",
                        "target": "cpp",
                        "dispatch_mode": "native",
                        "entry_modules": ["app.main"],
                        "modules": [
                            {
                                "module_id": "app.main",
                                "input": "raw/app.main.east3.json",
                                "output": "east3/app.main.east3.json",
                                "source_path": "app/main.py",
                                "is_entry": True,
                                "module_kind": "user",
                            }
                        ],
                        "global": {
                            "type_id_table": {},
                            "type_id_base_map": {},
                            "call_graph": {},
                            "sccs": [],
                            "non_escape_summary": {},
                            "container_ownership_hints_v1": {},
                        },
                        "diagnostics": {"warnings": [], "errors": []},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(RuntimeError, "failed to parse linked EAST file"):
                load_linked_output(manifest_path)

    def test_link_modules_manifest_input_points_to_raw_east3_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entry_path = Path(tmp) / "app.main.east3.json"
            entry_path.write_text(
                json.dumps(
                    _module_doc(
                        "app.main",
                        source_path="app/main.py",
                    ),
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = link_modules([str(entry_path)], target="cpp", dispatch_mode="native")

            modules = result.manifest.get("modules")
            self.assertIsInstance(modules, list)
            assert isinstance(modules, list)
            entry = next(item for item in modules if isinstance(item, dict) and item.get("module_id") == "app.main")
            self.assertEqual(entry.get("input"), str(entry_path.resolve()))
            self.assertEqual(entry.get("source_path"), "app/main.py")

    def test_expand_defaults_uses_same_module_qualified_name(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "foo",
                    "arg_order": ["x", "y"],
                    "arg_defaults": {
                        "y": {"kind": "Constant", "value": 2},
                    },
                    "body": [],
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "func": {"kind": "Name", "id": "foo"},
                        "args": [{"kind": "Constant", "value": 1}],
                    },
                },
            ],
        )

        expand_cross_module_defaults([doc])

        body = doc["body"]
        assert isinstance(body, list)
        call = body[1]["value"]
        self.assertEqual(len(call["args"]), 2)
        self.assertEqual(call["args"][1]["value"], 2)

    def test_expand_defaults_uses_imported_symbol_module_id(self) -> None:
        dep_doc = _module_doc(
            "pkg.dep",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "foo",
                    "arg_order": ["x", "y"],
                    "arg_defaults": {
                        "y": {"kind": "Constant", "value": 9},
                    },
                    "body": [],
                }
            ],
        )
        main_doc = _module_doc(
            "app.main",
            meta_extra={
                "import_symbols": {
                    "foo": {"module": "pkg.dep", "name": "foo"},
                }
            },
            body=[
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "func": {"kind": "Name", "id": "foo"},
                        "args": [{"kind": "Constant", "value": 1}],
                    },
                }
            ],
        )

        expand_cross_module_defaults([dep_doc, main_doc])

        body = main_doc["body"]
        assert isinstance(body, list)
        call = body[0]["value"]
        self.assertEqual(len(call["args"]), 2)
        self.assertEqual(call["args"][1]["value"], 9)

    def test_expand_defaults_uses_explicit_module_ids_when_meta_is_missing(self) -> None:
        dep_doc = {
            "kind": "Module",
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "foo",
                    "arg_order": ["x", "y"],
                    "arg_defaults": {
                        "y": {"kind": "Constant", "value": 9},
                    },
                    "body": [],
                }
            ],
        }
        main_doc = {
            "kind": "Module",
            "meta": {
                "import_symbols": {
                    "foo": {"module": "pkg.dep", "name": "foo"},
                }
            },
            "body": [
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "func": {"kind": "Name", "id": "foo"},
                        "args": [{"kind": "Constant", "value": 1}],
                        "keywords": [],
                    },
                }
            ],
        }

        expand_cross_module_defaults([("pkg.dep", dep_doc), ("app.main", main_doc)])

        body = main_doc["body"]
        assert isinstance(body, list)
        call = body[0]["value"]
        self.assertEqual(len(call["args"]), 2)
        self.assertEqual(call["args"][1]["value"], 9)

    def test_expand_defaults_uses_imported_module_symbol_runtime_module_id(self) -> None:
        dep_doc = _module_doc(
            "pytra.std.os",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "mkdir",
                    "arg_order": ["p", "exist_ok"],
                    "arg_defaults": {
                        "exist_ok": {"kind": "Constant", "resolved_type": "bool", "value": False},
                    },
                    "body": [],
                }
            ],
        )
        main_doc = _module_doc(
            "pytra.std.pathlib",
            meta_extra={
                "import_symbols": {
                    "os": {"module": "pytra.std", "name": "os"},
                }
            },
            body=[
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "resolved_type": "None",
                        "func": {
                            "kind": "Attribute",
                            "attr": "mkdir",
                            "value": {
                                "kind": "Name",
                                "id": "os",
                                "resolved_type": "module",
                                "runtime_module_id": "pytra.std.os",
                            },
                        },
                        "args": [{"kind": "Constant", "resolved_type": "str", "value": "tmp"}],
                        "keywords": [],
                        "runtime_module_id": "pytra.std.os",
                        "runtime_symbol": "mkdir",
                        "resolved_runtime_call": "os.mkdir",
                    },
                }
            ],
        )

        expand_cross_module_defaults([dep_doc, main_doc])

        body = main_doc["body"]
        assert isinstance(body, list)
        call = body[0]["value"]
        self.assertEqual(len(call["args"]), 2)
        self.assertFalse(call["args"][1]["value"])

    def test_expand_defaults_does_not_expand_ambiguous_object_method_calls(self) -> None:
        doc_a = _module_doc(
            "pkg.a",
            body=[
                {
                    "kind": "ClassDef",
                    "name": "A",
                    "body": [
                        {
                            "kind": "FunctionDef",
                            "name": "run",
                            "arg_order": ["self", "x", "y"],
                            "arg_defaults": {
                                "y": {"kind": "Constant", "value": 1},
                            },
                            "body": [],
                        }
                    ],
                }
            ],
        )
        doc_b = _module_doc(
            "pkg.b",
            body=[
                {
                    "kind": "ClassDef",
                    "name": "B",
                    "body": [
                        {
                            "kind": "FunctionDef",
                            "name": "run",
                            "arg_order": ["self", "x", "y"],
                            "arg_defaults": {
                                "y": {"kind": "Constant", "value": 2},
                            },
                            "body": [],
                        }
                    ],
                }
            ],
        )
        main_doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "func": {
                            "kind": "Attribute",
                            "value": {"kind": "Name", "id": "obj"},
                            "attr": "run",
                        },
                        "args": [{"kind": "Constant", "value": 3}],
                    },
                }
            ],
        )

        expand_cross_module_defaults([doc_a, doc_b, main_doc])

        body = main_doc["body"]
        assert isinstance(body, list)
        call = body[0]["value"]
        self.assertEqual(len(call["args"]), 1)

    def test_emitters_consume_canonical_str_method_builtin_calls(self) -> None:
        doc = _fixture_doc("test/fixture/east3-opt/strings/str_methods.east3")

        go_code = emit_go_module(doc)
        cpp_code = emit_cpp_module(doc)

        self.assertIn("a := py_str_strip(s)", go_code)
        self.assertIn('j := py_str_join(":", parts)', go_code)
        self.assertIn("str a = py_str_strip(s);", cpp_code)
        self.assertIn('str j = py_str_join(str(":"), parts);', cpp_code)

    def test_go_runtime_mapping_declares_container_dispatch_placeholders(self) -> None:
        mapping = load_runtime_mapping(ROOT / "src" / "runtime" / "go" / "mapping.json")

        self.assertEqual(mapping.calls.get("list_ctor"), "__LIST_CTOR__")
        self.assertEqual(mapping.calls.get("list.append"), "__LIST_APPEND__")
        self.assertEqual(mapping.calls.get("list.pop"), "__LIST_POP__")
        self.assertEqual(mapping.calls.get("list.clear"), "__LIST_CLEAR__")
        self.assertEqual(mapping.calls.get("dict.get"), "__DICT_GET__")
        self.assertEqual(mapping.calls.get("dict.items"), "__DICT_ITEMS__")
        self.assertEqual(mapping.calls.get("dict.keys"), "__DICT_KEYS__")
        self.assertEqual(mapping.calls.get("dict.values"), "__DICT_VALUES__")
        self.assertEqual(mapping.calls.get("set.add"), "__SET_ADD__")
        self.assertEqual(mapping.calls.get("sorted"), "py_sorted")

    def test_go_emitter_handles_plain_set_constructor_without_link_normalization(self) -> None:
        doc = _fixture_doc("test/fixture/east3-opt/collections/nested_types.east3")

        go_code = emit_go_module(doc)

        self.assertIn("map[string]struct{}{}", go_code)
        self.assertNotIn("set()", go_code)

    def test_cpp_emitter_handles_plain_bytes_constructor_without_link_normalization(self) -> None:
        doc = _fixture_doc("test/fixture/east3-opt/typing/bytes_basic.east3")

        cpp_code = emit_cpp_module(doc)

        self.assertIn("bytes{uint8(1), uint8(2), uint8(3), uint8(255)}", cpp_code)
        self.assertNotIn("bytes(", cpp_code)

    def test_cpp_emitter_includes_runtime_dependency_headers(self) -> None:
        doc = _fixture_doc("test/fixture/east3-opt/typing/bytes_basic.east3")

        cpp_code = emit_cpp_module(doc)

        self.assertIn('#include "core/py_runtime.h"', cpp_code)
        self.assertIn('#include "built_in/io_ops.h"', cpp_code)
        self.assertIn('#include "utils/assertions.h"', cpp_code)

    def test_cpp_emitter_uses_mapping_for_runtime_container_helpers(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "Assign",
                    "target": {"kind": "Name", "id": "xs", "resolved_type": "list[int64]"},
                    "declare": True,
                    "decl_type": "list[int64]",
                    "declare_init": True,
                    "value": {"kind": "List", "resolved_type": "list[int64]", "elements": []},
                },
                {
                    "kind": "Assign",
                    "target": {"kind": "Name", "id": "d", "resolved_type": "dict[str,int64]"},
                    "declare": True,
                    "decl_type": "dict[str,int64]",
                    "declare_init": True,
                    "value": {"kind": "Dict", "resolved_type": "dict[str,int64]", "entries": []},
                },
                {
                    "kind": "Assign",
                    "target": {"kind": "Name", "id": "s", "resolved_type": "set[str]"},
                    "declare": True,
                    "decl_type": "set[str]",
                    "declare_init": True,
                    "value": {"kind": "Set", "resolved_type": "set[str]", "elements": []},
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "runtime_call": "list.append",
                        "builtin_name": "append",
                        "func": {
                            "kind": "Attribute",
                            "value": {"kind": "Name", "id": "xs", "resolved_type": "list[int64]"},
                            "attr": "append",
                        },
                        "args": [{"kind": "Constant", "value": 1, "resolved_type": "int64"}],
                    },
                },
                {
                    "kind": "Assign",
                    "target": {"kind": "Name", "id": "item", "resolved_type": "int64"},
                    "declare": True,
                    "decl_type": "int64",
                    "declare_init": True,
                    "value": {
                        "kind": "Call",
                        "lowered_kind": "BuiltinCall",
                        "runtime_call": "dict.get",
                        "builtin_name": "get",
                        "resolved_type": "int64",
                        "func": {
                            "kind": "Attribute",
                            "value": {"kind": "Name", "id": "d", "resolved_type": "dict[str,int64]"},
                            "attr": "get",
                        },
                        "args": [
                            {"kind": "Constant", "value": "x", "resolved_type": "str"},
                            {"kind": "Constant", "value": 0, "resolved_type": "int64"},
                        ],
                    },
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "lowered_kind": "BuiltinCall",
                        "runtime_call": "set.add",
                        "builtin_name": "add",
                        "func": {
                            "kind": "Attribute",
                            "value": {"kind": "Name", "id": "s", "resolved_type": "set[str]"},
                            "attr": "add",
                        },
                        "args": [{"kind": "Constant", "value": "x", "resolved_type": "str"}],
                    },
                },
            ],
        )

        cpp_code = emit_cpp_module(doc)

        self.assertIn("py_list_append_mut(xs, int64(1));", cpp_code)
        self.assertIn('int64 item = py_dict_get(d, str("x"), int64(0));', cpp_code)
        self.assertIn('py_set_add_mut(s, str("x"));', cpp_code)
        self.assertNotIn("push_back(", cpp_code)

    def test_cpp_emitter_uses_mapping_for_string_numeric_cast_helpers(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "Assign",
                    "target": {"kind": "Name", "id": "i", "resolved_type": "int64"},
                    "declare": True,
                    "decl_type": "int64",
                    "declare_init": True,
                    "value": {
                        "kind": "Call",
                        "lowered_kind": "BuiltinCall",
                        "runtime_call": "py_int_from_str",
                        "builtin_name": "int",
                        "resolved_type": "int64",
                        "func": {"kind": "Name", "id": "int"},
                        "args": [{"kind": "Constant", "value": "12", "resolved_type": "str"}],
                    },
                },
                {
                    "kind": "Assign",
                    "target": {"kind": "Name", "id": "f", "resolved_type": "float64"},
                    "declare": True,
                    "decl_type": "float64",
                    "declare_init": True,
                    "value": {
                        "kind": "Call",
                        "lowered_kind": "BuiltinCall",
                        "runtime_call": "py_float_from_str",
                        "builtin_name": "float",
                        "resolved_type": "float64",
                        "func": {"kind": "Name", "id": "float"},
                        "args": [{"kind": "Constant", "value": "1.5", "resolved_type": "str"}],
                    },
                },
            ],
        )

        cpp_code = emit_cpp_module(doc)

        self.assertIn('std::stoll(str("12"))', cpp_code)
        self.assertIn('std::stod(str("1.5"))', cpp_code)
        self.assertNotIn("py_int_from_str(", cpp_code)
        self.assertNotIn("py_float_from_str(", cpp_code)

    def test_cpp_emitter_emits_main_only_for_entry_modules(self) -> None:
        doc = _module_doc(
            "lib.worker",
            meta_extra={
                "emit_context": {
                    "module_id": "lib.worker",
                    "is_entry": False,
                }
            },
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "run",
                    "arg_types": {},
                    "arg_order": [],
                    "arg_defaults": {},
                    "arg_usage": {},
                    "return_type": "None",
                    "body": [{"kind": "Pass"}],
                }
            ],
        )
        doc["main_guard_body"] = [
            {
                "kind": "Expr",
                "value": {
                    "kind": "Call",
                    "lowered_kind": "BuiltinCall",
                    "runtime_call": "py_print",
                    "builtin_name": "print",
                    "args": [{"kind": "Constant", "value": "boot", "resolved_type": "str"}],
                },
            }
        ]

        cpp_code = emit_cpp_module(doc)

        self.assertNotIn("__pytra_main_guard", cpp_code)
        self.assertNotIn("int main()", cpp_code)

    def test_cpp_emitter_entry_module_keeps_main_guard(self) -> None:
        doc = _module_doc(
            "app.main",
            meta_extra={
                "emit_context": {
                    "module_id": "app.main",
                    "is_entry": True,
                }
            },
            body=[],
        )
        doc["main_guard_body"] = [
            {
                "kind": "Expr",
                "value": {
                    "kind": "Call",
                    "lowered_kind": "BuiltinCall",
                    "runtime_call": "py_print",
                    "builtin_name": "print",
                    "args": [{"kind": "Constant", "value": "boot", "resolved_type": "str"}],
                },
            }
        ]

        cpp_code = emit_cpp_module(doc)

        self.assertIn("void __pytra_main_guard()", cpp_code)
        self.assertIn("int main()", cpp_code)
        self.assertIn("__pytra_main_guard();", cpp_code)

    def test_cpp_emitter_rewrites_runtime_module_alias_calls_to_direct_symbols(self) -> None:
        doc = _module_doc(
            "app.main",
            meta_extra={
                "import_modules": {"json": "pytra.std.json"},
                "linked_program_v1": {"module_id": "app.main", "resolved_dependencies_v1": ["pytra.std.json"]},
            },
            body=[
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "func": {
                            "kind": "Attribute",
                            "value": {"kind": "Name", "id": "json"},
                            "attr": "loads",
                        },
                        "args": [{"kind": "Name", "id": "text"}],
                    },
                }
            ],
        )

        cpp_code = emit_cpp_module(doc)

        self.assertIn('loads(text);', cpp_code)
        self.assertNotIn('json.loads(text);', cpp_code)

    def test_cpp_emitter_rewrites_skipped_runtime_module_alias_calls_without_pytra_hardcode(self) -> None:
        doc = _module_doc(
            "app.main",
            meta_extra={
                "import_modules": {"custom": "runtime.custom"},
                "linked_program_v1": {"module_id": "app.main", "resolved_dependencies_v1": ["runtime.custom"]},
            },
            body=[
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "func": {
                            "kind": "Attribute",
                            "value": {"kind": "Name", "id": "custom", "resolved_type": "module"},
                            "attr": "helper",
                            "runtime_module_id": "runtime.custom",
                            "runtime_symbol": "helper",
                        },
                        "args": [],
                    },
                }
            ],
        )

        mapping = RuntimeMapping(
            builtin_prefix="rt_",
            calls={},
            skip_module_prefixes=["runtime."],
        )
        with patch("toolchain2.emit.cpp.emitter.load_runtime_mapping", return_value=mapping):
            cpp_code = emit_cpp_module(doc)

        self.assertIn("rt_helper();", cpp_code)
        self.assertNotIn("custom.helper();", cpp_code)

    def test_cpp_emitter_applies_save_gif_keyword_defaults_adapter(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "func": {"kind": "Name", "id": "save_gif"},
                        "args": [
                            {"kind": "Name", "id": "out_path", "resolved_type": "str"},
                            {"kind": "Name", "id": "width", "resolved_type": "int64"},
                            {"kind": "Name", "id": "height", "resolved_type": "int64"},
                            {"kind": "Name", "id": "frames", "resolved_type": "list[bytes]"},
                            {"kind": "Call", "func": {"kind": "Name", "id": "grayscale_palette"}, "args": [], "keywords": [], "resolved_type": "bytes"},
                        ],
                        "keywords": [
                            {"arg": "delay_cs", "value": {"kind": "Constant", "value": 5, "resolved_type": "int64"}},
                            {"arg": "loop", "value": {"kind": "Constant", "value": 0, "resolved_type": "int64"}},
                        ],
                        "runtime_call_adapter_kind": "image.save_gif.keyword_defaults",
                    },
                }
            ],
        )

        cpp_code = emit_cpp_module(doc)

        self.assertIn("save_gif(out_path, width, height, frames, grayscale_palette(), int64(5), int64(0));", cpp_code)

    def test_runtime_bundle_emits_header_only_for_native_companion_modules(self) -> None:
        doc = _fixture_doc("src/runtime/east/built_in/io_ops.east")
        if "meta" not in doc:
            doc["meta"] = {}
        doc["meta"]["linked_program_v1"] = {
            "module_id": "pytra.built_in.io_ops",
            "resolved_dependencies_v1": ["pytra.core.py_runtime"],
        }

        with tempfile.TemporaryDirectory() as tmp:
            header_path, source_path = emit_runtime_module_artifacts(
                "pytra.built_in.io_ops",
                doc,
                output_dir=Path(tmp),
                source_path=str(ROOT / "src" / "pytra" / "built_in" / "io_ops.py"),
            )

            self.assertTrue(Path(header_path).exists())
            self.assertEqual(source_path, "")
            header_text = Path(header_path).read_text(encoding="utf-8")
            self.assertIn('#include "runtime/cpp/built_in/io_ops.h"', header_text)

    def test_cpp_runtime_bundle_pathlib_filters_host_only_includes_and_reuses_header(self) -> None:
        doc = _fixture_doc("src/runtime/east/std/pathlib.east")
        meta = doc.setdefault("meta", {})
        assert isinstance(meta, dict)
        meta["linked_program_v1"] = {"module_id": "pytra.std.pathlib"}

        with tempfile.TemporaryDirectory() as tmp:
            header_path, source_path = emit_runtime_module_artifacts(
                "pytra.std.pathlib",
                doc,
                output_dir=Path(tmp),
                source_path=str(ROOT / "src" / "pytra" / "std" / "pathlib.py"),
            )

            self.assertNotEqual(source_path, "")
            header_text = Path(header_path).read_text(encoding="utf-8")
            source_text = Path(source_path).read_text(encoding="utf-8")

        self.assertNotIn('pytra/typing.h', header_text)
        self.assertNotIn('pytra/typing.h', source_text)
        self.assertNotIn('os/path.h', header_text)
        self.assertNotIn('#include "glob.h"', header_text)
        self.assertIn("Path joinpath(const list<object>& parts) const;", header_text)
        self.assertNotIn("struct Path {", source_text)
        self.assertIn('#include "std/os_path.h"', source_text)
        self.assertIn('#include "std/glob.h"', source_text)
        self.assertIn("splitext(", source_text)
        self.assertIn("py_str_slice(", source_text)
        self.assertNotIn("py_str(", source_text)

    def test_cpp_runtime_paths_skip_host_only_template_imports(self) -> None:
        dep_ids = collect_cpp_dependency_module_ids(
            "pytra.built_in.numeric_ops",
            {
                "import_bindings": [
                    {
                        "module_id": "pytra.std",
                        "runtime_module_id": "pytra.std.template",
                        "runtime_group": "std",
                        "resolved_binding_kind": "module",
                        "host_only": True,
                    },
                    {
                        "module_id": "pytra.core.py_runtime",
                    },
                ]
            },
        )

        self.assertEqual(dep_ids, ["pytra.core.py_runtime"])

    def test_cpp_runtime_paths_skip_std_template_runtime_module_binding(self) -> None:
        dep_ids = collect_cpp_dependency_module_ids(
            "pytra.built_in.numeric_ops",
            {
                "import_resolution": {
                    "bindings": [
                        {
                            "module_id": "pytra.std",
                            "runtime_module_id": "pytra.std.template",
                            "runtime_group": "std",
                            "resolved_binding_kind": "module",
                        },
                        {
                            "module_id": "pytra.core.py_runtime",
                            "runtime_module_id": "pytra.core.py_runtime",
                            "runtime_group": "core",
                        },
                    ]
                }
            },
        )

        self.assertEqual(dep_ids, ["pytra.core.py_runtime"])

    def test_runtime_discovery_exposes_shared_runtime_rel_tail(self) -> None:
        self.assertEqual(resolve_runtime_module_rel_tail("pytra.std.json"), "std/json")
        self.assertEqual(resolve_runtime_module_rel_tail("pytra.built_in.numeric_ops"), "built_in/numeric_ops")
        self.assertEqual(resolve_runtime_module_rel_tail("pytra.utils.png"), "utils/png")
        self.assertEqual(resolve_runtime_module_rel_tail("pytra.core.py_runtime"), "core/py_runtime")
        self.assertEqual(resolve_runtime_module_rel_tail("app.main"), "")
        self.assertTrue(is_runtime_namespace_module("pytra.std"))
        self.assertTrue(is_runtime_namespace_module("pytra.core"))
        self.assertFalse(is_runtime_namespace_module("pytra.std.json"))

    def test_cpp_runtime_paths_delegate_rel_tail_to_shared_runtime_loader(self) -> None:
        self.assertEqual(runtime_rel_tail_for_module("pytra.std.json"), "std/json")
        self.assertEqual(runtime_rel_tail_for_module("pytra.core.py_runtime"), "core/py_runtime")
        self.assertEqual(cpp_include_for_module("pytra.core.py_runtime"), "core/py_runtime.h")
        self.assertEqual(cpp_include_for_module("pytra.std"), "")
        self.assertTrue(is_runtime_internal_helper_module("pytra.core.list"))
        self.assertFalse(is_runtime_internal_helper_module("pytra.core.py_runtime"))
        self.assertTrue(is_type_only_dependency_module_id("pytra.typing"))
        self.assertTrue(is_type_only_dependency_module_id("pytra.std.template"))

    def test_cpp_runtime_paths_skip_pytra_types_type_only_imports(self) -> None:
        dep_ids = collect_cpp_dependency_module_ids(
            "pytra.std.json",
            {
                "import_bindings": [
                    {
                        "module_id": "pytra.types",
                        "runtime_module_id": "pytra.types",
                        "binding_kind": "symbol",
                        "local_name": "int64",
                    },
                    {
                        "module_id": "pytra.built_in.contains",
                        "runtime_module_id": "pytra.built_in.contains",
                        "runtime_group": "built_in",
                    },
                ]
            },
        )

        self.assertEqual(dep_ids, ["pytra.built_in.contains"])

    def test_cpp_runtime_bundle_keeps_template_runtime_helpers_header_only(self) -> None:
        doc = _fixture_doc("src/runtime/east/built_in/numeric_ops.east")
        meta = doc.setdefault("meta", {})
        assert isinstance(meta, dict)
        meta["linked_program_v1"] = {"module_id": "pytra.built_in.numeric_ops"}

        with tempfile.TemporaryDirectory() as tmp:
            header_path, source_path = emit_runtime_module_artifacts(
                "pytra.built_in.numeric_ops",
                doc,
                output_dir=Path(tmp),
                source_path=str(ROOT / "src" / "pytra" / "built_in" / "numeric_ops.py"),
            )

            header_text = Path(header_path).read_text(encoding="utf-8")

        self.assertEqual(source_path, "")
        self.assertIn("template <class T>", header_text)
        self.assertIn("T py_max(const T& a, const T& b) {", header_text)

    def test_cpp_runtime_bundle_keeps_extern_decls_for_native_companion_headers(self) -> None:
        doc = _fixture_doc("src/runtime/east/std/os_path.east")
        meta = doc.setdefault("meta", {})
        assert isinstance(meta, dict)
        meta["linked_program_v1"] = {"module_id": "pytra.std.os_path"}

        with tempfile.TemporaryDirectory() as tmp:
            header_path, source_path = emit_runtime_module_artifacts(
                "pytra.std.os_path",
                doc,
                output_dir=Path(tmp),
                source_path=str(ROOT / "src" / "pytra" / "std" / "os_path.py"),
            )

            header_text = Path(header_path).read_text(encoding="utf-8")

        self.assertEqual(source_path, "")
        self.assertIn("str join(const str& a, const str& b);", header_text)
        self.assertIn("str dirname(const str& p);", header_text)
        self.assertIn("bool exists(const str& p);", header_text)

    def test_runtime_pathlib_lane_uses_string_ops_for_string_methods(self) -> None:
        doc = _fixture_doc("src/runtime/east/std/pathlib.east")
        method_calls: list[dict[str, object]] = []
        for node in _walk_nodes(doc):
            if node.get("kind") != "Call":
                continue
            func = node.get("func")
            if not isinstance(func, dict) or func.get("kind") != "Attribute":
                continue
            if func.get("attr") not in ("startswith", "endswith"):
                continue
            method_calls.append(node)

        self.assertEqual(len(method_calls), 2)
        for node in method_calls:
            self.assertEqual(node.get("runtime_module_id"), "pytra.built_in.string_ops")
            self.assertIn(node.get("runtime_call"), ("str.startswith", "str.endswith", "py_startswith", "py_endswith"))

    def test_cpp_emitter_uses_mutable_ref_for_reassigned_bytearray_param(self) -> None:
        doc = _module_doc(
            "pytra.utils.png",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "_png_append",
                    "arg_types": {"dst": "bytearray", "src": "bytearray"},
                    "arg_order": ["dst", "src"],
                    "arg_defaults": {},
                    "arg_usage": {"dst": "reassigned", "src": "readonly"},
                    "return_type": "None",
                    "body": [{"kind": "Pass"}],
                }
            ],
        )

        cpp_code = emit_cpp_module(doc, allow_runtime_module=True)

        self.assertIn("void _png_append(bytearray& dst, const bytearray& src)", cpp_code)

    def test_cpp_runtime_helpers_emit_template_prefix_for_generic_function_types(self) -> None:
        doc = _module_doc(
            "pytra.built_in.numeric_ops",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "py_max",
                    "arg_types": {"a": "T", "b": "T"},
                    "arg_order": ["a", "b"],
                    "arg_defaults": {},
                    "return_type": "T",
                    "body": [{"kind": "Return", "value": {"kind": "Name", "id": "a", "resolved_type": "T"}}],
                }
            ],
        )

        cpp_code = emit_cpp_module(doc, allow_runtime_module=True)

        self.assertIn("template <class T>\nT py_max(const T& a, const T& b)", cpp_code)

    def test_cpp_emitter_drops_const_when_self_arg_usage_is_reassigned(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "ClassDef",
                    "name": "Parser",
                    "body": [
                        {
                            "kind": "FunctionDef",
                            "name": "add_expr",
                            "arg_types": {"self": "Parser", "node": "int64"},
                            "arg_order": ["self", "node"],
                            "arg_defaults": {},
                            "arg_usage": {"self": "reassigned", "node": "readonly"},
                            "return_type": "int64",
                            "body": [{"kind": "Return", "value": {"kind": "Constant", "value": 0, "resolved_type": "int64"}}],
                        }
                    ],
                }
            ],
        )

        cpp_code = emit_cpp_module(doc)

        self.assertIn("int64 add_expr(int64 node);", cpp_code)
        self.assertIn("int64 Parser::add_expr(int64 node) {", cpp_code)
        self.assertNotIn("add_expr(int64 node) const", cpp_code)

    def test_cpp_emitter_types_int64_literals_for_generic_runtime_calls(self) -> None:
        doc = _module_doc(
            "app.main",
            meta_extra={
                "import_bindings": [
                    {
                        "module_id": "pytra.built_in.numeric_ops",
                        "local_name": "py_max",
                        "binding_kind": "symbol",
                        "runtime_module_id": "pytra.built_in.numeric_ops",
                        "runtime_symbol": "py_max",
                    }
                ]
            },
            body=[
                {
                    "kind": "Assign",
                    "target": {"kind": "Name", "id": "v", "resolved_type": "int64"},
                    "declare": True,
                    "decl_type": "int64",
                    "declare_init": True,
                    "value": {"kind": "Constant", "value": 1, "resolved_type": "int64"},
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "func": {"kind": "Name", "id": "py_max"},
                        "args": [
                            {"kind": "Constant", "value": 0, "resolved_type": "int64"},
                            {"kind": "Name", "id": "v", "resolved_type": "int64"},
                        ],
                    },
                },
            ],
        )

        cpp_code = emit_cpp_module(doc)

        self.assertIn("py_max(int64(0), v);", cpp_code)

    def test_cpp_emitter_uses_fresh_discard_names_for_range_targets(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "ForCore",
                    "iter_plan": {
                        "kind": "StaticRangeForPlan",
                        "start": {"kind": "Constant", "value": 0, "resolved_type": "int64"},
                        "stop": {"kind": "Constant", "value": 2, "resolved_type": "int64"},
                        "step": {"kind": "Constant", "value": 1, "resolved_type": "int64"},
                    },
                    "target_plan": {"id": "_", "target_type": "int64", "unused": True},
                    "body": [{"kind": "Pass"}],
                },
                {
                    "kind": "ForCore",
                    "iter_plan": {
                        "kind": "StaticRangeForPlan",
                        "start": {"kind": "Constant", "value": 0, "resolved_type": "int64"},
                        "stop": {"kind": "Constant", "value": 3, "resolved_type": "int64"},
                        "step": {"kind": "Constant", "value": 1, "resolved_type": "int64"},
                    },
                    "target_plan": {"id": "_", "target_type": "int64", "unused": True},
                    "body": [{"kind": "Pass"}],
                },
            ],
        )

        cpp_code = emit_cpp_module(doc)

        self.assertIn("for (int64 __discard_1 = 0; __discard_1 < 2; __discard_1 += 1)", cpp_code)
        self.assertIn("for (int64 __discard_2 = 0; __discard_2 < 3; __discard_2 += 1)", cpp_code)
        self.assertNotIn("for (_ = 0;", cpp_code)

    def test_cpp_emitter_uses_list_truthiness_and_mutating_pop_helper(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "Assign",
                    "target": {"kind": "Name", "id": "stack", "resolved_type": "list[int64]"},
                    "declare": True,
                    "decl_type": "list[int64]",
                    "declare_init": True,
                    "value": {
                        "kind": "List",
                        "resolved_type": "list[int64]",
                        "elements": [{"kind": "Constant", "value": 1, "resolved_type": "int64"}],
                    },
                },
                {
                    "kind": "While",
                    "test": {"kind": "Name", "id": "stack", "resolved_type": "list[int64]"},
                    "body": [
                        {
                            "kind": "Expr",
                            "value": {
                                "kind": "Call",
                                "lowered_kind": "BuiltinCall",
                                "runtime_call": "list.pop",
                                "builtin_name": "pop",
                                "func": {
                                    "kind": "Attribute",
                                    "value": {"kind": "Name", "id": "stack", "resolved_type": "list[int64]"},
                                    "attr": "pop",
                                },
                                "args": [],
                            },
                        }
                    ],
                    "orelse": [],
                },
            ],
        )

        cpp_code = emit_cpp_module(doc)

        self.assertIn("Object<list<int64>> stack = rc_list_from_value(list<int64>{int64(1)});", cpp_code)
        self.assertIn("while (py_to_bool(stack)) {", cpp_code)
        self.assertIn("py_list_pop_mut(stack);", cpp_code)

    def test_cpp_emitter_defaults_container_locals_to_ref_wrappers(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "build",
                    "arg_types": {},
                    "arg_order": [],
                    "arg_defaults": {},
                    "arg_usage": {},
                    "return_type": "None",
                    "body": [
                        {"kind": "VarDecl", "name": "xs", "type": "list[int64]"},
                        {"kind": "VarDecl", "name": "env", "type": "dict[str,int64]"},
                        {"kind": "VarDecl", "name": "seen", "type": "set[int64]"},
                    ],
                }
            ],
        )

        cpp_code = emit_cpp_module(doc)

        self.assertIn("Object<list<int64>> xs = rc_list_new<int64>();", cpp_code)
        self.assertIn("Object<dict<str, int64>> env = rc_dict_new<str, int64>();", cpp_code)
        self.assertIn("Object<set<int64>> seen = rc_set_new<int64>();", cpp_code)

    def test_cpp_emitter_allows_hinted_container_value_locals(self) -> None:
        doc = _module_doc(
            "app.main",
            meta_extra={
                "linked_program_v1": {
                    "container_ownership_hints_v1": {
                        "container_value_locals_v1": {
                            "app.main::build": {
                                "version": "1",
                                "locals": ["xs"],
                            }
                        }
                    }
                }
            },
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "build",
                    "arg_types": {},
                    "arg_order": [],
                    "arg_defaults": {},
                    "arg_usage": {},
                    "return_type": "None",
                    "body": [
                        {"kind": "VarDecl", "name": "xs", "type": "list[int64]"},
                        {"kind": "VarDecl", "name": "env", "type": "dict[str,int64]"},
                    ],
                }
            ],
        )

        cpp_code = emit_cpp_module(doc)

        self.assertIn("list<int64> xs = list<int64>{};", cpp_code)
        self.assertIn("Object<dict<str, int64>> env = rc_dict_new<str, int64>();", cpp_code)

    def test_go_emitter_defaults_to_ref_container_locals(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "build",
                    "arg_types": {},
                    "arg_order": [],
                    "arg_defaults": {},
                    "arg_usage": {},
                    "return_type": "None",
                    "body": [
                        {"kind": "VarDecl", "name": "xs", "type": "list[int64]"},
                        {"kind": "VarDecl", "name": "env", "type": "dict[str,int64]"},
                        {"kind": "VarDecl", "name": "seen", "type": "set[int64]"},
                    ],
                }
            ],
        )

        go_code = emit_go_module(doc)

        self.assertIn("var xs *PyList[int64] = NewPyList[int64]()", go_code)
        self.assertIn("var env *PyDict[string, int64] = NewPyDict[string, int64]()", go_code)
        self.assertIn("var seen *PySet[int64] = NewPySet[int64]()", go_code)

    def test_go_emitter_allows_hinted_container_value_locals(self) -> None:
        doc = _module_doc(
            "app.main",
            meta_extra={
                "linked_program_v1": {
                    "container_ownership_hints_v1": {
                        "container_value_locals_v1": {
                            "app.main::build": {
                                "version": "1",
                                "locals": ["xs"],
                            }
                        }
                    }
                }
            },
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "build",
                    "arg_types": {},
                    "arg_order": [],
                    "arg_defaults": {},
                    "arg_usage": {},
                    "return_type": "None",
                    "body": [
                        {"kind": "VarDecl", "name": "xs", "type": "list[int64]"},
                        {"kind": "VarDecl", "name": "env", "type": "dict[str,int64]"},
                    ],
                }
            ],
        )

        go_code = emit_go_module(doc)

        self.assertIn("var xs []int64 = nil", go_code)
        self.assertIn("var env *PyDict[string, int64] = NewPyDict[string, int64]()", go_code)

    def test_cpp_emitter_wraps_container_builtin_results_as_ref_handles(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "run_case",
                    "arg_types": {},
                    "arg_order": [],
                    "arg_defaults": {},
                    "arg_usage": {},
                    "return_type": "None",
                    "body": [
                        {
                            "kind": "Assign",
                            "target": {"kind": "Name", "id": "d", "resolved_type": "dict[str,int64]"},
                            "declare": True,
                            "decl_type": "dict[str,int64]",
                            "declare_init": True,
                            "value": {"kind": "Dict", "resolved_type": "dict[str,int64]", "entries": []},
                        },
                        {
                            "kind": "Assign",
                            "target": {"kind": "Name", "id": "ks", "resolved_type": "list[str]"},
                            "declare": True,
                            "decl_type": "list[str]",
                            "declare_init": True,
                            "value": {
                                "kind": "Call",
                                "lowered_kind": "BuiltinCall",
                                "runtime_call": "dict.keys",
                                "builtin_name": "keys",
                                "resolved_type": "list[str]",
                                "func": {
                                    "kind": "Attribute",
                                    "value": {"kind": "Name", "id": "d", "resolved_type": "dict[str,int64]"},
                                    "attr": "keys",
                                },
                                "args": [],
                            },
                        },
                    ],
                }
            ],
        )

        cpp_code = emit_cpp_module(doc)

        self.assertIn("Object<list<str>> ks = rc_list_from_value(py_dict_keys(d));", cpp_code)

    def test_go_emitter_wraps_container_builtin_results_as_ref_handles(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "run_case",
                    "arg_types": {},
                    "arg_order": [],
                    "arg_defaults": {},
                    "arg_usage": {},
                    "return_type": "None",
                    "body": [
                        {
                            "kind": "Assign",
                            "target": {"kind": "Name", "id": "d", "resolved_type": "dict[str,int64]"},
                            "declare": True,
                            "decl_type": "dict[str,int64]",
                            "declare_init": True,
                            "value": {"kind": "Dict", "resolved_type": "dict[str,int64]", "entries": []},
                        },
                        {
                            "kind": "Assign",
                            "target": {"kind": "Name", "id": "ks", "resolved_type": "list[str]"},
                            "declare": True,
                            "decl_type": "list[str]",
                            "declare_init": True,
                            "value": {
                                "kind": "Call",
                                "lowered_kind": "BuiltinCall",
                                "runtime_call": "dict.keys",
                                "builtin_name": "keys",
                                "resolved_type": "list[str]",
                                "func": {
                                    "kind": "Attribute",
                                    "value": {"kind": "Name", "id": "d", "resolved_type": "dict[str,int64]"},
                                    "attr": "keys",
                                },
                                "args": [],
                            },
                        },
                    ],
                }
            ],
        )

        go_code = emit_go_module(doc)

        self.assertIn("var d *PyDict[string, int64] = NewPyDict[string, int64]()", go_code)
        self.assertIn("var ks *PyList[string] = PyListFromSlice[string](", go_code)

    def test_cpp_emitter_supports_set_literals_as_ref_wrappers(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "Assign",
                    "target": {"kind": "Name", "id": "seen", "resolved_type": "set[int64]"},
                    "declare": True,
                    "decl_type": "set[int64]",
                    "declare_init": True,
                    "value": {
                        "kind": "Set",
                        "resolved_type": "set[int64]",
                        "elements": [
                            {"kind": "Constant", "value": 1, "resolved_type": "int64"},
                            {"kind": "Constant", "value": 2, "resolved_type": "int64"},
                        ],
                    },
                }
            ],
        )

        cpp_code = emit_cpp_module(doc)

        self.assertIn("Object<set<int64>> seen = rc_set_from_value(set<int64>{int64(1), int64(2)});", cpp_code)

    def test_cpp_emitter_uses_py_at_for_dict_reads_but_keeps_subscript_store_targets(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "read_env",
                    "arg_types": {"env": "dict[str,int64]", "name": "str"},
                    "arg_order": ["env", "name"],
                    "arg_defaults": {},
                    "arg_usage": {"env": "readonly", "name": "readonly"},
                    "return_type": "int64",
                    "body": [
                        {
                            "kind": "Return",
                            "value": {
                                "kind": "Subscript",
                                "value": {"kind": "Name", "id": "env", "resolved_type": "dict[str,int64]"},
                                "slice": {"kind": "Name", "id": "name", "resolved_type": "str"},
                                "resolved_type": "int64",
                            },
                        }
                    ],
                },
                {
                    "kind": "FunctionDef",
                    "name": "write_env",
                    "arg_types": {"env": "dict[str,int64]"},
                    "arg_order": ["env"],
                    "arg_defaults": {},
                    "arg_usage": {"env": "reassigned"},
                    "return_type": "None",
                    "body": [
                        {
                            "kind": "Assign",
                            "target": {
                                "kind": "Subscript",
                                "value": {"kind": "Name", "id": "env", "resolved_type": "dict[str,int64]"},
                                "slice": {"kind": "Constant", "value": "x", "resolved_type": "str"},
                                "resolved_type": "int64",
                            },
                            "value": {"kind": "Constant", "value": 1, "resolved_type": "int64"},
                        }
                    ],
                },
            ],
        )

        cpp_code = emit_cpp_module(doc)

        self.assertIn("return py_at(env, name);", cpp_code)
        self.assertIn('(*(env))[str("x")] = int64(1);', cpp_code)

    def test_cpp_emitter_rewrites_negative_unary_list_index_from_size(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "tail",
                    "arg_types": {"stack": "list[int64]"},
                    "arg_order": ["stack"],
                    "arg_defaults": {},
                    "arg_usage": {"stack": "readonly"},
                    "return_type": "int64",
                    "body": [
                        {
                            "kind": "Return",
                            "value": {
                                "kind": "Subscript",
                                "value": {"kind": "Name", "id": "stack", "resolved_type": "list[int64]"},
                                "slice": {
                                    "kind": "UnaryOp",
                                    "op": "USub",
                                    "operand": {"kind": "Constant", "value": 1, "resolved_type": "int64"},
                                    "resolved_type": "int64",
                                },
                                "resolved_type": "int64",
                            },
                        }
                    ],
                }
            ],
        )

        cpp_code = emit_cpp_module(doc)

        self.assertIn("return py_list_at_ref(stack, (py_len(stack) - int64(1)));", cpp_code)

    def test_emitters_treat_runtime_call_int_as_cast_without_link_normalization(self) -> None:
        doc = _fixture_doc("test/fixture/east3-opt/typing/intenum_basic.east3")

        go_code = emit_go_module(doc)
        cpp_code = emit_cpp_module(doc)

        self.assertIn("int64(Status_ERROR)", go_code)
        self.assertNotIn("py_int(Status_ERROR)", go_code)
        self.assertIn("static_cast<int64>(Status::ERROR)", cpp_code)
        self.assertNotIn("py_int(Status::ERROR)", cpp_code)

    def test_cpp_emitter_skips_binop_casts_for_implicit_promotions(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "BinOp",
                        "op": "Add",
                        "resolved_type": "int64",
                        "left": {"kind": "Name", "id": "a", "resolved_type": "int64"},
                        "right": {"kind": "Constant", "value": 1, "resolved_type": "int64"},
                        "casts": [
                            {"on": "left", "from": "int8", "to": "int64", "reason": "numeric_promotion"}
                        ],
                    },
                }
            ],
            meta_extra={"emit_context": {"module_id": "app.main", "is_entry": False}},
        )

        cpp_code = emit_cpp_module(doc)

        self.assertIn("(a + int64(1));", cpp_code)
        self.assertNotIn("static_cast<int64_t>(a)", cpp_code)

    def test_cpp_emitter_keeps_binop_casts_outside_implicit_promotions(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "BinOp",
                        "op": "Add",
                        "resolved_type": "uint8",
                        "left": {"kind": "Name", "id": "a", "resolved_type": "uint8"},
                        "right": {"kind": "Constant", "value": 1, "resolved_type": "uint8"},
                        "casts": [
                            {"on": "left", "from": "int64", "to": "uint8", "reason": "narrowing"}
                        ],
                    },
                }
            ],
            meta_extra={"emit_context": {"module_id": "app.main", "is_entry": False}},
        )

        cpp_code = emit_cpp_module(doc)

        self.assertIn("static_cast<uint8>(a)", cpp_code)

    def test_go_emitter_runtime_symbol_prefix_uses_skip_modules_without_pytra_hardcode(self) -> None:
        doc = _module_doc(
            "app.main",
            meta_extra={
                "import_bindings": [
                    {
                        "module_id": "runtime.custom",
                        "local_name": "helper",
                        "binding_kind": "symbol",
                    }
                ]
            },
            body=[
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "func": {"kind": "Name", "id": "helper"},
                        "args": [],
                    },
                }
            ],
        )

        mapping = RuntimeMapping(
            builtin_prefix="rt_",
            calls={},
            skip_module_prefixes=["runtime."],
        )
        with patch("toolchain2.emit.go.emitter.load_runtime_mapping", return_value=mapping):
            go_code = emit_go_module(doc)

        self.assertIn("rt_helper()", go_code)

    def test_go_emitter_uses_runtime_metadata_for_skipped_module_values(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "run",
                    "arg_types": {},
                    "arg_order": [],
                    "arg_defaults": {},
                    "arg_index": {},
                    "return_type": "float64",
                    "arg_usage": {},
                    "renamed_symbols": {},
                    "docstring": None,
                    "body": [
                        {
                            "kind": "Return",
                            "value": {
                                "kind": "Call",
                                "resolved_type": "float64",
                                "func": {
                                    "kind": "Attribute",
                                    "resolved_type": "callable",
                                    "value": {
                                        "kind": "Name",
                                        "id": "math",
                                        "resolved_type": "module",
                                    },
                                    "attr": "sin",
                                },
                                "args": [
                                    {
                                        "kind": "Attribute",
                                        "resolved_type": "float64",
                                        "value": {
                                            "kind": "Name",
                                            "id": "math",
                                            "resolved_type": "module",
                                        },
                                        "attr": "pi",
                                        "runtime_module_id": "pytra.std.math",
                                        "runtime_symbol": "pi",
                                        "runtime_symbol_dispatch": "value",
                                    }
                                ],
                                "keywords": [],
                                "resolved_runtime_call": "math.sin",
                                "runtime_module_id": "pytra.std.math",
                                "runtime_symbol": "sin",
                            },
                        }
                    ],
                }
            ],
        )

        go_code = emit_go_module(doc)

        self.assertIn("return py_sin(py_pi)", go_code)
        self.assertNotIn("math.Pi", go_code)

    def test_cpp_emitter_maps_math_module_calls_to_std_symbols(self) -> None:
        doc = _module_doc(
            "app.main",
            meta_extra={
                "import_modules": {
                    "math": "pytra.std.math",
                }
            },
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "run",
                    "arg_types": {},
                    "arg_order": [],
                    "arg_defaults": {},
                    "arg_index": {},
                    "return_type": "float64",
                    "arg_usage": {},
                    "renamed_symbols": {},
                    "docstring": None,
                    "body": [
                        {
                            "kind": "Return",
                            "value": {
                                "kind": "Call",
                                "resolved_type": "float64",
                                "func": {
                                    "kind": "Attribute",
                                    "resolved_type": "callable",
                                    "value": {
                                        "kind": "Name",
                                        "id": "math",
                                        "resolved_type": "module",
                                    },
                                    "attr": "sin",
                                    "runtime_module_id": "pytra.std.math",
                                    "runtime_symbol": "sin",
                                },
                                "args": [
                                    {
                                        "kind": "Attribute",
                                        "resolved_type": "float64",
                                        "value": {
                                            "kind": "Name",
                                            "id": "math",
                                            "resolved_type": "module",
                                        },
                                        "attr": "pi",
                                        "runtime_module_id": "pytra.std.math",
                                        "runtime_symbol": "pi",
                                        "runtime_symbol_dispatch": "value",
                                    }
                                ],
                                "keywords": [],
                                "resolved_runtime_call": "math.sin",
                                "runtime_module_id": "pytra.std.math",
                                "runtime_symbol": "sin",
                            },
                        }
                    ],
                }
            ],
        )

        cpp_code = emit_cpp_module(doc)

        self.assertIn("return std::sin(M_PI);", cpp_code)
        self.assertNotIn("return ::sin(::pi);", cpp_code)

    def test_go_emitter_emits_pathlib_class_and_uses_native_os_path_helpers(self) -> None:
        doc = _fixture_doc("src/runtime/east/std/pathlib.east")
        meta = doc.setdefault("meta", {})
        assert isinstance(meta, dict)
        meta["linked_program_v1"] = {"module_id": "pytra.std.pathlib"}

        go_code = emit_go_module(doc)

        self.assertIn("type Path struct", go_code)
        self.assertIn("func NewPath(", go_code)
        self.assertIn("func (self *Path) joinpath(", go_code)
        self.assertIn("join(", go_code)
        self.assertIn("dirname(", go_code)
        self.assertIn("os.ReadFile(self._value)", go_code)
        self.assertIn("os.WriteFile(self._value, []byte(text), 0644)", go_code)
        self.assertNotIn("// with f {", go_code)
        self.assertNotIn("py_Path(", go_code)
        self.assertNotIn("py_pathlib_write_text", go_code)

    def test_go_emitter_reads_runtime_module_value_symbols_without_call(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "run",
                    "arg_types": {},
                    "arg_order": [],
                    "arg_defaults": {},
                    "arg_index": {},
                    "return_type": "list[str]",
                    "arg_usage": {},
                    "renamed_symbols": {},
                    "docstring": None,
                    "body": [
                        {
                            "kind": "Return",
                            "value": {
                                "kind": "Attribute",
                                "resolved_type": "list[str]",
                                "value": {
                                    "kind": "Name",
                                    "id": "sys",
                                    "resolved_type": "module",
                                    "runtime_module_id": "pytra.std.sys",
                                },
                                "attr": "argv",
                                "runtime_module_id": "pytra.std.sys",
                                "runtime_symbol": "argv",
                                "runtime_symbol_dispatch": "value",
                            },
                        }
                    ],
                }
            ],
        )

        go_code = emit_go_module(doc)

        self.assertIn("return py_argv", go_code)
        self.assertNotIn("return py_argv()", go_code)

    def test_cpp_emitter_reads_runtime_module_value_symbols_without_call(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "run",
                    "arg_types": {},
                    "arg_order": [],
                    "arg_defaults": {},
                    "arg_index": {},
                    "return_type": "list[str]",
                    "arg_usage": {},
                    "renamed_symbols": {},
                    "docstring": None,
                    "body": [
                        {
                            "kind": "Return",
                            "value": {
                                "kind": "Attribute",
                                "resolved_type": "list[str]",
                                "value": {
                                    "kind": "Name",
                                    "id": "sys",
                                    "resolved_type": "module",
                                    "runtime_module_id": "pytra.std.sys",
                                },
                                "attr": "argv",
                                "runtime_module_id": "pytra.std.sys",
                                "runtime_symbol": "argv",
                                "runtime_symbol_dispatch": "value",
                            },
                        }
                    ],
                }
            ],
        )

        cpp_code = emit_cpp_module(doc)

        self.assertIn("return argv;", cpp_code)
        self.assertNotIn("return argv();", cpp_code)

    def test_cpp_emitter_calls_property_getters_with_parens(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "ClassDef",
                    "name": "Thing",
                    "body": [],
                },
                {
                    "kind": "FunctionDef",
                    "name": "read_prop",
                    "arg_types": {"obj": "Thing"},
                    "arg_order": ["obj"],
                    "arg_defaults": {},
                    "arg_index": {"obj": 0},
                    "return_type": "int64",
                    "arg_usage": {"obj": "readonly"},
                    "renamed_symbols": {},
                    "docstring": None,
                    "body": [
                        {
                            "kind": "Return",
                            "value": {
                                "kind": "Attribute",
                                "resolved_type": "int64",
                                "attribute_access_kind": "property_getter",
                                "value": {
                                    "kind": "Name",
                                    "id": "obj",
                                    "resolved_type": "Thing",
                                },
                                "attr": "size",
                            },
                        }
                    ],
                },
            ],
        )

        cpp_code = emit_cpp_module(doc)

        self.assertIn("return obj.size();", cpp_code)
        self.assertNotIn("return obj.size;", cpp_code)

    def test_cpp_emitter_lowers_raise_to_typed_throw(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "fail",
                    "arg_types": {},
                    "arg_order": [],
                    "arg_defaults": {},
                    "arg_index": {},
                    "return_type": "None",
                    "arg_usage": {},
                    "renamed_symbols": {},
                    "docstring": None,
                    "body": [
                        {
                            "kind": "Raise",
                            "exc": {
                                "kind": "Call",
                                "resolved_type": "Exception",
                                "builtin_name": "Exception",
                                "func": {"kind": "Name", "id": "Exception", "resolved_type": "callable"},
                                "args": [{"kind": "Constant", "value": "boom", "resolved_type": "str"}],
                                "keywords": [],
                            },
                            "cause": None,
                        }
                    ],
                }
            ],
        )

        cpp_code = emit_cpp_module(doc)

        self.assertIn('throw Exception(str("boom"));', cpp_code)

    def test_cpp_emitter_lowers_try_handlers_and_finally_via_common_renderer(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "handle",
                    "arg_types": {"flag": "bool"},
                    "arg_order": ["flag"],
                    "arg_defaults": {},
                    "arg_index": {"flag": 0},
                    "return_type": "int64",
                    "arg_usage": {"flag": "readonly"},
                    "renamed_symbols": {},
                    "docstring": None,
                    "body": [
                        {
                            "kind": "Try",
                            "body": [
                                {
                                    "kind": "If",
                                    "test": {"kind": "Name", "id": "flag", "resolved_type": "bool"},
                                    "body": [
                                        {
                                            "kind": "Raise",
                                            "exc": {
                                                "kind": "Call",
                                                "resolved_type": "ValueError",
                                                "builtin_name": "ValueError",
                                                "func": {"kind": "Name", "id": "ValueError", "resolved_type": "callable"},
                                                "args": [{"kind": "Constant", "value": "bad", "resolved_type": "str"}],
                                                "keywords": [],
                                            },
                                            "cause": None,
                                        }
                                    ],
                                    "orelse": [
                                        {"kind": "Return", "value": {"kind": "Constant", "value": 1, "resolved_type": "int64"}}
                                    ],
                                }
                            ],
                            "handlers": [
                                {
                                    "kind": "ExceptHandler",
                                    "type": {"kind": "Name", "id": "ValueError"},
                                    "name": "err",
                                    "body": [{"kind": "Return", "value": {"kind": "Constant", "value": 2, "resolved_type": "int64"}}],
                                },
                                {
                                    "kind": "ExceptHandler",
                                    "type": {"kind": "Name", "id": "Exception"},
                                    "name": None,
                                    "body": [{"kind": "Return", "value": {"kind": "Constant", "value": 3, "resolved_type": "int64"}}],
                                },
                            ],
                            "finalbody": [
                                {
                                    "kind": "Expr",
                                    "value": {
                                        "kind": "Call",
                                        "func": {"kind": "Name", "id": "cleanup"},
                                        "args": [],
                                        "keywords": [],
                                    },
                                }
                            ],
                            "orelse": [],
                        }
                    ],
                }
            ],
        )

        cpp_code = emit_cpp_module(doc)

        self.assertIn("auto __finally", cpp_code)
        self.assertIn("try {", cpp_code)
        self.assertIn("catch (const ValueError& err) {", cpp_code)
        self.assertIn("catch (const Exception&) {", cpp_code)
        self.assertIn("cleanup();", cpp_code)

    def test_cpp_emitter_preserves_exception_class_inheritance_and_super_init(self) -> None:
        doc = _module_doc(
            "pytra.built_in.error",
            body=[
                {
                    "kind": "ClassDef",
                    "name": "Exception",
                    "base": "BaseException",
                    "body": [
                        {
                            "kind": "ClosureDef",
                            "name": "__init__",
                            "arg_types": {"self": "Exception", "msg": "str"},
                            "arg_order": ["self", "msg"],
                            "arg_defaults": {},
                            "arg_index": {"self": 0, "msg": 1},
                            "return_type": "None",
                            "arg_usage": {"self": "readonly", "msg": "readonly"},
                            "renamed_symbols": {},
                            "body": [
                                {
                                    "kind": "Expr",
                                    "value": {
                                        "kind": "Call",
                                        "func": {
                                            "kind": "Attribute",
                                            "value": {"kind": "Call", "func": {"kind": "Name", "id": "super"}, "args": [], "keywords": []},
                                            "attr": "__init__",
                                        },
                                        "args": [{"kind": "Name", "id": "msg", "resolved_type": "str"}],
                                        "keywords": [],
                                    },
                                }
                            ],
                        }
                    ],
                },
                {
                    "kind": "ClassDef",
                    "name": "ValueError",
                    "base": "Exception",
                    "body": [
                        {
                            "kind": "ClosureDef",
                            "name": "__init__",
                            "arg_types": {"self": "ValueError", "msg": "str"},
                            "arg_order": ["self", "msg"],
                            "arg_defaults": {},
                            "arg_index": {"self": 0, "msg": 1},
                            "return_type": "None",
                            "arg_usage": {"self": "readonly", "msg": "readonly"},
                            "renamed_symbols": {},
                            "body": [
                                {
                                    "kind": "Expr",
                                    "value": {
                                        "kind": "Call",
                                        "func": {
                                            "kind": "Attribute",
                                            "value": {"kind": "Call", "func": {"kind": "Name", "id": "super"}, "args": [], "keywords": []},
                                            "attr": "__init__",
                                        },
                                        "args": [{"kind": "Name", "id": "msg", "resolved_type": "str"}],
                                        "keywords": [],
                                    },
                                }
                            ],
                        }
                    ],
                },
            ],
        )

        cpp_code = emit_cpp_module(doc)

        self.assertIn("class Exception : public BaseException {", cpp_code)
        self.assertIn("class ValueError : public Exception {", cpp_code)
        self.assertIn("Exception::Exception(const str& msg) : BaseException(msg) {", cpp_code)
        self.assertIn("ValueError::ValueError(const str& msg) : Exception(msg) {", cpp_code)

    def test_cpp_emitter_uses_value_select_boolops_for_strings(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "choose",
                    "arg_types": {"left": "str", "right": "str"},
                    "arg_order": ["left", "right"],
                    "arg_defaults": {},
                    "arg_index": {"left": 0, "right": 1},
                    "return_type": "str",
                    "arg_usage": {"left": "readonly", "right": "readonly"},
                    "renamed_symbols": {},
                    "docstring": None,
                    "body": [
                        {
                            "kind": "Return",
                            "value": {
                                "kind": "BoolOp",
                                "op": "Or",
                                "resolved_type": "str",
                                "values": [
                                    {"kind": "Name", "id": "left", "resolved_type": "str"},
                                    {"kind": "Name", "id": "right", "resolved_type": "str"},
                                ],
                            },
                        }
                    ],
                }
            ],
        )

        cpp_code = emit_cpp_module(doc)

        self.assertIn("return (left ? left : right);", cpp_code)
        self.assertNotIn("left || right", cpp_code)

    def test_cpp_emitter_uses_py_to_bool_for_container_boolop_value_select(self) -> None:
        doc = _module_doc(
            "pytra.built_in.string_ops",
            meta_extra={"linked_program_v1": {"module_id": "pytra.built_in.string_ops"}},
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "pick_parts",
                    "arg_types": {"parts": "list[str]", "fallback": "list[str]"},
                    "arg_order": ["parts", "fallback"],
                    "arg_defaults": {},
                    "arg_index": {"parts": 0, "fallback": 1},
                    "return_type": "list[str]",
                    "arg_usage": {"parts": "readonly", "fallback": "readonly"},
                    "renamed_symbols": {},
                    "docstring": None,
                    "body": [
                        {
                            "kind": "Return",
                            "value": {
                                "kind": "BoolOp",
                                "op": "Or",
                                "resolved_type": "list[str]",
                                "values": [
                                    {"kind": "Name", "id": "parts", "resolved_type": "list[str]"},
                                    {"kind": "Name", "id": "fallback", "resolved_type": "list[str]"},
                                ],
                            },
                        }
                    ],
                }
            ],
        )

        cpp_code = emit_cpp_module(doc, allow_runtime_module=True)

        self.assertIn("return (py_to_bool(parts) ? parts : fallback);", cpp_code)

    def test_cpp_emitter_ignores_type_alias_statements(self) -> None:
        doc = _module_doc(
            "pytra.std.argparse",
            meta_extra={"linked_program_v1": {"module_id": "pytra.std.argparse"}},
            body=[
                {
                    "kind": "TypeAlias",
                    "name": "ArgValue",
                    "value": {"kind": "Name", "id": "object", "resolved_type": "type"},
                },
                {
                    "kind": "FunctionDef",
                    "name": "identity",
                    "arg_types": {"x": "str"},
                    "arg_order": ["x"],
                    "arg_defaults": {},
                    "arg_index": {"x": 0},
                    "return_type": "str",
                    "arg_usage": {"x": "readonly"},
                    "renamed_symbols": {},
                    "docstring": None,
                    "body": [{"kind": "Return", "value": {"kind": "Name", "id": "x", "resolved_type": "str"}}],
                },
            ],
        )

        cpp_code = emit_cpp_module(doc, allow_runtime_module=True)

        self.assertIn("str identity(", cpp_code)
        self.assertNotIn("TypeAlias", cpp_code)

    def test_cpp_emitter_reorders_argparse_add_argument_keywords_into_positional_slots(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "setup",
                    "arg_types": {"p": "ArgumentParser"},
                    "arg_order": ["p"],
                    "arg_defaults": {},
                    "arg_index": {"p": 0},
                    "return_type": "None",
                    "arg_usage": {"p": "readonly"},
                    "renamed_symbols": {},
                    "docstring": None,
                    "body": [
                        {
                            "kind": "Expr",
                            "value": {
                                "kind": "Call",
                                "resolved_type": "None",
                                "func": {
                                    "kind": "Attribute",
                                    "value": {"kind": "Name", "id": "p", "resolved_type": "ArgumentParser"},
                                    "attr": "add_argument",
                                },
                                "args": [
                                    {"kind": "Constant", "resolved_type": "str", "value": "-m"},
                                    {"kind": "Constant", "resolved_type": "str", "value": "--mode"},
                                ],
                                "keywords": [
                                    {
                                        "arg": "choices",
                                        "value": {
                                            "kind": "List",
                                            "resolved_type": "list[str]",
                                            "elements": [
                                                {"kind": "Constant", "resolved_type": "str", "value": "a"},
                                                {"kind": "Constant", "resolved_type": "str", "value": "b"},
                                            ],
                                        },
                                    },
                                    {
                                        "arg": "default",
                                        "value": {"kind": "Constant", "resolved_type": "str", "value": "a"},
                                    },
                                ],
                            },
                        }
                    ],
                }
            ],
        )

        cpp_code = emit_cpp_module(doc)

        self.assertIn('p.add_argument(str("-m"), str("--mode"), str(""), str(""), str(""), str(""), rc_list_from_value(list<str>{str("a"), str("b")}), str("a"));', cpp_code)

    def test_cpp_emitter_boxes_any_dict_literals_with_object_values(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "build_payload",
                    "arg_types": {},
                    "arg_order": [],
                    "arg_defaults": {},
                    "arg_index": {},
                    "return_type": "dict[str,Any]",
                    "arg_usage": {},
                    "renamed_symbols": {},
                    "docstring": None,
                    "body": [
                        {
                            "kind": "Return",
                            "value": {
                                "kind": "Box",
                                "resolved_type": "dict[str,Any]",
                                "value": {
                                    "kind": "Dict",
                                    "resolved_type": "dict[str,int64]",
                                    "entries": [
                                        {
                                            "key": {"kind": "Constant", "resolved_type": "str", "value": "n"},
                                            "value": {"kind": "Constant", "resolved_type": "int64", "value": 1},
                                        },
                                        {
                                            "key": {"kind": "Constant", "resolved_type": "str", "value": "s"},
                                            "value": {"kind": "Constant", "resolved_type": "str", "value": "x"},
                                        },
                                    ],
                                },
                            },
                        }
                    ],
                }
            ],
        )

        cpp_code = emit_cpp_module(doc)

        self.assertIn('return rc_dict_from_value(dict<str, object>{{str("n"), object(int64(1))}, {str("s"), object(str("x"))}});', cpp_code)

    def test_cpp_emitter_unboxes_object_builtin_cast_args(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "as_int",
                    "arg_types": {"items": "list[Any]"},
                    "arg_order": ["items"],
                    "arg_defaults": {},
                    "arg_index": {"items": 0},
                    "return_type": "int64",
                    "arg_usage": {"items": "readonly"},
                    "renamed_symbols": {},
                    "docstring": None,
                    "body": [
                        {
                            "kind": "Return",
                            "value": {
                                "kind": "Call",
                                "lowered_kind": "BuiltinCall",
                                "resolved_type": "int64",
                                "runtime_call": "int",
                                "func": {"kind": "Name", "id": "int", "resolved_type": "callable"},
                                "args": [
                                    {
                                        "kind": "Unbox",
                                        "resolved_type": "Obj",
                                        "value": {
                                            "kind": "Subscript",
                                            "resolved_type": "Any",
                                            "value": {"kind": "Name", "id": "items", "resolved_type": "list[Any]"},
                                            "slice": {"kind": "Constant", "resolved_type": "int64", "value": 0},
                                        },
                                    }
                                ],
                            },
                        }
                    ],
                }
            ],
        )

        cpp_code = emit_cpp_module(doc)

        self.assertIn("return (py_list_at_ref(items, int64(0))).unbox<int64, PYTRA_TID_INT>();", cpp_code)
        self.assertNotIn("static_cast<int64>(py_list_at_ref(items, int64(0)))", cpp_code)

    def test_cpp_emitter_boxes_empty_unknown_dict_as_string_key_object_values(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "default_map",
                    "arg_types": {},
                    "arg_order": [],
                    "arg_defaults": {},
                    "arg_index": {},
                    "return_type": "object",
                    "arg_usage": {},
                    "renamed_symbols": {},
                    "docstring": None,
                    "body": [
                        {
                            "kind": "Return",
                            "value": {
                                "kind": "Box",
                                "resolved_type": "object",
                                "value": {
                                    "kind": "Dict",
                                    "resolved_type": "dict[unknown,unknown]",
                                    "entries": [],
                                },
                            },
                        }
                    ],
                }
            ],
        )

        cpp_code = emit_cpp_module(doc)

        self.assertIn("return object(rc_dict_from_value(dict<str, object>{}));", cpp_code)
        self.assertNotIn("dict<object, object>{}", cpp_code)

    def test_go_emitter_uses_list_index_helper_for_list_receivers(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "run",
                    "arg_types": {"uchars": "list[str]", "ch": "str"},
                    "arg_order": ["uchars", "ch"],
                    "arg_defaults": {},
                    "arg_index": {"uchars": 0, "ch": 1},
                    "return_type": "int64",
                    "arg_usage": {"uchars": "readonly", "ch": "readonly"},
                    "renamed_symbols": {},
                    "docstring": None,
                    "body": [
                        {
                            "kind": "Return",
                            "value": {
                                "kind": "Call",
                                "resolved_type": "int64",
                                "lowered_kind": "BuiltinCall",
                                "builtin_name": "index",
                                "runtime_call": "list.index",
                                "runtime_module_id": "pytra.core.list",
                                "runtime_symbol": "list.index",
                                "runtime_call_adapter_kind": "builtin",
                                "semantic_tag": "stdlib.method.index",
                                "func": {
                                    "kind": "Attribute",
                                    "resolved_type": "unknown",
                                    "value": {
                                        "kind": "Name",
                                        "id": "uchars",
                                        "resolved_type": "list[str]",
                                    },
                                    "attr": "index",
                                },
                                "args": [{"kind": "Name", "id": "ch", "resolved_type": "str"}],
                                "keywords": [],
                                "runtime_owner": {
                                    "kind": "Name",
                                    "id": "uchars",
                                    "resolved_type": "list[str]",
                                },
                            },
                        }
                    ],
                }
            ],
        )

        go_code = emit_go_module(doc)

        self.assertIn("return py_list_index(uchars, ch)", go_code)
        self.assertNotIn("py_str_index(uchars, ch)", go_code)

    def test_linker_normalizes_runtime_type_aliases_and_builtin_refs_for_argparse(self) -> None:
        result = link_modules(
            [str(ROOT / "test/fixture/east3-opt/stdlib/argparse_extended.east3")],
            target="go",
        )
        modules = {module.module_id: module for module in result.linked_modules}

        self.assertIn("pytra.std.argparse", modules)

        runtime_go = emit_go_module(modules["pytra.std.argparse"].east_doc)
        entry_go = emit_go_module(next(module.east_doc for module in result.linked_modules if module.is_entry))

        self.assertNotIn("*ArgValue", runtime_go)
        self.assertIn("map[string]interface{}", runtime_go)
        self.assertIn("py_str_replace(", runtime_go)
        self.assertIn("py_str_lstrip(", runtime_go)
        self.assertNotIn("[]any{}", entry_go)
        self.assertIn("[]string{}", entry_go)

    def test_linker_normalizes_runtime_type_aliases_for_json(self) -> None:
        result = link_modules(
            [str(ROOT / "test/fixture/east3-opt/stdlib/json_extended.east3")],
            target="go",
        )
        modules = {module.module_id: module for module in result.linked_modules}

        self.assertIn("pytra.std.json", modules)
        runtime_go = emit_go_module(modules["pytra.std.json"].east_doc)

        self.assertNotIn("map[string]*JsonVal", runtime_go)
        self.assertNotIn("[]*JsonVal", runtime_go)
        self.assertIn("map[string]interface{}", runtime_go)
        self.assertIn("[]interface{}", runtime_go)
        self.assertNotIn("py_str(k).(string)", runtime_go)
        self.assertNotIn("py_str(py_to_int64(v)).(string)", runtime_go)
        self.assertNotIn("py_str(py_to_float64(v)).(string)", runtime_go)
        self.assertNotIn("item_sep.(string)", runtime_go)
        self.assertNotIn("key_sep.(string)", runtime_go)

    def test_go_emitter_keeps_comprehensions_as_iife_instead_of_placeholder(self) -> None:
        doc = _fixture_doc("test/fixture/east3-opt/collections/comprehension_dict_set.east3")

        go_code = emit_go_module(doc)

        self.assertIn("func() map[", go_code)
        self.assertIn("__comp_result := map[", go_code)
        self.assertNotIn("nil /*", go_code)

    def test_go_emitter_returns_mutated_bytearray_helpers(self) -> None:
        doc = _fixture_doc("test/pytra/east3-opt/utils/png.east3")

        go_code = emit_go_module(doc)

        self.assertIn("func _png_append(dst []byte, src []byte) []byte {", go_code)
        self.assertIn("return dst", go_code)
        self.assertIn("out = _png_append(out, []byte{byte(120), byte(1)})", go_code)

    def test_go_emitter_uses_marker_interfaces_for_user_class_isinstance(self) -> None:
        doc = _fixture_doc("test/fixture/east3-opt/oop/class_inherit_basic.east3")

        go_code = emit_go_module(doc)

        self.assertIn("func (_ Base) __pytra_is_Base() {}", go_code)
        self.assertIn("func (_ Child) __pytra_is_Child() {}", go_code)
        self.assertIn("interface{ __pytra_is_Base() }", go_code)
        self.assertNotIn("any(c).(*Base)", go_code)

    def test_go_emitter_uses_exact_helpers_for_pod_isinstance(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "IsInstance",
                        "value": {"kind": "Name", "id": "x16", "resolved_type": "int16"},
                        "expected_type_id": {"kind": "Name", "id": "int16"},
                        "resolved_type": "bool",
                    },
                }
            ],
        )

        go_code = emit_go_module(doc)

        self.assertIn("py_is_exact_int16(x16)", go_code)

    def test_go_emitter_keeps_int64_constants_typed_in_calls(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "func": {"kind": "Name", "id": "consume"},
                        "args": [{"kind": "Constant", "value": 123, "resolved_type": "int64"}],
                        "keywords": [],
                    },
                }
            ],
        )

        go_code = emit_go_module(doc)

        self.assertIn("consume(int64(123))", go_code)

    def test_go_emitter_lowers_class_vars_and_staticmethods_without_instance_fields(self) -> None:
        class_doc = _fixture_doc("test/fixture/east3-opt/oop/class_member.east3")
        static_doc = _fixture_doc("test/fixture/east3-opt/oop/staticmethod_basic.east3")

        class_go = emit_go_module(class_doc)
        static_go = emit_go_module(static_doc)

        self.assertIn("var Counter_value int64 = 0", class_go)
        self.assertIn("func NewCounter() *Counter {", class_go)
        self.assertIn("Counter_value += 1", class_go)
        self.assertNotIn("func NewCounter(value int64) *Counter {", class_go)
        self.assertIn("py_print(MathUtil_double(5))", static_go)
        self.assertIn("py_print(MathUtil_triple(4))", static_go)
        self.assertNotIn("MathUtil.double(5)", static_go)

    def test_go_emitter_lowers_super_calls_and_polymorphic_base_params(self) -> None:
        super_doc = _fixture_doc("test/fixture/east3-opt/oop/super_init.east3")
        dispatch_doc = _fixture_doc("test/fixture/east3-opt/oop/inheritance_virtual_dispatch_multilang.east3")

        super_go = emit_go_module(super_doc)
        dispatch_go = emit_go_module(dispatch_doc)

        self.assertIn("obj.Base = *NewBase()", super_go)
        self.assertIn("(\"loud-\" + self.Dog.speak())", dispatch_go)
        self.assertIn("type __pytra_iface_Animal interface {", dispatch_go)
        self.assertIn("func call_via_animal(a __pytra_iface_Animal) string {", dispatch_go)
        self.assertIn("func call_via_dog(d __pytra_iface_Dog) string {", dispatch_go)

    def test_cpp_emitter_drops_const_on_class_storage_mutation_and_lowers_super_calls(self) -> None:
        class_doc = _fixture_doc("test/fixture/east3-opt/oop/class_member.east3")
        super_doc = _fixture_doc("test/fixture/east3-opt/oop/super_init.east3")
        dispatch_doc = _fixture_doc("test/fixture/east3-opt/oop/inheritance_virtual_dispatch_multilang.east3")

        class_cpp = emit_cpp_module(class_doc)
        super_cpp = emit_cpp_module(super_doc)
        dispatch_cpp = emit_cpp_module(dispatch_doc)

        self.assertIn("int64 Counter::inc()", class_cpp)
        self.assertNotIn("int64 Counter::inc() const", class_cpp)
        self.assertIn("Counter::value += int64(1);", class_cpp)
        self.assertNotIn("super()", super_cpp)
        self.assertIn("Dog::speak()", dispatch_cpp)

    def test_linker_excludes_traits_from_type_id_table_and_annotates_trait_isinstance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entry_path = Path(tmp) / "app.east3.json"
            entry_path.write_text(
                json.dumps(
                    _module_doc(
                        "app",
                        body=[
                            {
                                "kind": "ClassDef",
                                "name": "Drawable",
                                "decorators": ["trait"],
                                "meta": {
                                    "trait_v1": {
                                        "schema_version": 1,
                                        "methods": [{"name": "draw", "args": ["self"], "return_type": "None"}],
                                        "extends_traits": [],
                                    }
                                },
                                "body": [],
                            },
                            {
                                "kind": "ClassDef",
                                "name": "Circle",
                                "decorators": ["implements(Drawable)"],
                                "meta": {"implements_v1": {"schema_version": 1, "traits": ["Drawable"]}},
                                "body": [],
                            },
                            {
                                "kind": "FunctionDef",
                                "name": "ok",
                                "arg_types": {"d": "Drawable"},
                                "arg_order": ["d"],
                                "arg_defaults": {},
                                "arg_index": {"d": 0},
                                "return_type": "bool",
                                "arg_usage": {},
                                "renamed_symbols": {},
                                "body": [
                                    {
                                        "kind": "Return",
                                        "value": {
                                            "kind": "IsInstance",
                                            "value": {"kind": "Name", "id": "d", "resolved_type": "Drawable"},
                                            "expected_type_id": {"kind": "Name", "id": "Drawable"},
                                            "resolved_type": "bool",
                                        },
                                    }
                                ],
                            },
                        ],
                    ),
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = link_modules([str(entry_path)], target="cpp", dispatch_mode="native")

        linked = next(module.east_doc for module in result.linked_modules if module.module_id == "app")
        self.assertEqual(linked.get("meta", {}).get("emit_context"), {"module_id": "app", "is_entry": True})
        linked_program = linked.get("meta", {}).get("linked_program_v1", {})
        self.assertNotIn("trait_id_table_v1", linked_program)
        self.assertNotIn("class_trait_masks_v1", linked_program)
        self.assertNotIn("app.Drawable", linked_program.get("type_id_resolved_v1", {}))
        self.assertIn("app.Circle", linked_program.get("type_id_resolved_v1", {}))

        trait_check = next(
            node for node in _walk_nodes(linked)
            if node.get("kind") == "Constant" and isinstance(node.get("value"), bool)
        )
        self.assertEqual(trait_check.get("value"), True)
        self.assertEqual(trait_check.get("resolved_type"), "bool")

    def test_cpp_emitter_lowers_traits_to_virtual_interfaces_and_trait_masks(self) -> None:
        doc = _module_doc(
            "app",
            body=[
                {
                    "kind": "ClassDef",
                    "name": "Drawable",
                    "decorators": ["trait"],
                    "meta": {
                        "trait_v1": {
                            "schema_version": 1,
                            "methods": [{"name": "draw", "args": ["self"], "return_type": "None"}],
                            "extends_traits": [],
                        }
                    },
                    "body": [
                        {
                            "kind": "FunctionDef",
                            "name": "draw",
                            "arg_types": {"self": "Drawable"},
                            "arg_order": ["self"],
                            "arg_defaults": {},
                            "arg_index": {"self": 0},
                            "return_type": "None",
                            "arg_usage": {},
                            "renamed_symbols": {},
                            "body": [],
                        }
                    ],
                },
                {
                    "kind": "ClassDef",
                    "name": "Circle",
                    "decorators": ["implements(Drawable)"],
                    "meta": {"implements_v1": {"schema_version": 1, "traits": ["Drawable"]}},
                    "body": [
                        {
                            "kind": "FunctionDef",
                            "name": "draw",
                            "arg_types": {"self": "Circle"},
                            "arg_order": ["self"],
                            "arg_defaults": {},
                            "arg_index": {"self": 0},
                            "return_type": "None",
                            "arg_usage": {},
                            "renamed_symbols": {},
                            "meta": {"trait_impl_v1": {"schema_version": 1, "trait_name": "Drawable", "method_name": "draw"}},
                            "body": [{"kind": "Pass"}],
                        }
                    ],
                },
                {
                    "kind": "FunctionDef",
                    "name": "ok",
                    "arg_types": {"d": "Drawable"},
                    "arg_order": ["d"],
                    "arg_defaults": {},
                    "arg_index": {"d": 0},
                    "return_type": "bool",
                    "arg_usage": {},
                    "renamed_symbols": {},
                    "body": [
                        {
                            "kind": "Return",
                            "value": {"kind": "Constant", "value": True, "resolved_type": "bool"},
                        },
                    ],
                },
            ],
            meta_extra={
                "linked_program_v1": {
                    "module_id": "app",
                    "type_id_resolved_v1": {"app.Circle": 1000},
                    "type_info_table_v1": {"app.Circle": {"id": 1000, "entry": 1000, "exit": 1001}},
                }
            },
        )

        cpp_code = emit_cpp_module(doc)

        self.assertIn("class Drawable {", cpp_code)
        self.assertIn("virtual void draw() const = 0;", cpp_code)
        self.assertIn("class Circle : virtual public Drawable {", cpp_code)
        self.assertIn("void draw() const override;", cpp_code)
        self.assertNotIn("__pytra_trait_bits", cpp_code)
        self.assertIn("return true;", cpp_code)

    def test_go_emitter_lowers_traits_to_interfaces_and_trait_assertions(self) -> None:
        doc = _module_doc(
            "app",
            body=[
                {
                    "kind": "ClassDef",
                    "name": "Drawable",
                    "decorators": ["trait"],
                    "meta": {
                        "trait_v1": {
                            "schema_version": 1,
                            "methods": [{"name": "draw", "args": ["self"], "return_type": "None"}],
                            "extends_traits": [],
                        }
                    },
                    "body": [
                        {
                            "kind": "FunctionDef",
                            "name": "draw",
                            "arg_types": {"self": "Drawable"},
                            "arg_order": ["self"],
                            "arg_defaults": {},
                            "arg_index": {"self": 0},
                            "return_type": "None",
                            "arg_usage": {},
                            "renamed_symbols": {},
                            "body": [],
                        }
                    ],
                },
                {
                    "kind": "ClassDef",
                    "name": "Circle",
                    "decorators": ["implements(Drawable)"],
                    "meta": {"implements_v1": {"schema_version": 1, "traits": ["Drawable"]}},
                    "body": [
                        {
                            "kind": "FunctionDef",
                            "name": "draw",
                            "arg_types": {"self": "Circle"},
                            "arg_order": ["self"],
                            "arg_defaults": {},
                            "arg_index": {"self": 0},
                            "return_type": "None",
                            "arg_usage": {},
                            "renamed_symbols": {},
                            "meta": {"trait_impl_v1": {"schema_version": 1, "trait_name": "Drawable", "method_name": "draw"}},
                            "body": [{"kind": "Pass"}],
                        }
                    ],
                },
                {
                    "kind": "FunctionDef",
                    "name": "ok",
                    "arg_types": {"d": "Drawable"},
                    "arg_order": ["d"],
                    "arg_defaults": {},
                    "arg_index": {"d": 0},
                    "return_type": "bool",
                    "arg_usage": {},
                    "renamed_symbols": {},
                    "body": [
                        {
                            "kind": "Return",
                            "value": {"kind": "Constant", "value": True, "resolved_type": "bool"},
                        }
                    ],
                },
            ],
        )

        go_code = emit_go_module(doc)

        self.assertIn("type Drawable interface {", go_code)
        self.assertIn("\tdraw()", go_code)
        self.assertIn("func ok(d Drawable) bool {", go_code)
        self.assertIn("return true", go_code)

    def test_go_emitter_turns_returning_try_into_return_iife(self) -> None:
        doc = _fixture_doc("test/pytra/east3-opt/utils/assertions.east3")

        go_code = emit_go_module(doc)

        self.assertIn("return func() bool {", go_code)
        self.assertIn("__try_result = (py_to_string(actual) == py_to_string(expected))", go_code)
        self.assertIn("__try_result = (actual == expected)", go_code)

    def test_go_emitter_uses_len_based_truthiness_for_bytes_ifexp(self) -> None:
        doc = _fixture_doc("test/fixture/east3-opt/typing/bytes_truthiness.east3")

        go_code = emit_go_module(doc)

        self.assertIn("if len(payload) > 0 {", go_code)
        self.assertIn("for len(payload) > 0 {", go_code)
        self.assertIn("return py_ternary_int(len(payload) > 0, 1, 0)", go_code)

    def test_go_emitter_keeps_tuple_star_args_as_backing_slice_indexes(self) -> None:
        doc = _fixture_doc("test/fixture/east3-opt/typing/starred_call_tuple_basic.east3")

        go_code = emit_go_module(doc)

        self.assertIn("rgb := []any{1, 2, 3}", go_code)
        self.assertIn("mix_rgb(py_to_int64(rgb[0]), py_to_int64(rgb[1]), py_to_int64(rgb[2]))", go_code)
        self.assertNotIn("rgb.([]any)", go_code)

    def test_go_emitter_wraps_optional_scalars_with_typed_temporaries(self) -> None:
        doc = _fixture_doc("test/fixture/east3-opt/typing/none_optional.east3")

        go_code = emit_go_module(doc)

        self.assertIn("func maybe_value(flag bool) *int64 {", go_code)
        self.assertIn("var __opt_1 int64 = 42", go_code)
        self.assertIn("var __opt_3 int64 = py_to_int64(__unbox_2)", go_code)
        self.assertIn("var __opt_5 int64 = __dict_get_4", go_code)

    def test_go_emitter_lowers_enum_family_to_named_int_consts(self) -> None:
        enum_go = emit_go_module(_fixture_doc("test/fixture/east3-opt/typing/enum_basic.east3"))
        intenum_go = emit_go_module(_fixture_doc("test/fixture/east3-opt/typing/intenum_basic.east3"))
        intflag_go = emit_go_module(_fixture_doc("test/fixture/east3-opt/typing/intflag_basic.east3"))

        self.assertIn("type Color int64", enum_go)
        self.assertIn("Color_RED Color = 1", enum_go)
        self.assertIn("Color_BLUE Color = 2", enum_go)
        self.assertNotIn("Enum", enum_go)
        self.assertIn("type Status int64", intenum_go)
        self.assertIn("Status_ERROR Status = 1", intenum_go)
        self.assertNotIn("IntEnum", intenum_go)
        self.assertIn("type Perm int64", intflag_go)
        self.assertIn("Perm_READ Perm = 1", intflag_go)
        self.assertIn("Perm((Perm_READ | Perm_WRITE))", intflag_go)
        self.assertNotIn("IntFlag", intflag_go)

    def test_cpp_emitter_lowers_enum_family_to_scoped_int_enums(self) -> None:
        enum_cpp = emit_cpp_module(_fixture_doc("test/fixture/east3-opt/typing/enum_basic.east3"))
        intenum_cpp = emit_cpp_module(_fixture_doc("test/fixture/east3-opt/typing/intenum_basic.east3"))
        intflag_cpp = emit_cpp_module(_fixture_doc("test/fixture/east3-opt/typing/intflag_basic.east3"))

        self.assertIn("enum class Color : int64 {", enum_cpp)
        self.assertIn("RED = int64(1)", enum_cpp)
        self.assertIn("BLUE = int64(2)", enum_cpp)
        self.assertNotIn("class Color : public Enum", enum_cpp)
        self.assertIn("enum class Status : int64 {", intenum_cpp)
        self.assertIn("(static_cast<int64>(Status::OK) == int64(0))", intenum_cpp)
        self.assertIn("enum class Perm : int64 {", intflag_cpp)
        self.assertIn("static_cast<Perm>(static_cast<int64>(Perm::READ) | static_cast<int64>(Perm::WRITE))", intflag_cpp)
        self.assertNotIn("class Perm : public IntFlag", intflag_cpp)

    def test_go_emitter_spreads_typed_varargs_and_keeps_plain_class_ctor_zero_arg(self) -> None:
        doc = _fixture_doc("test/fixture/east3-opt/signature/ok_typed_varargs_representative.east3")

        go_code = emit_go_module(doc)

        self.assertIn("func NewControllerState() *ControllerState {", go_code)
        self.assertIn("merge_controller_states(target, []*ControllerState{lhs, rhs}...)", go_code)

    def test_go_emitter_uses_range_target_type_from_east3(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "run",
                    "arg_types": {},
                    "arg_order": [],
                    "arg_defaults": {},
                    "arg_index": {},
                    "return_type": "None",
                    "arg_usage": {},
                    "renamed_symbols": {},
                    "docstring": None,
                    "body": [
                        {
                            "kind": "ForCore",
                            "iter_mode": "static_fastpath",
                            "iter_plan": {
                                "kind": "StaticRangeForPlan",
                                "start": {"kind": "Constant", "value": 0, "resolved_type": "int64"},
                                "stop": {"kind": "Constant", "value": 3, "resolved_type": "int64"},
                                "step": {"kind": "Constant", "value": 1, "resolved_type": "int64"},
                            },
                            "target_plan": {
                                "kind": "NameTarget",
                                "id": "i",
                                "target_type": "int32",
                            },
                            "body": [],
                            "orelse": [],
                        }
                    ],
                }
            ],
        )

        go_code = emit_go_module(doc)

        self.assertIn("for i := int32(0); i < int32(3); i += int32(1) {", go_code)

    def test_cpp_emitter_uses_range_target_type_from_east3(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "run",
                    "arg_types": {},
                    "arg_order": [],
                    "arg_defaults": {},
                    "arg_index": {},
                    "return_type": "None",
                    "arg_usage": {},
                    "renamed_symbols": {},
                    "docstring": None,
                    "body": [
                        {
                            "kind": "ForCore",
                            "iter_mode": "static_fastpath",
                            "iter_plan": {
                                "kind": "StaticRangeForPlan",
                                "start": {"kind": "Constant", "value": 0, "resolved_type": "int64"},
                                "stop": {"kind": "Constant", "value": 3, "resolved_type": "int64"},
                                "step": {"kind": "Constant", "value": 1, "resolved_type": "int64"},
                            },
                            "target_plan": {
                                "kind": "NameTarget",
                                "id": "i",
                                "target_type": "int32",
                            },
                            "body": [],
                            "orelse": [],
                        }
                    ],
                }
            ],
        )

        cpp_code = emit_cpp_module(doc)

        self.assertIn("for (int32_t i = 0; i < 3; i += 1) {", cpp_code)
        self.assertNotIn("for (int64_t i = 0; i < 3; i += 1) {", cpp_code)

    def test_go_emitter_does_not_invent_local_call_casts(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "takes_float",
                    "arg_types": {"x": "float64"},
                    "arg_order": ["x"],
                    "arg_defaults": {},
                    "arg_index": {"x": 0},
                    "return_type": "float64",
                    "arg_usage": {},
                    "renamed_symbols": {},
                    "docstring": None,
                    "body": [
                        {
                            "kind": "Return",
                            "value": {"kind": "Name", "id": "x", "resolved_type": "float64"},
                        }
                    ],
                },
                {
                    "kind": "FunctionDef",
                    "name": "run",
                    "arg_types": {},
                    "arg_order": [],
                    "arg_defaults": {},
                    "arg_index": {},
                    "return_type": "float64",
                    "arg_usage": {},
                    "renamed_symbols": {},
                    "docstring": None,
                    "body": [
                        {
                            "kind": "AnnAssign",
                            "target": {"kind": "Name", "id": "n", "resolved_type": "int64"},
                            "decl_type": "int64",
                            "resolved_type": "int64",
                            "value": {"kind": "Constant", "value": 3, "resolved_type": "int64"},
                        },
                        {
                            "kind": "Return",
                            "value": {
                                "kind": "Call",
                                "resolved_type": "float64",
                                "func": {"kind": "Name", "id": "takes_float", "resolved_type": "callable"},
                                "args": [{"kind": "Name", "id": "n", "resolved_type": "int64"}],
                                "keywords": [],
                            },
                        },
                    ],
                },
            ],
        )

        go_code = emit_go_module(doc)

        self.assertIn("return takes_float(n)", go_code)
        self.assertNotIn("takes_float(float64(n))", go_code)

    def test_go_emitter_does_not_invent_assignment_casts(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "run",
                    "arg_types": {},
                    "arg_order": [],
                    "arg_defaults": {},
                    "arg_index": {},
                    "return_type": "float64",
                    "arg_usage": {},
                    "renamed_symbols": {},
                    "docstring": None,
                    "body": [
                        {
                            "kind": "AnnAssign",
                            "target": {"kind": "Name", "id": "n", "resolved_type": "int64"},
                            "decl_type": "int64",
                            "resolved_type": "int64",
                            "value": {"kind": "Constant", "value": 3, "resolved_type": "int64"},
                        },
                        {
                            "kind": "AnnAssign",
                            "target": {"kind": "Name", "id": "x", "resolved_type": "float64"},
                            "decl_type": "float64",
                            "resolved_type": "float64",
                            "value": {"kind": "Name", "id": "n", "resolved_type": "int64"},
                        },
                        {
                            "kind": "AugAssign",
                            "target": {"kind": "Name", "id": "x", "resolved_type": "float64"},
                            "op": "Add",
                            "value": {"kind": "Name", "id": "n", "resolved_type": "int64"},
                        },
                        {
                            "kind": "Return",
                            "value": {"kind": "Name", "id": "x", "resolved_type": "float64"},
                        },
                    ],
                }
            ],
        )

        go_code = emit_go_module(doc)

        self.assertIn("var x float64 = n", go_code)
        self.assertIn("x += n", go_code)
        self.assertNotIn("var x float64 = float64(n)", go_code)
        self.assertNotIn("x += float64(n)", go_code)

    def test_go_emitter_does_not_infer_assignment_decl_type_from_value(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "run",
                    "arg_types": {},
                    "arg_order": [],
                    "arg_defaults": {},
                    "arg_index": {},
                    "return_type": "None",
                    "arg_usage": {},
                    "renamed_symbols": {},
                    "docstring": None,
                    "body": [
                        {
                            "kind": "Assign",
                            "target": {"kind": "Name", "id": "n", "resolved_type": "unknown"},
                            "value": {"kind": "Constant", "value": 3, "resolved_type": "int64"},
                            "declare": True,
                        }
                    ],
                }
            ],
        )

        go_code = emit_go_module(doc)

        self.assertIn("n := 3", go_code)
        self.assertNotIn("var n int64 = 3", go_code)

    def test_cpp_emitter_does_not_infer_assignment_decl_type_from_value(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "run",
                    "arg_types": {},
                    "arg_order": [],
                    "arg_defaults": {},
                    "arg_index": {},
                    "return_type": "None",
                    "arg_usage": {},
                    "renamed_symbols": {},
                    "docstring": None,
                    "body": [
                        {
                            "kind": "Assign",
                            "target": {"kind": "Name", "id": "n", "resolved_type": "unknown"},
                            "value": {"kind": "Constant", "value": 3, "resolved_type": "int64"},
                            "declare": True,
                        }
                    ],
                }
            ],
        )

        cpp_code = emit_cpp_module(doc)

        self.assertIn("auto n = 3;", cpp_code)
        self.assertNotIn("int64_t n = 3;", cpp_code)

    def test_cpp_emitter_renders_unknown_vardecl_as_auto(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "run",
                    "arg_types": {},
                    "arg_order": [],
                    "arg_defaults": {},
                    "arg_index": {},
                    "return_type": "None",
                    "arg_usage": {},
                    "renamed_symbols": {},
                    "docstring": None,
                    "body": [
                        {
                            "kind": "VarDecl",
                            "name": "tmp",
                            "type": "unknown",
                        }
                    ],
                }
            ],
        )

        cpp_code = emit_cpp_module(doc)

        self.assertIn("auto tmp = {};", cpp_code)
        self.assertNotIn("int64_t tmp = 0;", cpp_code)

    def test_go_emitter_does_not_short_circuit_name_unbox_from_decl_type(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "run",
                    "arg_types": {},
                    "arg_order": [],
                    "arg_defaults": {},
                    "arg_index": {},
                    "return_type": "str",
                    "arg_usage": {},
                    "renamed_symbols": {},
                    "docstring": None,
                    "body": [
                        {
                            "kind": "AnnAssign",
                            "target": {"kind": "Name", "id": "text", "resolved_type": "str"},
                            "decl_type": "str",
                            "resolved_type": "str",
                            "value": {"kind": "Constant", "value": "x", "resolved_type": "str"},
                        },
                        {
                            "kind": "Return",
                            "value": {
                                "kind": "Unbox",
                                "target": "str",
                                "value": {"kind": "Name", "id": "text", "resolved_type": "unknown"},
                            },
                        },
                    ],
                }
            ],
        )

        go_code = emit_go_module(doc)

        self.assertIn("return text.(string)", go_code)
        self.assertNotIn("\n\treturn text\n", go_code)

    def test_go_emitter_does_not_invent_dict_get_default_casts(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "run",
                    "arg_types": {"d": "dict[str,float64]"},
                    "arg_order": ["d"],
                    "arg_defaults": {},
                    "arg_index": {"d": 0},
                    "return_type": "float64",
                    "arg_usage": {},
                    "renamed_symbols": {},
                    "docstring": None,
                    "body": [
                        {
                            "kind": "Return",
                            "value": {
                                "kind": "Call",
                                "resolved_type": "float64",
                                "lowered_kind": "BuiltinCall",
                                "builtin_name": "get",
                                "runtime_call": "dict.get",
                                "func": {
                                    "kind": "Attribute",
                                    "resolved_type": "callable",
                                    "value": {"kind": "Name", "id": "d", "resolved_type": "dict[str,float64]"},
                                    "attr": "get",
                                },
                                "args": [
                                    {"kind": "Constant", "value": "x", "resolved_type": "str"},
                                    {"kind": "Constant", "value": 0, "resolved_type": "int64"},
                                ],
                                "keywords": [],
                            },
                        }
                    ],
                }
            ],
        )

        go_code = emit_go_module(doc)

        self.assertIn("return func() float64 {", go_code)
        self.assertIn("return 0", go_code)
        self.assertNotIn("return float64(0)", go_code)

    def test_go_emitter_uses_yields_dynamic_for_dict_get_assertion(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "run",
                    "arg_types": {"d": "dict[str,int64]"},
                    "arg_order": ["d"],
                    "arg_defaults": {},
                    "arg_index": {"d": 0},
                    "return_type": "int64",
                    "arg_usage": {},
                    "renamed_symbols": {},
                    "docstring": None,
                    "body": [
                        {
                            "kind": "Return",
                            "value": {
                                "kind": "Call",
                                "resolved_type": "int64",
                                "yields_dynamic": True,
                                "lowered_kind": "BuiltinCall",
                                "builtin_name": "get",
                                "runtime_call": "dict.get",
                                "func": {
                                    "kind": "Attribute",
                                    "resolved_type": "callable",
                                    "value": {"kind": "Name", "id": "d", "resolved_type": "dict[str,int64]"},
                                    "attr": "get",
                                },
                                "args": [
                                    {"kind": "Constant", "value": "x", "resolved_type": "str"},
                                    {"kind": "Constant", "value": 0, "resolved_type": "int64"},
                                ],
                                "keywords": [],
                            },
                        }
                    ],
                }
            ],
        )

        go_code = emit_go_module(doc)

        self.assertIn("py_to_int64(py_dict_get(", go_code)
        self.assertNotIn("return func() int64 {", go_code)

    def test_go_emitter_uses_yields_dynamic_for_list_pop_assertion(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "run",
                    "arg_types": {"xs": "list[int64]"},
                    "arg_order": ["xs"],
                    "arg_defaults": {},
                    "arg_index": {"xs": 0},
                    "return_type": "int64",
                    "arg_usage": {},
                    "renamed_symbols": {},
                    "docstring": None,
                    "body": [
                        {
                            "kind": "Return",
                            "value": {
                                "kind": "Call",
                                "resolved_type": "int64",
                                "yields_dynamic": True,
                                "lowered_kind": "BuiltinCall",
                                "builtin_name": "pop",
                                "runtime_call": "list.pop",
                                "func": {
                                    "kind": "Attribute",
                                    "resolved_type": "callable",
                                    "value": {"kind": "Name", "id": "xs", "resolved_type": "list[int64]"},
                                    "attr": "pop",
                                },
                                "args": [],
                                "keywords": [],
                            },
                        }
                    ],
                }
            ],
        )

        go_code = emit_go_module(doc)

        self.assertIn("py_to_int64(py_list_pop(&xs))", go_code)
        self.assertNotIn("func() int64 {", go_code)

    def test_go_emitter_does_not_invent_dict_literal_entry_casts(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "run",
                    "arg_types": {},
                    "arg_order": [],
                    "arg_defaults": {},
                    "arg_index": {},
                    "return_type": "dict[str,float64]",
                    "arg_usage": {},
                    "renamed_symbols": {},
                    "docstring": None,
                    "body": [
                        {
                            "kind": "AnnAssign",
                            "target": {"kind": "Name", "id": "n", "resolved_type": "int64"},
                            "decl_type": "int64",
                            "resolved_type": "int64",
                            "value": {"kind": "Constant", "value": 3, "resolved_type": "int64"},
                        },
                        {
                            "kind": "Return",
                            "value": {
                                "kind": "Dict",
                                "resolved_type": "dict[str,float64]",
                                "entries": [
                                    {
                                        "key": {"kind": "Constant", "value": "x", "resolved_type": "str"},
                                        "value": {"kind": "Name", "id": "n", "resolved_type": "int64"},
                                    }
                                ],
                            },
                        },
                    ],
                }
            ],
        )

        go_code = emit_go_module(doc)

        self.assertIn("return map[string]float64{\"x\": n}", go_code)
        self.assertNotIn("\"x\": float64(n)", go_code)

    def test_go_emitter_does_not_invent_optional_scalar_casts(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "run",
                    "arg_types": {},
                    "arg_order": [],
                    "arg_defaults": {},
                    "arg_index": {},
                    "return_type": "float64 | None",
                    "arg_usage": {},
                    "renamed_symbols": {},
                    "docstring": None,
                    "body": [
                        {
                            "kind": "AnnAssign",
                            "target": {"kind": "Name", "id": "n", "resolved_type": "int64"},
                            "decl_type": "int64",
                            "resolved_type": "int64",
                            "value": {"kind": "Constant", "value": 3, "resolved_type": "int64"},
                        },
                        {
                            "kind": "Return",
                            "value": {"kind": "Name", "id": "n", "resolved_type": "int64"},
                        },
                    ],
                }
            ],
        )

        go_code = emit_go_module(doc)

        self.assertIn("var __opt_", go_code)
        self.assertIn("= n", go_code)
        self.assertNotIn("float64(n)", go_code)

    def test_go_emitter_does_not_invent_list_literal_entry_casts(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "run",
                    "arg_types": {},
                    "arg_order": [],
                    "arg_defaults": {},
                    "arg_index": {},
                    "return_type": "list[float64]",
                    "arg_usage": {},
                    "renamed_symbols": {},
                    "docstring": None,
                    "body": [
                        {
                            "kind": "AnnAssign",
                            "target": {"kind": "Name", "id": "n", "resolved_type": "int64"},
                            "decl_type": "int64",
                            "resolved_type": "int64",
                            "value": {"kind": "Constant", "value": 3, "resolved_type": "int64"},
                        },
                        {
                            "kind": "Return",
                            "value": {
                                "kind": "List",
                                "resolved_type": "list[float64]",
                                "elements": [{"kind": "Name", "id": "n", "resolved_type": "int64"}],
                            },
                        },
                    ],
                }
            ],
        )

        go_code = emit_go_module(doc)

        self.assertIn("return []float64{n}", go_code)
        self.assertNotIn("[]float64{float64(n)}", go_code)

    def test_go_emitter_does_not_infer_dict_literal_type_from_decl_hint(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "run",
                    "arg_types": {},
                    "arg_order": [],
                    "arg_defaults": {},
                    "arg_index": {},
                    "return_type": "dict[str,int64]",
                    "arg_usage": {},
                    "renamed_symbols": {},
                    "docstring": None,
                    "body": [
                        {
                            "kind": "Return",
                            "value": {
                                "kind": "Dict",
                                "resolved_type": "dict[str,int64]",
                                "decl_type": "dict[str,float64]",
                                "entries": [
                                    {
                                        "key": {"kind": "Constant", "value": "x", "resolved_type": "str"},
                                        "value": {"kind": "Constant", "value": 1, "resolved_type": "int64"},
                                    }
                                ],
                            },
                        }
                    ],
                }
            ],
        )

        go_code = emit_go_module(doc)

        self.assertIn("return map[string]int64{\"x\": 1}", go_code)
        self.assertNotIn("map[string]float64", go_code)

    def test_cpp_emitter_runtime_symbol_prefix_uses_skip_modules_without_pytra_hardcode(self) -> None:
        doc = _module_doc(
            "app.main",
            meta_extra={
                "import_bindings": [
                    {
                        "module_id": "runtime.custom",
                        "local_name": "helper",
                        "binding_kind": "symbol",
                    }
                ]
            },
            body=[
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "func": {"kind": "Name", "id": "helper"},
                        "args": [],
                    },
                }
            ],
        )

        mapping = RuntimeMapping(
            builtin_prefix="rt_",
            calls={},
            skip_module_prefixes=["runtime."],
        )
        with patch("toolchain2.emit.cpp.emitter.load_runtime_mapping", return_value=mapping):
            cpp_code = emit_cpp_module(doc)

        self.assertIn("rt_helper();", cpp_code)

    def test_cpp_emitter_uses_exact_helpers_for_pod_isinstance(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "IsInstance",
                        "value": {"kind": "Name", "id": "x16", "resolved_type": "int16"},
                        "expected_type_id": {"kind": "Name", "id": "int16"},
                        "resolved_type": "bool",
                    },
                }
            ],
        )

        cpp_code = emit_cpp_module(doc)

        self.assertIn("py_runtime_value_exact_is<int16>(x16)", cpp_code)

    def test_cpp_emitter_supports_container_type_ids_for_isinstance(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "IsInstance",
                        "value": {"kind": "Name", "id": "dyn", "resolved_type": "object"},
                        "expected_type_id": {"kind": "Name", "id": "list"},
                        "resolved_type": "bool",
                    },
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "IsInstance",
                        "value": {"kind": "Name", "id": "items", "resolved_type": "dict[str,int64]"},
                        "expected_type_id": {"kind": "Name", "id": "dict"},
                        "resolved_type": "bool",
                    },
                },
            ],
        )

        cpp_code = emit_cpp_module(doc)

        self.assertIn("py_runtime_object_isinstance(dyn, PYTRA_TID_LIST)", cpp_code)
        self.assertIn("py_runtime_value_isinstance(items, PYTRA_TID_DICT)", cpp_code)

    def test_cpp_emitter_iterates_dicts_as_keys_for_direct_for_loops(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "ForCore",
                    "iter_mode": "runtime_protocol",
                    "iter_plan": {
                        "kind": "RuntimeIterForPlan",
                        "iter_expr": {
                            "kind": "Name",
                            "id": "values",
                            "resolved_type": "dict[str,int64]",
                        },
                    },
                    "target_plan": {
                        "kind": "NameTarget",
                        "id": "key",
                        "target_type": "str",
                    },
                    "body": [
                        {
                            "kind": "Assign",
                            "target": {"kind": "Name", "id": "_", "resolved_type": "str"},
                            "value": {"kind": "Name", "id": "key", "resolved_type": "str"},
                            "declare": True,
                            "decl_type": "str",
                            "unused": True,
                        }
                    ],
                    "orelse": [],
                }
            ],
        )

        cpp_code = emit_cpp_module(doc)

        self.assertIn("for (const auto& __entry_", cpp_code)
        self.assertIn("str key = __entry_", cpp_code)
        self.assertIn(".first;", cpp_code)

    def test_cpp_emitter_supports_type_id_boundary_nodes_and_clear_methods(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "ObjTypeId",
                        "value": {"kind": "Name", "id": "dyn", "resolved_type": "object"},
                        "resolved_type": "int64",
                    },
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "IsSubtype",
                        "actual_type_id": {"kind": "Constant", "value": 1001, "resolved_type": "int64"},
                        "expected_type_id": {"kind": "Constant", "value": 1000, "resolved_type": "int64"},
                        "resolved_type": "bool",
                    },
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "IsSubclass",
                        "actual_type_id": {"kind": "Constant", "value": 1001, "resolved_type": "int64"},
                        "expected_type_id": {"kind": "Constant", "value": 1000, "resolved_type": "int64"},
                        "resolved_type": "bool",
                    },
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "lowered_kind": "BuiltinCall",
                        "builtin_name": "clear",
                        "runtime_call": "dict.clear",
                        "resolved_type": "None",
                        "func": {
                            "kind": "Attribute",
                            "value": {"kind": "Name", "id": "state", "resolved_type": "dict[str,int64]"},
                            "attr": "clear",
                        },
                        "args": [],
                    },
                },
            ],
        )

        cpp_code = emit_cpp_module(doc)

        self.assertIn("py_runtime_object_type_id(dyn)", cpp_code)
        self.assertIn("py_runtime_type_id_is_subtype(int64(1001), int64(1000))", cpp_code)
        self.assertIn("py_runtime_type_id_issubclass(int64(1001), int64(1000))", cpp_code)
        self.assertIn("state.clear();", cpp_code)

    def test_cpp_emitter_uses_linked_type_ids_for_nominal_classes(self) -> None:
        doc = _module_doc(
            "app.main",
            meta_extra={
                "linked_program_v1": {
                    "module_id": "app.main",
                    "type_id_resolved_v1": {"app.main.Path": 1000},
                    "type_info_table_v1": {
                        "app.main.Path": {"id": 1000, "entry": 1000, "exit": 1001},
                    },
                },
            },
            body=[
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "IsInstance",
                        "value": {"kind": "Name", "id": "dyn", "resolved_type": "object"},
                        "expected_type_id": {"kind": "Name", "id": "Path", "resolved_type": "type"},
                        "resolved_type": "bool",
                    },
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Box",
                        "value": {"kind": "Name", "id": "p", "resolved_type": "Path"},
                        "resolved_type": "object",
                    },
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "ObjTypeId",
                        "value": {"kind": "Name", "id": "p", "resolved_type": "Path"},
                        "resolved_type": "int64",
                    },
                },
            ],
        )

        cpp_code = emit_cpp_module(doc)

        self.assertIn("py_runtime_object_isinstance(dyn, static_cast<pytra_type_id>(1000))", cpp_code)
        self.assertIn("object(make_object<Path>(1000, p))", cpp_code)
        self.assertIn("static_cast<pytra_type_id>(1000)", cpp_code)

    def test_cpp_header_gen_emits_forward_decls_before_class_bodies(self) -> None:
        doc = _module_doc(
            "pytra.std.json",
            body=[
                {
                    "kind": "ClassDef",
                    "name": "JsonObj",
                    "field_types": {"raw": "dict[str,object]"},
                    "body": [
                        {
                            "kind": "FunctionDef",
                            "name": "get",
                            "arg_types": {"self": "JsonObj", "key": "str"},
                            "arg_order": ["self", "key"],
                            "arg_defaults": {},
                            "arg_usage": {"self": "readonly", "key": "readonly"},
                            "return_type": "JsonValue | None",
                            "body": [],
                        }
                    ],
                },
                {
                    "kind": "ClassDef",
                    "name": "JsonValue",
                    "field_types": {"raw": "object"},
                    "body": [],
                },
            ],
        )

        header_text = build_cpp_header_from_east3("pytra.std.json", doc, rel_header_path="std/json.h")

        self.assertIn("struct JsonObj;", header_text)
        self.assertIn("struct JsonValue;", header_text)
        self.assertLess(header_text.index("struct JsonValue;"), header_text.index("struct JsonObj {"))

    def test_cpp_header_gen_preserves_exception_class_inheritance(self) -> None:
        doc = _module_doc(
            "pytra.built_in.error",
            body=[
                {"kind": "ClassDef", "name": "PytraError", "field_types": {"msg": "str"}, "body": []},
                {"kind": "ClassDef", "name": "BaseException", "base": "PytraError", "field_types": {}, "body": []},
                {"kind": "ClassDef", "name": "Exception", "base": "BaseException", "field_types": {}, "body": []},
                {"kind": "ClassDef", "name": "ValueError", "base": "Exception", "field_types": {}, "body": []},
            ],
        )

        header_text = build_cpp_header_from_east3("pytra.built_in.error", doc, rel_header_path="built_in/error.h")

        self.assertIn("struct BaseException : public PytraError {", header_text)
        self.assertIn("struct Exception : public BaseException {", header_text)
        self.assertIn("struct ValueError : public Exception {", header_text)

    def test_cpp_emitter_uses_py_str_slice_for_string_index(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "hex_digit",
                    "arg_types": {"digits": "str", "i": "int64"},
                    "arg_order": ["digits", "i"],
                    "arg_defaults": {},
                    "arg_usage": {"digits": "readonly", "i": "readonly"},
                    "return_type": "str",
                    "body": [
                        {
                            "kind": "Return",
                            "value": {
                                "kind": "Subscript",
                                "value": {"kind": "Name", "id": "digits", "resolved_type": "str"},
                                "slice": {"kind": "Name", "id": "i", "resolved_type": "int64"},
                                "resolved_type": "str",
                            },
                        }
                    ],
                }
            ],
        )

        cpp_code = emit_cpp_module(doc)

        self.assertIn("return py_str_slice(digits, i, (i + int64(1)));", cpp_code)

    def test_cpp_emitter_fails_fast_on_unsupported_expr_kind(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "MysteryExpr",
                    },
                }
            ],
        )

        with self.assertRaisesRegex(RuntimeError, "unsupported_expr_kind"):
            emit_cpp_module(doc)

    def test_go_emitter_fails_fast_on_unsupported_expr_kind(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "MysteryExpr",
                    },
                }
            ],
        )

        with self.assertRaisesRegex(RuntimeError, "unsupported_expr_kind"):
            emit_go_module(doc)

    def test_cpp_emitter_fails_fast_on_unknown_builtin_without_symbol(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "lowered_kind": "BuiltinCall",
                        "args": [],
                        "func": {"kind": "Constant", "value": None},
                    },
                }
            ],
        )

        with self.assertRaisesRegex(RuntimeError, "unknown_builtin"):
            emit_cpp_module(doc)

    def test_cpp_emitter_fails_fast_on_unmapped_dotted_runtime_call(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "lowered_kind": "BuiltinCall",
                        "runtime_call": "pkg.helper",
                        "args": [],
                        "func": {"kind": "Name", "id": "helper"},
                    },
                }
            ],
        )

        with self.assertRaisesRegex(RuntimeError, "unmapped_runtime_call"):
            emit_cpp_module(doc)

    def test_cpp_emitter_fails_fast_on_unsupported_for_shape(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "ForCore",
                    "body": [],
                }
            ],
        )

        with self.assertRaisesRegex(RuntimeError, "unsupported_for"):
            emit_cpp_module(doc)

    def test_cpp_emitter_fails_fast_on_unknown_statement_kind(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "For",
                    "body": [],
                }
            ],
        )

        with self.assertRaisesRegex(RuntimeError, "unsupported_stmt_kind"):
            emit_cpp_module(doc)

    def test_go_emitter_fails_fast_on_unknown_statement_kind(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "For",
                    "body": [],
                }
            ],
        )

        with self.assertRaisesRegex(RuntimeError, "unsupported_stmt_kind"):
            emit_go_module(doc)

    def test_cpp_emitter_fails_fast_on_unsupported_slice_shape(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Subscript",
                        "value": {"kind": "Name", "id": "obj", "resolved_type": "object"},
                        "slice": {
                            "kind": "Slice",
                            "lower": {"kind": "Constant", "value": 0, "resolved_type": "int64"},
                            "upper": {"kind": "Constant", "value": 1, "resolved_type": "int64"},
                        },
                        "resolved_type": "object",
                    },
                }
            ],
        )

        with self.assertRaisesRegex(RuntimeError, "unsupported_slice_shape"):
            emit_cpp_module(doc)

    def test_cpp_emitter_fails_fast_on_unsupported_assign_target(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "Assign",
                    "targets": ["bad-target"],
                    "value": {"kind": "Constant", "value": 1, "resolved_type": "int64"},
                }
            ],
        )

        with self.assertRaisesRegex(RuntimeError, "unsupported_assign_target"):
            emit_cpp_module(doc)


if __name__ == "__main__":
    unittest.main()
