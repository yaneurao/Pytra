from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from toolchain.compiler import multilang_extern_runtime_realign_contract as contract_mod
from toolchain.frontends import extern_var
from toolchain.frontends import runtime_symbol_index


def _collect_contract_shape_issues() -> list[str]:
    issues: list[str] = []
    manifest = contract_mod.build_multilang_extern_runtime_realign_contract_manifest()
    if manifest["category_order"] != contract_mod.EXTERN_CATEGORY_ORDER:
        issues.append("extern category order drifted from fixed contract")
    if manifest["ambient_targets"] != contract_mod.AMBIENT_EXTERN_TARGETS:
        issues.append("ambient extern target order drifted from fixed contract")
    if manifest["runtime_module_order"] != contract_mod.RUNTIME_EXTERN_MODULE_ORDER:
        issues.append("runtime extern module order drifted from fixed contract")
    if manifest["runtime_extern_contract_allowed_keys"] != contract_mod.RUNTIME_EXTERN_CONTRACT_ALLOWED_KEYS:
        issues.append("runtime extern contract keys drifted from fixed contract")
    if manifest["runtime_extern_symbol_allowed_keys"] != contract_mod.RUNTIME_EXTERN_SYMBOL_ALLOWED_KEYS:
        issues.append("runtime extern symbol keys drifted from fixed contract")
    if manifest["runtime_extern_symbol_kind_order"] != contract_mod.RUNTIME_EXTERN_SYMBOL_KIND_ORDER:
        issues.append("runtime extern symbol kinds drifted from fixed contract")
    if tuple(sorted(extern_var._AMBIENT_EXTERN_SUPPORTED_TARGETS)) != contract_mod.AMBIENT_EXTERN_TARGETS:
        issues.append("ambient extern target support drifted from fixed contract")
    return issues


def _collect_runtime_symbol_index_issues() -> list[str]:
    issues: list[str] = []
    for module_id in contract_mod.RUNTIME_EXTERN_MODULE_ORDER:
        runtime_module_id = contract_mod.runtime_inventory_module_id_to_runtime_module_id(module_id)
        module_doc = runtime_symbol_index.lookup_runtime_module_doc(runtime_module_id)
        if not module_doc:
            issues.append(f"runtime extern module missing from runtime symbol index: {module_id} -> {runtime_module_id}")
            continue
        extern_contract = runtime_symbol_index.lookup_runtime_module_extern_contract(runtime_module_id)
        if not extern_contract:
            issues.append(f"runtime extern contract missing: {module_id} -> {runtime_module_id}")
            continue
        if set(extern_contract.keys()) != set(contract_mod.RUNTIME_EXTERN_CONTRACT_ALLOWED_KEYS):
            issues.append(f"runtime extern contract keys drifted: {module_id} -> {runtime_module_id}")
        if extern_contract.get("schema_version") != 1:
            issues.append(f"runtime extern contract schema_version drifted: {module_id} -> {runtime_module_id}")
        function_symbols = extern_contract.get("function_symbols")
        value_symbols = extern_contract.get("value_symbols")
        if not isinstance(function_symbols, list):
            issues.append(f"runtime extern function_symbols are not a list: {module_id} -> {runtime_module_id}")
            continue
        if not isinstance(value_symbols, list):
            issues.append(f"runtime extern value_symbols are not a list: {module_id} -> {runtime_module_id}")
            continue
        seen_symbols: set[str] = set()
        for symbol_name in function_symbols:
            if not isinstance(symbol_name, str) or symbol_name.strip() == "":
                issues.append(f"runtime extern function symbol is invalid: {module_id} -> {runtime_module_id}")
                continue
            if symbol_name in seen_symbols:
                issues.append(f"duplicate runtime extern symbol in contract: {module_id} -> {runtime_module_id}: {symbol_name}")
                continue
            seen_symbols.add(symbol_name)
            extern_doc = runtime_symbol_index.lookup_runtime_symbol_extern_doc(runtime_module_id, symbol_name)
            if not extern_doc:
                issues.append(f"runtime extern symbol doc missing: {module_id} -> {runtime_module_id}: {symbol_name}")
                continue
            if set(extern_doc.keys()) != set(contract_mod.RUNTIME_EXTERN_SYMBOL_ALLOWED_KEYS):
                issues.append(f"runtime extern symbol keys drifted: {module_id} -> {runtime_module_id}: {symbol_name}")
            if extern_doc.get("schema_version") != 1:
                issues.append(f"runtime extern symbol schema_version drifted: {module_id} -> {runtime_module_id}: {symbol_name}")
            if extern_doc.get("kind") != "function":
                issues.append(f"runtime extern function symbol kind drifted: {module_id} -> {runtime_module_id}: {symbol_name}")
        for symbol_name in value_symbols:
            if not isinstance(symbol_name, str) or symbol_name.strip() == "":
                issues.append(f"runtime extern value symbol is invalid: {module_id} -> {runtime_module_id}")
                continue
            if symbol_name in seen_symbols:
                issues.append(f"duplicate runtime extern symbol in contract: {module_id} -> {runtime_module_id}: {symbol_name}")
                continue
            seen_symbols.add(symbol_name)
            extern_doc = runtime_symbol_index.lookup_runtime_symbol_extern_doc(runtime_module_id, symbol_name)
            if not extern_doc:
                issues.append(f"runtime extern symbol doc missing: {module_id} -> {runtime_module_id}: {symbol_name}")
                continue
            if set(extern_doc.keys()) != set(contract_mod.RUNTIME_EXTERN_SYMBOL_ALLOWED_KEYS):
                issues.append(f"runtime extern symbol keys drifted: {module_id} -> {runtime_module_id}: {symbol_name}")
            if extern_doc.get("schema_version") != 1:
                issues.append(f"runtime extern symbol schema_version drifted: {module_id} -> {runtime_module_id}: {symbol_name}")
            if extern_doc.get("kind") != "value":
                issues.append(f"runtime extern value symbol kind drifted: {module_id} -> {runtime_module_id}: {symbol_name}")
    return issues


def _collect_doc_wiring_issues() -> list[str]:
    issues: list[str] = []
    for rel, needles in contract_mod.SPEC_WIRING_RULES_JA.items():
        text = (ROOT / rel).read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                issues.append(f"missing ja spec extern contract wording: {rel}: {needle}")
    for rel, needles in contract_mod.SPEC_WIRING_RULES_EN.items():
        text = (ROOT / rel).read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                issues.append(f"missing en spec extern contract wording: {rel}: {needle}")
    for rel, needles in contract_mod.PLAN_WIRING_RULES_JA.items():
        text = (ROOT / rel).read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                issues.append(f"missing ja plan extern contract wording: {rel}: {needle}")
    for rel, needles in contract_mod.PLAN_WIRING_RULES_EN.items():
        text = (ROOT / rel).read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                issues.append(f"missing en plan extern contract wording: {rel}: {needle}")
    return issues


def main() -> int:
    issues = (
        _collect_contract_shape_issues()
        + _collect_runtime_symbol_index_issues()
        + _collect_doc_wiring_issues()
    )
    if issues:
        for issue in issues:
            print("[FAIL]", issue)
        return 1
    print("[OK] multilang extern runtime realign contract is locked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
