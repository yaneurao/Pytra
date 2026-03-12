from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.toolchain.compiler.backend_registry import get_backend_spec_typed as host_get_backend_spec_typed
from src.toolchain.compiler.backend_registry import list_backend_targets as host_list_backend_targets
from src.toolchain.compiler.backend_registry_metadata import backend_target_order
from src.toolchain.compiler.backend_registry_metadata import get_backend_metadata
from src.toolchain.compiler.backend_registry_metadata import get_program_writer_ref
from src.toolchain.compiler.backend_registry_metadata import get_runtime_hook_descriptor
from src.toolchain.compiler.backend_registry_static import get_backend_spec_typed as static_get_backend_spec_typed
from src.toolchain.compiler.backend_registry_static import list_backend_targets as static_list_backend_targets


class BackendRegistryMetadataTest(unittest.TestCase):
    def test_target_order_is_shared_between_host_and_static_registries(self) -> None:
        shared_order = list(backend_target_order())
        self.assertEqual(host_list_backend_targets(), shared_order)
        self.assertEqual(static_list_backend_targets(), shared_order)

    def test_backend_specs_share_target_and_extension_metadata(self) -> None:
        for target in backend_target_order():
            metadata = get_backend_metadata(target)
            host_spec = host_get_backend_spec_typed(target)
            static_spec = static_get_backend_spec_typed(target)
            self.assertEqual(host_spec.carrier.target_lang, metadata["target_lang"])
            self.assertEqual(static_spec.carrier.target_lang, metadata["target_lang"])
            self.assertEqual(host_spec.carrier.extension, metadata["extension"])
            self.assertEqual(static_spec.carrier.extension, metadata["extension"])

    def test_cpp_options_and_schema_come_from_shared_metadata(self) -> None:
        metadata = get_backend_metadata("cpp")
        host_spec = host_get_backend_spec_typed("cpp")
        static_spec = static_get_backend_spec_typed("cpp")
        self.assertEqual(host_spec.carrier.default_options_by_layer, metadata["default_options"])
        self.assertEqual(static_spec.carrier.default_options_by_layer, metadata["default_options"])
        self.assertEqual(host_spec.carrier.option_schema_by_layer, metadata["option_schema"])
        self.assertEqual(static_spec.carrier.option_schema_by_layer, metadata["option_schema"])

    def test_metadata_rejects_unknown_runtime_hook_key(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "unsupported runtime hook key: missing-hook"):
            get_runtime_hook_descriptor("missing-hook")

    def test_metadata_rejects_unknown_program_writer_key(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "unsupported program writer key: missing-writer"):
            get_program_writer_ref("missing-writer")

    def test_php_runtime_hook_ships_generated_pathlib(self) -> None:
        desc = get_runtime_hook_descriptor("php")
        self.assertEqual(desc.get("kind"), "php_runtime")
        files = desc.get("files")
        self.assertIsInstance(files, list)
        self.assertIn(("generated/std/pathlib.php", "std/pathlib.php"), files)
