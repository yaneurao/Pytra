// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/predicates.py
// generated-by: tools/gen_runtime_from_manifest.py

import Foundation


func py_any(_ values: Any) -> Bool {
    var i: Int64 = Int64(0)
    var n: Int64 = __pytra_int(__pytra_len(values))
    while (__pytra_int(i) < __pytra_int(n)) {
        if __pytra_truthy(__pytra_getIndex(values, i)) {
            return true
        }
        i += Int64(1)
    }
    return false
}

func py_all(_ values: Any) -> Bool {
    var i: Int64 = Int64(0)
    var n: Int64 = __pytra_int(__pytra_len(values))
    while (__pytra_int(i) < __pytra_int(n)) {
        if (!__pytra_truthy(__pytra_getIndex(values, i))) {
            return false
        }
        i += Int64(1)
    }
    return true
}
