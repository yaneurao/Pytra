"""Normalize runtime_call values to match emitter expectations.

§5 準拠: Any/object 禁止, pytra.std.* のみ, selfhost 対象。

toolchain2 の resolve/compile が設定する runtime_call と、
既存 emitter (toolchain/emit/cpp) が期待する runtime_call にずれがある。
このパスは linked module の BuiltinCall ノードの runtime_call を正規化する。

注: これは暫定互換レイヤ。toolchain2/emit/ が完成すれば不要になる。
"""

from __future__ import annotations

from pytra.std.json import JsonVal


# runtime_call の正規化マップ
# key: toolchain2 が生成する値, value: 旧 emitter が期待する値
_RUNTIME_CALL_MAP: dict[str, str] = {
    "int": "static_cast",
    "float": "static_cast",
    "len": "py_len",
    "py_enumerate_object": "py_enumerate",
    "py_reversed_object": "py_reversed",
    "str.join": "py_join",
    "str.strip": "py_strip",
    "str.lstrip": "py_lstrip",
    "str.rstrip": "py_rstrip",
    "str.startswith": "py_startswith",
    "str.endswith": "py_endswith",
    "str.replace": "py_replace",
    "str.find": "py_find",
    "str.rfind": "py_rfind",
    "str.upper": "py_upper",
    "str.lower": "py_lower",
    "str.split": "py_split",
    "str.count": "py_count",
    "str.index": "py_index",
    "list.index": "py_list_index",
}

# builtin_name ベースのコンストラクタ正規化
_CTOR_MAP: dict[str, str] = {
    "bytearray": "bytearray_ctor",
    "bytes": "bytes_ctor",
    "set": "set_ctor",
}


def normalize_runtime_calls(doc: dict[str, JsonVal]) -> None:
    """Walk the EAST3 doc and normalize runtime_call values in-place."""
    _walk(doc)


# Names that should be lowered to BuiltinCall if they appear as plain Call
_BUILTIN_CALL_NAMES: set[str] = {
    "bytearray", "bytes", "set", "list", "dict",
    "int", "float", "str", "bool",
    "len", "enumerate", "reversed", "range",
    "print", "type", "isinstance", "issubclass",
    "ord", "chr", "abs", "min", "max", "sum",
    "any", "all", "sorted", "zip", "map", "filter",
    "iter", "next", "hash", "id", "repr",
    "round", "divmod", "pow",
}

# Method names that should be lowered to BuiltinCall
_BUILTIN_METHOD_LOWER: dict[str, str] = {
    # list methods
    "append": "list.append",
    "extend": "list.extend",
    "insert": "list.insert",
    "remove": "list.remove",
    "pop": "list.pop",
    "clear": "list.clear",
    "sort": "list.sort",
    "reverse": "list.reverse",
    "index": "list.index",
    "count": "list.count",
    # dict methods
    "get": "dict.get",
    "items": "dict.items",
    "keys": "dict.keys",
    "values": "dict.values",
    # set methods
    "add": "set.add",
    "discard": "set.discard",
    # str methods
    "join": "str.join",
    "strip": "str.strip",
    "lstrip": "str.lstrip",
    "rstrip": "str.rstrip",
    "startswith": "str.startswith",
    "endswith": "str.endswith",
    "replace": "str.replace",
    "find": "str.find",
    "rfind": "str.rfind",
    "split": "str.split",
    "upper": "str.upper",
    "lower": "str.lower",
    "count": "str.count",
    "format": "str.format",
}


def _walk(node: JsonVal) -> None:
    """Recursively walk and normalize BuiltinCall nodes."""
    if isinstance(node, dict):
        kind = node.get("kind")
        lk = node.get("lowered_kind")

        if kind == "Call":
            if lk == "BuiltinCall":
                # Already a BuiltinCall: normalize runtime_call
                rc = node.get("runtime_call")
                bn = node.get("builtin_name")
                if isinstance(rc, str) and rc in _RUNTIME_CALL_MAP:
                    node["runtime_call"] = _RUNTIME_CALL_MAP[rc]
                elif isinstance(bn, str) and bn in _CTOR_MAP:
                    if isinstance(rc, str) and (rc == bn or rc == ""):
                        node["runtime_call"] = _CTOR_MAP[bn]
            elif lk == "" or lk is None:
                # Not yet lowered: check if it should be
                _try_lower_call(node)

        for v in node.values():
            _walk(v)
    elif isinstance(node, list):
        for item in node:
            _walk(item)


def _try_lower_call(call_node: dict[str, JsonVal]) -> None:
    """Try to lower a plain Call to BuiltinCall if it matches known builtins."""
    func = call_node.get("func")
    if not isinstance(func, dict):
        return

    func_kind = func.get("kind")

    if func_kind == "Name":
        # Direct function call: bytearray(), bytes(), etc.
        func_id = func.get("id")
        if isinstance(func_id, str) and func_id in _BUILTIN_CALL_NAMES:
            call_node["lowered_kind"] = "BuiltinCall"
            call_node["builtin_name"] = func_id
            # Set runtime_call
            if func_id in _CTOR_MAP:
                call_node["runtime_call"] = _CTOR_MAP[func_id]
            elif func_id in _RUNTIME_CALL_MAP:
                call_node["runtime_call"] = _RUNTIME_CALL_MAP[func_id]
            else:
                call_node["runtime_call"] = func_id

    elif func_kind == "Attribute":
        # Method call: x.append(), s.strip(), etc.
        attr = func.get("attr")
        if not isinstance(attr, str):
            return
        if attr in _BUILTIN_METHOD_LOWER:
            call_node["lowered_kind"] = "BuiltinCall"
            call_node["builtin_name"] = attr
            qualified = _BUILTIN_METHOD_LOWER[attr]
            if qualified in _RUNTIME_CALL_MAP:
                call_node["runtime_call"] = _RUNTIME_CALL_MAP[qualified]
            else:
                call_node["runtime_call"] = qualified
