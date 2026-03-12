import unittest

from toolchain.compiler.relative_import_jvm_package_bundle_contract import (
    RELATIVE_IMPORT_JVM_PACKAGE_BUNDLE_BACKENDS_V1,
    RELATIVE_IMPORT_JVM_PACKAGE_BUNDLE_HANDOFF_V1,
    RELATIVE_IMPORT_JVM_PACKAGE_BUNDLE_SCENARIOS_V1,
    relative_import_jvm_package_bundle_coverage_rows,
    relative_import_jvm_package_bundle_handoff_snapshot,
)
from tools.check_relative_import_jvm_package_bundle_contract import (
    EXPECTED_BACKENDS,
    EXPECTED_HANDOFF,
    EXPECTED_SCENARIOS,
    validate_relative_import_jvm_package_bundle_contract,
)


class RelativeImportJvmPackageBundleContractTest(unittest.TestCase):
    def test_validator_accepts_contract(self) -> None:
        validate_relative_import_jvm_package_bundle_contract()

    def test_scenarios_are_fixed(self) -> None:
        self.assertEqual(
            {entry["scenario_id"] for entry in RELATIVE_IMPORT_JVM_PACKAGE_BUNDLE_SCENARIOS_V1},
            set(EXPECTED_SCENARIOS),
        )

    def test_backend_order_and_lane_are_fixed(self) -> None:
        self.assertEqual(
            tuple(entry["backend"] for entry in RELATIVE_IMPORT_JVM_PACKAGE_BUNDLE_BACKENDS_V1),
            EXPECTED_BACKENDS,
        )
        self.assertTrue(
            all(
                entry["verification_lane"] == "transpile_smoke_locked"
                for entry in RELATIVE_IMPORT_JVM_PACKAGE_BUNDLE_BACKENDS_V1
            )
        )

    def test_handoff_is_fixed(self) -> None:
        self.assertEqual(RELATIVE_IMPORT_JVM_PACKAGE_BUNDLE_HANDOFF_V1, EXPECTED_HANDOFF)

    def test_current_bundle_coverage_state_is_locked(self) -> None:
        rows = relative_import_jvm_package_bundle_coverage_rows()
        self.assertEqual([row["backend"] for row in rows], list(EXPECTED_BACKENDS))
        self.assertTrue(
            all(row["contract_state"] == EXPECTED_HANDOFF["verification_lane"] for row in rows)
        )
        self.assertTrue(
            all(row["evidence_lane"] == "package_project_transpile" for row in rows)
        )

    def test_handoff_snapshot_matches_backend_coverage_inventory(self) -> None:
        self.assertEqual(
            relative_import_jvm_package_bundle_handoff_snapshot(),
            {
                "next_rollout_backends": EXPECTED_HANDOFF["followup_backends"],
                "next_verification_lane": EXPECTED_HANDOFF["followup_verification_lane"],
                "fail_closed_lane": EXPECTED_HANDOFF["fail_closed_lane"],
            },
        )


if __name__ == "__main__":
    unittest.main()
