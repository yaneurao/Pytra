// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/predicates.py
// generated-by: tools/gen_runtime_from_manifest.py

import Foundation


func py_any(_ values: Any) -> Bool {
    do {
        let __iter_0 = __pytra_as_list(values)
        var __i_1: Int64 = 0
        while __i_1 < Int64(__iter_0.count) {
            let value = __iter_0[Int(__i_1)]
            if __pytra_truthy(value) {
                return true
            }
            __i_1 += 1
        }
    }
    return false
}

func py_all(_ values: Any) -> Bool {
    do {
        let __iter_0 = __pytra_as_list(values)
        var __i_1: Int64 = 0
        while __i_1 < Int64(__iter_0.count) {
            let value = __iter_0[Int(__i_1)]
            if (!__pytra_truthy(value)) {
                return false
            }
            __i_1 += 1
        }
    }
    return true
}
