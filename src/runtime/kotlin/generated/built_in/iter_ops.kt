// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/iter_ops.py
// generated-by: tools/gen_runtime_from_manifest.py



fun py_reversed_object(values: Any?): MutableList<Any?> {
    var out: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    var i: Long = (__pytra_len(values) - 1L)
    while ((__pytra_int(i) >= __pytra_int(0L))) {
        out.add(__pytra_get_index(values, i))
        i -= 1L
    }
    return out
}

fun py_enumerate_object(values: Any?, start: Long): MutableList<Any?> {
    var out: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    var i: Long = 0L
    var n: Long = __pytra_int(__pytra_len(values))
    while ((__pytra_int(i) < __pytra_int(n))) {
        out.add(mutableListOf((start + i), __pytra_get_index(values, i)))
        i += 1L
    }
    return out
}
