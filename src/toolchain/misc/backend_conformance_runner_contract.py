from __future__ import annotations

from typing import Final, TypedDict

from src.toolchain.misc import backend_conformance_harness_contract as harness_mod
from src.toolchain.misc import backend_feature_contract_inventory as feature_contract_mod


REPRESENTATIVE_CONFORMANCE_RUNNER_BACKENDS: Final[tuple[str, ...]] = (
    feature_contract_mod.FIRST_CONFORMANCE_BACKEND_ORDER
)

BACKEND_SELECTABLE_RUNNER_LANES: Final[tuple[str, ...]] = (
    harness_mod.BACKEND_SELECTABLE_CONFORMANCE_LANES
)

RUNNER_LANE_ENTRYPOINTS: Final[dict[str, str]] = {
    "emit": "src/pytra-cli.py",
    "runtime": "tools/check/runtime_parity_check.py",
}

RUNNER_SMOKE_FILES: Final[dict[str, str]] = {
    "cpp": "tools/unittest/emit/cpp/test_py2cpp_features.py",
    "rs": "tools/unittest/emit/rs/test_py2rs_smoke.py",
    "cs": "tools/unittest/emit/cs/test_py2cs_smoke.py",
}


class RepresentativeConformanceRunnerEntry(TypedDict):
    backend: str
    selectable_lanes: tuple[str, ...]
    emit_target: str
    runtime_target: str
    emit_entrypoint: str
    runtime_entrypoint: str
    smoke_file: str


REPRESENTATIVE_CONFORMANCE_RUNNER_INVENTORY: Final[
    tuple[RepresentativeConformanceRunnerEntry, ...]
] = tuple(
    {
        "backend": backend,
        "selectable_lanes": BACKEND_SELECTABLE_RUNNER_LANES,
        "emit_target": backend,
        "runtime_target": backend,
        "emit_entrypoint": RUNNER_LANE_ENTRYPOINTS["emit"],
        "runtime_entrypoint": RUNNER_LANE_ENTRYPOINTS["runtime"],
        "smoke_file": RUNNER_SMOKE_FILES[backend],
    }
    for backend in REPRESENTATIVE_CONFORMANCE_RUNNER_BACKENDS
)


def iter_representative_conformance_runner_inventory() -> tuple[RepresentativeConformanceRunnerEntry, ...]:
    return REPRESENTATIVE_CONFORMANCE_RUNNER_INVENTORY


def build_backend_conformance_runner_manifest() -> dict[str, object]:
    return {
        "inventory_version": 1,
        "backend_order": list(REPRESENTATIVE_CONFORMANCE_RUNNER_BACKENDS),
        "selectable_lanes": list(BACKEND_SELECTABLE_RUNNER_LANES),
        "lane_entrypoints": dict(RUNNER_LANE_ENTRYPOINTS),
        "runner_inventory": [
            {
                "backend": entry["backend"],
                "selectable_lanes": list(entry["selectable_lanes"]),
                "emit_target": entry["emit_target"],
                "runtime_target": entry["runtime_target"],
                "emit_entrypoint": entry["emit_entrypoint"],
                "runtime_entrypoint": entry["runtime_entrypoint"],
                "smoke_file": entry["smoke_file"],
            }
            for entry in iter_representative_conformance_runner_inventory()
        ],
    }
