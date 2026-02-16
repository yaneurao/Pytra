"""C++ 変換専用の基本型マップ。"""

from __future__ import annotations

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
