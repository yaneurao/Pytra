// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/iter_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

import Foundation


func py_reversed_object(_ values: Any) -> [Any] {
    var out: [Any] = __pytra_as_list([])
    var i: Int64 = (__pytra_len(values) - Int64(1))
    while (__pytra_int(i) >= __pytra_int(Int64(0))) {
        out.append(__pytra_getIndex(values, i))
        i -= Int64(1)
    }
    return out
}

func py_enumerate_object(_ values: Any, _ start: Int64) -> [Any] {
    var out: [Any] = __pytra_as_list([])
    var i: Int64 = Int64(0)
    var n: Int64 = __pytra_int(__pytra_len(values))
    while (__pytra_int(i) < __pytra_int(n)) {
        out.append([(start + i), __pytra_getIndex(values, i)])
        i += Int64(1)
    }
    return out
}
