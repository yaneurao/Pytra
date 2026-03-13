"""Seed inventory for bundle-based backend contract coverage tracking."""

from __future__ import annotations

from typing import Final, TypedDict

from src.toolchain.compiler import backend_feature_contract_inventory as feature_inventory_mod


BACKEND_CONTRACT_COVERAGE_TODO_ID: Final[str] = "P2-BACKEND-CONTRACT-COVERAGE-100-01"
BACKEND_CONTRACT_COVERAGE_PLAN_JA: Final[str] = (
    "docs/ja/plans/p2-backend-contract-coverage-100.md"
)
BACKEND_CONTRACT_COVERAGE_PLAN_EN: Final[str] = (
    "docs/en/plans/p2-backend-contract-coverage-100.md"
)

BUNDLE_KIND_ORDER: Final[tuple[str, ...]] = (
    "frontend",
    "emit",
    "runtime",
    "import_package",
    "ir2lang",
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

COVERAGE_ONLY_STATUS_ORDER: Final[tuple[str, ...]] = ("coverage_only_representative",)

SMOKE_TEST_PATH_BY_BACKEND: Final[dict[str, str]] = {
    "cpp": "test/unit/backends/cpp/test_py2cpp_features.py",
    "rs": "test/unit/backends/rs/test_py2rs_smoke.py",
    "cs": "test/unit/backends/cs/test_py2cs_smoke.py",
    "go": "test/unit/backends/go/test_py2go_smoke.py",
    "java": "test/unit/backends/java/test_py2java_smoke.py",
    "kt": "test/unit/backends/kotlin/test_py2kotlin_smoke.py",
    "scala": "test/unit/backends/scala/test_py2scala_smoke.py",
    "swift": "test/unit/backends/swift/test_py2swift_smoke.py",
    "nim": "test/unit/backends/nim/test_py2nim_smoke.py",
    "js": "test/unit/backends/js/test_py2js_smoke.py",
    "ts": "test/unit/backends/ts/test_py2ts_smoke.py",
    "lua": "test/unit/backends/lua/test_py2lua_smoke.py",
    "rb": "test/unit/backends/rb/test_py2rb_smoke.py",
    "php": "test/unit/backends/php/test_py2php_smoke.py",
}

CPP_RUNTIME_NEEDLE_BY_FIXTURE_STEM: Final[dict[str, str]] = {
    "property_method_call": "def test_property_method_call_runtime(self) -> None:",
    "list_bool_index": "def test_list_bool_index_runtime(self) -> None:",
}

SUPPORT_MATRIX_FIXTURES: Final[tuple[str, ...]] = tuple(
    sorted({row["representative_fixture"] for row in feature_inventory_mod.iter_representative_fixture_mapping()})
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


COVERAGE_BUNDLES_V1: Final[tuple[CoverageBundleEntry, ...]] = (
    {
        "bundle_id": "frontend_unit_contract_bundle",
        "bundle_kind": "frontend",
        "suite_kind": "test_unit",
        "harness_kind": "unittest_discover",
        "source_paths": (
            "test/unit/ir",
            "test/unit/common",
        ),
        "evidence_refs": (
            {
                "relpath": "test/unit/ir/test_east_core_parser_behavior_runtime.py",
                "needle": "class EastCoreParserBehaviorRuntimeTest(unittest.TestCase):",
            },
            {
                "relpath": "test/unit/ir/test_east2_to_east3_source_contract.py",
                "needle": "class East2ToEast3SourceContractTest(unittest.TestCase):",
            },
        ),
        "notes": "Frontend bundle owns parse/east/east3-lowering contract evidence from unit tests under test/unit/ir.",
    },
    {
        "bundle_id": "emit_backend_smoke_bundle",
        "bundle_kind": "emit",
        "suite_kind": "test_unit",
        "harness_kind": "unittest_discover",
        "source_paths": (
            "test/unit/backends",
            "test/unit/common/test_py2x_smoke_common.py",
        ),
        "evidence_refs": (
            {
                "relpath": "test/unit/common/test_py2x_smoke_common.py",
                "needle": "def test_add_fixture_transpile_via_py2x_for_non_cpp_targets(self) -> None:",
            },
            {
                "relpath": "test/unit/backends/js/test_py2js_smoke.py",
                "needle": "def test_representative_property_method_call_fixture_transpiles(self) -> None:",
            },
        ),
        "notes": "Emit bundle owns backend transpile smoke and compare-oriented representative fixture coverage.",
    },
    {
        "bundle_id": "runtime_parity_bundle",
        "bundle_kind": "runtime",
        "suite_kind": "test_transpile",
        "harness_kind": "runtime_parity_cli",
        "source_paths": (
            "tools/runtime_parity_check.py",
            "test/transpile",
        ),
        "evidence_refs": (
            {
                "relpath": "test/unit/tooling/test_runtime_parity_check_cli.py",
                "needle": "class RuntimeParityCheckCliTest(unittest.TestCase):",
            },
            {
                "relpath": "tools/runtime_parity_check.py",
                "needle": "return f\"test/transpile/{target}/{case_stem}\"",
            },
        ),
        "notes": "Runtime bundle owns staged sample/runtime parity verification driven from tools/runtime_parity_check.py and test/transpile artifacts.",
    },
    {
        "bundle_id": "import_package_bundle",
        "bundle_kind": "import_package",
        "suite_kind": "test_unit",
        "harness_kind": "unittest_discover",
        "source_paths": (
            "test/unit/backends/relative_import_native_path_smoke_support.py",
            "test/unit/backends/relative_import_jvm_package_smoke_support.py",
            "tools/check_relative_import_backend_coverage.py",
        ),
        "evidence_refs": (
            {
                "relpath": "test/unit/backends/go/test_py2go_smoke.py",
                "needle": "def test_cli_relative_import_native_path_bundle_scenarios_transpile_for_go(self) -> None:",
            },
            {
                "relpath": "test/unit/backends/java/test_py2java_smoke.py",
                "needle": "def test_cli_relative_import_jvm_package_bundle_scenarios_transpile_for_java(self) -> None:",
            },
            {
                "relpath": "tools/check_relative_import_backend_coverage.py",
                "needle": "print(\"[OK] relative import backend coverage inventory passed\")",
            },
        ),
        "notes": "Import/package bundle owns relative-import, package-layout, and module-graph smoke/checker coverage.",
    },
    {
        "bundle_id": "ir2lang_smoke_bundle",
        "bundle_kind": "ir2lang",
        "suite_kind": "test_ir",
        "harness_kind": "checker_cli",
        "source_paths": (
            "test/ir",
            "tools/check_ir2lang_smoke.py",
        ),
        "evidence_refs": (
            {
                "relpath": "test/ir/README.md",
                "needle": "backend-only",
            },
            {
                "relpath": "tools/check_ir2lang_smoke.py",
                "needle": "description=\"Run ir2lang smoke checks from fixed EAST3 fixtures\"",
            },
        ),
        "notes": "ir2lang bundle owns frontend-independent EAST3(JSON) to backend smoke coverage.",
    },
    {
        "bundle_id": "integration_gc_bundle",
        "bundle_kind": "integration",
        "suite_kind": "test_integration",
        "harness_kind": "native_compile_run",
        "source_paths": (
            "test/integration",
        ),
        "evidence_refs": (
            {
                "relpath": "test/integration/test_gc.cpp",
                "needle": "void test_multithread_atomic_rc() {",
            },
            {
                "relpath": "test/integration/test_gc.cpp",
                "needle": "std::cout << \"test_gc: all tests passed\" << std::endl;",
            },
        ),
        "notes": "Integration bundle owns backend-specific native runtime execution coverage such as GC/reference-count integration.",
    },
)


def _build_coverage_only_backend_evidence(
    fixture_stem: str,
) -> tuple[CoverageOnlyFixtureBackendEvidence, ...]:
    evidence: list[CoverageOnlyFixtureBackendEvidence] = []
    for backend in feature_inventory_mod.SUPPORT_MATRIX_BACKEND_ORDER:
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
        "fixture_stem": "property_method_call",
        "fixture_rel": "test/fixtures/typing/property_method_call.py",
        "status": "coverage_only_representative",
        "backend_evidence": _build_coverage_only_backend_evidence("property_method_call"),
        "notes": "Already covered across every backend smoke/runtime lane, but not yet promoted into the support-matrix representative inventory.",
    },
    {
        "fixture_stem": "list_bool_index",
        "fixture_rel": "test/fixtures/typing/list_bool_index.py",
        "status": "coverage_only_representative",
        "backend_evidence": _build_coverage_only_backend_evidence("list_bool_index"),
        "notes": "Already covered across every backend smoke/runtime lane, but still missing from the support-matrix representative inventory.",
    },
)


BACKEND_CONTRACT_COVERAGE_HANDOFF_V1: Final[dict[str, object]] = {
    "todo_id": BACKEND_CONTRACT_COVERAGE_TODO_ID,
    "plan_paths": (
        BACKEND_CONTRACT_COVERAGE_PLAN_JA,
        BACKEND_CONTRACT_COVERAGE_PLAN_EN,
    ),
    "bundle_order": tuple(bundle["bundle_id"] for bundle in COVERAGE_BUNDLES_V1),
    "bundle_kind_order": BUNDLE_KIND_ORDER,
    "suite_kind_order": SUITE_KIND_ORDER,
    "harness_kind_order": HARNESS_KIND_ORDER,
    "coverage_only_status_order": COVERAGE_ONLY_STATUS_ORDER,
}


def iter_backend_contract_coverage_bundles() -> tuple[CoverageBundleEntry, ...]:
    return COVERAGE_BUNDLES_V1


def iter_backend_contract_coverage_only_fixtures() -> tuple[CoverageOnlyFixtureEntry, ...]:
    return COVERAGE_ONLY_FIXTURE_ENTRIES_V1


def build_backend_contract_coverage_seed_manifest() -> dict[str, object]:
    return {
        "inventory_version": 1,
        "todo_id": BACKEND_CONTRACT_COVERAGE_HANDOFF_V1["todo_id"],
        "plan_paths": list(BACKEND_CONTRACT_COVERAGE_HANDOFF_V1["plan_paths"]),
        "bundle_kind_order": list(BUNDLE_KIND_ORDER),
        "suite_kind_order": list(SUITE_KIND_ORDER),
        "harness_kind_order": list(HARNESS_KIND_ORDER),
        "coverage_only_status_order": list(COVERAGE_ONLY_STATUS_ORDER),
        "bundle_order": list(BACKEND_CONTRACT_COVERAGE_HANDOFF_V1["bundle_order"]),
        "coverage_bundles": list(iter_backend_contract_coverage_bundles()),
        "coverage_only_fixtures": list(iter_backend_contract_coverage_only_fixtures()),
    }
