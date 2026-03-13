// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/sequence.py
// generated-by: tools/gen_runtime_from_manifest.py

package main


func py_range(start int64, stop int64, step int64) []any {
    var out []any = __pytra_as_list([]any{})
    if (step == int64(0)) {
        return __pytra_as_list(out)
    }
    if (step > int64(0)) {
        var i int64 = start
        for (i < stop) {
            out = append(out, i)
            i += step
        }
    } else {
        var i int64 = start
        for (i > stop) {
            out = append(out, i)
            i += step
        }
    }
    return __pytra_as_list(out)
}

func py_repeat(v string, n int64) string {
    if (n <= int64(0)) {
        return __pytra_str("")
    }
    var out string = __pytra_str("")
    var i int64 = int64(0)
    for (i < n) {
        out += v
        i += int64(1)
    }
    return __pytra_str(out)
}
