"""Pytra scalar type aliases for Pylance compatibility.

Python runtime: these are simply aliases to int/float.
Transpiler: recognizes these type names natively and ignores this import.
"""

int8 = int
uint8 = int
int16 = int
uint16 = int
int32 = int
uint32 = int
int64 = int
uint64 = int
float32 = float
float64 = float
