// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/sequence.py
// generated-by: tools/gen_runtime_from_manifest.py



fun py_range(start: Long, stop: Long, step: Long): MutableList<Any?> {
    var out: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    if ((__pytra_int(step) == __pytra_int(0L))) {
        return out
    }
    if ((__pytra_int(step) > __pytra_int(0L))) {
        var i: Long = start
        while ((__pytra_int(i) < __pytra_int(stop))) {
            out.add(i)
            i += step
        }
    } else {
        var i: Long = start
        while ((__pytra_int(i) > __pytra_int(stop))) {
            out.add(i)
            i += step
        }
    }
    return out
}

fun py_repeat(v: String, n: Long): String {
    if ((__pytra_int(n) <= __pytra_int(0L))) {
        return ""
    }
    var out: String = ""
    var i: Long = 0L
    while ((__pytra_int(i) < __pytra_int(n))) {
        out += v
        i += 1L
    }
    return out
}
