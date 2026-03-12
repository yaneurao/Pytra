// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/contains.py
// generated-by: tools/gen_runtime_from_manifest.py

import Foundation


func py_contains_dict_object(_ values: Any, _ key: Any) -> Bool {
    var needle: String = __pytra_str(key)
    do {
        let __iter_0 = __pytra_as_list(values)
        var __i_1: Int64 = 0
        while __i_1 < Int64(__iter_0.count) {
            let cur = __iter_0[Int(__i_1)]
            if (__pytra_str(cur) == __pytra_str(needle)) {
                return true
            }
            __i_1 += 1
        }
    }
    return false
}

func py_contains_list_object(_ values: Any, _ key: Any) -> Bool {
    do {
        let __iter_0 = __pytra_as_list(values)
        var __i_1: Int64 = 0
        while __i_1 < Int64(__iter_0.count) {
            let cur = __iter_0[Int(__i_1)]
            if (__pytra_str(cur) == __pytra_str(key)) {
                return true
            }
            __i_1 += 1
        }
    }
    return false
}

func py_contains_set_object(_ values: Any, _ key: Any) -> Bool {
    do {
        let __iter_0 = __pytra_as_list(values)
        var __i_1: Int64 = 0
        while __i_1 < Int64(__iter_0.count) {
            let cur = __iter_0[Int(__i_1)]
            if (__pytra_str(cur) == __pytra_str(key)) {
                return true
            }
            __i_1 += 1
        }
    }
    return false
}

func py_contains_str_object(_ values: Any, _ key: Any) -> Bool {
    var needle: String = __pytra_str(key)
    var haystack: String = __pytra_str(values)
    var n: Int64 = __pytra_len(haystack)
    var m: Int64 = __pytra_len(needle)
    if (__pytra_int(m) == __pytra_int(Int64(0))) {
        return true
    }
    var i: Int64 = Int64(0)
    var last: Int64 = (n - m)
    while (__pytra_int(i) <= __pytra_int(last)) {
        var j: Int64 = Int64(0)
        var ok: Bool = true
        while (__pytra_int(j) < __pytra_int(m)) {
            if (__pytra_str(__pytra_getIndex(haystack, (i + j))) != __pytra_str(__pytra_getIndex(needle, j))) {
                ok = false
                break
            }
            j += Int64(1)
        }
        if ok {
            return true
        }
        i += Int64(1)
    }
    return false
}
