#!/usr/bin/env python3
"""Guard runtime marker/layout policy for generated/native ownership boundaries.

Policy:
- For `rs/cs`, canonical generated lanes are `src/runtime/{rs,cs}/generated/**` and canonical
  handwritten lanes are `src/runtime/{rs,cs}/native/**`.
- Legacy `src/runtime/<lang>/pytra-gen/**` / `pytra-core/**` trees are still scanned for
  backends that have not yet rolled over to the `generated/native` layout.
- Generated lanes must include both `source:` and `generated-by:` markers.
- Handwritten lanes must not include generated markers.
- `src/runtime/cpp/generated/core/**` files must include both markers, while
  `src/runtime/cpp/native/core/**` must not.
- Legacy `src/runtime/cpp/core/**` compatibility files are not canonical and are checked
  only if they reappear unexpectedly.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = ROOT / "src" / "runtime"
ALLOWLIST_PATH = ROOT / "tools" / "runtime_core_gen_markers_allowlist.txt"

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
    ".rb",
    ".rs",
    ".scala",
    ".swift",
    ".ts",
}

SOURCE_RE = re.compile(r"source:\s*src/pytra/", re.IGNORECASE)
GENERATED_BY_RE = re.compile(r"generated-by:\s*", re.IGNORECASE)
PYTRA_CORE_FORBIDDEN_RE = re.compile(r"source:\s*src/pytra/(std|utils|built_in)/", re.IGNORECASE)


@dataclass(frozen=True)
class Finding:
    rel_path: str
    reason: str
    detail: str

    @property
    def key(self) -> str:
        return f"{self.rel_path}:{self.reason}"


def _iter_runtime_files(subdir: str) -> list[Path]:
    out: list[Path] = []
    if not RUNTIME_ROOT.exists():
        return out
    for p in sorted(RUNTIME_ROOT.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix.lower() not in TARGET_SUFFIXES:
            continue
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        if f"/{subdir}/" not in ("/" + rel):
            continue
        out.append(p)
    return out


def _iter_tree_files(base: Path) -> list[Path]:
    out: list[Path] = []
    if not base.exists():
        return out
    for p in sorted(base.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix.lower() not in TARGET_SUFFIXES:
            continue
        out.append(p)
    return out


def _is_excluded_gen_file(path: Path) -> bool:
    # allow docs/readme under generated lanes.
    return path.suffix.lower() in {".md", ".txt", ".json"}


def _iter_noncpp_generated_files() -> list[Path]:
    out = _iter_runtime_files("pytra-gen")
    out.extend(_iter_tree_files(RUNTIME_ROOT / "rs" / "generated"))
    out.extend(_iter_tree_files(RUNTIME_ROOT / "cs" / "generated"))
    uniq: dict[str, Path] = {}
    for path in out:
        uniq[str(path)] = path
    return [uniq[key] for key in sorted(uniq)]


def _iter_noncpp_native_files() -> list[Path]:
    out = _iter_runtime_files("pytra-core")
    out.extend(_iter_tree_files(RUNTIME_ROOT / "rs" / "native"))
    out.extend(_iter_tree_files(RUNTIME_ROOT / "cs" / "native"))
    uniq: dict[str, Path] = {}
    for path in out:
        uniq[str(path)] = path
    return [uniq[key] for key in sorted(uniq)]


def _append_missing_generated_markers(
    findings: list[Finding],
    path: Path,
    *,
    source_reason: str,
    generated_by_reason: str,
) -> None:
    rel = str(path.relative_to(ROOT)).replace("\\", "/")
    txt = path.read_text(encoding="utf-8", errors="ignore")
    if SOURCE_RE.search(txt) is None:
        findings.append(
            Finding(
                rel_path=rel,
                reason=source_reason,
                detail="missing `source:` marker",
            )
        )
    if GENERATED_BY_RE.search(txt) is None:
        findings.append(
            Finding(
                rel_path=rel,
                reason=generated_by_reason,
                detail="missing `generated-by:` marker",
            )
        )


def _append_forbidden_generated_markers(
    findings: list[Finding],
    path: Path,
    *,
    source_reason: str,
    generated_by_reason: str,
    detail_prefix: str,
    source_re: re.Pattern[str],
) -> None:
    rel = str(path.relative_to(ROOT)).replace("\\", "/")
    txt = path.read_text(encoding="utf-8", errors="ignore")
    if source_re.search(txt) is not None:
        findings.append(
            Finding(
                rel_path=rel,
                reason=source_reason,
                detail=f"contains generated source marker in {detail_prefix}",
            )
        )
    if GENERATED_BY_RE.search(txt) is not None:
        findings.append(
            Finding(
                rel_path=rel,
                reason=generated_by_reason,
                detail=f"contains `generated-by:` marker in {detail_prefix}",
            )
        )


def _collect_findings() -> list[Finding]:
    findings: list[Finding] = []

    for p in _iter_noncpp_generated_files():
        if _is_excluded_gen_file(p):
            continue
        _append_missing_generated_markers(
            findings,
            p,
            source_reason="gen_missing_source_marker",
            generated_by_reason="gen_missing_generated_by_marker",
        )

    for p in _iter_noncpp_native_files():
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        detail_prefix = "pytra-core" if "/pytra-core/" in ("/" + rel) else "native"
        _append_forbidden_generated_markers(
            findings,
            p,
            source_reason="core_contains_generated_source_marker",
            generated_by_reason="core_contains_generated_by_marker",
            detail_prefix=detail_prefix,
            source_re=PYTRA_CORE_FORBIDDEN_RE,
        )

    for p in _iter_tree_files(RUNTIME_ROOT / "cpp" / "generated" / "core"):
        _append_missing_generated_markers(
            findings,
            p,
            source_reason="cpp_generated_core_missing_source_marker",
            generated_by_reason="cpp_generated_core_missing_generated_by_marker",
        )

    for p in _iter_tree_files(RUNTIME_ROOT / "cpp" / "native" / "core"):
        _append_forbidden_generated_markers(
            findings,
            p,
            source_reason="cpp_native_core_contains_generated_source_marker",
            generated_by_reason="cpp_native_core_contains_generated_by_marker",
            detail_prefix="cpp/native/core",
            source_re=SOURCE_RE,
        )

    for p in _iter_tree_files(RUNTIME_ROOT / "cpp" / "core"):
        _append_forbidden_generated_markers(
            findings,
            p,
            source_reason="cpp_core_surface_contains_generated_source_marker",
            generated_by_reason="cpp_core_surface_contains_generated_by_marker",
            detail_prefix="cpp/core",
            source_re=SOURCE_RE,
        )

    uniq: dict[str, Finding] = {}
    for item in findings:
        uniq.setdefault(item.key, item)
    return sorted(uniq.values(), key=lambda x: x.key)


def _read_allowlist(path: Path) -> set[str]:
    if not path.exists():
        return set()
    out: set[str] = set()
    for row in path.read_text(encoding="utf-8").splitlines():
        line = row.strip()
        if line == "" or line.startswith("#"):
            continue
        out.add(line)
    return out


def _write_allowlist(path: Path, keys: list[str]) -> None:
    rows = [
        "# Auto-generated by tools/check_runtime_core_gen_markers.py --write-allowlist",
        "# key format: <repo-relative-path>:<reason>",
        "",
    ] + keys
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="check runtime generated/core marker and layout boundaries"
    )
    ap.add_argument(
        "--write-allowlist",
        action="store_true",
        help="overwrite allowlist with current findings",
    )
    args = ap.parse_args()

    findings = _collect_findings()
    key_map = {item.key: item for item in findings}
    keys = sorted(key_map.keys())

    if args.write_allowlist:
        _write_allowlist(ALLOWLIST_PATH, keys)
        print(
            "[OK] wrote allowlist:",
            ALLOWLIST_PATH.relative_to(ROOT),
            f"({len(keys)} entries)",
        )
        return 0

    allowed = _read_allowlist(ALLOWLIST_PATH)
    if len(allowed) == 0:
        if len(keys) == 0:
            print("[OK] runtime core/gen marker guard passed (no findings; allowlist empty)")
            return 0
        print(f"[FAIL] allowlist missing or empty: {ALLOWLIST_PATH.relative_to(ROOT)}")
        print("run: python3 tools/check_runtime_core_gen_markers.py --write-allowlist")
        return 1

    added = sorted(key for key in keys if key not in allowed)
    stale = sorted(key for key in allowed if key not in key_map)

    if len(added) > 0:
        print("[FAIL] runtime core/gen marker policy violations detected:")
        for key in added:
            item = key_map[key]
            print(f"  - {item.rel_path} [{item.reason}] {item.detail}")
        print("fix runtime layout/markers or refresh allowlist:")
        print("  python3 tools/check_runtime_core_gen_markers.py --write-allowlist")
        return 1

    print("[OK] runtime core/gen marker guard passed")
    print(f"  tracked baseline findings: {len(keys)}")
    if len(stale) > 0:
        print(f"  note: stale allowlist entries: {len(stale)} (cleanup recommended)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
