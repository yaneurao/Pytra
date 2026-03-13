// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/predicates.py
// generated-by: tools/gen_runtime_from_manifest.py

package main


func py_any(values *Any) bool {
    var i int64 = int64(0)
    var n int64 = __pytra_len(values)
    for (i < n) {
        if __pytra_truthy(__pytra_get_index(values, i)) {
            return __pytra_truthy(true)
        }
        i += int64(1)
    }
    return __pytra_truthy(false)
}

func py_all(values *Any) bool {
    var i int64 = int64(0)
    var n int64 = __pytra_len(values)
    for (i < n) {
        if (!__pytra_truthy(__pytra_get_index(values, i))) {
            return __pytra_truthy(false)
        }
        i += int64(1)
    }
    return __pytra_truthy(true)
}
