from __future__ import annotations

from pathlib import Path
from typing import Final, TypedDict

from src.toolchain.compiler import backend_conformance_inventory as inventory_mod
from src.toolchain.compiler import backend_conformance_runner_contract as runner_mod


STDLIB_RUNTIME_PARITY_STRATEGY_KIND: Final[str] = "stdlib_module_runtime_case"
STDLIB_RUNTIME_CASE_ROOT: Final[str] = "fixture"
STDLIB_RUNTIME_RUNNER_LANE: Final[str] = "runtime"
STDLIB_RUNTIME_COMPARE_UNIT: Final[str] = inventory_mod.CONFORMANCE_LANE_COMPARE_UNITS["runtime"]
STDLIB_RUNTIME_RUNNER_ENTRYPOINT: Final[str] = runner_mod.RUNNER_LANE_ENTRYPOINTS["runtime"]
STDLIB_RUNTIME_BACKEND_ORDER: Final[tuple[str, ...]] = runner_mod.REPRESENTATIVE_CONFORMANCE_RUNNER_BACKENDS


class RepresentativeStdlibRuntimeParityEntry(TypedDict):
    feature_id: str
    module_name: str
    case_stem: str
    representative_fixture: str
    strategy_kind: str
    case_root: str
    runner_lane: str
    runner_entrypoint: str
    compare_unit: str
    representative_backends: tuple[str, ...]


def _module_name_from_feature_id(feature_id: str) -> str:
    _stdlib, module_name, _feature_name = feature_id.split(".", 2)
    return module_name


def _fixture_stem(fixture_rel: str) -> str:
    return Path(fixture_rel).stem


REPRESENTATIVE_STDLIB_RUNTIME_PARITY: Final[tuple[RepresentativeStdlibRuntimeParityEntry, ...]] = tuple(
    {
        "feature_id": entry["feature_id"],
        "module_name": _module_name_from_feature_id(entry["feature_id"]),
        "case_stem": _fixture_stem(entry["representative_fixture"]),
        "representative_fixture": entry["representative_fixture"],
        "strategy_kind": STDLIB_RUNTIME_PARITY_STRATEGY_KIND,
        "case_root": STDLIB_RUNTIME_CASE_ROOT,
        "runner_lane": STDLIB_RUNTIME_RUNNER_LANE,
        "runner_entrypoint": STDLIB_RUNTIME_RUNNER_ENTRYPOINT,
        "compare_unit": STDLIB_RUNTIME_COMPARE_UNIT,
        "representative_backends": STDLIB_RUNTIME_BACKEND_ORDER,
    }
    for entry in inventory_mod.iter_representative_conformance_fixture_inventory()
    if entry["fixture_class"] == "pytra_std"
)


def iter_representative_stdlib_runtime_parity() -> tuple[RepresentativeStdlibRuntimeParityEntry, ...]:
    return REPRESENTATIVE_STDLIB_RUNTIME_PARITY


def build_backend_conformance_runtime_parity_manifest() -> dict[str, object]:
    return {
        "inventory_version": 1,
        "strategy_kind": STDLIB_RUNTIME_PARITY_STRATEGY_KIND,
        "case_root": STDLIB_RUNTIME_CASE_ROOT,
        "runner_lane": STDLIB_RUNTIME_RUNNER_LANE,
        "runner_entrypoint": STDLIB_RUNTIME_RUNNER_ENTRYPOINT,
        "compare_unit": STDLIB_RUNTIME_COMPARE_UNIT,
        "backend_order": list(STDLIB_RUNTIME_BACKEND_ORDER),
        "stdlib_runtime_modules": [
            {
                "feature_id": entry["feature_id"],
                "module_name": entry["module_name"],
                "case_stem": entry["case_stem"],
                "representative_fixture": entry["representative_fixture"],
                "strategy_kind": entry["strategy_kind"],
                "case_root": entry["case_root"],
                "runner_lane": entry["runner_lane"],
                "runner_entrypoint": entry["runner_entrypoint"],
                "compare_unit": entry["compare_unit"],
                "representative_backends": list(entry["representative_backends"]),
            }
            for entry in iter_representative_stdlib_runtime_parity()
        ],
    }
