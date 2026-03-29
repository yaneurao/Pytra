#!/usr/bin/env python3
"""Guard against direct runtime/stdlib dispatch literals in non-C++ emitters.

Policy:
- Non-C++ emitters must not hardcode runtime/stdlib dispatch with
  direct `"symbol"` literals (branch/table/context-based dispatch).
- Existing debt is tracked in an explicit allowlist.
- New direct-branch occurrences fail this check.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKENDS_ROOT = ROOT / "src" / "backends"
ALLOWLIST_PATH = ROOT / "tools" / "emitter_runtimecall_guardrails_allowlist.txt"

IGNORED_BACKENDS = {"cpp", "common"}
KEY_TOKENS = (
    "callee_name",
    "fn_name",
    "fn_name_raw",
    "owner_type",
    "attr_name",
    "attr",
    "call_name",
    "method_name",
    "module_id",
    "module_name",
    "owner_mod",
    "imported_mod",
    "binding_module",
    "export_name",
    "runtime_call",
    "resolved_runtime_call",
    "resolved_runtime_source",
    "semantic_tag",
)
CONTEXT_TOKENS = KEY_TOKENS + (
    "helper",
    "dispatch",
    "resolver",
    "runtime",
    "registry",
    "import_symbols",
)
TABLE_NAME_HINTS = (
    "helper",
    "dispatch",
    "runtime",
    "resolver",
    "registry",
    "symbol",
    "map",
    "table",
    "alias",
    "binding",
)
STRICT_BACKENDS = {"java"}
BANNED_SYMBOLS = (
    "py_assert_all",
    "py_assert_eq",
    "py_assert_stdout",
    "py_assert_true",
    "save_gif",
    "write_rgb_png",
)

BRANCH_RE = re.compile(r"^\s*(if|elif)\b")
CASE_RE = re.compile(r"^\s*case\b")
ASSIGN_RE = re.compile(r"^\s*([A-Za-z_]\w*)\s*(?::[^=]+)?=\s*(.+)$")
PATTERN_RULES: tuple[tuple[str, str, re.Pattern[str]], ...] = (
    (
        "math",
        "source_module_branch",
        re.compile(
            r"\b(owner|module_id|module_name|owner_mod|owner_module|imported_mod|mod|binding_module)\b"
            r"[^\n#]*(==|!=)\s*[\"'](math|json|time|pathlib)[\"']"
        ),
    ),
    (
        "pytra.utils.*",
        "source_module_prefix",
        re.compile(
            r"\bbinding_module\b[^\n#]*startswith\(\s*[\"']pytra\.utils\.[\"']\s*\)"
        ),
    ),
    (
        "pyMath*",
        "helper_name_branch",
        re.compile(r"\bruntime_symbol\b[^\n#]*startswith\(\s*[\"']pyMath[\"']\s*\)"),
    ),
    (
        "pyMath*",
        "helper_name_branch",
        re.compile(r"\bruntime_symbol\b[^\n#]*(==|!=)\s*[\"']pyMath[A-Za-z0-9_]+[\"']"),
    ),
    (
        ".pi/.e",
        "runtime_suffix_branch",
        re.compile(r"\bresolved_runtime\b[^\n#]*endswith\(\s*[\"']\.(pi|e)[\"']\s*\)"),
    ),
)


@dataclass(frozen=True)
class Finding:
    rel_path: str
    line_no: int
    symbol: str
    kind: str
    snippet: str

    @property
    def key(self) -> str:
        return f"{self.rel_path}:{self.line_no}:{self.symbol}"


def _iter_emitter_files() -> list[Path]:
    files: list[Path] = []
    if not BACKENDS_ROOT.exists():
        return files
    for backend_dir in sorted(BACKENDS_ROOT.iterdir()):
        if not backend_dir.is_dir():
            continue
        if backend_dir.name in IGNORED_BACKENDS:
            continue
        emitter_dir = backend_dir / "emitter"
        if not emitter_dir.exists():
            continue
        for path in sorted(emitter_dir.rglob("*.py")):
            if not path.is_file():
                continue
            files.append(path)
    return files


def _has_symbol_literal(raw: str, symbol: str) -> bool:
    return f'"{symbol}"' in raw or f"'{symbol}'" in raw


def _backend_name(rel_path: str) -> str:
    parts = rel_path.split("/")
    if len(parts) >= 4 and parts[0] == "src" and parts[1] == "backends":
        return parts[2]
    return ""


def _is_dispatch_var(name: str) -> bool:
    lowered = name.lower()
    return any(hint in lowered for hint in TABLE_NAME_HINTS)


def _balance_delta(line: str) -> int:
    return (
        line.count("{")
        + line.count("[")
        + line.count("(")
        - line.count("}")
        - line.count("]")
        - line.count(")")
    )


def _collect_dispatch_table_findings(rel_path: str, lines: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    active_depth = 0
    active_var = ""
    for line_no, raw in enumerate(lines, start=1):
        started_here = False
        if active_depth <= 0:
            active_depth = 0
            active_var = ""
            matched = ASSIGN_RE.match(raw)
            if matched is None:
                continue
            var_name = matched.group(1)
            rhs = matched.group(2)
            if not _is_dispatch_var(var_name):
                continue
            if all(ch not in rhs for ch in "{[("):
                continue
            active_var = var_name
            active_depth = _balance_delta(rhs)
            started_here = True
        for symbol in BANNED_SYMBOLS:
            if _has_symbol_literal(raw, symbol):
                findings.append(
                    Finding(
                        rel_path=rel_path,
                        line_no=line_no,
                        symbol=symbol,
                        kind=f"dispatch_table:{active_var or 'unknown'}",
                        snippet=raw.strip(),
                    )
                )
        if active_var != "" and not started_here:
            active_depth += _balance_delta(raw)
        if active_var != "" and active_depth <= 0:
            active_var = ""
            active_depth = 0
    return findings


def _collect_findings() -> list[Finding]:
    findings: list[Finding] = []
    for path in _iter_emitter_files():
        rel_path = str(path.relative_to(ROOT))
        lines = path.read_text(encoding="utf-8").splitlines()
        for line_no, raw in enumerate(lines, start=1):
            for symbol, kind, pattern in PATTERN_RULES:
                if pattern.search(raw) is None:
                    continue
                findings.append(
                    Finding(
                        rel_path=rel_path,
                        line_no=line_no,
                        symbol=symbol,
                        kind=kind,
                        snippet=raw.strip(),
                    )
                )
            symbol_hits = [symbol for symbol in BANNED_SYMBOLS if _has_symbol_literal(raw, symbol)]
            if len(symbol_hits) == 0:
                continue
            branch_like = BRANCH_RE.match(raw) is not None or CASE_RE.match(raw) is not None
            if branch_like and any(token in raw for token in KEY_TOKENS):
                for symbol in symbol_hits:
                    findings.append(
                        Finding(
                            rel_path=rel_path,
                            line_no=line_no,
                            symbol=symbol,
                            kind="branch",
                            snippet=raw.strip(),
                        )
                    )
                continue
            if any(token in raw for token in CONTEXT_TOKENS):
                for symbol in symbol_hits:
                    findings.append(
                        Finding(
                            rel_path=rel_path,
                            line_no=line_no,
                            symbol=symbol,
                            kind="context_literal",
                            snippet=raw.strip(),
                        )
                    )
        findings.extend(_collect_dispatch_table_findings(rel_path, lines))
    uniq: dict[str, Finding] = {}
    for item in findings:
        uniq.setdefault(item.key, item)
    findings = sorted(uniq.values(), key=lambda item: item.key)
    return findings


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
    header = [
        "# Auto-generated by tools/check_emitter_runtimecall_guardrails.py --write-allowlist",
        "# Non-C++ emitter runtime-call direct-branch baseline",
        "",
    ]
    path.write_text("\n".join(header + keys) + "\n", encoding="utf-8")


def _strict_backend_findings(findings: list[Finding]) -> list[Finding]:
    out: list[Finding] = []
    for item in findings:
        backend = _backend_name(item.rel_path)
        if backend in STRICT_BACKENDS:
            out.append(item)
    out.sort(key=lambda item: item.key)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Guard non-C++ emitter runtime-call hardcoded dispatch growth"
    )
    parser.add_argument(
        "--write-allowlist",
        action="store_true",
        help="overwrite allowlist with current findings",
    )
    args = parser.parse_args()

    findings = _collect_findings()
    keys = sorted(item.key for item in findings)
    finding_map = {item.key: item for item in findings}

    strict_hits = _strict_backend_findings(findings)
    if len(strict_hits) > 0:
        print("[FAIL] strict backend emitter contains direct runtime-call dispatch literals:")
        for finding in strict_hits:
            print(
                f"  - {finding.rel_path}:{finding.line_no} "
                f"[{finding.symbol}] ({finding.kind}) {finding.snippet}"
            )
        strict_targets = ",".join(sorted(STRICT_BACKENDS))
        print(
            "Strict backends must keep zero direct dispatch literals; "
            "resolve via EAST3 metadata only."
        )
        print(f"  strict backends: {strict_targets}")
        return 1

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
            print(
                "[OK] emitter runtime-call guardrails passed",
                "(no findings; allowlist empty)",
            )
            return 0
        print(f"[FAIL] allowlist missing or empty: {ALLOWLIST_PATH.relative_to(ROOT)}")
        print("run: python3 tools/check_emitter_runtimecall_guardrails.py --write-allowlist")
        return 1

    added = sorted(key for key in keys if key not in allowed)
    stale = sorted(key for key in allowed if key not in finding_map)

    if len(added) > 0:
        print("[FAIL] new direct runtime-call dispatch literal(s) detected:")
        for key in added:
            finding = finding_map[key]
            print(
                f"  - {finding.rel_path}:{finding.line_no} "
                f"[{finding.symbol}] ({finding.kind}) {finding.snippet}"
            )
        print("Resolve via lower/IR runtime_call path, or explicitly refresh allowlist after review:")
        print("  python3 tools/check_emitter_runtimecall_guardrails.py --write-allowlist")
        return 1

    print("[OK] emitter runtime-call guardrails passed")
    print(f"  tracked baseline findings: {len(keys)}")
    if len(stale) > 0:
        print(f"  note: stale allowlist entries: {len(stale)} (cleanup recommended)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
