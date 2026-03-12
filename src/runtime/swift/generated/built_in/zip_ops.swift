// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/zip_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

import Foundation


func zip(_ lhs: [Any], _ rhs: [Any]) -> [Any] {
    var out: [Any] = __pytra_as_list([])
    var i: Int64 = Int64(0)
    var n: Int64 = __pytra_len(lhs)
    if (__pytra_int(__pytra_len(rhs)) < __pytra_int(n)) {
        n = __pytra_len(rhs)
    }
    while (__pytra_int(i) < __pytra_int(n)) {
        out.append([__pytra_getIndex(lhs, i), __pytra_getIndex(rhs, i)])
        i += Int64(1)
    }
    return out
}
