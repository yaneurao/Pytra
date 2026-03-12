from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.toolchain.compiler import backend_conformance_summary_handoff_contract as conformance_summary_mod
from src.toolchain.compiler import backend_feature_contract_inventory as feature_contract_mod
from src.toolchain.compiler import backend_parity_matrix_contract as contract_mod

DOC_TARGETS = (
    ROOT / "docs/ja/language/backend-parity-matrix.md",
    ROOT / "docs/en/language/backend-parity-matrix.md",
)
CPP_DOC_TARGETS = (
    ROOT / "docs/ja/language/cpp/spec-support.md",
    ROOT / "docs/en/language/cpp/spec-support.md",
)


def _collect_contract_issues() -> list[str]:
    issues: list[str] = []
    if contract_mod.PARITY_MATRIX_BACKEND_ORDER != (
        "cpp",
        "rs",
        "cs",
        "js",
        "ts",
        "go",
        "java",
        "swift",
        "kt",
        "rb",
        "lua",
        "scala",
        "php",
        "nim",
    ):
        issues.append("backend parity matrix display order drifted away from the top-level benchmark order")
    if set(contract_mod.PARITY_MATRIX_BACKEND_ORDER) != set(feature_contract_mod.SUPPORT_MATRIX_BACKEND_ORDER):
        issues.append("backend parity matrix order no longer covers the same backend set as the feature contract support matrix")
    if contract_mod.PARITY_MATRIX_SUPPORT_STATE_ORDER != feature_contract_mod.SUPPORT_STATE_ORDER:
        issues.append("support state order drifted away from feature contract")
    if contract_mod.PARITY_MATRIX_SOURCE_DESTINATION != "support_matrix":
        issues.append("matrix source destination must stay fixed to support_matrix")
    if contract_mod.PARITY_MATRIX_IMPLEMENTATION_PHASE != "cell_seed_manifest":
        issues.append("matrix implementation phase drifted away from cell_seed_manifest baseline")
    if contract_mod.PARITY_MATRIX_CELL_SCHEMA_STATUS != "seed_populated":
        issues.append("matrix cell schema status drifted away from seed_populated baseline")
    if contract_mod.PARITY_MATRIX_CELL_SCHEMA_VERSION != 1:
        issues.append("matrix cell schema version drifted")
    if contract_mod.PARITY_MATRIX_CELL_COLLECTION_KEY != "backend_cells":
        issues.append("matrix cell collection key drifted")
    if contract_mod.PARITY_MATRIX_CELL_REQUIRED_KEYS != ("backend", "support_state", "evidence_kind"):
        issues.append("matrix cell required keys drifted")
    if contract_mod.PARITY_MATRIX_CELL_OPTIONAL_KEYS != ("details", "evidence_ref", "diagnostic_kind"):
        issues.append("matrix cell optional keys drifted")
    if contract_mod.PARITY_MATRIX_CELL_EVIDENCE_KIND_ORDER != (
        "build_run_smoke",
        "transpile_smoke",
        "contract_guard",
        "diagnostic_guard",
        "not_started_placeholder",
        "preview_guard",
    ):
        issues.append("matrix cell evidence kind order drifted")
    if contract_mod.PARITY_MATRIX_ALLOWED_EVIDENCE_KINDS_BY_STATE != {
        "supported": ("build_run_smoke", "transpile_smoke"),
        "fail_closed": ("contract_guard", "diagnostic_guard"),
        "not_started": ("not_started_placeholder",),
        "experimental": ("preview_guard", "transpile_smoke", "build_run_smoke"),
    }:
        issues.append("matrix state/evidence compatibility drifted")
    if contract_mod.PARITY_MATRIX_CELL_GAP_SUMMARY != {
        "seed_state_is_conservative": "Current backend cell seeds stay conservative outside the reviewed representative, secondary, and long-tail cells that already have direct transpile or build/run smoke evidence.",
        "docs_table_is_seed_only": "The docs page now renders the seeded 2D support table, but non-reviewed lanes still stay on placeholders outside the reviewed representative, secondary, and long-tail cells.",
        "cell_details_are_sparse": "Per-cell details/evidence_ref/diagnostic_kind remain sparse until follow-up row fill bundles land.",
    }:
        issues.append("matrix cell gap summary drifted")
    if contract_mod.REVIEWED_REPRESENTATIVE_CELL_OVERRIDES != {
        "syntax.assign.tuple_destructure": {
            "js": {"backend": "js", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "ts": {"backend": "ts", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "lua": {"backend": "lua", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "rb": {"backend": "rb", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "php": {"backend": "php", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "go": {"backend": "go", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "java": {"backend": "java", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "kt": {"backend": "kt", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "scala": {"backend": "scala", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "swift": {"backend": "swift", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "nim": {"backend": "nim", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "rs": {"backend": "rs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "cs": {"backend": "cs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
        },
        "syntax.expr.lambda": {
            "js": {"backend": "js", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "ts": {"backend": "ts", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "lua": {"backend": "lua", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "rb": {"backend": "rb", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "php": {"backend": "php", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "go": {"backend": "go", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "java": {"backend": "java", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "kt": {"backend": "kt", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "scala": {"backend": "scala", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "swift": {"backend": "swift", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "nim": {"backend": "nim", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "rs": {"backend": "rs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "cs": {"backend": "cs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
        },
        "syntax.expr.list_comprehension": {
            "js": {"backend": "js", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "ts": {"backend": "ts", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "lua": {"backend": "lua", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "rb": {"backend": "rb", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "php": {"backend": "php", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "go": {"backend": "go", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "java": {"backend": "java", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "kt": {"backend": "kt", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "scala": {"backend": "scala", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "swift": {"backend": "swift", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "nim": {"backend": "nim", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "rs": {"backend": "rs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "cs": {"backend": "cs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
        },
        "syntax.control.for_range": {
            "js": {"backend": "js", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "ts": {"backend": "ts", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "rb": {"backend": "rb", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "go": {"backend": "go", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "rs": {"backend": "rs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "cs": {"backend": "cs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "java": {"backend": "java", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "kt": {"backend": "kt", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "scala": {"backend": "scala", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "swift": {"backend": "swift", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "nim": {"backend": "nim", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "lua": {"backend": "lua", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "php": {"backend": "php", "support_state": "supported", "evidence_kind": "transpile_smoke"},
        },
        "syntax.control.try_raise": {
            "js": {"backend": "js", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "ts": {"backend": "ts", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "lua": {"backend": "lua", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "rb": {"backend": "rb", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "php": {"backend": "php", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "go": {"backend": "go", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "java": {"backend": "java", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "kt": {"backend": "kt", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "scala": {"backend": "scala", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "swift": {"backend": "swift", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "nim": {"backend": "nim", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "rs": {"backend": "rs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "cs": {"backend": "cs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
        },
        "syntax.oop.virtual_dispatch": {
            "rs": {"backend": "rs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "go": {"backend": "go", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "java": {"backend": "java", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "kt": {"backend": "kt", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "scala": {"backend": "scala", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "swift": {"backend": "swift", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "nim": {"backend": "nim", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "cs": {"backend": "cs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "js": {"backend": "js", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "ts": {"backend": "ts", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "lua": {"backend": "lua", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "rb": {"backend": "rb", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "php": {"backend": "php", "support_state": "supported", "evidence_kind": "transpile_smoke"},
        },
        "builtin.iter.enumerate": {
            "js": {"backend": "js", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "ts": {"backend": "ts", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "lua": {"backend": "lua", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "rb": {"backend": "rb", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "php": {"backend": "php", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "go": {"backend": "go", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "java": {"backend": "java", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "kt": {"backend": "kt", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "scala": {"backend": "scala", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "swift": {"backend": "swift", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "nim": {"backend": "nim", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "rs": {"backend": "rs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "cs": {"backend": "cs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
        },
        "builtin.iter.zip": {
            "js": {"backend": "js", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "ts": {"backend": "ts", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "rb": {"backend": "rb", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "go": {"backend": "go", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "java": {"backend": "java", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "kt": {"backend": "kt", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "scala": {"backend": "scala", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "swift": {"backend": "swift", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "nim": {"backend": "nim", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "rs": {"backend": "rs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "cs": {"backend": "cs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "lua": {"backend": "lua", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "php": {"backend": "php", "support_state": "supported", "evidence_kind": "transpile_smoke"},
        },
        "builtin.iter.range": {
            "js": {"backend": "js", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "ts": {"backend": "ts", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "rb": {"backend": "rb", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "go": {"backend": "go", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "rs": {"backend": "rs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "cs": {"backend": "cs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "java": {"backend": "java", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "kt": {"backend": "kt", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "scala": {"backend": "scala", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "swift": {"backend": "swift", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "nim": {"backend": "nim", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "lua": {"backend": "lua", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "php": {"backend": "php", "support_state": "supported", "evidence_kind": "transpile_smoke"},
        },
        "stdlib.json.loads_dumps": {
            "js": {"backend": "js", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "ts": {"backend": "ts", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "lua": {"backend": "lua", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "rb": {"backend": "rb", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "php": {"backend": "php", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "go": {"backend": "go", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "java": {"backend": "java", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "kt": {"backend": "kt", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "scala": {"backend": "scala", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "swift": {"backend": "swift", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "nim": {"backend": "nim", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "rs": {"backend": "rs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "cs": {"backend": "cs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
        },
        "stdlib.pathlib.path_ops": {
            "js": {"backend": "js", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "ts": {"backend": "ts", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "lua": {"backend": "lua", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "rb": {"backend": "rb", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "php": {"backend": "php", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "go": {"backend": "go", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "java": {"backend": "java", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "kt": {"backend": "kt", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "scala": {"backend": "scala", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "swift": {"backend": "swift", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "nim": {"backend": "nim", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "rs": {"backend": "rs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "cs": {"backend": "cs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
        },
        "stdlib.enum.enum_and_intflag": {
            "js": {"backend": "js", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "ts": {"backend": "ts", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "lua": {"backend": "lua", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "rb": {"backend": "rb", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "php": {"backend": "php", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "go": {"backend": "go", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "java": {"backend": "java", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "kt": {"backend": "kt", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "scala": {"backend": "scala", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "swift": {"backend": "swift", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "nim": {"backend": "nim", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "rs": {"backend": "rs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "cs": {"backend": "cs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
        },
        "stdlib.argparse.parse_args": {
            "js": {"backend": "js", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "ts": {"backend": "ts", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "lua": {"backend": "lua", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "rb": {"backend": "rb", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "php": {"backend": "php", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "go": {"backend": "go", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "java": {"backend": "java", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "kt": {"backend": "kt", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "scala": {"backend": "scala", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "swift": {"backend": "swift", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "nim": {"backend": "nim", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "rs": {"backend": "rs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "cs": {"backend": "cs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
        },
        "stdlib.re.sub": {
            "js": {"backend": "js", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "ts": {"backend": "ts", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "lua": {"backend": "lua", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "rb": {"backend": "rb", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "php": {"backend": "php", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "go": {"backend": "go", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "java": {"backend": "java", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "kt": {"backend": "kt", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "scala": {"backend": "scala", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "swift": {"backend": "swift", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "nim": {"backend": "nim", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "rs": {"backend": "rs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "cs": {"backend": "cs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
        },
        "builtin.type.isinstance": {
            "js": {"backend": "js", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "ts": {"backend": "ts", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "go": {"backend": "go", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "java": {"backend": "java", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "kt": {"backend": "kt", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "scala": {"backend": "scala", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "swift": {"backend": "swift", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "nim": {"backend": "nim", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "rs": {"backend": "rs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "cs": {"backend": "cs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "lua": {"backend": "lua", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "rb": {"backend": "rb", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "php": {"backend": "php", "support_state": "supported", "evidence_kind": "transpile_smoke"},
        },
        "builtin.bit.invert_and_mask": {
            "go": {"backend": "go", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "rs": {"backend": "rs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "cs": {"backend": "cs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "java": {"backend": "java", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "kt": {"backend": "kt", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "scala": {"backend": "scala", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "swift": {"backend": "swift", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "nim": {"backend": "nim", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "js": {"backend": "js", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "ts": {"backend": "ts", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "lua": {"backend": "lua", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "rb": {"backend": "rb", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "php": {"backend": "php", "support_state": "supported", "evidence_kind": "transpile_smoke"},
        },
        "stdlib.math.imported_symbols": {
            "js": {"backend": "js", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "ts": {"backend": "ts", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "lua": {"backend": "lua", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "rb": {"backend": "rb", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "php": {"backend": "php", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "go": {"backend": "go", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "java": {"backend": "java", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "kt": {"backend": "kt", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "scala": {"backend": "scala", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "swift": {"backend": "swift", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "nim": {"backend": "nim", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "rs": {"backend": "rs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            "cs": {"backend": "cs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
        },
    }:
        issues.append("reviewed representative cell overrides drifted")
    support_matrix_summary_entry = next(
        entry
        for entry in conformance_summary_mod.iter_representative_conformance_summary_handoff()
        if entry["summary_kind"] == conformance_summary_mod.CONFORMANCE_SUMMARY_KIND
    )
    if contract_mod.PARITY_MATRIX_SUMMARY_SOURCE != "conformance_summary_handoff.representative_summary_entries":
        issues.append("matrix summary source drifted away from conformance summary handoff")
    if contract_mod.PARITY_MATRIX_SUMMARY_KEYS != (
        "feature_id",
        "category",
        "fixture_class",
        "representative_fixture",
        "summary_kind",
        "shared_lanes",
        "backend_selectable_lanes",
        "backend_order",
        "runtime_lane_policy",
        "runtime_summary_source",
        "support_state_order",
        "downstream_task",
    ):
        issues.append("matrix summary keys drifted away from conformance summary handoff")
    if contract_mod.PARITY_MATRIX_DOWNSTREAM_TASK != feature_contract_mod.HANDOFF_TASK_IDS["support_matrix"]:
        issues.append("matrix downstream task drifted away from feature contract handoff")
    if contract_mod.PARITY_MATRIX_DOWNSTREAM_PLAN != feature_contract_mod.HANDOFF_PLAN_PATHS["support_matrix"]:
        issues.append("matrix downstream plan drifted away from feature contract handoff")
    if set(contract_mod.PARITY_MATRIX_PUBLISH_PATHS.keys()) != {"docs_ja", "docs_en", "tool_manifest"}:
        issues.append("matrix publish paths must stay fixed to docs_ja/docs_en/tool_manifest")
    if contract_mod.PARITY_MATRIX_CPP_DRILLDOWN_DOCS != {
        "docs_ja": "docs/ja/language/cpp/spec-support.md",
        "docs_en": "docs/en/language/cpp/spec-support.md",
    }:
        issues.append("cpp drilldown docs map drifted")
    if contract_mod.PARITY_MATRIX_DOC_ROLE_SPLIT != {
        "canonical_matrix": "The cross-backend backend parity matrix is the canonical source for feature x backend support-state reporting.",
        "cpp_drilldown": "The py2cpp support matrix is a cpp-only drill-down that refines the cpp lane without redefining the cross-backend taxonomy.",
    }:
        issues.append("doc role split drifted")
    if contract_mod.PARITY_MATRIX_DOC_MAINTENANCE_ORDER != (
        "update_matrix_contract_and_docs",
        "sync_cpp_drilldown_docs",
    ):
        issues.append("doc maintenance order drifted")
    if contract_mod.PARITY_MATRIX_SOURCE_MANIFESTS != {
        "feature_contract_seed": "backend_feature_contract_inventory.build_feature_contract_handoff_manifest",
        "conformance_summary_seed": "backend_conformance_summary_handoff_contract.build_backend_conformance_summary_handoff_manifest",
        "rollout_tier_seed": "backend_parity_rollout_tier_contract.build_backend_parity_rollout_tier_manifest",
    }:
        issues.append("matrix source manifests drifted")
    if contract_mod.PARITY_MATRIX_ROLLOUT_TIER_ORDER != ("representative", "secondary", "long_tail"):
        issues.append("matrix rollout tier order drifted")
    if contract_mod.PARITY_MATRIX_ROLLOUT_TIERS != (
        {
            "tier": "representative",
            "backend_order": ("cpp", "rs", "cs"),
            "downstream_task": contract_mod.PARITY_MATRIX_DOWNSTREAM_TASK,
            "downstream_plan": contract_mod.PARITY_MATRIX_DOWNSTREAM_PLAN,
        },
        {
            "tier": "secondary",
            "backend_order": ("go", "java", "kt", "scala", "swift", "nim"),
            "downstream_task": contract_mod.PARITY_MATRIX_DOWNSTREAM_TASK,
            "downstream_plan": contract_mod.PARITY_MATRIX_DOWNSTREAM_PLAN,
        },
        {
            "tier": "long_tail",
            "backend_order": ("js", "ts", "lua", "rb", "php"),
            "downstream_task": contract_mod.PARITY_MATRIX_DOWNSTREAM_TASK,
            "downstream_plan": contract_mod.PARITY_MATRIX_DOWNSTREAM_PLAN,
        },
    ):
        issues.append("matrix rollout tiers drifted")
    feature_ids = {entry["feature_id"] for entry in feature_contract_mod.iter_representative_support_matrix_handoff()}
    matrix_ids = {entry["feature_id"] for entry in contract_mod.iter_representative_parity_matrix_rows()}
    if matrix_ids != feature_ids:
        issues.append("matrix rows must cover exactly the representative support-matrix handoff inventory")
    for entry in contract_mod.iter_representative_parity_matrix_rows():
        if entry["backend_order"] != contract_mod.PARITY_MATRIX_BACKEND_ORDER:
            issues.append(f"{entry['feature_id']}: backend order drifted")
        if entry["support_state_order"] != contract_mod.PARITY_MATRIX_SUPPORT_STATE_ORDER:
            issues.append(f"{entry['feature_id']}: support state order drifted")
        if tuple(cell["backend"] for cell in entry["backend_cells"]) != contract_mod.PARITY_MATRIX_BACKEND_ORDER:
            issues.append(f"{entry['feature_id']}: backend cell order drifted")
        expected_cells = tuple(
            contract_mod._seed_backend_cell(entry["feature_id"], backend)
            for backend in contract_mod.PARITY_MATRIX_BACKEND_ORDER
        )
        if entry["backend_cells"] != expected_cells:
            issues.append(f"{entry['feature_id']}: reviewed backend cells drifted")
        for cell in entry["backend_cells"]:
            allowed_kinds = contract_mod.PARITY_MATRIX_ALLOWED_EVIDENCE_KINDS_BY_STATE[cell["support_state"]]
            if cell["evidence_kind"] not in allowed_kinds:
                issues.append(
                    f"{entry['feature_id']}:{cell['backend']}: evidence kind {cell['evidence_kind']} is not allowed for {cell['support_state']}"
                )
        if entry["summary_source"] != contract_mod.PARITY_MATRIX_SUMMARY_SOURCE:
            issues.append(f"{entry['feature_id']}: summary source drifted")
        if entry["summary_keys"] != contract_mod.PARITY_MATRIX_SUMMARY_KEYS:
            issues.append(f"{entry['feature_id']}: summary keys drifted")
        if entry["downstream_task"] != contract_mod.PARITY_MATRIX_DOWNSTREAM_TASK:
            issues.append(f"{entry['feature_id']}: downstream task drifted")
        if entry["downstream_plan"] != contract_mod.PARITY_MATRIX_DOWNSTREAM_PLAN:
            issues.append(f"{entry['feature_id']}: downstream plan drifted")
    return issues


def _collect_docs_issues() -> list[str]:
    issues: list[str] = []
    expected_table = contract_mod.build_backend_parity_matrix_html_table()
    for path in DOC_TARGETS:
        text = path.read_text(encoding="utf-8")
        if contract_mod.PARITY_MATRIX_DOC_TABLE_BEGIN_MARKER not in text:
            issues.append(f"missing table begin marker in {path.relative_to(ROOT)}")
            continue
        if contract_mod.PARITY_MATRIX_DOC_TABLE_END_MARKER not in text:
            issues.append(f"missing table end marker in {path.relative_to(ROOT)}")
            continue
        rendered = text.split(contract_mod.PARITY_MATRIX_DOC_TABLE_BEGIN_MARKER, 1)[1]
        rendered = rendered.split(contract_mod.PARITY_MATRIX_DOC_TABLE_END_MARKER, 1)[0].strip()
        if rendered != expected_table:
            issues.append(f"backend parity matrix table drifted in {path.relative_to(ROOT)}")
        if "./cpp/spec-support.md" not in text:
            issues.append(f"cpp drilldown link missing in {path.relative_to(ROOT)}")
        if path.name == "backend-parity-matrix.md":
            if path.parts[-3] == "ja":
                if "このページを正本とし、C++ 専用の詳細表は drill-down" not in text:
                    issues.append(f"canonical/drilldown note missing in {path.relative_to(ROOT)}")
                if "このページと tooling contract を先に更新し、その後で C++ の詳細表を同期します。" not in text:
                    issues.append(f"maintenance order note missing in {path.relative_to(ROOT)}")
                if "representative -> secondary -> long_tail の順で cell を埋めます。" not in text:
                    issues.append(f"rollout tier note missing in {path.relative_to(ROOT)}")
            else:
                if "Treat this page as the canonical source, and keep the C++ table as a drill-down" not in text:
                    issues.append(f"canonical/drilldown note missing in {path.relative_to(ROOT)}")
                if "Update this page and the tooling contract first, then sync the C++ drill-down table." not in text:
                    issues.append(f"maintenance order note missing in {path.relative_to(ROOT)}")
                if "Cells are filled in representative -> secondary -> long_tail order." not in text:
                    issues.append(f"rollout tier note missing in {path.relative_to(ROOT)}")
    for path in CPP_DOC_TARGETS:
        text = path.read_text(encoding="utf-8")
        if "../backend-parity-matrix.md" not in text:
            issues.append(f"backend parity matrix backlink missing in {path.relative_to(ROOT)}")
        if path.parts[-4] == "ja":
            if "cross-backend の正本は [backend-parity-matrix.md](../backend-parity-matrix.md)" not in text:
                issues.append(f"cpp drilldown role note missing in {path.relative_to(ROOT)}")
            if "まず canonical matrix を更新し、その後でこの C++ 詳細表を同期する" not in text:
                issues.append(f"cpp drilldown maintenance order note missing in {path.relative_to(ROOT)}")
        else:
            if "The canonical cross-backend source is [backend-parity-matrix.md](../backend-parity-matrix.md)" not in text:
                issues.append(f"cpp drilldown role note missing in {path.relative_to(ROOT)}")
            if "Update the canonical matrix first, then sync this C++ drill-down table." not in text:
                issues.append(f"cpp drilldown maintenance order note missing in {path.relative_to(ROOT)}")
    return issues


def _collect_manifest_issues() -> list[str]:
    issues: list[str] = []
    manifest = contract_mod.build_backend_parity_matrix_manifest()
    if set(manifest.keys()) != {
        "inventory_version",
        "source_manifests",
        "source_destination",
        "implementation_phase",
        "cell_schema_status",
        "cell_schema",
        "cell_gap_summary",
        "backend_order",
        "support_state_order",
        "publish_paths",
        "cpp_drilldown_docs",
        "doc_role_split",
        "maintenance_order",
        "rollout_tier_order",
        "rollout_tiers",
        "summary_source",
        "summary_keys",
        "row_keys",
        "matrix_rows",
    }:
        issues.append("manifest keys drifted")
    if manifest["source_manifests"] != contract_mod.PARITY_MATRIX_SOURCE_MANIFESTS:
        issues.append("manifest source_manifests drifted")
    if manifest["source_destination"] != contract_mod.PARITY_MATRIX_SOURCE_DESTINATION:
        issues.append("manifest source_destination drifted")
    if manifest["implementation_phase"] != contract_mod.PARITY_MATRIX_IMPLEMENTATION_PHASE:
        issues.append("manifest implementation_phase drifted")
    if manifest["cell_schema_status"] != contract_mod.PARITY_MATRIX_CELL_SCHEMA_STATUS:
        issues.append("manifest cell_schema_status drifted")
    if manifest["cell_schema"] != {
        "schema_version": contract_mod.PARITY_MATRIX_CELL_SCHEMA_VERSION,
        "collection_key": contract_mod.PARITY_MATRIX_CELL_COLLECTION_KEY,
        "required_keys": list(contract_mod.PARITY_MATRIX_CELL_REQUIRED_KEYS),
        "optional_keys": list(contract_mod.PARITY_MATRIX_CELL_OPTIONAL_KEYS),
        "support_state_order": list(contract_mod.PARITY_MATRIX_SUPPORT_STATE_ORDER),
        "evidence_kind_order": list(contract_mod.PARITY_MATRIX_CELL_EVIDENCE_KIND_ORDER),
        "allowed_evidence_kinds_by_state": {
            state: list(kinds)
            for state, kinds in contract_mod.PARITY_MATRIX_ALLOWED_EVIDENCE_KINDS_BY_STATE.items()
        },
    }:
        issues.append("manifest cell_schema drifted")
    if manifest["cell_gap_summary"] != contract_mod.PARITY_MATRIX_CELL_GAP_SUMMARY:
        issues.append("manifest cell_gap_summary drifted")
    if manifest["backend_order"] != list(contract_mod.PARITY_MATRIX_BACKEND_ORDER):
        issues.append("manifest backend_order drifted")
    if manifest["support_state_order"] != list(contract_mod.PARITY_MATRIX_SUPPORT_STATE_ORDER):
        issues.append("manifest support_state_order drifted")
    if manifest["publish_paths"] != contract_mod.PARITY_MATRIX_PUBLISH_PATHS:
        issues.append("manifest publish_paths drifted")
    if manifest["cpp_drilldown_docs"] != contract_mod.PARITY_MATRIX_CPP_DRILLDOWN_DOCS:
        issues.append("manifest cpp_drilldown_docs drifted")
    if manifest["doc_role_split"] != contract_mod.PARITY_MATRIX_DOC_ROLE_SPLIT:
        issues.append("manifest doc_role_split drifted")
    if manifest["maintenance_order"] != list(contract_mod.PARITY_MATRIX_DOC_MAINTENANCE_ORDER):
        issues.append("manifest maintenance_order drifted")
    if manifest["rollout_tier_order"] != list(contract_mod.PARITY_MATRIX_ROLLOUT_TIER_ORDER):
        issues.append("manifest rollout_tier_order drifted")
    if manifest["rollout_tiers"] != [
        {
            "tier": entry["tier"],
            "backend_order": list(entry["backend_order"]),
            "downstream_task": entry["downstream_task"],
            "downstream_plan": entry["downstream_plan"],
        }
        for entry in contract_mod.PARITY_MATRIX_ROLLOUT_TIERS
    ]:
        issues.append("manifest rollout_tiers drifted")
    if manifest["summary_source"] != contract_mod.PARITY_MATRIX_SUMMARY_SOURCE:
        issues.append("manifest summary_source drifted")
    if manifest["summary_keys"] != list(contract_mod.PARITY_MATRIX_SUMMARY_KEYS):
        issues.append("manifest summary_keys drifted")
    if manifest["row_keys"] != list(contract_mod.PARITY_MATRIX_ROW_KEYS):
        issues.append("manifest row_keys drifted")
    if len(manifest["matrix_rows"]) != len(contract_mod.iter_representative_parity_matrix_rows()):
        issues.append("manifest matrix_rows length drifted")
    for entry in manifest["matrix_rows"]:
        if [cell["backend"] for cell in entry["backend_cells"]] != list(contract_mod.PARITY_MATRIX_BACKEND_ORDER):
            issues.append(f"{entry['feature_id']}: manifest backend_cells order drifted")
    return issues


def main() -> int:
    issues = _collect_contract_issues()
    issues.extend(_collect_manifest_issues())
    issues.extend(_collect_docs_issues())
    if issues:
        print("[NG] backend parity matrix contract drift detected")
        for issue in issues:
            print(f" - {issue}")
        return 1
    print("[OK] backend parity matrix contract is fixed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
