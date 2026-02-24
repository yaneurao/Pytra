#!/usr/bin/env python3
"""Guard legacy *_module shims during runtime layout migration."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_LEGACY_MODULE_DIRS = [
    "cs_module",
    "go_module",
    "java_module",
    "kotlin_module",
    "swift_module",
]


def _check_js_shims(errors: list[str]) -> None:
    for path in sorted((ROOT / "src" / "js_module").glob("*.js")):
        name = path.name
        expected = f'module.exports = require("../runtime/js/pytra/{name}");'
        text = path.read_text(encoding="utf-8")
        if expected not in text:
            errors.append(f"js shim mismatch: {path.relative_to(ROOT)}")


def _check_ts_shims(errors: list[str]) -> None:
    for path in sorted((ROOT / "src" / "ts_module").glob("*.ts")):
        stem = path.stem
        expected = f'export * from "../runtime/ts/pytra/{stem}";'
        text = path.read_text(encoding="utf-8")
        if expected not in text:
            errors.append(f"ts shim mismatch: {path.relative_to(ROOT)}")


def _check_forbidden_refs(errors: list[str]) -> None:
    forbidden = ("/src/js_module/", "/src/ts_module/")
    for legacy in FORBIDDEN_LEGACY_MODULE_DIRS:
        forbidden += (f"/src/{legacy}/",)
    targets = [
        ROOT / "src" / "hooks",
        ROOT / "src" / "pytra",
        ROOT / "test" / "unit",
        ROOT / "sample" / "js",
        ROOT / "sample" / "ts",
    ]
    for base in targets:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for marker in forbidden:
                if marker in text:
                    errors.append(f"forbidden legacy path ref: {path.relative_to(ROOT)}")
                    break


def _check_legacy_runtime_modules_removed(errors: list[str]) -> None:
    for name in FORBIDDEN_LEGACY_MODULE_DIRS:
        module_dir = ROOT / "src" / name
        if module_dir.exists():
            entries = sorted(module_dir.rglob("*"))
            if entries:
                errors.append(f"legacy runtime module directory should not contain files: {module_dir.relative_to(ROOT)}")


def main() -> int:
    errors: list[str] = []
    _check_js_shims(errors)
    _check_ts_shims(errors)
    _check_legacy_runtime_modules_removed(errors)
    _check_forbidden_refs(errors)
    if errors:
        for e in errors:
            print(f"[NG] {e}")
        return 1
    print("[OK] runtime legacy shim guard passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
