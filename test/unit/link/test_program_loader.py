import tempfile
import unittest

from pytra.std import json
from pytra.std.pathlib import Path

from toolchain.link import LINK_INPUT_SCHEMA
from toolchain.link import LINK_OUTPUT_SCHEMA
from toolchain.link import build_linked_program_from_module_map
from toolchain.link import load_linked_output_bundle
from toolchain.link import load_link_input_doc
from toolchain.link import load_link_output_doc
from toolchain.link import load_linked_program
from toolchain.link import save_manifest_doc
from toolchain.link import validate_link_input_doc
from toolchain.link import validate_link_output_doc
from toolchain.link import write_link_input_bundle


def _east3_doc(dispatch_mode: str = "native") -> dict[str, object]:
    return {
        "kind": "Module",
        "east_stage": 3,
        "schema_version": 1,
        "meta": {"dispatch_mode": dispatch_mode},
        "body": [],
    }


class LinkedProgramLoaderTests(unittest.TestCase):
    def test_load_linked_program_sorts_modules_by_module_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a_path = root / "b.east3.json"
            z_path = root / "a.east3.json"
            a_path.write_text(json.dumps(_east3_doc(), ensure_ascii=False), encoding="utf-8")
            z_path.write_text(json.dumps(_east3_doc(), ensure_ascii=False), encoding="utf-8")
            manifest_path = root / "link-input.json"
            save_manifest_doc(
                manifest_path,
                {
                    "schema": LINK_INPUT_SCHEMA,
                    "target": "cpp",
                    "dispatch_mode": "native",
                    "entry_modules": ["app.z"],
                    "modules": [
                        {
                            "module_id": "app.z",
                            "path": "a.east3.json",
                            "source_path": "sample/py/z.py",
                            "is_entry": True,
                        },
                        {
                            "module_id": "app.a",
                            "path": "b.east3.json",
                            "source_path": "sample/py/a.py",
                            "is_entry": False,
                        },
                    ],
                },
            )

            program = load_linked_program(manifest_path)
            self.assertEqual(program.entry_modules, ("app.z",))
            self.assertEqual([item.module_id for item in program.modules], ["app.a", "app.z"])
            self.assertEqual(str(program.modules[0].path), str(program.modules[0].path.resolve()))
            self.assertEqual(str(program.modules[0].artifact_path), str(program.modules[0].artifact_path.resolve()))

    def test_load_linked_program_rejects_dispatch_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad_path = root / "bad.east3.json"
            bad_path.write_text(json.dumps(_east3_doc(dispatch_mode="type_id"), ensure_ascii=False), encoding="utf-8")
            manifest_path = root / "link-input.json"
            save_manifest_doc(
                manifest_path,
                {
                    "schema": LINK_INPUT_SCHEMA,
                    "target": "cpp",
                    "dispatch_mode": "native",
                    "entry_modules": ["app.bad"],
                    "modules": [
                        {
                            "module_id": "app.bad",
                            "path": "bad.east3.json",
                            "source_path": "sample/py/bad.py",
                            "is_entry": True,
                        }
                    ],
                },
            )

            with self.assertRaisesRegex(RuntimeError, "dispatch_mode mismatch"):
                load_linked_program(manifest_path)

    def test_load_link_input_doc_rejects_missing_entry_module(self) -> None:
        bad_doc = {
            "schema": LINK_INPUT_SCHEMA,
            "target": "cpp",
            "dispatch_mode": "native",
            "entry_modules": ["app.main"],
            "modules": [
                {
                    "module_id": "app.other",
                    "path": "other.east3.json",
                    "source_path": "sample/py/other.py",
                    "is_entry": False,
                }
            ],
        }
        with self.assertRaisesRegex(RuntimeError, "missing entry module"):
            validate_link_input_doc(bad_doc)

    def test_load_link_output_doc_validates_required_global_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = root / "link-output.json"
            save_manifest_doc(
                manifest_path,
                {
                    "schema": LINK_OUTPUT_SCHEMA,
                    "target": "cpp",
                    "dispatch_mode": "native",
                    "entry_modules": [],
                    "modules": [],
                    "global": {
                        "type_id_table": {},
                        "call_graph": {},
                        "sccs": [],
                        "non_escape_summary": {},
                        "container_ownership_hints_v1": {},
                    },
                    "diagnostics": {"warnings": [], "errors": []},
                },
            )
            doc = load_link_output_doc(manifest_path)
            self.assertEqual(doc["schema"], LINK_OUTPUT_SCHEMA)
            self.assertEqual([item.module_id for item in doc["modules"]], [])

    def test_load_link_output_doc_normalizes_and_sorts_module_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = root / "link-output.json"
            save_manifest_doc(
                manifest_path,
                {
                    "schema": LINK_OUTPUT_SCHEMA,
                    "target": "cpp",
                    "dispatch_mode": "native",
                    "entry_modules": ["app.main"],
                    "modules": [
                        {
                            "module_id": "app.main",
                            "input": "raw/app/main.east3.json",
                            "output": "linked/app/main.east3.json",
                            "source_path": "/tmp/main.py",
                            "is_entry": True,
                        },
                        {
                            "module_id": "app.helper",
                            "input": "raw/app/helper.east3.json",
                            "output": "linked/app/helper.east3.json",
                            "source_path": "/tmp/helper.py",
                            "is_entry": False,
                        },
                    ],
                    "global": {
                        "type_id_table": {},
                        "call_graph": {},
                        "sccs": [],
                        "non_escape_summary": {},
                        "container_ownership_hints_v1": {},
                    },
                    "diagnostics": {"warnings": [], "errors": []},
                },
            )
            doc = load_link_output_doc(manifest_path)
            self.assertEqual([item.module_id for item in doc["modules"]], ["app.helper", "app.main"])

    def test_load_link_output_doc_rejects_missing_linked_entry_module(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "missing link-output entry module"):
            validate_link_output_doc(
                {
                    "schema": LINK_OUTPUT_SCHEMA,
                    "target": "cpp",
                    "dispatch_mode": "native",
                    "entry_modules": ["app.main"],
                    "modules": [
                        {
                            "module_id": "app.other",
                            "input": "raw/app/other.east3.json",
                            "output": "linked/app/other.east3.json",
                            "source_path": "sample/py/other.py",
                            "is_entry": False,
                        }
                    ],
                    "global": {
                        "type_id_table": {},
                        "call_graph": {},
                        "sccs": [],
                        "non_escape_summary": {},
                        "container_ownership_hints_v1": {},
                    },
                    "diagnostics": {"warnings": [], "errors": []},
                }
            )

    def test_load_linked_program_rejects_linked_meta_in_raw_module(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad_doc = _east3_doc()
            bad_doc["meta"] = {
                "dispatch_mode": "native",
                "linked_program_v1": {"program_id": "p"},
            }
            mod_path = root / "bad.east3.json"
            mod_path.write_text(json.dumps(bad_doc, ensure_ascii=False), encoding="utf-8")
            manifest_path = root / "link-input.json"
            save_manifest_doc(
                manifest_path,
                {
                    "schema": LINK_INPUT_SCHEMA,
                    "target": "cpp",
                    "dispatch_mode": "native",
                    "entry_modules": ["app.bad"],
                    "modules": [
                        {
                            "module_id": "app.bad",
                            "path": "bad.east3.json",
                            "source_path": "sample/py/bad.py",
                            "is_entry": True,
                        }
                    ],
                },
            )
            with self.assertRaisesRegex(RuntimeError, "linked_program_v1"):
                load_linked_program(manifest_path)

    def test_build_linked_program_from_module_map_marks_entry_and_orders_modules(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main_py = root / "main.py"
            helper_py = root / "helper.py"
            program = build_linked_program_from_module_map(
                main_py,
                {
                    str(helper_py): {
                        "kind": "Module",
                        "east_stage": 3,
                        "schema_version": 1,
                        "meta": {"dispatch_mode": "native", "module_id": "app.helper"},
                        "body": [],
                    },
                    str(main_py): {
                        "kind": "Module",
                        "east_stage": 3,
                        "schema_version": 1,
                        "meta": {"dispatch_mode": "native", "module_id": "app.main"},
                        "body": [],
                    },
                },
                target="rs",
                dispatch_mode="native",
                options={"east3_opt_level": "1"},
            )

            self.assertIsNone(program.manifest_path)
            self.assertEqual(program.schema, LINK_INPUT_SCHEMA)
            self.assertEqual(program.entry_modules, ("app.main",))
            self.assertEqual([item.module_id for item in program.modules], ["app.helper", "app.main"])
            self.assertFalse(program.modules[0].is_entry)
            self.assertTrue(program.modules[1].is_entry)
            self.assertIsNone(program.modules[0].artifact_path)
            self.assertEqual(program.options["east3_opt_level"], "1")

    def test_build_linked_program_from_module_map_requires_entry_module(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main_py = root / "main.py"
            helper_py = root / "helper.py"
            with self.assertRaisesRegex(RuntimeError, "entry module not found"):
                build_linked_program_from_module_map(
                    main_py,
                    {
                        str(helper_py): {
                            "kind": "Module",
                            "east_stage": 3,
                            "schema_version": 1,
                            "meta": {"dispatch_mode": "native", "module_id": "app.helper"},
                            "body": [],
                        }
                    },
                    target="rs",
                    dispatch_mode="native",
                )

    def test_in_memory_program_rejects_link_input_serialization_without_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main_py = root / "main.py"
            program = build_linked_program_from_module_map(
                main_py,
                {
                    str(main_py): {
                        "kind": "Module",
                        "east_stage": 3,
                        "schema_version": 1,
                        "meta": {"dispatch_mode": "native", "module_id": "app.main"},
                        "body": [],
                    }
                },
                target="rs",
                dispatch_mode="native",
            )
            with self.assertRaisesRegex(RuntimeError, "manifest_path"):
                program.to_link_input_dict()

    def test_write_link_input_bundle_materializes_sorted_raw_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main_py = root / "main.py"
            helper_py = root / "helper.py"
            program = build_linked_program_from_module_map(
                main_py,
                {
                    str(main_py): {
                        "kind": "Module",
                        "east_stage": 3,
                        "schema_version": 1,
                        "meta": {"dispatch_mode": "native", "module_id": "app.main"},
                        "body": [],
                    },
                    str(helper_py): {
                        "kind": "Module",
                        "east_stage": 3,
                        "schema_version": 1,
                        "meta": {"dispatch_mode": "native", "module_id": "app.helper"},
                        "body": [],
                    },
                },
                target="cpp",
                dispatch_mode="native",
                options={"east3_opt_level": "1"},
            )
            dump_dir = root / "dump"
            manifest_path, raw_paths = write_link_input_bundle(dump_dir, program)
            manifest_doc = load_link_input_doc(manifest_path)

            self.assertEqual(
                [item.path for item in manifest_doc["modules"]],
                ["raw/app/helper.east3.json", "raw/app/main.east3.json"],
            )
            self.assertEqual(
                [str(item).replace(str(dump_dir) + "/", "") for item in raw_paths],
                ["raw/app/helper.east3.json", "raw/app/main.east3.json"],
            )

    def test_load_linked_output_bundle_sorts_modules_and_tracks_artifact_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            linked_dir = root / "linked"
            linked_dir.mkdir(parents=True, exist_ok=True)
            helper_path = linked_dir / "app" / "helper.east3.json"
            helper_path.parent.mkdir(parents=True, exist_ok=True)
            main_path = linked_dir / "app" / "main.east3.json"
            helper_doc = _east3_doc()
            helper_doc["meta"] = {
                "dispatch_mode": "native",
                "module_id": "app.helper",
                "linked_program_v1": {
                    "program_id": "app.main",
                    "module_id": "app.helper",
                    "entry_modules": ["app.main"],
                    "type_id_resolved_v1": {},
                    "non_escape_summary": {},
                    "container_ownership_hints_v1": {},
                },
            }
            main_doc = _east3_doc()
            main_doc["meta"] = {
                "dispatch_mode": "native",
                "module_id": "app.main",
                "linked_program_v1": {
                    "program_id": "app.main",
                    "module_id": "app.main",
                    "entry_modules": ["app.main"],
                    "type_id_resolved_v1": {},
                    "non_escape_summary": {},
                    "container_ownership_hints_v1": {},
                },
            }
            helper_path.write_text(json.dumps(helper_doc, ensure_ascii=False), encoding="utf-8")
            main_path.write_text(json.dumps(main_doc, ensure_ascii=False), encoding="utf-8")
            manifest_path = root / "link-output.json"
            save_manifest_doc(
                manifest_path,
                {
                    "schema": LINK_OUTPUT_SCHEMA,
                    "target": "cpp",
                    "dispatch_mode": "native",
                    "entry_modules": ["app.main"],
                    "modules": [
                        {
                            "module_id": "app.main",
                            "input": "raw/app/main.east3.json",
                            "output": "linked/app/main.east3.json",
                            "source_path": str(root / "main.py"),
                            "is_entry": True,
                        },
                        {
                            "module_id": "app.helper",
                            "input": "raw/app/helper.east3.json",
                            "output": "linked/app/helper.east3.json",
                            "source_path": str(root / "helper.py"),
                            "is_entry": False,
                        },
                    ],
                    "global": {
                        "type_id_table": {},
                        "call_graph": {},
                        "sccs": [],
                        "non_escape_summary": {},
                        "container_ownership_hints_v1": {},
                    },
                    "diagnostics": {"warnings": [], "errors": []},
                },
            )

            manifest_doc, modules = load_linked_output_bundle(manifest_path)
            self.assertEqual([item.module_id for item in manifest_doc["modules"]], ["app.helper", "app.main"])
            self.assertEqual([item.module_id for item in modules], ["app.helper", "app.main"])
            self.assertEqual(str(modules[0].artifact_path), str(helper_path.resolve()))


if __name__ == "__main__":
    unittest.main()
