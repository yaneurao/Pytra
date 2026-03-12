import unittest

from toolchain.compiler.relative_import_jvm_package_bundle_contract import (
    RELATIVE_IMPORT_JVM_PACKAGE_BUNDLE_BACKENDS_V1,
    RELATIVE_IMPORT_JVM_PACKAGE_BUNDLE_HANDOFF_V1,
    RELATIVE_IMPORT_JVM_PACKAGE_BUNDLE_SCENARIOS_V1,
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
                entry["verification_lane"] == "jvm_package_bundle_rollout"
                for entry in RELATIVE_IMPORT_JVM_PACKAGE_BUNDLE_BACKENDS_V1
            )
        )

    def test_handoff_is_fixed(self) -> None:
        self.assertEqual(RELATIVE_IMPORT_JVM_PACKAGE_BUNDLE_HANDOFF_V1, EXPECTED_HANDOFF)


if __name__ == "__main__":
    unittest.main()
