// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/contains.py
// generated-by: tools/gen_runtime_from_manifest.py

package main


func py_contains_dict_object(values any, key any) bool {
    var needle string = __pytra_str(__pytra_str(key))
    __iter_0 := __pytra_as_list(values)
    for __i_1 := int64(0); __i_1 < int64(len(__iter_0)); __i_1 += 1 {
        cur := __iter_0[__i_1]
        if (__pytra_str(cur) == __pytra_str(needle)) {
            return __pytra_truthy(true)
        }
    }
    return __pytra_truthy(false)
}

func py_contains_list_object(values any, key any) bool {
    __iter_0 := __pytra_as_list(values)
    for __i_1 := int64(0); __i_1 < int64(len(__iter_0)); __i_1 += 1 {
        cur := __iter_0[__i_1]
        if (cur == key) {
            return __pytra_truthy(true)
        }
    }
    return __pytra_truthy(false)
}

func py_contains_set_object(values any, key any) bool {
    __iter_0 := __pytra_as_list(values)
    for __i_1 := int64(0); __i_1 < int64(len(__iter_0)); __i_1 += 1 {
        cur := __iter_0[__i_1]
        if (cur == key) {
            return __pytra_truthy(true)
        }
    }
    return __pytra_truthy(false)
}

func py_contains_str_object(values any, key any) bool {
    var needle string = __pytra_str(__pytra_str(key))
    var haystack string = __pytra_str(__pytra_str(values))
    var n int64 = __pytra_len(haystack)
    var m int64 = __pytra_len(needle)
    if (m == int64(0)) {
        return __pytra_truthy(true)
    }
    var i int64 = int64(0)
    var last int64 = (n - m)
    for (i <= last) {
        var j int64 = int64(0)
        var ok bool = __pytra_truthy(true)
        for (j < m) {
            if (__pytra_str(__pytra_str(__pytra_get_index(haystack, (i + j)))) != __pytra_str(__pytra_str(__pytra_get_index(needle, j)))) {
                ok = __pytra_truthy(false)
                break
            }
            j += int64(1)
        }
        if ok {
            return __pytra_truthy(true)
        }
        i += int64(1)
    }
    return __pytra_truthy(false)
}
