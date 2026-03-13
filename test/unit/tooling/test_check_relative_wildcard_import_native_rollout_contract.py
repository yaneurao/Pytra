import unittest

from toolchain.compiler.relative_wildcard_import_native_rollout_contract import (
    RELATIVE_WILDCARD_IMPORT_NATIVE_BACKENDS_V1,
    RELATIVE_WILDCARD_IMPORT_NATIVE_CPP_BASELINE_V1,
    RELATIVE_WILDCARD_IMPORT_NATIVE_HANDOFF_V1,
)
from tools.check_relative_wildcard_import_native_rollout_contract import (
    EXPECTED_BACKENDS,
    EXPECTED_BUNDLE_ORDER,
    EXPECTED_FOCUSED_VERIFICATION_LANES,
    validate_relative_wildcard_import_native_rollout_contract,
)


class RelativeWildcardImportNativeRolloutContractTest(unittest.TestCase):
    def test_validator_accepts_current_inventory(self) -> None:
        validate_relative_wildcard_import_native_rollout_contract()

    def test_cpp_baseline_stays_build_run_locked(self) -> None:
        self.assertEqual(
            RELATIVE_WILDCARD_IMPORT_NATIVE_CPP_BASELINE_V1,
            {
                "backend": "cpp",
                "current_contract_state": "build_run_locked",
                "current_evidence_lane": "multi_file_build_run",
                "representative_import_form": "from .helper import *",
            },
        )

    def test_native_backend_inventory_is_exact(self) -> None:
        self.assertEqual(
            tuple(row["backend"] for row in RELATIVE_WILDCARD_IMPORT_NATIVE_BACKENDS_V1),
            EXPECTED_BACKENDS,
        )

    def test_all_native_backends_start_fail_closed(self) -> None:
        state_by_backend = {
            row["backend"]: row["current_contract_state"]
            for row in RELATIVE_WILDCARD_IMPORT_NATIVE_BACKENDS_V1
        }
        self.assertEqual(
            state_by_backend,
            {
                "go": "transpile_smoke_locked",
                "java": "transpile_smoke_locked",
                "kotlin": "transpile_smoke_locked",
                "lua": "transpile_smoke_locked",
                "nim": "transpile_smoke_locked",
                "php": "transpile_smoke_locked",
                "ruby": "transpile_smoke_locked",
                "scala": "transpile_smoke_locked",
                "swift": "transpile_smoke_locked",
            },
        )
        self.assertTrue(
            all(
                row["fail_closed_lane"] == "backend_specific_fail_closed"
                for row in RELATIVE_WILDCARD_IMPORT_NATIVE_BACKENDS_V1
            )
        )

    def test_bundle_order_is_fixed(self) -> None:
        self.assertEqual(
            RELATIVE_WILDCARD_IMPORT_NATIVE_HANDOFF_V1["bundle_order"],
            EXPECTED_BUNDLE_ORDER,
        )

    def test_current_bundle_state_tracks_native_path_rollout(self) -> None:
        self.assertEqual(
            RELATIVE_WILDCARD_IMPORT_NATIVE_HANDOFF_V1["current_bundle_id"],
            "longtail_native_bundle",
        )
        self.assertEqual(
            RELATIVE_WILDCARD_IMPORT_NATIVE_HANDOFF_V1["current_bundle_state"],
            "transpile_smoke_locked",
        )
        self.assertEqual(
            RELATIVE_WILDCARD_IMPORT_NATIVE_HANDOFF_V1["current_contract_state"],
            "transpile_smoke_locked",
        )

    def test_archived_plan_paths_are_fixed(self) -> None:
        self.assertEqual(
            tuple(RELATIVE_WILDCARD_IMPORT_NATIVE_HANDOFF_V1["active_plan_paths"]),
            (
                "docs/ja/plans/archive/20260314-p0-relative-wildcard-import-native-rollout.md",
                "docs/en/plans/archive/20260314-p0-relative-wildcard-import-native-rollout.md",
            ),
        )

    def test_parity_doc_handoff_is_fixed(self) -> None:
        self.assertEqual(
            RELATIVE_WILDCARD_IMPORT_NATIVE_HANDOFF_V1["backend_parity_docs"],
            (
                "docs/ja/language/backend-parity-matrix.md",
                "docs/en/language/backend-parity-matrix.md",
            ),
        )
        self.assertEqual(
            RELATIVE_WILDCARD_IMPORT_NATIVE_HANDOFF_V1["focused_verification_lanes"],
            EXPECTED_FOCUSED_VERIFICATION_LANES,
        )


if __name__ == "__main__":
    unittest.main()
