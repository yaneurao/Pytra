#!/usr/bin/env python3
"""Guard JSON artifact loaders against raw object-tree decode reintroduction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TARGET_FILES = [
    "src/py2x.py",
    "src/east2x.py",
    "src/toolchain/ir/east_io.py",
    "src/toolchain/link/link_manifest_io.py",
    "src/toolchain/link/materializer.py",
    "src/toolchain/link/program_loader.py",
    "src/toolchain/frontends/transpile_cli.py",
    "src/toolchain/frontends/runtime_symbol_index.py",
    "src/toolchain/emit/common/emitter/code_emitter.py",
    "src/toolchain/emit/js/emitter/js_emitter.py",
]
REQUIRED_SNIPPET = "json.loads_obj("
FORBIDDEN_SNIPPET = "json.loads("


@dataclass(frozen=True)
class Finding:
    rel_path: str
    reason: str

    @property
    def key(self) -> str:
        return f"{self.rel_path}:{self.reason}"


def _collect_findings(root: Path = ROOT) -> list[Finding]:
    findings: list[Finding] = []
    for rel_path in TARGET_FILES:
        path = root / rel_path
        if not path.exists():
            findings.append(Finding(rel_path=rel_path, reason="missing_file"))
            continue
        text = path.read_text(encoding="utf-8")
        if REQUIRED_SNIPPET not in text:
            findings.append(Finding(rel_path=rel_path, reason="missing_loads_obj"))
        if FORBIDDEN_SNIPPET in text:
            findings.append(Finding(rel_path=rel_path, reason="raw_json_loads"))
    return findings


def main() -> int:
    findings = _collect_findings(ROOT)
    if len(findings) > 0:
        print("[FAIL] jsonvalue decode boundary guard failed")
        for item in findings:
            print(" -", item.key)
        print("Use json.loads_obj(...) at JSON artifact boundaries.")
        return 1

    print("[OK] jsonvalue decode boundary guard passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
