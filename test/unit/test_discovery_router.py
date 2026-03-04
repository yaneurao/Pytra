"""Top-level unittest discovery router for domain-split unit tests.

This file keeps `python -m unittest discover -s test/unit -p "test*.py"`
working after moving tests under domain directories without turning each
directory into a Python package.
"""

from __future__ import annotations

import fnmatch
import importlib.util
import sys
import unittest
from pathlib import Path
from types import ModuleType


def _ensure_sys_path(repo_root: Path, unit_root: Path) -> None:
    for entry in (repo_root, repo_root / "src", unit_root):
        p = entry.as_posix()
        if p not in sys.path:
            sys.path.insert(0, p)


def _iter_test_files(start_dir: Path, pattern: str) -> list[Path]:
    if not start_dir.exists():
        return []
    files: list[Path] = []
    for path in sorted(start_dir.rglob("*.py")):
        if fnmatch.fnmatch(path.name, pattern):
            files.append(path)
    return files


def _module_name_for(path: Path, unit_root: Path) -> str:
    rel = path.relative_to(unit_root).with_suffix("")
    return "pytra_unit_" + "_".join(rel.parts)


def _load_module_from_path(module_name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, path.as_posix())
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load module from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_suite_from_dir(
    loader: unittest.TestLoader,
    unit_root: Path,
    start_dir: Path,
    pattern: str,
) -> unittest.TestSuite:
    suite = unittest.TestSuite()
    for path in _iter_test_files(start_dir, pattern):
        module_name = _module_name_for(path, unit_root)
        mod = _load_module_from_path(module_name, path)
        suite.addTests(loader.loadTestsFromModule(mod))
    return suite


def load_tests(
    loader: unittest.TestLoader,
    tests: unittest.TestSuite,
    pattern: str | None,
) -> unittest.TestSuite:
    del tests
    eff_pattern = pattern if isinstance(pattern, str) and pattern != "" else "test*.py"
    unit_root = Path(__file__).resolve().parent
    repo_root = unit_root.parents[1]
    _ensure_sys_path(repo_root, unit_root)

    suite = unittest.TestSuite()
    suite.addTests(_load_suite_from_dir(loader, unit_root, unit_root / "common", eff_pattern))
    backends_root = unit_root / "backends"
    if backends_root.exists():
        for lang_dir in sorted(p for p in backends_root.iterdir() if p.is_dir()):
            suite.addTests(_load_suite_from_dir(loader, unit_root, lang_dir, eff_pattern))
    suite.addTests(_load_suite_from_dir(loader, unit_root, unit_root / "ir", eff_pattern))
    suite.addTests(_load_suite_from_dir(loader, unit_root, unit_root / "tooling", eff_pattern))
    suite.addTests(_load_suite_from_dir(loader, unit_root, unit_root / "selfhost", eff_pattern))
    return suite
