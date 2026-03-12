// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/zip_ops.py
// generated-by: tools/gen_runtime_from_manifest.py



fun zip(lhs: MutableList<Any?>, rhs: MutableList<Any?>): MutableList<Any?> {
    var out: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    var i: Long = 0L
    var n: Long = __pytra_len(lhs)
    if ((__pytra_int(__pytra_len(rhs)) < __pytra_int(n))) {
        n = __pytra_len(rhs)
    }
    while ((__pytra_int(i) < __pytra_int(n))) {
        out.add(mutableListOf(__pytra_get_index(lhs, i), __pytra_get_index(rhs, i)))
        i += 1L
    }
    return out
}
