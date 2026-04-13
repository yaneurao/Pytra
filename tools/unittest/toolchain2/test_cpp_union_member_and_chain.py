from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'src').exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / 'src') not in sys.path:
    sys.path.insert(0, str(ROOT / 'src'))

from toolchain.common.types import select_union_member_type
from toolchain.parse.py.parse_python import parse_python_file
from toolchain.resolve.py.builtin_registry import load_builtin_registry
from toolchain.resolve.py.resolver import resolve_east1_to_east2
from toolchain.compile.lower import lower_east2_to_east3
from toolchain.emit.cpp.emitter import emit_cpp_module


def _load_registry() -> object:
    return load_builtin_registry(
        ROOT / 'test' / 'include' / 'east1' / 'py' / 'built_in' / 'builtins.py.east1',
        ROOT / 'test' / 'include' / 'east1' / 'py' / 'built_in' / 'containers.py.east1',
        ROOT / 'test' / 'include' / 'east1' / 'py' / 'std',
    )


def _resolve_lower(source: str) -> dict[str, object]:
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / 'snippet.py'
        src.write_text(source, encoding='utf-8')
        east2 = parse_python_file(str(src))
        east2['source_path'] = 'src/app/snippet.py'
        resolve_east1_to_east2(east2, registry=_load_registry())
        return lower_east2_to_east3(east2)


class Toolchain2CppUnionMemberAndChainTests(unittest.TestCase):
    def test_select_union_member_type_matches_recursive_alias_lane(self) -> None:
        self.assertEqual(select_union_member_type('JsonVal', 'Node'), 'dict[str,JsonVal]')
        self.assertEqual(select_union_member_type('JsonVal', 'dict[str,JsonVal]'), 'dict[str,JsonVal]')
        self.assertEqual(select_union_member_type('JsonVal', 'list[JsonVal]'), 'list[JsonVal]')

    def test_cpp_emitter_stores_jsonval_dict_member_without_covariant_copy(self) -> None:
        east3 = _resolve_lower(
            'from pytra.std.json import JsonVal\n'
            'Node = dict[str, JsonVal]\n\n'
            'def f(value: JsonVal) -> list[JsonVal]:\n'
            '    out: list[JsonVal] = []\n'
            '    if isinstance(value, dict):\n'
            '        out.append(value)\n'
            '    return out\n'
        )
        cpp_code = emit_cpp_module(east3)
        self.assertIn('py_list_append_mut(out, ::std::get<Object<dict<str, JsonVal>>>((*value)));', cpp_code)
        self.assertNotIn('__cov_', cpp_code)
        self.assertNotIn('push_back(__item_', cpp_code)

    def test_else_branch_narrows_remaining_union_member(self) -> None:
        east3 = _resolve_lower(
            'from pytra.std.json import JsonVal\n\n'
            'def check_two_member(y: str | int) -> list[bool]:\n'
            '    checks: list[bool] = []\n'
            '    if isinstance(y, str):\n'
            '        checks.append(True)\n'
            '    else:\n'
            '        remainder: int = y % 3\n'
            '        checks.append(True)\n'
            '    return checks\n'
        )
        fn = next(stmt for stmt in east3['body'] if isinstance(stmt, dict) and stmt.get('kind') == 'FunctionDef')
        if_stmt = next(stmt for stmt in fn['body'] if isinstance(stmt, dict) and stmt.get('kind') == 'If')
        ann_assign = next(stmt for stmt in if_stmt['orelse'] if isinstance(stmt, dict) and stmt.get('kind') == 'AnnAssign')
        binop = ann_assign['value']
        left = binop['left']
        self.assertEqual(left.get('kind'), 'Unbox')
        self.assertEqual(left.get('target'), 'int64')
        self.assertEqual(left.get('resolved_type'), 'int64')
        self.assertEqual(left.get('value', {}).get('resolved_type'), 'str | int64')


if __name__ == '__main__':
    unittest.main()
