// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/sequence.py
// generated-by: tools/gen_runtime_from_manifest.py

import Foundation


func py_range(_ start: Int64, _ stop: Int64, _ step: Int64) -> [Any] {
    var out: [Any] = __pytra_as_list([])
    if (__pytra_int(step) == __pytra_int(Int64(0))) {
        return out
    }
    if (__pytra_int(step) > __pytra_int(Int64(0))) {
        var i: Int64 = start
        while (__pytra_int(i) < __pytra_int(stop)) {
            out.append(i)
            i += step
        }
    } else {
        var i: Int64 = start
        while (__pytra_int(i) > __pytra_int(stop)) {
            out.append(i)
            i += step
        }
    }
    return out
}

func py_repeat(_ v: String, _ n: Int64) -> String {
    if (__pytra_int(n) <= __pytra_int(Int64(0))) {
        return ""
    }
    var out: String = ""
    var i: Int64 = Int64(0)
    while (__pytra_int(i) < __pytra_int(n)) {
        out += v
        i += Int64(1)
    }
    return out
}
