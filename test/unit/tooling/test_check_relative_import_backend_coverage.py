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

    def test_cpp_is_only_build_run_locked_backend(self) -> None:
        locked = [
            row["backend"]
            for row in RELATIVE_IMPORT_BACKEND_COVERAGE_V1
            if row["contract_state"] == "build_run_locked"
        ]
        self.assertEqual(locked, ["cpp"])

    def test_rs_cs_go_java_js_kotlin_lua_nim_php_ruby_scala_swift_ts_are_transpile_smoke_locked(self) -> None:
        locked = [
            row["backend"]
            for row in RELATIVE_IMPORT_BACKEND_COVERAGE_V1
            if row["contract_state"] == "transpile_smoke_locked"
        ]
        self.assertEqual(
            locked,
            ["rs", "cs", "go", "java", "js", "kotlin", "lua", "nim", "php", "ruby", "scala", "swift", "ts"],
        )

    def test_no_backend_is_fail_closed_locked_anymore(self) -> None:
        locked = [
            row["backend"]
            for row in RELATIVE_IMPORT_BACKEND_COVERAGE_V1
            if row["contract_state"] == "fail_closed_locked"
        ]
        self.assertEqual(locked, [])

    def test_jvm_package_bundle_uses_package_project_transpile_evidence_lane(self) -> None:
        rows = [
            row
            for row in RELATIVE_IMPORT_BACKEND_COVERAGE_V1
            if row["backend"] in {"java", "kotlin", "scala"}
        ]
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row["evidence_lane"] == "package_project_transpile" for row in rows))

    def test_native_path_bundle_uses_native_emitter_evidence_lane(self) -> None:
        rows = [
            row
            for row in RELATIVE_IMPORT_BACKEND_COVERAGE_V1
            if row["backend"] in {"go", "nim", "swift"}
        ]
        self.assertEqual(len(rows), 3)
        self.assertTrue(
            all(row["evidence_lane"] == "native_emitter_function_body_transpile" for row in rows)
        )

    def test_lua_uses_native_emitter_function_body_transpile_evidence_lane(self) -> None:
        rows = [
            row
            for row in RELATIVE_IMPORT_BACKEND_COVERAGE_V1
            if row["backend"] == "lua"
        ]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["contract_state"], "transpile_smoke_locked")
        self.assertEqual(rows[0]["evidence_lane"], "native_emitter_function_body_transpile")

    def test_lua_php_ruby_use_native_emitter_function_body_transpile_evidence_lane(self) -> None:
        rows = [
            row
            for row in RELATIVE_IMPORT_BACKEND_COVERAGE_V1
            if row["backend"] in {"lua", "php", "ruby"}
        ]
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row["contract_state"] == "transpile_smoke_locked" for row in rows))
        self.assertTrue(all(row["evidence_lane"] == "native_emitter_function_body_transpile" for row in rows))

    def test_ruby_uses_native_emitter_function_body_transpile_evidence_lane(self) -> None:
        rows = [
            row
            for row in RELATIVE_IMPORT_BACKEND_COVERAGE_V1
            if row["backend"] == "ruby"
        ]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["contract_state"], "transpile_smoke_locked")
        self.assertEqual(rows[0]["evidence_lane"], "native_emitter_function_body_transpile")

    def test_validator_accepts_noncpp_rollout_inventory(self) -> None:
        validate_relative_import_noncpp_rollout()

    def test_noncpp_rollout_covers_all_expected_backends(self) -> None:
        self.assertEqual(
            {row["backend"] for row in RELATIVE_IMPORT_NONCPP_ROLLOUT_V1},
            set(EXPECTED_BACKENDS),
        )

    def test_rollout_inventory_tracks_locked_and_remaining_second_wave(self) -> None:
        first_wave = [
            row for row in RELATIVE_IMPORT_NONCPP_ROLLOUT_V1 if row["rollout_wave"] == "first_wave"
        ]
        self.assertEqual([row["backend"] for row in first_wave], ["rs", "cs"])
        self.assertTrue(
            all(row["next_verification_lane"] == "transpile_smoke_locked" for row in first_wave)
        )
        locked_second_wave = [
            row["backend"]
            for row in RELATIVE_IMPORT_NONCPP_ROLLOUT_V1
            if row["backend"] in {"js", "ts"}
        ]
        self.assertEqual(locked_second_wave, ["js", "ts"])
        native_path_bundle = [
            row["backend"]
            for row in RELATIVE_IMPORT_NONCPP_ROLLOUT_V1
            if row["next_verification_lane"] == "transpile_smoke_locked"
            and row["backend"] in {"go", "nim", "swift"}
        ]
        self.assertEqual(
            native_path_bundle,
            ["go", "nim", "swift"],
        )
        remaining_second_wave = [
            row["backend"]
            for row in RELATIVE_IMPORT_NONCPP_ROLLOUT_V1
            if row["next_verification_lane"] == "transpile_smoke_locked"
            and row["backend"] in {"java", "kotlin", "scala"}
        ]
        self.assertEqual(
            remaining_second_wave,
            ["java", "kotlin", "scala"],
        )
        longtail = [
            row["backend"]
            for row in RELATIVE_IMPORT_NONCPP_ROLLOUT_V1
            if row["rollout_wave"] == "long_tail"
        ]
        self.assertEqual(longtail, ["lua", "php", "ruby"])
        lua_rows = [
            row
            for row in RELATIVE_IMPORT_NONCPP_ROLLOUT_V1
            if row["backend"] == "lua"
        ]
        self.assertEqual(len(lua_rows), 1)
        self.assertEqual(lua_rows[0]["next_verification_lane"], "transpile_smoke_locked")
        php_rows = [
            row
            for row in RELATIVE_IMPORT_NONCPP_ROLLOUT_V1
            if row["backend"] == "php"
        ]
        self.assertEqual(len(php_rows), 1)
        self.assertEqual(php_rows[0]["next_verification_lane"], "transpile_smoke_locked")
        ruby_rows = [
            row
            for row in RELATIVE_IMPORT_NONCPP_ROLLOUT_V1
            if row["backend"] == "ruby"
        ]
        self.assertEqual(len(ruby_rows), 1)
        self.assertEqual(ruby_rows[0]["next_verification_lane"], "transpile_smoke_locked")

    def test_validator_accepts_noncpp_rollout_handoff(self) -> None:
        validate_relative_import_noncpp_rollout_handoff()

    def test_noncpp_rollout_handoff_is_fixed(self) -> None:
        self.assertEqual(
            RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1,
            EXPECTED_NONCPP_ROLLOUT_HANDOFF,
        )

    def test_noncpp_rollout_handoff_tracks_bundle_order(self) -> None:
        self.assertEqual(
            RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1["second_wave_bundle_order"],
            (
                "locked_js_ts_smoke_bundle",
                "native_path_bundle",
                "jvm_package_bundle",
            ),
        )
        self.assertEqual(
            RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1["next_rollout_bundle_backends"],
            (),
        )
        self.assertEqual(
            RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1["followup_rollout_bundle_backends"],
            (),
        )
        self.assertEqual(
            RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1["current_bundle_smoke_locked_backends"],
            ("lua", "php", "ruby"),
        )
        self.assertEqual(
            RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1["current_bundle_fail_closed_locked_backends"],
            (),
        )
        self.assertEqual(
            RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1["current_bundle_contract_state"],
            "transpile_smoke_locked",
        )
        self.assertEqual(
            RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1["current_bundle_evidence_lane"],
            "native_emitter_function_body_transpile",
        )
        self.assertEqual(
            RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1["followup_verification_lane"],
            "none",
        )
        self.assertEqual(
            RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1["next_verification_lane"],
            "none",
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
            self.assertIn(
                RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1["current_bundle_evidence_lane"],
                doc_text,
            )
            self.assertIn(
                RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1["followup_verification_lane"],
                doc_text,
            )
            self.assertIn(
                RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1["followup_rollout_bundle"],
                doc_text,
            )
            for bundle_id in RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1["second_wave_bundle_order"]:
                self.assertIn(bundle_id, doc_text)


if __name__ == "__main__":
    unittest.main()
