from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))


HOST_REGISTRY = ROOT / "src" / "toolchain" / "compiler" / "backend_registry.py"
STATIC_REGISTRY = ROOT / "src" / "toolchain" / "compiler" / "backend_registry_static.py"

_SHARED_MODULE = "toolchain.compiler.backend_registry_shared"
_TYPED_BOUNDARY_MODULE = "toolchain.compiler.typed_boundary"

_HOST_ONLY_PRIVATE_FUNCS = {
    "_module_symbol",
    "_load_callable",
    "_split_symbol_ref",
    "_load_callable_ref",
    "_load_backend_spec",
}
_STATIC_ONLY_PRIVATE_FUNCS = {
    "_resolve_callable_ref",
    "_build_backend_spec",
    "_normalize_backend_specs",
}
_HOST_ONLY_PRIVATE_STATE = {"_SPEC_CACHE"}
_STATIC_ONLY_PRIVATE_STATE = {
    "_STATIC_CALLABLES",
    "_BACKEND_SPECS",
    "_BACKEND_RUNTIME_SPECS",
}


def _parse_module(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _top_level_function_signatures(tree: ast.Module) -> dict[str, tuple[tuple[str, ...], tuple[str, ...], int, str, str]]:
    out: dict[str, tuple[tuple[str, ...], tuple[str, ...], int, str, str]] = {}
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        out[node.name] = (
            tuple(arg.arg for arg in node.args.args),
            tuple(arg.arg for arg in node.args.kwonlyargs),
            len(node.args.defaults),
            node.args.vararg.arg if node.args.vararg is not None else "",
            node.args.kwarg.arg if node.args.kwarg is not None else "",
        )
    return out


def _imported_names(tree: ast.Module, module_name: str) -> set[str]:
    out: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == module_name:
            for alias in node.names:
                out.add(alias.name)
    return out


def _private_function_names(tree: ast.Module) -> set[str]:
    out: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("_"):
            out.add(node.name)
    return out


def _collect_assigned_names(target: ast.expr) -> set[str]:
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, (ast.Tuple, ast.List)):
        out: set[str] = set()
        for item in target.elts:
            out.update(_collect_assigned_names(item))
        return out
    return set()


def _private_state_names(tree: ast.Module) -> set[str]:
    out: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                for name in _collect_assigned_names(target):
                    if name.startswith("_"):
                        out.add(name)
        elif isinstance(node, ast.AnnAssign):
            for name in _collect_assigned_names(node.target):
                if name.startswith("_"):
                    out.add(name)
    return out


class BackendRegistryDriftGuardTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.host_tree = _parse_module(HOST_REGISTRY)
        cls.static_tree = _parse_module(STATIC_REGISTRY)

    def test_public_function_signatures_match(self) -> None:
        host_sigs = {
            name: sig
            for name, sig in _top_level_function_signatures(self.host_tree).items()
            if not name.startswith("_")
        }
        static_sigs = {
            name: sig
            for name, sig in _top_level_function_signatures(self.static_tree).items()
            if not name.startswith("_")
        }
        self.assertEqual(host_sigs, static_sigs)

    def test_shared_helper_imports_match(self) -> None:
        self.assertEqual(
            _imported_names(self.host_tree, _SHARED_MODULE),
            _imported_names(self.static_tree, _SHARED_MODULE),
        )

    def test_typed_boundary_imports_match(self) -> None:
        self.assertEqual(
            _imported_names(self.host_tree, _TYPED_BOUNDARY_MODULE),
            _imported_names(self.static_tree, _TYPED_BOUNDARY_MODULE),
        )

    def test_private_function_drift_is_limited(self) -> None:
        host_private = _private_function_names(self.host_tree)
        static_private = _private_function_names(self.static_tree)
        self.assertEqual(host_private - static_private, _HOST_ONLY_PRIVATE_FUNCS)
        self.assertEqual(static_private - host_private, _STATIC_ONLY_PRIVATE_FUNCS)

    def test_private_state_drift_is_limited(self) -> None:
        host_state = _private_state_names(self.host_tree)
        static_state = _private_state_names(self.static_tree)
        self.assertEqual(host_state - static_state, _HOST_ONLY_PRIVATE_STATE)
        self.assertEqual(static_state - host_state, _STATIC_ONLY_PRIVATE_STATE)


if __name__ == "__main__":
    unittest.main()
