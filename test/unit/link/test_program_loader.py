import tempfile
import unittest

from pytra.std import json
from pytra.std.pathlib import Path

from toolchain.link import LINK_INPUT_SCHEMA
from toolchain.link import LINK_OUTPUT_SCHEMA
from toolchain.link import load_link_input_doc
from toolchain.link import load_link_output_doc
from toolchain.link import load_linked_program
from toolchain.link import save_manifest_doc
from toolchain.link import validate_link_input_doc


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
                    "entry_modules": ["app.main"],
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


if __name__ == "__main__":
    unittest.main()
