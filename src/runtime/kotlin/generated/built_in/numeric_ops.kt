// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/numeric_ops.py
// generated-by: tools/gen_runtime_from_manifest.py



fun sum(values: MutableList<Any?>): T {
    if ((__pytra_int(__pytra_len(values)) == __pytra_int(0L))) {
        return 0L
    }
    var acc: Any? = (__pytra_get_index(values, 0L) - __pytra_get_index(values, 0L))
    var i: Long = 0L
    var n: Long = __pytra_len(values)
    while ((__pytra_int(i) < __pytra_int(n))) {
        acc += __pytra_get_index(values, i)
        i += 1L
    }
    return acc
}

fun py_min(a: T, b: T): T {
    if ((__pytra_float(a) < __pytra_float(b))) {
        return a
    }
    return b
}

fun py_max(a: T, b: T): T {
    if ((__pytra_float(a) > __pytra_float(b))) {
        return a
    }
    return b
}
