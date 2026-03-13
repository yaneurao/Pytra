// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/assertions.py
// generated-by: tools/gen_runtime_from_manifest.py



fun _eq_any(actual: Any?, expected: Any?): Boolean {
    return (__pytra_str(py_to_string(actual)) == __pytra_str(py_to_string(expected)))
    return (__pytra_str(actual) == __pytra_str(expected))
    return false
}

fun py_assert_true(cond: Boolean, label: String): Boolean {
    if (cond) {
        return true
    }
    if ((__pytra_str(label) != __pytra_str(""))) {
        __pytra_print(__pytra_any_default())
    } else {
        __pytra_print("[assert_true] False")
    }
    return false
}

fun py_assert_eq(actual: Any?, expected: Any?, label: String): Boolean {
    var ok: Boolean = _eq_any(actual, expected)
    if (ok) {
        return true
    }
    if ((__pytra_str(label) != __pytra_str(""))) {
        __pytra_print(__pytra_any_default())
    } else {
        __pytra_print(__pytra_any_default())
    }
    return false
}

fun py_assert_all(results: MutableList<Any?>, label: String): Boolean {
    val __iter_0 = __pytra_as_list(results)
    var __i_1: Long = 0L
    while (__i_1 < __iter_0.size.toLong()) {
        val v: Boolean = __pytra_truthy(__iter_0[__i_1.toInt()])
        if ((!v)) {
            if ((__pytra_str(label) != __pytra_str(""))) {
                __pytra_print(__pytra_any_default())
            } else {
                __pytra_print("[assert_all] False")
            }
            return false
        }
        __i_1 += 1L
    }
    return true
}

fun py_assert_stdout(expected_lines: MutableList<Any?>, fn: Any?): Boolean {
    return true
}
