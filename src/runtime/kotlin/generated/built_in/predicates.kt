// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/predicates.py
// generated-by: tools/gen_runtime_from_manifest.py



fun py_any(values: Any): Boolean {
    var i: Long = 0L
    var n: Long = __pytra_int(__pytra_len(values))
    while ((__pytra_int(i) < __pytra_int(n))) {
        if (__pytra_truthy(__pytra_get_index(values, i))) {
            return true
        }
        i += 1L
    }
    return false
}

fun py_all(values: Any): Boolean {
    var i: Long = 0L
    var n: Long = __pytra_int(__pytra_len(values))
    while ((__pytra_int(i) < __pytra_int(n))) {
        if ((!__pytra_truthy(__pytra_get_index(values, i)))) {
            return false
        }
        i += 1L
    }
    return true
}
