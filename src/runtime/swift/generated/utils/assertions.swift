// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/assertions.py
// generated-by: tools/gen_runtime_from_manifest.py

import Foundation


func _eq_any(_ actual: Any, _ expected: Any) -> Bool {
    return (__pytra_str(py_to_string(actual)) == __pytra_str(py_to_string(expected)))
    return (__pytra_str(actual) == __pytra_str(expected))
    return false
}

func py_assert_true(_ cond: Bool, _ label: String) -> Bool {
    if cond {
        return true
    }
    if (__pytra_str(label) != __pytra_str("")) {
        __pytra_print(__pytra_any_default())
    } else {
        __pytra_print("[assert_true] False")
    }
    return false
}

func py_assert_eq(_ actual: Any, _ expected: Any, _ label: String) -> Bool {
    var ok: Bool = _eq_any(actual, expected)
    if ok {
        return true
    }
    if (__pytra_str(label) != __pytra_str("")) {
        __pytra_print(__pytra_any_default())
    } else {
        __pytra_print(__pytra_any_default())
    }
    return false
}

func py_assert_all(_ results: [Any], _ label: String) -> Bool {
    do {
        let __iter_0 = __pytra_as_list(results)
        var __i_1: Int64 = 0
        while __i_1 < Int64(__iter_0.count) {
            let v: Bool = __pytra_truthy(__iter_0[Int(__i_1)])
            if (!v) {
                if (__pytra_str(label) != __pytra_str("")) {
                    __pytra_print(__pytra_any_default())
                } else {
                    __pytra_print("[assert_all] False")
                }
                return false
            }
            __i_1 += 1
        }
    }
    return true
}

func py_assert_stdout(_ expected_lines: [Any], _ fn: Any) -> Bool {
    return true
}
