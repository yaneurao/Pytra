// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/numeric_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

package main


func sum(values []any) *T {
    if (__pytra_len(values) == int64(0)) {
        return __pytra_as_T(int64(0))
    }
    var acc any = (__pytra_as_T(__pytra_get_index(values, int64(0))) - __pytra_as_T(__pytra_get_index(values, int64(0))))
    var i int64 = int64(0)
    var n int64 = __pytra_len(values)
    for (i < n) {
        acc += __pytra_as_T(__pytra_get_index(values, i))
        i += int64(1)
    }
    return __pytra_as_T(acc)
}

func py_min(a *T, b *T) *T {
    if (a < b) {
        return __pytra_as_T(a)
    }
    return __pytra_as_T(b)
}

func py_max(a *T, b *T) *T {
    if (a > b) {
        return __pytra_as_T(a)
    }
    return __pytra_as_T(b)
}
