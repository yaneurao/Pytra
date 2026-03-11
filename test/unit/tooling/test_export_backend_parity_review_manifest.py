from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout

from src.toolchain.compiler.backend_parity_review_contract import (
    build_backend_parity_review_manifest,
)
from tools import export_backend_parity_review_manifest as export_mod


class ExportBackendParityReviewManifestTest(unittest.TestCase):
    def test_export_matches_manifest(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            self.assertEqual(export_mod.main(), 0)
        self.assertEqual(json.loads(buffer.getvalue()), build_backend_parity_review_manifest())


if __name__ == "__main__":
    unittest.main()
