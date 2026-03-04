#!/usr/bin/env python3
"""Generate Java std runtime modules from canonical pytra std sources.

Source of truth:
- src/pytra/std/time.py
- src/pytra/std/json.py
- src/pytra/std/pathlib.py
- src/pytra/std/math.py
"""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

MODULE_SOURCE: dict[str, str] = {
    "time": "src/pytra/std/time.py",
    "json": "src/pytra/std/json.py",
    "pathlib": "src/pytra/std/pathlib.py",
    "math": "src/pytra/std/math.py",
}

OUTPUT_MAP: dict[str, str] = {
    "time": "src/runtime/java/pytra-gen/std/time.java",
    "json": "src/runtime/java/pytra-gen/std/json.java",
    "pathlib": "src/runtime/java/pytra-gen/std/pathlib.java",
    "math": "src/runtime/java/pytra-gen/std/math.java",
}


def _parse_modules(raw: str) -> list[str]:
    items = [x.strip() for x in raw.split(",") if x.strip() != ""]
    if len(items) == 0 or raw.strip() == "all":
        return list(MODULE_SOURCE.keys())
    unknown = [x for x in items if x not in MODULE_SOURCE]
    if len(unknown) > 0:
        raise RuntimeError("unknown module(s): " + ", ".join(unknown))
    return items


def _run_py2x(module_name: str, source_rel: str) -> str:
    src = ROOT / source_rel
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / (module_name + ".java")
        cp = subprocess.run(
            ["python3", "src/py2x.py", str(src), "--target", "java", "-o", str(out)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if cp.returncode != 0:
            msg = cp.stderr.strip() or cp.stdout.strip() or ("exit=" + str(cp.returncode))
            raise RuntimeError("py2x failed [java:" + source_rel + "]: " + msg)
        return out.read_text(encoding="utf-8")


def _inject_header(text: str, source_rel: str) -> str:
    header = "\n".join(
        [
            "// AUTO-GENERATED FILE. DO NOT EDIT.",
            "// source: " + source_rel,
            "// generated-by: tools/gen_java_std_runtime_from_canonical.py",
        ]
    )
    body = text.rstrip("\n")
    return header + "\n\n" + body + "\n"


def generate(modules: list[str], *, check: bool, dry_run: bool) -> tuple[int, int]:
    checked = 0
    updated = 0
    for module in modules:
        source_rel = MODULE_SOURCE[module]
        out_rel = OUTPUT_MAP[module]
        out_path = ROOT / out_rel
        rendered = _inject_header(_run_py2x(module, source_rel), source_rel)
        current = out_path.read_text(encoding="utf-8") if out_path.exists() else None
        changed = current != rendered
        checked += 1
        if dry_run:
            print(module + " -> " + out_rel + (" [changed]" if changed else " [same]"))
            continue
        if check:
            if changed:
                raise RuntimeError("stale generated runtime: " + out_rel)
            continue
        if changed:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(rendered, encoding="utf-8")
            updated += 1
            print("updated: " + out_rel)
        else:
            print("unchanged: " + out_rel)
    return checked, updated


def main() -> int:
    parser = argparse.ArgumentParser(description="generate Java std runtime modules from canonical pytra std")
    parser.add_argument("--modules", default="all", help="comma separated module list or 'all'")
    parser.add_argument("--check", action="store_true", help="fail when generated output differs")
    parser.add_argument("--dry-run", action="store_true", help="show plan without writing")
    args = parser.parse_args()

    modules = _parse_modules(args.modules)
    checked, updated = generate(modules, check=bool(args.check), dry_run=bool(args.dry_run))
    print("summary: checked=" + str(checked) + " updated=" + str(updated))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
