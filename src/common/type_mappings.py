"""ターゲット言語別の基本型マップ。"""

from __future__ import annotations

CS_PRIMITIVE_TYPES = {
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

CPP_PRIMITIVE_TYPES = {
    "int": "long long",
    "int8": "int8_t",
    "uint8": "uint8_t",
    "int16": "int16_t",
    "uint16": "uint16_t",
    "int32": "int32_t",
    "uint32": "uint32_t",
    "int64": "int64_t",
    "uint64": "uint64_t",
    "float": "double",
    "float32": "float",
    "str": "string",
    "bool": "bool",
    "None": "void",
}
