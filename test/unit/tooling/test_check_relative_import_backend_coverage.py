import unittest

from toolchain.compiler.relative_import_backend_coverage import (
    RELATIVE_IMPORT_BACKEND_COVERAGE_V1,
    RELATIVE_IMPORT_NONCPP_ROLLOUT_V1,
)
from tools.check_relative_import_backend_coverage import (
    EXPECTED_BACKENDS,
    validate_relative_import_backend_coverage,
    validate_relative_import_noncpp_rollout,
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

    def test_validator_accepts_noncpp_rollout_inventory(self) -> None:
        validate_relative_import_noncpp_rollout()

    def test_noncpp_rollout_covers_all_expected_backends(self) -> None:
        self.assertEqual(
            {row["backend"] for row in RELATIVE_IMPORT_NONCPP_ROLLOUT_V1},
            set(EXPECTED_BACKENDS),
        )

    def test_first_wave_is_rs_and_cs_with_transpile_smoke(self) -> None:
        first_wave = [
            row for row in RELATIVE_IMPORT_NONCPP_ROLLOUT_V1 if row["rollout_wave"] == "first_wave"
        ]
        self.assertEqual([row["backend"] for row in first_wave], ["rs", "cs"])
        self.assertTrue(
            all(row["next_verification_lane"] == "transpile_smoke" for row in first_wave)
        )


if __name__ == "__main__":
    unittest.main()
