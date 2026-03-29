"""Machine-readable seed inventory for bundle-based backend contract coverage."""

from __future__ import annotations

from typing import Final, TypedDict

from src.toolchain.misc import backend_feature_contract_inventory as feature_inventory_mod


BACKEND_CONTRACT_COVERAGE_TODO_ID: Final[str] = "P2-BACKEND-CONTRACT-COVERAGE-100-01"
BACKEND_CONTRACT_COVERAGE_PLAN_JA: Final[str] = (
    "docs/ja/plans/archive/20260314-p2-backend-contract-coverage-100.md"
)
BACKEND_CONTRACT_COVERAGE_PLAN_EN: Final[str] = (
    "docs/en/plans/archive/20260314-p2-backend-contract-coverage-100.md"
)

COVERAGE_BUNDLE_ORDER: Final[tuple[str, ...]] = (
    "frontend",
    "emit",
    "runtime",
    "import_package",
    "east2x",
    "integration",
)

SUITE_KIND_ORDER: Final[tuple[str, ...]] = (
    "test_unit",
    "test_ir",
    "test_integration",
    "test_transpile",
)

HARNESS_KIND_ORDER: Final[tuple[str, ...]] = (
    "unittest_discover",
    "runtime_parity_cli",
    "checker_cli",
    "native_compile_run",
)

TAXONOMY_HARNESS_KIND_ORDER: Final[tuple[str, ...]] = (
    "frontend_parse_diagnostic",
    "east_document_compare",
    "east3_document_compare",
    "backend_emit_compare",
    "runtime_parity_compare",
    "package_graph_transpile",
    "ir_json_emit_compare",
    "native_compile_run",
)

SUITE_FAMILY_ORDER: Final[tuple[str, ...]] = (
    "unit_common",
    "unit_backends",
    "unit_ir",
    "unit_link",
    "unit_selfhost",
    "unit_tooling",
    "ir_fixture",
    "integration",
    "transpile_artifact",
)

COVERAGE_ONLY_STATUS_ORDER: Final[tuple[str, ...]] = ("coverage_only_representative",)
PROMOTION_CANDIDATE_STATUS_ORDER: Final[tuple[str, ...]] = (
    "support_matrix_promotion_candidate",
)
UNPUBLISHED_FIXTURE_STATUS_ORDER: Final[tuple[str, ...]] = (
    "support_matrix_promotion_candidate",
    "coverage_only_representative",
)
UNPUBLISHED_FIXTURE_TARGET_ORDER: Final[tuple[str, ...]] = (
    "support_matrix",
    "coverage_matrix_only",
)
LIVE_SUITE_ROLE_ORDER: Final[tuple[str, ...]] = ("direct_matrix_input", "supporting_only")

SMOKE_TEST_PATH_BY_BACKEND: Final[dict[str, str]] = {
    "cpp": "tools/unittest/emit/cpp/test_py2cpp_features.py",
    "rs": "tools/unittest/emit/rs/test_py2rs_smoke.py",
    "cs": "tools/unittest/emit/cs/test_py2cs_smoke.py",
    "go": "tools/unittest/emit/go/test_py2go_smoke.py",
    "java": "tools/unittest/emit/java/test_py2java_smoke.py",
    "kt": "tools/unittest/emit/kotlin/test_py2kotlin_smoke.py",
    "scala": "tools/unittest/emit/scala/test_py2scala_smoke.py",
    "swift": "tools/unittest/emit/swift/test_py2swift_smoke.py",
    "nim": "tools/unittest/emit/nim/test_py2nim_smoke.py",
    "js": "tools/unittest/emit/js/test_py2js_smoke.py",
    "ts": "tools/unittest/emit/ts/test_py2ts_smoke.py",
    "lua": "tools/unittest/emit/lua/test_py2lua_smoke.py",
    "rb": "tools/unittest/emit/rb/test_py2rb_smoke.py",
    "php": "tools/unittest/emit/php/test_py2php_smoke.py",
}

CPP_RUNTIME_NEEDLE_BY_FIXTURE_STEM: Final[dict[str, str]] = {
    "property_method_call": "def test_property_method_call_runtime(self) -> None:",
    "list_bool_index": "def test_list_bool_index_runtime(self) -> None:",
}

SUPPORT_MATRIX_FIXTURES: Final[tuple[str, ...]] = tuple(
    sorted(
        {
            row["representative_fixture"]
            for row in feature_inventory_mod.iter_representative_fixture_mapping()
        }
    )
)


class CoverageEvidenceRef(TypedDict):
    relpath: str
    needle: str


class CoverageBundleEntry(TypedDict):
    bundle_id: str
    bundle_kind: str
    suite_kind: str
    harness_kind: str
    source_paths: tuple[str, ...]
    evidence_refs: tuple[CoverageEvidenceRef, ...]
    notes: str


class CoverageBundleTaxonomyEntry(TypedDict):
    bundle_id: str
    source_roots: tuple[str, ...]
    suite_ids: tuple[str, ...]
    harness_kinds: tuple[str, ...]
    notes: str


class LiveSuiteFamilyEntry(TypedDict):
    suite_id: str
    suite_kind: str
    source_roots: tuple[str, ...]
    coverage_role: str
    bundle_candidates: tuple[str, ...]
    notes: str


class CoverageOnlyFixtureBackendEvidence(TypedDict):
    backend: str
    relpath: str
    needle: str


class CoverageOnlyFixtureEntry(TypedDict):
    fixture_stem: str
    fixture_rel: str
    status: str
    backend_evidence: tuple[CoverageOnlyFixtureBackendEvidence, ...]
    notes: str


class PromotionCandidateFixtureEntry(TypedDict):
    fixture_stem: str
    fixture_rel: str
    status: str
    proposed_feature_id: str
    proposed_category: str
    proposed_title: str
    backend_evidence: tuple[CoverageOnlyFixtureBackendEvidence, ...]
    notes: str


class UnpublishedMultiBackendFixtureEntry(TypedDict):
    fixture_rel: str
    fixture_stem: str
    status: str
    target_surface: str
    proposed_feature_id: str
    proposed_category: str
    proposed_title: str
    observed_backends: tuple[str, ...]
    notes: str


def feature_backend_order() -> tuple[str, ...]:
    return tuple(SMOKE_TEST_PATH_BY_BACKEND)


COVERAGE_BUNDLE_TAXONOMY_V1: Final[tuple[CoverageBundleTaxonomyEntry, ...]] = (
    {
        "bundle_id": "frontend",
        "source_roots": ("tools/unittest/common", "tools/unittest/ir"),
        "suite_ids": ("unit_common", "unit_ir"),
        "harness_kinds": (
            "frontend_parse_diagnostic",
            "east_document_compare",
            "east3_document_compare",
        ),
        "notes": "Parse/EAST/EAST3-lowering ownership for contract coverage.",
    },
    {
        "bundle_id": "emit",
        "source_roots": ("test/unit/backends", "tools/unittest/common/test_py2x_smoke_common.py"),
        "suite_ids": ("unit_backends", "unit_common"),
        "harness_kinds": ("backend_emit_compare",),
        "notes": "Backend emitter smoke and compare coverage.",
    },
    {
        "bundle_id": "runtime",
        "source_roots": ("work/transpile", "tools/runtime_parity_check.py"),
        "suite_ids": ("transpile_artifact",),
        "harness_kinds": ("runtime_parity_compare",),
        "notes": "Representative runtime parity and staged artifact coverage.",
    },
    {
        "bundle_id": "import_package",
        "source_roots": (
            "tools/unittest/emit/relative_import_native_path_smoke_support.py",
            "tools/unittest/emit/relative_import_jvm_package_smoke_support.py",
            "tools/check_relative_import_backend_coverage.py",
        ),
        "suite_ids": ("unit_backends", "unit_common"),
        "harness_kinds": ("package_graph_transpile",),
        "notes": "Relative import, package layout, and module-graph coverage.",
    },
    {
        "bundle_id": "east2x",
        "source_roots": ("test/ir", "tools/check_east2x_smoke.py"),
        "suite_ids": ("ir_fixture",),
        "harness_kinds": ("ir_json_emit_compare",),
        "notes": "Frontend-independent EAST3(JSON) to backend smoke coverage.",
    },
    {
        "bundle_id": "integration",
        "source_roots": ("test/integration",),
        "suite_ids": ("integration",),
        "harness_kinds": ("native_compile_run",),
        "notes": "Backend-specific execution/runtime integration coverage.",
    },
)


LIVE_SUITE_FAMILY_INVENTORY_V1: Final[tuple[LiveSuiteFamilyEntry, ...]] = (
    {
        "suite_id": "unit_common",
        "suite_kind": "test_unit",
        "source_roots": ("tools/unittest/common",),
        "coverage_role": "direct_matrix_input",
        "bundle_candidates": ("frontend", "emit", "import_package"),
        "notes": "Shared frontend/backend smoke helpers and CLI-facing tests.",
    },
    {
        "suite_id": "unit_backends",
        "suite_kind": "test_unit",
        "source_roots": ("test/unit/backends",),
        "coverage_role": "direct_matrix_input",
        "bundle_candidates": ("emit", "runtime", "import_package"),
        "notes": "Representative backend smoke and backend-specific checks.",
    },
    {
        "suite_id": "unit_ir",
        "suite_kind": "test_unit",
        "source_roots": ("tools/unittest/ir",),
        "coverage_role": "direct_matrix_input",
        "bundle_candidates": ("frontend",),
        "notes": "Parser/EAST/EAST3-lowering contracts.",
    },
    {
        "suite_id": "unit_link",
        "suite_kind": "test_unit",
        "source_roots": ("test/unit/link",),
        "coverage_role": "supporting_only",
        "bundle_candidates": (),
        "notes": "Linker-only validation that supports coverage bundles indirectly.",
    },
    {
        "suite_id": "unit_selfhost",
        "suite_kind": "test_unit",
        "source_roots": ("test/unit/selfhost",),
        "coverage_role": "supporting_only",
        "bundle_candidates": (),
        "notes": "Selfhost preparation/build helpers, not a direct matrix source.",
    },
    {
        "suite_id": "unit_tooling",
        "suite_kind": "test_unit",
        "source_roots": ("test/unit/tooling",),
        "coverage_role": "supporting_only",
        "bundle_candidates": (),
        "notes": "Tooling/checker tests that police bundle inventories.",
    },
    {
        "suite_id": "ir_fixture",
        "suite_kind": "test_ir",
        "source_roots": ("test/ir",),
        "coverage_role": "direct_matrix_input",
        "bundle_candidates": ("east2x",),
        "notes": "Frontend-independent IR-to-backend smoke fixtures.",
    },
    {
        "suite_id": "integration",
        "suite_kind": "test_integration",
        "source_roots": ("test/integration",),
        "coverage_role": "direct_matrix_input",
        "bundle_candidates": ("integration",),
        "notes": "Backend-specific execution/runtime integration suites.",
    },
    {
        "suite_id": "transpile_artifact",
        "suite_kind": "test_transpile",
        "source_roots": ("work/transpile",),
        "coverage_role": "direct_matrix_input",
        "bundle_candidates": ("runtime",),
        "notes": "Artifact and parity-driven staged runtime verification.",
    },
)


COVERAGE_BUNDLES_V1: Final[tuple[CoverageBundleEntry, ...]] = (
    {
        "bundle_id": "frontend_unit_contract_bundle",
        "bundle_kind": "frontend",
        "suite_kind": "test_unit",
        "harness_kind": "unittest_discover",
        "source_paths": ("tools/unittest/ir", "tools/unittest/common"),
        "evidence_refs": (
            {
                "relpath": "tools/unittest/ir/test_east_core_parser_behavior_runtime.py",
                "needle": "class EastCoreParserBehaviorRuntimeTest(unittest.TestCase):",
            },
            {
                "relpath": "tools/unittest/ir/test_east2_to_east3_source_contract.py",
                "needle": "class East2ToEast3SourceContractTest(unittest.TestCase):",
            },
        ),
        "notes": "Frontend bundle owns parse/EAST/EAST3-lowering unit-test evidence.",
    },
    {
        "bundle_id": "emit_backend_smoke_bundle",
        "bundle_kind": "emit",
        "suite_kind": "test_unit",
        "harness_kind": "unittest_discover",
        "source_paths": (
            "test/unit/backends",
            "tools/unittest/common/test_py2x_smoke_common.py",
        ),
        "evidence_refs": (
            {
                "relpath": "tools/unittest/common/test_py2x_smoke_common.py",
                "needle": "def test_add_fixture_transpile_via_py2x_for_non_cpp_targets(self) -> None:",
            },
            {
                "relpath": "tools/unittest/emit/js/test_py2js_smoke.py",
                "needle": "def test_representative_property_method_call_fixture_transpiles(self) -> None:",
            },
        ),
        "notes": "Emit bundle owns backend transpile smoke and compare coverage.",
    },
    {
        "bundle_id": "runtime_parity_bundle",
        "bundle_kind": "runtime",
        "suite_kind": "test_transpile",
        "harness_kind": "runtime_parity_cli",
        "source_paths": ("tools/runtime_parity_check.py", "work/transpile"),
        "evidence_refs": (
            {
                "relpath": "test/unit/tooling/test_runtime_parity_check_cli.py",
                "needle": "class RuntimeParityCheckCliTest(unittest.TestCase):",
            },
            {
                "relpath": "tools/runtime_parity_check.py",
                "needle": 'return f"work/transpile/{target}/{case_stem}"',
            },
        ),
        "notes": "Runtime bundle owns staged sample/runtime parity verification.",
    },
    {
        "bundle_id": "import_package_bundle",
        "bundle_kind": "import_package",
        "suite_kind": "test_unit",
        "harness_kind": "unittest_discover",
        "source_paths": (
            "tools/unittest/common/test_relative_import_semantics.py",
            "tools/unittest/emit/relative_import_native_path_smoke_support.py",
            "tools/unittest/emit/relative_import_jvm_package_smoke_support.py",
            "tools/check_relative_import_backend_coverage.py",
        ),
        "evidence_refs": (
            {
                "relpath": "tools/unittest/common/test_relative_import_semantics.py",
                "needle": "class RelativeImportSemanticsTest(unittest.TestCase):",
            },
            {
                "relpath": "tools/unittest/emit/go/test_py2go_smoke.py",
                "needle": "def test_cli_relative_import_native_path_bundle_scenarios_transpile_for_go(self) -> None:",
            },
            {
                "relpath": "tools/unittest/emit/java/test_py2java_smoke.py",
                "needle": "def test_cli_relative_import_jvm_package_bundle_scenarios_transpile_for_java(self) -> None:",
            },
            {
                "relpath": "tools/check_relative_import_backend_coverage.py",
                "needle": 'print("[OK] relative import backend coverage inventory passed")',
            },
        ),
        "notes": "Import/package bundle owns relative-import and package-layout smoke.",
    },
    {
        "bundle_id": "east2x_smoke_bundle",
        "bundle_kind": "east2x",
        "suite_kind": "test_ir",
        "harness_kind": "checker_cli",
        "source_paths": ("test/ir", "tools/check_east2x_smoke.py"),
        "evidence_refs": (
            {
                "relpath": "test/ir/README.md",
                "needle": "backend-only",
            },
            {
                "relpath": "tools/check_east2x_smoke.py",
                "needle": 'description="Run east2x smoke checks from fixed EAST3 fixtures"',
            },
        ),
        "notes": "east2x bundle owns backend-only EAST3(JSON) smoke coverage.",
    },
    {
        "bundle_id": "integration_gc_bundle",
        "bundle_kind": "integration",
        "suite_kind": "test_integration",
        "harness_kind": "native_compile_run",
        "source_paths": ("test/integration",),
        "evidence_refs": (
            {
                "relpath": "test/integration/test_gc.cpp",
                "needle": "void test_multithread_atomic_rc() {",
            },
            {
                "relpath": "test/integration/test_gc.cpp",
                "needle": 'std::cout << "test_gc: all tests passed" << std::endl;',
            },
        ),
        "notes": "Integration bundle owns backend-specific native runtime execution coverage.",
    },
)


def _build_coverage_only_backend_evidence(
    fixture_stem: str,
) -> tuple[CoverageOnlyFixtureBackendEvidence, ...]:
    evidence: list[CoverageOnlyFixtureBackendEvidence] = []
    for backend in feature_backend_order():
        relpath = SMOKE_TEST_PATH_BY_BACKEND[backend]
        if backend == "cpp":
            evidence.append(
                {
                    "backend": backend,
                    "relpath": relpath,
                    "needle": CPP_RUNTIME_NEEDLE_BY_FIXTURE_STEM[fixture_stem],
                }
            )
            continue
        evidence.append(
            {
                "backend": backend,
                "relpath": relpath,
                "needle": f"def test_representative_{fixture_stem}_fixture_transpiles(self) -> None:",
            }
        )
    return tuple(evidence)


COVERAGE_ONLY_FIXTURE_ENTRIES_V1: Final[tuple[CoverageOnlyFixtureEntry, ...]] = (
    {
        "fixture_stem": "list_bool_index",
        "fixture_rel": "test/fixtures/typing/list_bool_index.py",
        "status": "coverage_only_representative",
        "backend_evidence": _build_coverage_only_backend_evidence("list_bool_index"),
        "notes": (
            "Already exercised across every backend smoke/runtime lane, but should stay "
            "coverage-only because it primarily locks typed-container regression behavior."
        ),
    },
)


PROMOTION_CANDIDATE_FIXTURE_ENTRIES_V1: Final[tuple[PromotionCandidateFixtureEntry, ...]] = (
    {
        "fixture_stem": "property_method_call",
        "fixture_rel": "test/fixtures/typing/property_method_call.py",
        "status": "support_matrix_promotion_candidate",
        "proposed_feature_id": "syntax.oop.property_method_call",
        "proposed_category": "syntax",
        "proposed_title": "property access and method call",
        "backend_evidence": _build_coverage_only_backend_evidence("property_method_call"),
        "notes": (
            "Already exercised across every backend smoke/runtime lane and fills the "
            "current support-matrix gap around `@property` reads reused inside methods."
        ),
    },
)


UNPUBLISHED_MULTI_BACKEND_FIXTURE_INVENTORY_V1: Final[
    tuple[UnpublishedMultiBackendFixtureEntry, ...]
] = (
    {
        "fixture_rel": "test/fixtures/typing/property_method_call.py",
        "fixture_stem": "property_method_call",
        "status": "support_matrix_promotion_candidate",
        "target_surface": "support_matrix",
        "proposed_feature_id": "syntax.oop.property_method_call",
        "proposed_category": "syntax",
        "proposed_title": "property access and method call",
        "observed_backends": tuple(
            item["backend"]
            for item in _build_coverage_only_backend_evidence("property_method_call")
        ),
        "notes": (
            "Already exercised across every backend smoke/runtime lane and is the next"
            " candidate to promote into the representative support matrix."
        ),
    },
    {
        "fixture_rel": "test/fixtures/typing/list_bool_index.py",
        "fixture_stem": "list_bool_index",
        "status": "coverage_only_representative",
        "target_surface": "coverage_matrix_only",
        "proposed_feature_id": "",
        "proposed_category": "",
        "proposed_title": "",
        "observed_backends": tuple(
            item["backend"]
            for item in _build_coverage_only_backend_evidence("list_bool_index")
        ),
        "notes": (
            "Already exercised across every backend smoke/runtime lane, but should stay"
            " coverage-only because it primarily locks runtime regression behavior."
        ),
    },
)


BACKEND_CONTRACT_COVERAGE_HANDOFF_V1: Final[dict[str, object]] = {
    "todo_id": BACKEND_CONTRACT_COVERAGE_TODO_ID,
    "plan_paths": (
        BACKEND_CONTRACT_COVERAGE_PLAN_JA,
        BACKEND_CONTRACT_COVERAGE_PLAN_EN,
    ),
    "bundle_order": tuple(bundle["bundle_id"] for bundle in COVERAGE_BUNDLES_V1),
    "coverage_bundle_order": COVERAGE_BUNDLE_ORDER,
    "suite_family_order": SUITE_FAMILY_ORDER,
    "suite_kind_order": SUITE_KIND_ORDER,
    "harness_kind_order": HARNESS_KIND_ORDER,
    "taxonomy_harness_kind_order": TAXONOMY_HARNESS_KIND_ORDER,
    "coverage_only_status_order": COVERAGE_ONLY_STATUS_ORDER,
    "promotion_candidate_status_order": PROMOTION_CANDIDATE_STATUS_ORDER,
    "unpublished_fixture_status_order": UNPUBLISHED_FIXTURE_STATUS_ORDER,
    "unpublished_fixture_target_order": UNPUBLISHED_FIXTURE_TARGET_ORDER,
    "live_suite_role_order": LIVE_SUITE_ROLE_ORDER,
}


def iter_coverage_bundle_taxonomy() -> tuple[CoverageBundleTaxonomyEntry, ...]:
    return COVERAGE_BUNDLE_TAXONOMY_V1


def iter_live_suite_family_inventory() -> tuple[LiveSuiteFamilyEntry, ...]:
    return LIVE_SUITE_FAMILY_INVENTORY_V1


def iter_backend_contract_coverage_bundles() -> tuple[CoverageBundleEntry, ...]:
    return COVERAGE_BUNDLES_V1


def iter_backend_contract_coverage_only_fixtures() -> tuple[CoverageOnlyFixtureEntry, ...]:
    return COVERAGE_ONLY_FIXTURE_ENTRIES_V1


def iter_backend_contract_promotion_candidate_fixtures() -> tuple[PromotionCandidateFixtureEntry, ...]:
    return PROMOTION_CANDIDATE_FIXTURE_ENTRIES_V1


def iter_unpublished_multi_backend_fixture_inventory() -> tuple[UnpublishedMultiBackendFixtureEntry, ...]:
    return UNPUBLISHED_MULTI_BACKEND_FIXTURE_INVENTORY_V1


def build_backend_contract_coverage_seed_manifest() -> dict[str, object]:
    return {
        "inventory_version": 1,
        "todo_id": BACKEND_CONTRACT_COVERAGE_HANDOFF_V1["todo_id"],
        "plan_paths": list(BACKEND_CONTRACT_COVERAGE_HANDOFF_V1["plan_paths"]),
        "coverage_bundle_order": list(COVERAGE_BUNDLE_ORDER),
        "suite_family_order": list(SUITE_FAMILY_ORDER),
        "suite_kind_order": list(SUITE_KIND_ORDER),
        "harness_kind_order": list(HARNESS_KIND_ORDER),
        "taxonomy_harness_kind_order": list(TAXONOMY_HARNESS_KIND_ORDER),
        "coverage_only_status_order": list(COVERAGE_ONLY_STATUS_ORDER),
        "promotion_candidate_status_order": list(PROMOTION_CANDIDATE_STATUS_ORDER),
        "unpublished_fixture_status_order": list(UNPUBLISHED_FIXTURE_STATUS_ORDER),
        "unpublished_fixture_target_order": list(UNPUBLISHED_FIXTURE_TARGET_ORDER),
        "live_suite_role_order": list(LIVE_SUITE_ROLE_ORDER),
        "bundle_order": list(BACKEND_CONTRACT_COVERAGE_HANDOFF_V1["bundle_order"]),
        "coverage_bundle_taxonomy": list(iter_coverage_bundle_taxonomy()),
        "live_suite_families": list(iter_live_suite_family_inventory()),
        "coverage_bundles": list(iter_backend_contract_coverage_bundles()),
        "coverage_only_fixtures": list(iter_backend_contract_coverage_only_fixtures()),
        "promotion_candidate_fixtures": list(iter_backend_contract_promotion_candidate_fixtures()),
        "unpublished_multi_backend_fixtures": list(
            iter_unpublished_multi_backend_fixture_inventory()
        ),
    }
