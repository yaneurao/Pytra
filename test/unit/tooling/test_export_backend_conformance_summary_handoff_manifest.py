from __future__ import annotations

import io
import json
import unittest
from unittest.mock import patch

from src.toolchain.compiler import backend_conformance_summary_handoff_contract as contract_mod
from tools import export_backend_conformance_summary_handoff_manifest as export_mod


class ExportBackendConformanceSummaryHandoffManifestTest(unittest.TestCase):
    def test_main_emits_current_summary_handoff_manifest(self) -> None:
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            rc = export_mod.main()
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(buf.getvalue()), contract_mod.build_backend_conformance_summary_handoff_manifest())


if __name__ == "__main__":
    unittest.main()
