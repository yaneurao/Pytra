// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/iter_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

import Foundation


func py_reversed_object(_ values: Any) -> [Any] {
    var out: [Any] = __pytra_as_list([])
    do {
        let __iter_0 = __pytra_as_list(values)
        var __i_1: Int64 = 0
        while __i_1 < Int64(__iter_0.count) {
            let value = __iter_0[Int(__i_1)]
            out.append(value)
            __i_1 += 1
        }
    }
    return __pytra_as_list(reversed(out))
}

func py_enumerate_object(_ values: Any, _ start: Int64) -> [Any] {
    var out: [Any] = __pytra_as_list([])
    var i: Int64 = start
    do {
        let __iter_0 = __pytra_as_list(values)
        var __i_1: Int64 = 0
        while __i_1 < Int64(__iter_0.count) {
            let value = __iter_0[Int(__i_1)]
            out.append([i, value])
            i += Int64(1)
            __i_1 += 1
        }
    }
    return out
}
