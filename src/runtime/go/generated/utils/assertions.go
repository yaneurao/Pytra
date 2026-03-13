// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/assertions.py
// generated-by: tools/gen_runtime_from_manifest.py

package main


func _eq_any(actual any, expected any) bool {
    return __pytra_truthy((py_to_string(actual) == py_to_string(expected)))
    return __pytra_truthy((actual == expected))
    return false
}

func py_assert_true(cond bool, label string) bool {
    if cond {
        return __pytra_truthy(true)
    }
    if (__pytra_str(label) != __pytra_str("")) {
        __pytra_print(nil)
    } else {
        __pytra_print("[assert_true] False")
    }
    return __pytra_truthy(false)
}

func py_assert_eq(actual any, expected any, label string) bool {
    var ok bool = __pytra_truthy(_eq_any(actual, expected))
    if ok {
        return __pytra_truthy(true)
    }
    if (__pytra_str(label) != __pytra_str("")) {
        __pytra_print(nil)
    } else {
        __pytra_print(nil)
    }
    return __pytra_truthy(false)
}

func py_assert_all(results []any, label string) bool {
    __iter_0 := __pytra_as_list(results)
    for __i_1 := int64(0); __i_1 < int64(len(__iter_0)); __i_1 += 1 {
        var v bool = __pytra_truthy(__iter_0[__i_1])
        if (!v) {
            if (__pytra_str(label) != __pytra_str("")) {
                __pytra_print(nil)
            } else {
                __pytra_print("[assert_all] False")
            }
            return __pytra_truthy(false)
        }
    }
    return __pytra_truthy(true)
}

func py_assert_stdout(expected_lines []any, fn any) bool {
    return __pytra_truthy(true)
}
