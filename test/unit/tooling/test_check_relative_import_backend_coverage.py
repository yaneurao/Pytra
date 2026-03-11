import unittest

from src.toolchain.compiler.relative_import_backend_coverage import (
    RELATIVE_IMPORT_BACKEND_COVERAGE_V1,
)
from tools.check_relative_import_backend_coverage import (
    EXPECTED_BACKENDS,
    validate_relative_import_backend_coverage,
)


class RelativeImportBackendCoverageTest(unittest.TestCase):
    def test_validator_accepts_current_inventory(self) -> None:
        validate_relative_import_backend_coverage()

    def test_inventory_covers_all_expected_backends(self) -> None:
        self.assertEqual(
            {row["backend"] for row in RELATIVE_IMPORT_BACKEND_COVERAGE_V1},
            set(EXPECTED_BACKENDS),
        )

    def test_cpp_is_only_locked_backend(self) -> None:
        locked = [
            row["backend"]
            for row in RELATIVE_IMPORT_BACKEND_COVERAGE_V1
            if row["contract_state"] == "build_run_locked"
        ]
        self.assertEqual(locked, ["cpp"])


if __name__ == "__main__":
    unittest.main()
