// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/iter_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

package main


func py_reversed_object(values any) []any {
    var out []any = __pytra_as_list([]any{})
    var i int64 = (__pytra_len(values) - int64(1))
    for (i >= int64(0)) {
        out = append(out, __pytra_get_index(values, i))
        i -= int64(1)
    }
    return __pytra_as_list(out)
}

func py_enumerate_object(values any, start int64) []any {
    var out []any = __pytra_as_list([]any{})
    var i int64 = int64(0)
    var n int64 = __pytra_len(values)
    for (i < n) {
        out = append(out, []any{(start + i), __pytra_get_index(values, i)})
        i += int64(1)
    }
    return __pytra_as_list(out)
}
