import unittest

from toolchain.compiler.relative_import_ruby_support_contract import (
    RELATIVE_IMPORT_RUBY_SUPPORT_BACKEND_V1,
    RELATIVE_IMPORT_RUBY_SUPPORT_HANDOFF_V1,
    RELATIVE_IMPORT_RUBY_SUPPORT_SCENARIOS_V1,
    RELATIVE_IMPORT_RUBY_SUPPORT_SMOKE_V1,
    relative_import_ruby_support_parent_backend_snapshot,
)
from tools.check_relative_import_ruby_support_contract import (
    EXPECTED_BACKEND,
    EXPECTED_HANDOFF,
    EXPECTED_SCENARIOS,
    EXPECTED_SMOKE,
    validate_relative_import_ruby_support_contract,
)


class RelativeImportRubySupportContractTest(unittest.TestCase):
    def test_validator_accepts_contract(self) -> None:
        validate_relative_import_ruby_support_contract()

    def test_scenarios_are_fixed(self) -> None:
        self.assertEqual(
            {entry["scenario_id"] for entry in RELATIVE_IMPORT_RUBY_SUPPORT_SCENARIOS_V1},
            set(EXPECTED_SCENARIOS),
        )

    def test_backend_contract_is_fixed(self) -> None:
        self.assertEqual(RELATIVE_IMPORT_RUBY_SUPPORT_BACKEND_V1, EXPECTED_BACKEND)

    def test_smoke_contract_is_fixed(self) -> None:
        self.assertEqual(RELATIVE_IMPORT_RUBY_SUPPORT_SMOKE_V1, EXPECTED_SMOKE)

    def test_handoff_is_fixed(self) -> None:
        self.assertEqual(RELATIVE_IMPORT_RUBY_SUPPORT_HANDOFF_V1, EXPECTED_HANDOFF)

    def test_parent_backend_snapshot_matches_generic_contract(self) -> None:
        self.assertEqual(
            relative_import_ruby_support_parent_backend_snapshot(),
            {
                "backend": "ruby",
                "scenario_ids": EXPECTED_BACKEND["scenario_ids"],
                "current_contract_state": EXPECTED_BACKEND["current_contract_state"],
                "current_evidence_lane": EXPECTED_BACKEND["current_evidence_lane"],
                "verification_lane": EXPECTED_BACKEND["verification_lane"],
                "fail_closed_lane": EXPECTED_BACKEND["fail_closed_lane"],
            },
        )


if __name__ == "__main__":
    unittest.main()
