// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/iter_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

package main


func py_reversed_object(values any) []any {
    var out []any = __pytra_as_list([]any{})
    __iter_0 := __pytra_as_list(values)
    for __i_1 := int64(0); __i_1 < int64(len(__iter_0)); __i_1 += 1 {
        value := __iter_0[__i_1]
        out = append(out, value)
    }
    return __pytra_as_list(reversed(out))
}

func py_enumerate_object(values any, start int64) []any {
    var out []any = __pytra_as_list([]any{})
    var i int64 = start
    __iter_0 := __pytra_as_list(values)
    for __i_1 := int64(0); __i_1 < int64(len(__iter_0)); __i_1 += 1 {
        value := __iter_0[__i_1]
        out = append(out, []any{i, value})
        i += int64(1)
    }
    return __pytra_as_list(out)
}
