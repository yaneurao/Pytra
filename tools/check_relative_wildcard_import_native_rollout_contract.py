#!/usr/bin/env python3
"""Validate the relative wildcard import native rollout contract."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from toolchain.compiler.relative_wildcard_import_native_rollout_contract import (
    RELATIVE_WILDCARD_IMPORT_NATIVE_BACKENDS_V1,
    RELATIVE_WILDCARD_IMPORT_NATIVE_CPP_BASELINE_V1,
    RELATIVE_WILDCARD_IMPORT_NATIVE_HANDOFF_V1,
)


EXPECTED_BACKENDS = (
    "go",
    "java",
    "kotlin",
    "lua",
    "nim",
    "php",
    "ruby",
    "scala",
    "swift",
)

EXPECTED_BUNDLE_ORDER = (
    "native_path_bundle",
    "jvm_package_bundle",
    "longtail_native_bundle",
)


def validate_relative_wildcard_import_native_rollout_contract() -> None:
    cpp = RELATIVE_WILDCARD_IMPORT_NATIVE_CPP_BASELINE_V1
    if cpp != {
        "backend": "cpp",
        "current_contract_state": "build_run_locked",
        "current_evidence_lane": "multi_file_build_run",
        "representative_import_form": "from .helper import *",
    }:
        raise SystemExit("relative wildcard import cpp baseline drifted")
    seen = tuple(row["backend"] for row in RELATIVE_WILDCARD_IMPORT_NATIVE_BACKENDS_V1)
    if seen != EXPECTED_BACKENDS:
        raise SystemExit(
            "relative wildcard import native backend inventory drifted: "
            f"expected={EXPECTED_BACKENDS}, got={seen}"
        )
    transpile_bundle = {"go", "java", "kotlin", "lua", "nim", "php", "ruby", "scala", "swift"}
    for row in RELATIVE_WILDCARD_IMPORT_NATIVE_BACKENDS_V1:
        expected_state = (
            "transpile_smoke_locked"
            if row["backend"] in transpile_bundle
            else "fail_closed_locked"
        )
        if row["current_contract_state"] != expected_state:
            raise SystemExit(
                "relative wildcard import native backend state drifted: "
                f"{row['backend']}={row['current_contract_state']}, expected={expected_state}"
            )
        if (
            row["backend"] in transpile_bundle
            and row["current_evidence_lane"] != "module_graph_bundle_transpile"
        ):
            raise SystemExit(
                "relative wildcard import native evidence lane drifted: "
                f"{row['backend']}={row['current_evidence_lane']}, expected=module_graph_bundle_transpile"
            )
        if row["fail_closed_lane"] != "backend_specific_fail_closed":
            raise SystemExit(
                "relative wildcard import native backends must stay on backend_specific_fail_closed: "
                f"{row['backend']}={row['fail_closed_lane']}"
            )
        if tuple(row["expected_error_family"]) != (
            "unsupported relative import form: wildcard import",
        ):
            raise SystemExit(
                "relative wildcard import native error family drifted: "
                f"{row['backend']}={row['expected_error_family']}"
            )
    if RELATIVE_WILDCARD_IMPORT_NATIVE_HANDOFF_V1["bundle_order"] != EXPECTED_BUNDLE_ORDER:
        raise SystemExit("relative wildcard import native bundle order drifted")
    if tuple(RELATIVE_WILDCARD_IMPORT_NATIVE_HANDOFF_V1["backends"]) != EXPECTED_BACKENDS:
        raise SystemExit("relative wildcard import native handoff backend list drifted")
    if RELATIVE_WILDCARD_IMPORT_NATIVE_HANDOFF_V1["current_bundle_state"] != "transpile_smoke_locked":
        raise SystemExit(
            "relative wildcard import native current bundle state must stay transpile_smoke_locked"
        )
    if (
        RELATIVE_WILDCARD_IMPORT_NATIVE_HANDOFF_V1["current_fail_closed_lane"]
        != "backend_specific_fail_closed"
    ):
        raise SystemExit("relative wildcard import native fail-closed lane drifted")
    if RELATIVE_WILDCARD_IMPORT_NATIVE_HANDOFF_V1["current_bundle_id"] != "longtail_native_bundle":
        raise SystemExit("relative wildcard import native current bundle id must stay longtail_native_bundle")
    if RELATIVE_WILDCARD_IMPORT_NATIVE_HANDOFF_V1["current_contract_state"] != "transpile_smoke_locked":
        raise SystemExit(
            "relative wildcard import native handoff contract state must stay transpile_smoke_locked"
        )
    for plan_path in RELATIVE_WILDCARD_IMPORT_NATIVE_HANDOFF_V1["active_plan_paths"]:
        if not (ROOT / plan_path).is_file():
            raise SystemExit(f"missing relative wildcard import native plan: {plan_path}")


if __name__ == "__main__":
    validate_relative_wildcard_import_native_rollout_contract()
