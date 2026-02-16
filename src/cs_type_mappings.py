"""C# 変換専用の基本型マップ。"""

from __future__ import annotations

CS_PRIMITIVE_TYPES = {
    # Python 標準の int は C# では long として扱う（既存実装方針）。
    "int": "long",
    "int8": "sbyte",
    "uint8": "byte",
    "int16": "short",
    "uint16": "ushort",
    "int32": "int",
    "uint32": "uint",
    "int64": "long",
    "uint64": "ulong",
    "float": "double",
    "float32": "float",
    "str": "string",
    "bool": "bool",
    "None": "void",
    "object": "object",
}
