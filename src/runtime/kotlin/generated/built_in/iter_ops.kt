// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/iter_ops.py
// generated-by: tools/gen_runtime_from_manifest.py



fun py_reversed_object(values: Any?): MutableList<Any?> {
    var out: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    val __iter_0 = __pytra_as_list(values)
    var __i_1: Long = 0L
    while (__i_1 < __iter_0.size.toLong()) {
        val value = __iter_0[__i_1.toInt()]
        out.add(value)
        __i_1 += 1L
    }
    return __pytra_as_list(reversed(out))
}

fun py_enumerate_object(values: Any?, start: Long): MutableList<Any?> {
    var out: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    var i: Long = start
    val __iter_0 = __pytra_as_list(values)
    var __i_1: Long = 0L
    while (__i_1 < __iter_0.size.toLong()) {
        val value = __iter_0[__i_1.toInt()]
        out.add(mutableListOf(i, value))
        i += 1L
        __i_1 += 1L
    }
    return out
}
