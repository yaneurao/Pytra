from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from toolchain2.link.linker import link_modules


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
        "source_path": source_path or module_id.replace(".", "/") + ".py",
        "meta": meta,
        "body": body if body is not None else [],
    }


class LinkFunctionSignatureHintTests(unittest.TestCase):
    def test_linker_attaches_imported_function_signature_and_return_hint(self) -> None:
        lib_doc = _module_doc(
            "app.lib",
            body=[
                {
                    "kind": "ClassDef",
                    "name": "Path",
                    "class_storage_hint": "ref",
                    "body": [],
                },
                {
                    "kind": "FunctionDef",
                    "name": "make_path",
                    "arg_order": ["raw"],
                    "arg_types": {"raw": "str"},
                    "return_type": "Path",
                    "body": [],
                },
            ],
        )
        entry_doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "func": {"kind": "Name", "id": "make_path", "resolved_type": "callable"},
                        "args": [{"kind": "Constant", "value": "tmp", "resolved_type": "str"}],
                        "keywords": [],
                        "resolved_type": "unknown",
                    },
                }
            ],
            meta_extra={
                "import_symbols": {
                    "make_path": {"module": "app.lib", "name": "make_path"},
                    "Path": {"module": "app.lib", "name": "Path"},
                },
                "import_bindings": [
                    {
                        "module_id": "app.lib",
                        "export_name": "make_path",
                        "local_name": "make_path",
                        "binding_kind": "symbol",
                    },
                    {
                        "module_id": "app.lib",
                        "export_name": "Path",
                        "local_name": "Path",
                        "binding_kind": "symbol",
                    },
                ],
            },
        )

        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            entry_path = tmpdir / "app.main.east3.json"
            lib_path = tmpdir / "app.lib.east3.json"
            entry_path.write_text(json.dumps(entry_doc), encoding="utf-8")
            lib_path.write_text(json.dumps(lib_doc), encoding="utf-8")
            result = link_modules([str(entry_path), str(lib_path)], target="rs", dispatch_mode="native")

        linked_entry = next(m.east_doc for m in result.linked_modules if m.module_id == "app.main")
        body = linked_entry.get("body", [])
        assert isinstance(body, list)
        expr = body[0]
        assert isinstance(expr, dict)
        call = expr.get("value")
        assert isinstance(call, dict)
        self.assertEqual(call.get("resolved_type"), "Path")
        self.assertEqual(call.get("resolved_storage_hint"), "ref")
        fn_sig = call.get("function_signature_v1")
        self.assertIsInstance(fn_sig, dict)
        self.assertEqual(fn_sig.get("name"), "make_path")
        self.assertEqual(fn_sig.get("return_type"), "Path")


if __name__ == "__main__":
    unittest.main()
