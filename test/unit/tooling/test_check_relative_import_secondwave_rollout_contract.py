import unittest
from pathlib import Path

from toolchain.compiler.relative_import_secondwave_rollout_contract import (
    RELATIVE_IMPORT_LONGTAIL_BACKENDS_V1,
    RELATIVE_IMPORT_SECONDWAVE_BACKENDS_V1,
    RELATIVE_IMPORT_SECONDWAVE_HANDOFF_V1,
    RELATIVE_IMPORT_SECONDWAVE_REPRESENTATIVE_SCENARIOS_V1,
)
from tools.check_relative_import_secondwave_rollout_contract import (
    EXPECTED_HANDOFF,
    EXPECTED_LONGTAIL_BACKENDS,
    EXPECTED_SCENARIOS,
    EXPECTED_SECONDWAVE_BACKENDS,
    validate_relative_import_secondwave_rollout_contract,
)


ROOT = Path(__file__).resolve().parents[3]


class RelativeImportSecondwaveRolloutContractTest(unittest.TestCase):
    def test_validator_accepts_current_contract(self) -> None:
        validate_relative_import_secondwave_rollout_contract()

    def test_backend_groups_are_fixed(self) -> None:
        self.assertEqual(RELATIVE_IMPORT_SECONDWAVE_BACKENDS_V1, EXPECTED_SECONDWAVE_BACKENDS)
        self.assertEqual(RELATIVE_IMPORT_LONGTAIL_BACKENDS_V1, EXPECTED_LONGTAIL_BACKENDS)

    def test_representative_scenarios_are_fixed(self) -> None:
        self.assertEqual(
            RELATIVE_IMPORT_SECONDWAVE_REPRESENTATIVE_SCENARIOS_V1,
            EXPECTED_SCENARIOS,
        )

    def test_handoff_is_fixed(self) -> None:
        self.assertEqual(RELATIVE_IMPORT_SECONDWAVE_HANDOFF_V1, EXPECTED_HANDOFF)

    def test_backend_parity_docs_link_live_secondwave_plan(self) -> None:
        for doc_path in RELATIVE_IMPORT_SECONDWAVE_HANDOFF_V1["backend_parity_docs"]:
            text = (ROOT / doc_path).read_text(encoding="utf-8")
            for plan_path in RELATIVE_IMPORT_SECONDWAVE_HANDOFF_V1["active_plan_paths"]:
                self.assertIn(Path(plan_path).name, text)
            self.assertIn(RELATIVE_IMPORT_SECONDWAVE_HANDOFF_V1["verification_lane"], text)
            self.assertIn(RELATIVE_IMPORT_SECONDWAVE_HANDOFF_V1["fail_closed_lane"], text)


if __name__ == "__main__":
    unittest.main()
