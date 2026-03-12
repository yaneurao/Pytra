// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/zip_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

package main


func zip(lhs []any, rhs []any) []any {
    var out []any = __pytra_as_list([]any{})
    var i int64 = int64(0)
    var n int64 = __pytra_len(lhs)
    if (__pytra_len(rhs) < n) {
        n = __pytra_len(rhs)
    }
    for (i < n) {
        out = append(out, []any{__pytra_as_A(__pytra_get_index(lhs, i)), __pytra_as_B(__pytra_get_index(rhs, i))})
        i += int64(1)
    }
    return __pytra_as_list(out)
}
