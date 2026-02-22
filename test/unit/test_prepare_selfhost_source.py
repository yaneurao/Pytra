from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tools" / "prepare_selfhost_source.py"


def _load_prepare_module() -> object:
    spec = importlib.util.spec_from_file_location("prepare_selfhost_source", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to load tools/prepare_selfhost_source.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _slice_block(text: str, start_marker: str, end_marker: str) -> str:
    i = text.find(start_marker)
    if i < 0:
        raise RuntimeError(f"start marker not found: {start_marker}")
    j = text.find(end_marker, i + len(start_marker))
    if j < 0:
        raise RuntimeError(f"end marker not found: {end_marker}")
    return text[i:j]


class PrepareSelfhostSourceTest(unittest.TestCase):
    def test_remove_import_line_removes_required_imports(self) -> None:
        mod = _load_prepare_module()
        py2cpp_text = mod.SRC_PY2CPP.read_text(encoding="utf-8")
        removed = mod._remove_import_line(py2cpp_text)
        self.assertNotIn(
            "from pytra.compiler.east_parts.code_emitter import CodeEmitter\n",
            removed,
        )
        self.assertNotIn(
            "from pytra.compiler.transpile_cli import dump_codegen_options_text, parse_py2cpp_argv, resolve_codegen_options, validate_codegen_options\n",
            removed,
        )
        self.assertNotIn(
            "from hooks.cpp.hooks.cpp_hooks import build_cpp_hooks\n",
            removed,
        )

    def test_remove_import_line_raises_when_required_import_missing(self) -> None:
        mod = _load_prepare_module()
        broken = (
            "from pytra.compiler.east_parts.code_emitter import CodeEmitter\n"
            "from pytra.compiler.transpile_cli import dump_codegen_options_text, parse_py2cpp_argv, resolve_codegen_options, validate_codegen_options\n"
        )
        with self.assertRaisesRegex(RuntimeError, "build_cpp_hooks import"):
            mod._remove_import_line(broken)

    def test_extract_support_blocks_includes_build_cpp_hooks_stub(self) -> None:
        mod = _load_prepare_module()
        support_blocks = mod._extract_support_blocks()
        self.assertIn("def build_cpp_hooks() -> dict[str, Any]:", support_blocks)
        self.assertIn("return {}", support_blocks)

    def test_load_cpp_hooks_uses_support_stub_in_merged_source(self) -> None:
        mod = _load_prepare_module()
        py2cpp_text = mod.SRC_PY2CPP.read_text(encoding="utf-8")
        base_text = mod.SRC_BASE.read_text(encoding="utf-8")
        support_blocks = mod._extract_support_blocks()
        base_class = mod._strip_triple_quoted_docstrings(mod._extract_code_emitter_class(base_text))
        merged = mod._insert_code_emitter(mod._remove_import_line(py2cpp_text), base_class, support_blocks)
        load_cpp_hooks_block = _slice_block(
            merged,
            "def load_cpp_hooks(",
            "\n\ndef load_cpp_identifier_rules(",
        )
        self.assertIn("hooks = build_cpp_hooks()", load_cpp_hooks_block)
        self.assertIn("try:", load_cpp_hooks_block)
        self.assertIn("if isinstance(hooks, dict):", load_cpp_hooks_block)
        self.assertIn("def build_cpp_hooks() -> dict[str, Any]:", merged)

    def test_hook_patch_only_replaces_call_hook_body(self) -> None:
        mod = _load_prepare_module()
        py2cpp_text = mod.SRC_PY2CPP.read_text(encoding="utf-8")
        base_text = mod.SRC_BASE.read_text(encoding="utf-8")
        support_blocks = mod._extract_support_blocks()
        base_class = mod._strip_triple_quoted_docstrings(mod._extract_code_emitter_class(base_text))
        merged = mod._insert_code_emitter(mod._remove_import_line(py2cpp_text), base_class, support_blocks)
        patched = mod._patch_code_emitter_hooks_for_selfhost(merged)

        pre_call_hook1 = _slice_block(merged, "    def _call_hook1(", "\n    def _call_hook2(")
        post_call_hook1 = _slice_block(patched, "    def _call_hook1(", "\n    def _call_hook2(")
        self.assertEqual(post_call_hook1, pre_call_hook1)
        self.assertIn("return self._call_hook(", post_call_hook1)
        self.assertNotIn("pass", post_call_hook1)

        post_call_hook = _slice_block(patched, "    def _call_hook(", "\n    def _call_hook1(")
        self.assertIn("return None", post_call_hook)
        self.assertNotIn("pass", post_call_hook)

        hook_emit_stmt_block = _slice_block(patched, "    def hook_on_emit_stmt(", "\n    def hook_on_emit_stmt_kind(")
        self.assertIn("v = self._call_hook1(", hook_emit_stmt_block)
        self.assertIn("if isinstance(v, bool):", hook_emit_stmt_block)
        self.assertNotIn("pass", hook_emit_stmt_block)

    def test_hook_patch_raises_when_markers_missing(self) -> None:
        mod = _load_prepare_module()
        with self.assertRaisesRegex(RuntimeError, "_call_hook block"):
            mod._patch_code_emitter_hooks_for_selfhost("class CodeEmitter:\n    pass\n")

        broken_order = (
            "class CodeEmitter:\n"
            "    def _call_hook(self):\n"
            "        return None\n"
            "    def hook_on_emit_stmt(self):\n"
            "        return None\n"
        )
        with self.assertRaisesRegex(RuntimeError, "_call_hook1 marker"):
            mod._patch_code_emitter_hooks_for_selfhost(broken_order)


if __name__ == "__main__":
    unittest.main()
