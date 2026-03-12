// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/contains.py
// generated-by: tools/gen_runtime_from_manifest.py



fun py_contains_dict_object(values: Any?, key: Any?): Boolean {
    var needle: String = __pytra_str(key)
    val __iter_0 = __pytra_as_list(values)
    var __i_1: Long = 0L
    while (__i_1 < __iter_0.size.toLong()) {
        val cur = __iter_0[__i_1.toInt()]
        if ((__pytra_str(cur) == __pytra_str(needle))) {
            return true
        }
        __i_1 += 1L
    }
    return false
}

fun py_contains_list_object(values: Any?, key: Any?): Boolean {
    val __iter_0 = __pytra_as_list(values)
    var __i_1: Long = 0L
    while (__i_1 < __iter_0.size.toLong()) {
        val cur = __iter_0[__i_1.toInt()]
        if ((__pytra_str(cur) == __pytra_str(key))) {
            return true
        }
        __i_1 += 1L
    }
    return false
}

fun py_contains_set_object(values: Any?, key: Any?): Boolean {
    val __iter_0 = __pytra_as_list(values)
    var __i_1: Long = 0L
    while (__i_1 < __iter_0.size.toLong()) {
        val cur = __iter_0[__i_1.toInt()]
        if ((__pytra_str(cur) == __pytra_str(key))) {
            return true
        }
        __i_1 += 1L
    }
    return false
}

fun py_contains_str_object(values: Any?, key: Any?): Boolean {
    var needle: String = __pytra_str(key)
    var haystack: String = __pytra_str(values)
    var n: Long = __pytra_len(haystack)
    var m: Long = __pytra_len(needle)
    if ((__pytra_int(m) == __pytra_int(0L))) {
        return true
    }
    var i: Long = 0L
    var last: Long = (n - m)
    while ((__pytra_int(i) <= __pytra_int(last))) {
        var j: Long = 0L
        var ok: Boolean = true
        while ((__pytra_int(j) < __pytra_int(m))) {
            if ((__pytra_str(__pytra_get_index(haystack, (i + j))) != __pytra_str(__pytra_get_index(needle, j)))) {
                ok = false
                break
            }
            j += 1L
        }
        if (ok) {
            return true
        }
        i += 1L
    }
    return false
}
