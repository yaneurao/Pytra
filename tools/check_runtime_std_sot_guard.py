#!/usr/bin/env python3
"""Guard source-of-truth runtime policy for std/utils modules.

Policy (phase-1):
- Canonical module logic must come from `src/pytra/std/*.py` or `src/pytra/utils/*.py`.
- Handwritten runtime implementations of guarded module symbols are prohibited outside
  `src/runtime/*/pytra-gen/**`.
- Existing debt is tracked explicitly in `tools/runtime_std_sot_allowlist.txt`.

Current guarded module set:
- json (`pyJsonLoads` / `pyJsonDumps`)
- assertions (`py_assert_*`)
- re (`Match` / `strip_group`)
- typing (`TypeVar`)
- C++ std/utils runtime shape (`gen` generated modules + required core impl split)
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
    "typing": GuardRule(
        text_patterns=[
            re.compile(r"\bTypeVar\s*\("),
        ],
        path_patterns=[
            re.compile(r"/std/typing\.[^/]+$"),
        ],
    ),
}

CPP_GENERATED_STD_MODULES = [
    "dataclasses",
    "glob",
    "json",
    "math",
    "os",
    "pathlib",
    "random",
    "re",
    "sys",
    "time",
    "timeit",
    "traceback",
    "typing",
]

CPP_HEADER_ONLY_STD_MODULES = {
    "math",
}

CPP_GENERATED_UTILS_MODULES = [
    "assertions",
    "gif",
    "png",
]

# module basename -> canonical Python source path.
CPP_CANONICAL_SOURCE_BY_MODULE: dict[str, str] = {
    "dataclasses": "src/pytra/std/dataclasses.py",
    "glob": "src/pytra/std/glob.py",
    "json": "src/pytra/std/json.py",
    "math": "src/pytra/std/math.py",
    "os": "src/pytra/std/os.py",
    "pathlib": "src/pytra/std/pathlib.py",
    "random": "src/pytra/std/random.py",
    "re": "src/pytra/std/re.py",
    "sys": "src/pytra/std/sys.py",
    "time": "src/pytra/std/time.py",
    "timeit": "src/pytra/std/timeit.py",
    "traceback": "src/pytra/std/traceback.py",
    "typing": "src/pytra/std/typing.py",
    "assertions": "src/pytra/utils/assertions.py",
    "gif": "src/pytra/utils/gif.py",
    "png": "src/pytra/utils/png.py",
}

# required handwritten core impl files.
CPP_REQUIRED_CORE_IMPL_FILES: dict[str, str] = {
    "dataclasses-impl.h": "src/runtime/cpp/core/std/dataclasses-impl.h",
    "math.cpp": "src/runtime/cpp/core/std/math.cpp",
    "math-impl.h": "src/runtime/cpp/core/std/math-impl.h",
    "math-impl.cpp": "src/runtime/cpp/core/std/math-impl.cpp",
    "time-impl.h": "src/runtime/cpp/core/std/time-impl.h",
    "time-impl.cpp": "src/runtime/cpp/core/std/time-impl.cpp",
}


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
    # C++ runtime has migrated to core/gen layout.
    return rel_path.startswith("src/runtime/cpp/gen/")


def _check_cpp_runtime_shape(violations: list[str]) -> None:
    # 1) Generated std/utils modules must exist under gen with canonical source marker.
    for module_name in CPP_GENERATED_STD_MODULES:
        source_rel = CPP_CANONICAL_SOURCE_BY_MODULE[module_name]
        for ext in ("h", "cpp"):
            gen_rel = f"src/runtime/cpp/gen/std/{module_name}.{ext}"
            gen_path = ROOT / gen_rel
            if ext == "cpp" and module_name in CPP_HEADER_ONLY_STD_MODULES:
                if gen_path.exists():
                    violations.append(
                        f"[{module_name}] header-only module must not generate runtime source: {gen_rel}"
                    )
                continue
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
            gen_rel = f"src/runtime/cpp/gen/utils/{module_name}.{ext}"
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

    # 2) Required handwritten impl split must remain under core.
    for _name, core_rel in CPP_REQUIRED_CORE_IMPL_FILES.items():
        core_path = ROOT / core_rel
        if not core_path.exists():
            violations.append(f"[cpp-core-impl] missing core implementation file: {core_rel}")


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
