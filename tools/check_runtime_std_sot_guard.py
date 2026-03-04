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
- C++ math shape (`pytra-gen/std/math.*` + `pytra-core/std/math-impl.*`)
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
    # Keep this strict and path-based; generated artifacts must live in pytra-gen.
    return "/pytra-gen/" in ("/" + rel_path)


def _check_cpp_math_shape(violations: list[str]) -> None:
    required = [
        "src/runtime/cpp/pytra-gen/std/math.h",
        "src/runtime/cpp/pytra-gen/std/math.cpp",
        "src/runtime/cpp/pytra-core/std/math-impl.h",
        "src/runtime/cpp/pytra-core/std/math-impl.cpp",
        "src/runtime/cpp/pytra/std/math.h",
        "src/runtime/cpp/pytra/std/math.cpp",
    ]
    for rel in required:
        if not (ROOT / rel).exists():
            violations.append(f"[math] missing required runtime file: {rel}")

    gen_header = ROOT / "src/runtime/cpp/pytra-gen/std/math.h"
    gen_source = ROOT / "src/runtime/cpp/pytra-gen/std/math.cpp"
    marker = "source: src/pytra/std/math.py"
    if gen_header.exists():
        txt = gen_header.read_text(encoding="utf-8", errors="ignore")
        if marker not in txt:
            violations.append(
                "[math] src/runtime/cpp/pytra-gen/std/math.h missing canonical source marker"
            )
    if gen_source.exists():
        txt = gen_source.read_text(encoding="utf-8", errors="ignore")
        if marker not in txt:
            violations.append(
                "[math] src/runtime/cpp/pytra-gen/std/math.cpp missing canonical source marker"
            )

    fw_header = ROOT / "src/runtime/cpp/pytra/std/math.h"
    if fw_header.exists():
        txt = fw_header.read_text(encoding="utf-8", errors="ignore")
        if "runtime/cpp/pytra-gen/std/math.h" not in txt:
            violations.append(
                "[math] src/runtime/cpp/pytra/std/math.h must forward to pytra-gen/std/math.h"
            )
    fw_source = ROOT / "src/runtime/cpp/pytra/std/math.cpp"
    if fw_source.exists():
        txt = fw_source.read_text(encoding="utf-8", errors="ignore")
        if "runtime/cpp/pytra-gen/std/math.cpp" not in txt:
            violations.append(
                "[math] src/runtime/cpp/pytra/std/math.cpp must forward to pytra-gen/std/math.cpp"
            )

    impl_header = ROOT / "src/runtime/cpp/pytra-core/std/math-impl.h"
    if impl_header.exists():
        txt = impl_header.read_text(encoding="utf-8", errors="ignore")
        if "namespace pytra::std::math_impl" not in txt:
            violations.append(
                "[math] src/runtime/cpp/pytra-core/std/math-impl.h must define math_impl namespace"
            )
    impl_source = ROOT / "src/runtime/cpp/pytra-core/std/math-impl.cpp"
    if impl_source.exists():
        txt = impl_source.read_text(encoding="utf-8", errors="ignore")
        if "namespace pytra::std::math_impl" not in txt:
            violations.append(
                "[math] src/runtime/cpp/pytra-core/std/math-impl.cpp must define math_impl namespace"
            )


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

    _check_cpp_math_shape(violations)

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
            print(
                "  fix: move implementation to src/pytra/* canonical source and generate under pytra-gen"
            )
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
