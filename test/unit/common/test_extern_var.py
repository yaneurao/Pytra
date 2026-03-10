from __future__ import annotations

import unittest

from toolchain.frontends.extern_var import AmbientExternBinding
from toolchain.frontends.extern_var import collect_ambient_global_extern_bindings
from toolchain.frontends.extern_var import validate_ambient_global_target_support


class AmbientExternVarAdapterTest(unittest.TestCase):
    def test_collect_bindings_returns_typed_carrier(self) -> None:
        east_doc = {
            "meta": {"module_id": "demo.module"},
            "body": [
                {
                    "kind": "AnnAssign",
                    "target": {"kind": "Name", "id": "document"},
                    "meta": {
                        "extern_var_v1": {
                            "schema_version": 1,
                            "symbol": "document",
                            "same_name": 1,
                        }
                    },
                },
                {
                    "kind": "AnnAssign",
                    "target": {"kind": "Name", "id": "doc"},
                    "meta": {
                        "extern_var_v1": {
                            "schema_version": 1,
                            "symbol": "window.document",
                            "same_name": 0,
                        }
                    },
                },
            ],
        }

        self.assertEqual(
            collect_ambient_global_extern_bindings(east_doc),
            [
                AmbientExternBinding(local_name="document", symbol="document"),
                AmbientExternBinding(local_name="doc", symbol="window.document"),
            ],
        )

    def test_validate_formats_typed_binding_names(self) -> None:
        east_doc = {
            "meta": {"module_id": "demo.module"},
            "body": [
                {
                    "kind": "AnnAssign",
                    "target": {"kind": "Name", "id": "document"},
                    "meta": {
                        "extern_var_v1": {
                            "schema_version": 1,
                            "symbol": "document",
                            "same_name": 1,
                        }
                    },
                }
            ],
        }

        with self.assertRaises(RuntimeError) as cm:
            validate_ambient_global_target_support(east_doc, target="rs")

        self.assertIn(
            "ambient extern variables are not supported for target rs: demo.module::document -> document",
            str(cm.exception),
        )

    def test_validate_allows_supported_targets(self) -> None:
        east_doc = {
            "meta": {"module_id": "demo.module"},
            "body": [
                {
                    "kind": "AnnAssign",
                    "target": {"kind": "Name", "id": "document"},
                    "meta": {
                        "extern_var_v1": {
                            "schema_version": 1,
                            "symbol": "document",
                            "same_name": 1,
                        }
                    },
                }
            ],
        }

        self.assertIs(validate_ambient_global_target_support(east_doc, target="js"), east_doc)
        self.assertIs(validate_ambient_global_target_support(east_doc, target="ts"), east_doc)


if __name__ == "__main__":
    unittest.main()
