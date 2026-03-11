import unittest
from pathlib import Path

from toolchain.compiler.relative_import_backend_coverage import (
    RELATIVE_IMPORT_BACKEND_COVERAGE_V1,
    RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1,
    RELATIVE_IMPORT_NONCPP_ROLLOUT_V1,
)
from tools.check_relative_import_backend_coverage import (
    EXPECTED_NONCPP_ROLLOUT_HANDOFF,
    EXPECTED_BACKENDS,
    validate_relative_import_backend_coverage,
    validate_relative_import_noncpp_rollout_handoff,
    validate_relative_import_noncpp_rollout,
)

ROOT = Path(__file__).resolve().parents[3]


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

    def test_rs_and_cs_are_first_wave_transpile_smoke_locked(self) -> None:
        locked = [
            row["backend"]
            for row in RELATIVE_IMPORT_BACKEND_COVERAGE_V1
            if row["contract_state"] == "transpile_smoke_locked"
        ]
        self.assertEqual(locked, ["rs", "cs"])

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

    def test_validator_accepts_noncpp_rollout_handoff(self) -> None:
        validate_relative_import_noncpp_rollout_handoff()

    def test_noncpp_rollout_handoff_is_fixed(self) -> None:
        self.assertEqual(
            RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1,
            EXPECTED_NONCPP_ROLLOUT_HANDOFF,
        )

    def test_backend_parity_docs_link_live_noncpp_rollout_plan(self) -> None:
        for doc_path in RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1["backend_parity_docs"]:
            doc_text = (ROOT / doc_path).read_text(encoding="utf-8")
            for plan_path in RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1["next_rollout_plan"]:
                self.assertIn(Path(plan_path).name, doc_text)
            self.assertIn(
                RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1["next_verification_lane"],
                doc_text,
            )
            self.assertIn(
                RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1["fail_closed_lane"],
                doc_text,
            )


if __name__ == "__main__":
    unittest.main()
