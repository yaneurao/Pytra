import unittest

from toolchain.compiler.relative_import_firstwave_smoke_contract import (
    RELATIVE_IMPORT_FIRST_WAVE_BACKENDS_V1,
    RELATIVE_IMPORT_FIRST_WAVE_SCENARIOS_V1,
)
from tools.check_relative_import_firstwave_smoke_contract import (
    EXPECTED_BACKENDS,
    EXPECTED_SCENARIOS,
    validate_relative_import_firstwave_smoke_contract,
)


class RelativeImportFirstWaveSmokeContractTest(unittest.TestCase):
    def test_validator_accepts_contract(self) -> None:
        validate_relative_import_firstwave_smoke_contract()

    def test_scenarios_are_fixed(self) -> None:
        self.assertEqual(
            {entry["scenario_id"] for entry in RELATIVE_IMPORT_FIRST_WAVE_SCENARIOS_V1},
            set(EXPECTED_SCENARIOS),
        )

    def test_backend_order_and_lane_are_fixed(self) -> None:
        self.assertEqual(
            tuple(entry["backend"] for entry in RELATIVE_IMPORT_FIRST_WAVE_BACKENDS_V1),
            EXPECTED_BACKENDS,
        )
        self.assertTrue(
            all(entry["verification_lane"] == "transpile_smoke" for entry in RELATIVE_IMPORT_FIRST_WAVE_BACKENDS_V1)
        )


if __name__ == "__main__":
    unittest.main()
