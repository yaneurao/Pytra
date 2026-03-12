#!/usr/bin/env python3
"""Guard source-of-truth runtime policy for std/utils modules.

Policy (phase-1):
- Canonical module logic must come from `src/pytra/std/*.py` or `src/pytra/utils/*.py`.
- Handwritten runtime implementations of guarded module symbols are prohibited outside
  `src/runtime/*/pytra-gen/**` and `src/runtime/{rs,cs}/generated/**`.
- Existing debt is tracked explicitly in `tools/runtime_std_sot_allowlist.txt`.

Current guarded module set:
- json (`pyJsonLoads` / `pyJsonDumps`)
- assertions (`py_assert_*`)
- re (`Match` / `strip_group`)
- C++ std/utils runtime shape (`generated/` + `pytra/` ownership + required manual impl split)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = ROOT / "src" / "runtime"
ALLOWLIST_PATH = ROOT / "tools" / "runtime_std_sot_allowlist.txt"

TARGET_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".go",
    ".h",
    ".hpp",
    ".java",
    ".js",
    ".kt",
    ".lua",
    ".nim",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".scala",
    ".swift",
    ".ts",
}

@dataclass(frozen=True)
class GuardRule:
    text_patterns: list[re.Pattern[str]]
    path_patterns: list[re.Pattern[str]]


RULES: dict[str, GuardRule] = {
    "json": GuardRule(
        text_patterns=[
            re.compile(r"\bpyJsonLoads\b"),
            re.compile(r"\bpyJsonDumps\b"),
            re.compile(r"\bclass\s+json\b"),
        ],
        path_patterns=[],
    ),
    "assertions": GuardRule(
        text_patterns=[
            re.compile(r"\bpy_assert_true\b"),
            re.compile(r"\bpy_assert_eq\b"),
            re.compile(r"\bpy_assert_all\b"),
            re.compile(r"\bpy_assert_stdout\b"),
        ],
        path_patterns=[
            re.compile(r"/utils/assertions\.[^/]+$"),
        ],
    ),
    "re": GuardRule(
        text_patterns=[
            re.compile(r"\bstrip_group\s*\("),
            re.compile(r"\bclass\s+Match\b"),
            re.compile(r"\bstruct\s+Match\b"),
        ],
        path_patterns=[
            re.compile(r"/std/re\.[^/]+$"),
        ],
    ),
}

CPP_GENERATED_STD_MODULES = [
    "argparse",
    "glob",
    "json",
    "math",
    "os",
    "os_path",
    "pathlib",
    "random",
    "re",
    "sys",
    "time",
    "timeit",
]

CPP_HEADER_ONLY_STD_MODULES = {
    "math",
    "glob",
    "os",
    "os_path",
    "sys",
    "time",
}

CPP_STD_HEADER_LOCATIONS: dict[str, str] = {
    "argparse": "src/runtime/cpp/generated/std/argparse.h",
    "glob": "src/runtime/cpp/generated/std/glob.h",
    "json": "src/runtime/cpp/generated/std/json.h",
    "math": "src/runtime/cpp/generated/std/math.h",
    "os": "src/runtime/cpp/generated/std/os.h",
    "os_path": "src/runtime/cpp/generated/std/os_path.h",
    "pathlib": "src/runtime/cpp/generated/std/pathlib.h",
    "random": "src/runtime/cpp/generated/std/random.h",
    "re": "src/runtime/cpp/generated/std/re.h",
    "sys": "src/runtime/cpp/generated/std/sys.h",
    "time": "src/runtime/cpp/generated/std/time.h",
    "timeit": "src/runtime/cpp/generated/std/timeit.h",
}

CPP_STD_SOURCE_LOCATIONS: dict[str, str] = {
    "argparse": "src/runtime/cpp/generated/std/argparse.cpp",
    "glob": "src/runtime/cpp/generated/std/glob.cpp",
    "json": "src/runtime/cpp/generated/std/json.cpp",
    "os": "src/runtime/cpp/generated/std/os.cpp",
    "os_path": "src/runtime/cpp/generated/std/os_path.cpp",
    "pathlib": "src/runtime/cpp/generated/std/pathlib.cpp",
    "random": "src/runtime/cpp/generated/std/random.cpp",
    "re": "src/runtime/cpp/generated/std/re.cpp",
    "sys": "src/runtime/cpp/generated/std/sys.cpp",
    "time": "src/runtime/cpp/generated/std/time.cpp",
    "timeit": "src/runtime/cpp/generated/std/timeit.cpp",
}

CPP_GENERATED_UTILS_MODULES = [
    "assertions",
    "gif",
    "png",
]

CPP_UTILS_HEADER_LOCATIONS: dict[str, str] = {
    "assertions": "src/runtime/cpp/generated/utils/assertions.h",
    "gif": "src/runtime/cpp/generated/utils/gif.h",
    "png": "src/runtime/cpp/generated/utils/png.h",
}

CPP_UTILS_SOURCE_LOCATIONS: dict[str, str] = {
    "assertions": "src/runtime/cpp/generated/utils/assertions.cpp",
    "gif": "src/runtime/cpp/generated/utils/gif.cpp",
    "png": "src/runtime/cpp/generated/utils/png.cpp",
}

# module basename -> canonical Python source path.
CPP_CANONICAL_SOURCE_BY_MODULE: dict[str, str] = {
    "argparse": "src/pytra/std/argparse.py",
    "glob": "src/pytra/std/glob.py",
    "json": "src/pytra/std/json.py",
    "math": "src/pytra/std/math.py",
    "os": "src/pytra/std/os.py",
    "os_path": "src/pytra/std/os_path.py",
    "pathlib": "src/pytra/std/pathlib.py",
    "random": "src/pytra/std/random.py",
    "re": "src/pytra/std/re.py",
    "sys": "src/pytra/std/sys.py",
    "time": "src/pytra/std/time.py",
    "timeit": "src/pytra/std/timeit.py",
    "assertions": "src/pytra/utils/assertions.py",
    "gif": "src/pytra/utils/gif.py",
    "png": "src/pytra/utils/png.py",
}

# required handwritten native companion files.
CPP_REQUIRED_CORE_IMPL_FILES: dict[str, str] = {
    "glob.cpp": "src/runtime/cpp/native/std/glob.cpp",
    "math.cpp": "src/runtime/cpp/native/std/math.cpp",
    "os.cpp": "src/runtime/cpp/native/std/os.cpp",
    "os_path.cpp": "src/runtime/cpp/native/std/os_path.cpp",
    "sys.cpp": "src/runtime/cpp/native/std/sys.cpp",
    "time.cpp": "src/runtime/cpp/native/std/time.cpp",
}

CPP_ROOT_GENERATED_RUNTIME_FILES: set[str] = set()
CPP_ROOT_GENERATED_RUNTIME_FILES.update(CPP_STD_HEADER_LOCATIONS.values())
CPP_ROOT_GENERATED_RUNTIME_FILES.update(CPP_STD_SOURCE_LOCATIONS.values())
CPP_ROOT_GENERATED_RUNTIME_FILES.update(CPP_UTILS_HEADER_LOCATIONS.values())
CPP_ROOT_GENERATED_RUNTIME_FILES.update(CPP_UTILS_SOURCE_LOCATIONS.values())


def _parse_allowlist() -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    if not ALLOWLIST_PATH.exists():
        return out
    for line in ALLOWLIST_PATH.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        parts = s.split()
        if len(parts) != 2:
            raise RuntimeError(
                "invalid allowlist line (expected: '<module> <path>'): " + s
            )
        module_name, rel_path = parts
        if module_name not in RULES:
            raise RuntimeError(
                f"allowlist has unknown module '{module_name}': {rel_path}"
            )
        if rel_path.startswith("/"):
            raise RuntimeError("allowlist path must be repository-relative: " + rel_path)
        out.setdefault(module_name, set()).add(rel_path)
    return out


def _iter_runtime_files() -> list[Path]:
    out: list[Path] = []
    if not RUNTIME_ROOT.exists():
        return out
    for p in sorted(RUNTIME_ROOT.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix not in TARGET_SUFFIXES:
            continue
        out.append(p)
    return out


def _is_generated_runtime(rel_path: str) -> bool:
    # Keep this strict and path-based.
    if "/pytra-gen/" in ("/" + rel_path):
        return True
    if rel_path.startswith("src/runtime/rs/generated/"):
        return True
    if rel_path.startswith("src/runtime/cs/generated/"):
        return True
    if rel_path.startswith("src/runtime/cpp/pytra/"):
        return True
    # C++ generated std/utils files.
    return rel_path in CPP_ROOT_GENERATED_RUNTIME_FILES


def _check_cpp_runtime_shape(violations: list[str]) -> None:
    # 1) Generated std/utils modules must exist under runtime/cpp/* with canonical source marker.
    for module_name in CPP_GENERATED_STD_MODULES:
        source_rel = CPP_CANONICAL_SOURCE_BY_MODULE[module_name]
        for ext in ("h", "cpp"):
            if ext == "cpp" and module_name in CPP_HEADER_ONLY_STD_MODULES:
                custom_src_rel = CPP_STD_SOURCE_LOCATIONS.get(module_name)
                if isinstance(custom_src_rel, str) and custom_src_rel != "":
                    gen_path = ROOT / custom_src_rel
                    if gen_path.exists():
                        violations.append(
                            f"[{module_name}] header-only module must not generate runtime source: {custom_src_rel}"
                        )
                continue
            custom_hdr_rel = CPP_STD_HEADER_LOCATIONS.get(module_name)
            custom_src_rel = CPP_STD_SOURCE_LOCATIONS.get(module_name)
            gen_rel = custom_hdr_rel if ext == "h" else custom_src_rel
            if not isinstance(gen_rel, str) or gen_rel == "":
                violations.append(f"[{module_name}] missing configured runtime location for .{ext}")
                continue
            gen_path = ROOT / gen_rel
            if not gen_path.exists():
                violations.append(f"[{module_name}] missing generated runtime file: {gen_rel}")
                continue
            txt = gen_path.read_text(encoding="utf-8", errors="ignore")
            marker = "source: " + source_rel
            if marker not in txt:
                violations.append(
                    f"[{module_name}] {gen_rel} missing canonical source marker ({marker})"
                )

    for module_name in CPP_GENERATED_UTILS_MODULES:
        source_rel = CPP_CANONICAL_SOURCE_BY_MODULE[module_name]
        for ext in ("h", "cpp"):
            custom_hdr_rel = CPP_UTILS_HEADER_LOCATIONS.get(module_name)
            custom_src_rel = CPP_UTILS_SOURCE_LOCATIONS.get(module_name)
            gen_rel = custom_hdr_rel if ext == "h" else custom_src_rel
            if not isinstance(gen_rel, str) or gen_rel == "":
                violations.append(f"[{module_name}] missing configured runtime location for .{ext}")
                continue
            gen_path = ROOT / gen_rel
            if not gen_path.exists():
                violations.append(f"[{module_name}] missing generated runtime file: {gen_rel}")
                continue
            txt = gen_path.read_text(encoding="utf-8", errors="ignore")
            marker = "source: " + source_rel
            if marker not in txt:
                violations.append(
                    f"[{module_name}] {gen_rel} missing canonical source marker ({marker})"
                )

    # 2) Required handwritten impl split must remain under native/std as plain `.cpp`.
    for _name, core_rel in CPP_REQUIRED_CORE_IMPL_FILES.items():
        core_path = ROOT / core_rel
        if not core_path.exists():
            violations.append(f"[cpp-manual-impl] missing manual implementation file: {core_rel}")


def main() -> int:
    allow = _parse_allowlist()

    violations: list[str] = []
    stale_allow: list[str] = []
    used_allow: set[tuple[str, str]] = set()

    for p in _iter_runtime_files():
        rel = str(p.relative_to(ROOT)).replace("\\\\", "/")
        if _is_generated_runtime(rel):
            continue
        txt = p.read_text(encoding="utf-8", errors="ignore")
        for module_name, rule in RULES.items():
            hit = False
            for path_pat in rule.path_patterns:
                if path_pat.search(rel):
                    hit = True
                    break
            if not hit:
                for txt_pat in rule.text_patterns:
                    if txt_pat.search(txt):
                        hit = True
                        break
            if not hit:
                continue
            allowed_paths = allow.get(module_name, set())
            if rel in allowed_paths:
                used_allow.add((module_name, rel))
                continue
            violations.append(f"[{module_name}] {rel}")

    _check_cpp_runtime_shape(violations)

    for module_name, paths in allow.items():
        for rel in sorted(paths):
            if (module_name, rel) not in used_allow:
                stale_allow.append(f"[{module_name}] {rel}")

    if violations or stale_allow:
        print("[FAIL] runtime std/utils source-of-truth guard failed")
        if violations:
            print("  disallowed handwritten runtime implementation detected:")
            for item in violations:
                print("    - " + item)
            print("  fix: move implementation to src/pytra/* canonical source and generate runtime artifacts")
        if stale_allow:
            print("  stale allowlist entries (remove them):")
            for item in stale_allow:
                print("    - " + item)
        return 1

    tracked = sum(len(v) for v in allow.values())
    print("[OK] runtime std/utils source-of-truth guard passed")
    print(f"  rules: {', '.join(sorted(RULES.keys()))}")
    print(f"  allowlist entries used: {tracked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
