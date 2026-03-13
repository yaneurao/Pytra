// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/numeric_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

import Foundation


func sum(_ values: [Any]) -> T {
    if (__pytra_int(__pytra_len(values)) == __pytra_int(Int64(0))) {
        return Int64(0)
    }
    var acc: Any = (__pytra_getIndex(values, Int64(0)) - __pytra_getIndex(values, Int64(0)))
    var i: Int64 = Int64(0)
    var n: Int64 = __pytra_len(values)
    while (__pytra_int(i) < __pytra_int(n)) {
        acc += __pytra_getIndex(values, i)
        i += Int64(1)
    }
    return acc
}

func py_min(_ a: T, _ b: T) -> T {
    if (__pytra_float(a) < __pytra_float(b)) {
        return a
    }
    return b
}

func py_max(_ a: T, _ b: T) -> T {
    if (__pytra_float(a) > __pytra_float(b)) {
        return a
    }
    return b
}
