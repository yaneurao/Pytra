"""Cross-target contract for runtime `@extern` ownership realignment."""

from __future__ import annotations

from pathlib import Path
from typing import Final, TypedDict

from src.toolchain.frontends import extern_var
from src.toolchain.frontends import runtime_symbol_index
from src.toolchain.compiler import multilang_extern_runtime_realign_inventory as inventory_mod


ROOT = Path(__file__).resolve().parents[3]


EXTERN_CATEGORY_ORDER: Final[tuple[str, ...]] = (
    "runtime_extern_declaration_only",
    "native_owner_implementation",
    "ambient_global_extern",
    "host_fallback_extern_expr",
)

RUNTIME_EXTERN_CONTRACT_ALLOWED_KEYS: Final[tuple[str, ...]] = (
    "schema_version",
    "function_symbols",
    "value_symbols",
)

RUNTIME_EXTERN_SYMBOL_ALLOWED_KEYS: Final[tuple[str, ...]] = (
    "schema_version",
    "kind",
)

RUNTIME_EXTERN_SYMBOL_KIND_ORDER: Final[tuple[str, ...]] = ("function", "value")

AMBIENT_EXTERN_TARGETS: Final[tuple[str, ...]] = tuple(
    sorted(extern_var._AMBIENT_EXTERN_SUPPORTED_TARGETS)
)


def _inventory_module_id_to_runtime_module_id(module_id: str) -> str:
    if module_id.startswith("std/"):
        tail = module_id[len("std/") :].replace("/", ".")
        return "pytra.std." + tail
    if module_id.startswith("built_in/"):
        tail = module_id[len("built_in/") :].replace("/", ".")
        return "pytra.built_in." + tail
    return module_id.replace("/", ".")


RUNTIME_EXTERN_MODULE_ORDER: Final[tuple[str, ...]] = tuple(
    _inventory_module_id_to_runtime_module_id(module_id)
    for module_id in inventory_mod.MODULE_ORDER
)

SPEC_WIRING_RULES_JA: Final[dict[str, tuple[str, ...]]] = {
    "docs/ja/spec/spec-abi.md": (
        "runtime SoT 上の `@extern` は declaration-only metadata であり、target 実装 owner を表さない。",
        "native owner 実装の所在は runtime layout / manifest / runtime symbol index が担う。",
        "ambient global 変数宣言の `extern()` / `extern(\"symbol\")` は runtime `@extern` とは別系統として扱う。",
    ),
    "docs/ja/spec/spec-runtime.md": (
        "`extern_contract_v1` / `extern_v1` は declaration-only metadata として扱い、native owner 実装の所在を表してはならない。",
        "ambient global 変数宣言の `extern()` / `extern(\"symbol\")` は runtime SoT `@extern` とは別系統であり、runtime symbol index の native owner 決定へ混ぜてはならない。",
    ),
}

SPEC_WIRING_RULES_EN: Final[dict[str, tuple[str, ...]]] = {
    "docs/en/spec/spec-abi.md": (
        "runtime-SoT `@extern` is declaration-only metadata and does not identify the target implementation owner.",
        "runtime layout / manifest / runtime symbol index define the native implementation owner.",
        "ambient-global `extern()` / `extern(\"symbol\")` is a separate category from runtime `@extern`.",
    ),
    "docs/en/spec/spec-runtime.md": (
        "`extern_contract_v1` / `extern_v1` must stay declaration-only metadata and must not encode the native implementation owner.",
        "Ambient-global `extern()` / `extern(\"symbol\")` is separate from runtime-SoT `@extern` and must not participate in runtime symbol index ownership decisions.",
    ),
}

PLAN_WIRING_RULES_JA: Final[dict[str, tuple[str, ...]]] = {
    "docs/ja/plans/p2-multilang-extern-runtime-realign.md": (
        "`S1-02` として、runtime SoT `@extern` を declaration-only、native owner 実装を runtime layout / manifest / runtime symbol index、ambient global `extern()` を別系統に固定する contract/checker/spec wording を追加した。",
    ),
}

PLAN_WIRING_RULES_EN: Final[dict[str, tuple[str, ...]]] = {
    "docs/en/plans/p2-multilang-extern-runtime-realign.md": (
        "For `S1-02`, add a contract/checker/spec wording that fixes runtime-SoT `@extern` as declaration-only metadata, native ownership to runtime layout / manifest / runtime symbol index, and ambient-global `extern()` as a separate category.",
    ),
}


class RuntimeExternContractManifest(TypedDict):
    category_order: tuple[str, ...]
    ambient_targets: tuple[str, ...]
    runtime_module_order: tuple[str, ...]
    runtime_extern_contract_allowed_keys: tuple[str, ...]
    runtime_extern_symbol_allowed_keys: tuple[str, ...]
    runtime_extern_symbol_kind_order: tuple[str, ...]


def runtime_inventory_module_id_to_runtime_module_id(module_id: str) -> str:
    module_name = module_id.strip().replace("/", ".")
    if module_name.startswith("std."):
        return "pytra." + module_name
    if module_name.startswith("built_in."):
        return "pytra." + module_name
    return module_name


def build_multilang_extern_runtime_realign_contract_manifest() -> RuntimeExternContractManifest:
    return {
        "category_order": EXTERN_CATEGORY_ORDER,
        "ambient_targets": AMBIENT_EXTERN_TARGETS,
        "runtime_module_order": RUNTIME_EXTERN_MODULE_ORDER,
        "runtime_extern_contract_allowed_keys": RUNTIME_EXTERN_CONTRACT_ALLOWED_KEYS,
        "runtime_extern_symbol_allowed_keys": RUNTIME_EXTERN_SYMBOL_ALLOWED_KEYS,
        "runtime_extern_symbol_kind_order": RUNTIME_EXTERN_SYMBOL_KIND_ORDER,
    }


def iter_runtime_extern_module_contract_rows() -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for module_id in RUNTIME_EXTERN_MODULE_ORDER:
        runtime_module_id = runtime_inventory_module_id_to_runtime_module_id(module_id)
        extern_contract = runtime_symbol_index.lookup_runtime_module_extern_contract(runtime_module_id)
        rows.append(
            {
                "module_id": module_id,
                "runtime_module_id": runtime_module_id,
                "extern_contract": extern_contract,
            }
        )
    return tuple(rows)
