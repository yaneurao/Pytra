import unittest

from toolchain.compiler.relative_import_longtail_support_contract import (
    RELATIVE_IMPORT_LONGTAIL_SUPPORT_BACKENDS_V1,
    RELATIVE_IMPORT_LONGTAIL_SUPPORT_HANDOFF_V1,
    RELATIVE_IMPORT_LONGTAIL_SUPPORT_SCENARIOS_V1,
    relative_import_longtail_support_archive_snapshot,
    relative_import_longtail_support_coverage_rows,
    relative_import_longtail_support_handoff_snapshot,
)
from tools.check_relative_import_longtail_support_contract import (
    EXPECTED_BACKENDS,
    EXPECTED_FOCUSED_VERIFICATION_LANES,
    EXPECTED_HANDOFF,
    EXPECTED_SCENARIOS,
    validate_relative_import_longtail_support_contract,
)


class RelativeImportLongtailSupportContractTest(unittest.TestCase):
    def test_validator_accepts_contract(self) -> None:
        validate_relative_import_longtail_support_contract()

    def test_scenarios_are_fixed(self) -> None:
        self.assertEqual(
            {entry["scenario_id"] for entry in RELATIVE_IMPORT_LONGTAIL_SUPPORT_SCENARIOS_V1},
            set(EXPECTED_SCENARIOS),
        )

    def test_backend_order_and_current_lane_are_fixed(self) -> None:
        self.assertEqual(
            tuple(entry["backend"] for entry in RELATIVE_IMPORT_LONGTAIL_SUPPORT_BACKENDS_V1),
            EXPECTED_BACKENDS,
        )
        self.assertEqual(
            RELATIVE_IMPORT_LONGTAIL_SUPPORT_BACKENDS_V1[0]["current_contract_state"],
            "transpile_smoke_locked",
        )
        self.assertEqual(
            RELATIVE_IMPORT_LONGTAIL_SUPPORT_BACKENDS_V1[0]["current_evidence_lane"],
            "native_emitter_function_body_transpile",
        )
        self.assertEqual(
            RELATIVE_IMPORT_LONGTAIL_SUPPORT_BACKENDS_V1[1]["current_contract_state"],
            "transpile_smoke_locked",
        )
        self.assertEqual(
            RELATIVE_IMPORT_LONGTAIL_SUPPORT_BACKENDS_V1[1]["current_evidence_lane"],
            "native_emitter_function_body_transpile",
        )
        self.assertTrue(
            all(
                entry["current_contract_state"] == "fail_closed_locked"
                and entry["current_evidence_lane"] == "backend_native_fail_closed"
                for entry in RELATIVE_IMPORT_LONGTAIL_SUPPORT_BACKENDS_V1[2:]
            )
        )
        self.assertEqual(
            tuple(
                entry["focused_verification_lane"]
                for entry in RELATIVE_IMPORT_LONGTAIL_SUPPORT_BACKENDS_V1
            ),
            EXPECTED_FOCUSED_VERIFICATION_LANES,
        )

    def test_handoff_is_fixed(self) -> None:
        self.assertEqual(RELATIVE_IMPORT_LONGTAIL_SUPPORT_HANDOFF_V1, EXPECTED_HANDOFF)

    def test_current_bundle_coverage_state_is_mixed_rollout_locked(self) -> None:
        rows = relative_import_longtail_support_coverage_rows()
        self.assertEqual([row["backend"] for row in rows], list(EXPECTED_BACKENDS))
        self.assertEqual(rows[0]["contract_state"], "transpile_smoke_locked")
        self.assertEqual(rows[0]["evidence_lane"], "native_emitter_function_body_transpile")
        self.assertEqual(rows[1]["contract_state"], "transpile_smoke_locked")
        self.assertEqual(rows[1]["evidence_lane"], "native_emitter_function_body_transpile")
        self.assertTrue(
            all(row["contract_state"] == "fail_closed_locked" for row in rows[2:])
        )
        self.assertTrue(
            all(row["evidence_lane"] == "backend_native_fail_closed" for row in rows[2:])
        )

    def test_archive_snapshot_matches_archived_bundle_handoff(self) -> None:
        self.assertEqual(
            relative_import_longtail_support_archive_snapshot(),
            {
                "prereq_bundle_id": EXPECTED_HANDOFF["prereq_bundle_id"],
                "prereq_current_contract_state": "fail_closed_locked",
                "prereq_current_evidence_lane": "backend_native_fail_closed",
                "prereq_followup_bundle_id": EXPECTED_HANDOFF["bundle_id"],
                "prereq_followup_verification_lane": EXPECTED_HANDOFF["verification_lane"],
            },
        )

    def test_handoff_snapshot_matches_backend_coverage_inventory(self) -> None:
        self.assertEqual(
            relative_import_longtail_support_handoff_snapshot(),
            {
                "next_rollout_backends": EXPECTED_HANDOFF["remaining_rollout_backends"],
                "next_verification_lane": EXPECTED_HANDOFF["verification_lane"],
                "current_bundle_contract_state": EXPECTED_HANDOFF["current_contract_state"],
                "current_bundle_evidence_lane": EXPECTED_HANDOFF["current_evidence_lane"],
                "current_bundle_smoke_locked_backends": ("lua", "php"),
                "current_bundle_fail_closed_locked_backends": ("ruby",),
                "focused_verification_lanes": EXPECTED_FOCUSED_VERIFICATION_LANES,
            },
        )


if __name__ == "__main__":
    unittest.main()
