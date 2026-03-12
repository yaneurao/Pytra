#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.toolchain.compiler import noncpp_runtime_layout_contract as contract_mod


MANIFEST_PATH = ROOT / "tools" / "runtime_generation_manifest.json"
CS_EMITTER_PATH = ROOT / "src" / "backends" / "cs" / "emitter" / "cs_emitter.py"
CS_BUILD_PROFILE_PATH = ROOT / "src" / "toolchain" / "compiler" / "pytra_cli_profiles.py"
CS_SMOKE_PATH = ROOT / "test" / "unit" / "backends" / "cs" / "test_py2cs_smoke.py"


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _manifest_text() -> str:
    return _load_text(MANIFEST_PATH)


def _collect_contract_issues() -> list[str]:
    issues: list[str] = []
    entries = contract_mod.iter_cs_std_lane_ownership()
    module_names = tuple(entry["module_name"] for entry in entries)
    if module_names != ("json", "pathlib", "math", "re", "argparse", "enum"):
        issues.append("cs std lane ownership module order drifted")
    if contract_mod.CS_STD_GENERATED_STATE_ORDER != (
        "canonical_generated",
        "compare_artifact",
        "blocked",
        "no_runtime_module",
    ):
        issues.append("generated state order drifted")
    if contract_mod.CS_STD_CANONICAL_LANE_ORDER != (
        "generated/std",
        "native/std",
        "native/built_in",
        "no_runtime_module",
    ):
        issues.append("canonical lane order drifted")
    return issues


def _collect_csharp_lane_issues() -> list[str]:
    issues: list[str] = []
    manifest_text = _manifest_text()
    emitter_text = _load_text(CS_EMITTER_PATH)
    build_profile_text = _load_text(CS_BUILD_PROFILE_PATH)
    smoke_text = _load_text(CS_SMOKE_PATH)

    for entry in contract_mod.iter_cs_std_lane_ownership():
        module_name = entry["module_name"]
        canonical_lane = entry["canonical_lane"]
        generated_state = entry["generated_std_state"]
        generated_rel = entry["generated_std_rel"]
        native_rel = entry["native_rel"]
        fixture_rel = entry["representative_fixture"]
        if not (ROOT / fixture_rel).exists():
            issues.append(f"missing representative fixture: {module_name}: {fixture_rel}")
        for needle in entry["smoke_guard_needles"]:
            if needle not in smoke_text:
                issues.append(f"missing C# smoke guard for {module_name}: {needle}")

        if generated_state == "compare_artifact":
            if generated_rel == "":
                issues.append(f"compare_artifact lane missing generated path: {module_name}")
            elif not (ROOT / generated_rel).exists():
                issues.append(f"missing generated compare artifact: {module_name}: {generated_rel}")
            else:
                generated_text = _load_text(ROOT / generated_rel)
                if "generated-by: tools/gen_runtime_from_manifest.py" not in generated_text:
                    issues.append(f"generated compare artifact missing marker: {module_name}: {generated_rel}")
            if generated_rel not in manifest_text:
                issues.append(f"manifest missing C# std output path: {module_name}")
        elif generated_state == "blocked":
            if generated_rel != "":
                issues.append(f"blocked module must not set generated path: {module_name}")
            if f"src/runtime/cs/generated/std/{module_name}.cs" in manifest_text:
                issues.append(f"blocked module unexpectedly owns a C# generated std target: {module_name}")
        elif generated_state == "no_runtime_module":
            if generated_rel != "":
                issues.append(f"no_runtime_module must not set generated path: {module_name}")
            if f"src/runtime/cs/generated/std/{module_name}.cs" in manifest_text:
                issues.append(f"no_runtime_module unexpectedly owns a C# generated std target: {module_name}")
        else:
            issues.append(f"unknown generated state: {module_name}: {generated_state}")

        if canonical_lane == "native/std":
            if native_rel == "":
                issues.append(f"native/std lane missing native path: {module_name}")
            elif not (ROOT / native_rel).exists():
                issues.append(f"missing native/std module: {module_name}: {native_rel}")
            if native_rel not in build_profile_text:
                issues.append(f"native/std module missing from C# build profile: {module_name}")
            if generated_rel != "" and generated_rel in build_profile_text:
                issues.append(f"generated compare artifact leaked into C# build profile: {module_name}")
            if entry["canonical_runtime_symbol"] != "" and entry["canonical_runtime_symbol"] not in emitter_text and entry["canonical_runtime_symbol"] not in smoke_text:
                issues.append(f"native/std canonical runtime symbol not referenced: {module_name}")
            if module_name == "json" and "Pytra.CsModule.json." not in emitter_text:
                issues.append("json canonical emitter lane drifted from Pytra.CsModule.json")
        elif canonical_lane == "native/built_in":
            if native_rel == "":
                issues.append(f"native/built_in lane missing native path: {module_name}")
            elif not (ROOT / native_rel).exists():
                issues.append(f"missing native/built_in module: {module_name}: {native_rel}")
            if native_rel not in build_profile_text:
                issues.append(f"native/built_in module missing from C# build profile: {module_name}")
            if generated_rel != "" and generated_rel in build_profile_text:
                issues.append(f"generated compare artifact leaked into C# build profile: {module_name}")
            if entry["canonical_runtime_symbol"] != "" and entry["canonical_runtime_symbol"] not in emitter_text and entry["canonical_runtime_symbol"] not in smoke_text:
                issues.append(f"native/built_in canonical runtime symbol not referenced: {module_name}")
        elif canonical_lane == "no_runtime_module":
            if native_rel != "":
                issues.append(f"no_runtime_module must not set native path: {module_name}")
            generated_runtime_rel = f"src/runtime/cs/generated/std/{module_name}.cs"
            native_runtime_rel = f"src/runtime/cs/native/std/{module_name}.cs"
            if generated_runtime_rel in build_profile_text or (ROOT / generated_runtime_rel).exists():
                issues.append(f"{module_name} unexpectedly owns a generated/std runtime module")
            if native_runtime_rel in build_profile_text or (ROOT / native_runtime_rel).exists():
                issues.append(f"{module_name} unexpectedly owns a native/std runtime module")
        else:
            issues.append(f"unknown canonical lane: {module_name}: {canonical_lane}")
    if 'return "Pytra.CsModule.math"' not in emitter_text:
        issues.append("math module alias target drifted from Pytra.CsModule.math")
    if 'return "Pytra.CsModule.py_path"' not in emitter_text:
        issues.append("pathlib symbol alias target drifted from Pytra.CsModule.py_path")
    return issues


def main() -> int:
    issues = _collect_contract_issues() + _collect_csharp_lane_issues()
    if issues:
        for issue in issues:
            print("[FAIL]", issue)
        return 1
    print("[OK] non-C++ runtime layout contract is classified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
