// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/predicates.py
// generated-by: tools/gen_runtime_from_manifest.py

package main


func py_any(values *Any) bool {
    __iter_0 := __pytra_as_list(values)
    for __i_1 := int64(0); __i_1 < int64(len(__iter_0)); __i_1 += 1 {
        value := __iter_0[__i_1]
        if __pytra_truthy(value) {
            return __pytra_truthy(true)
        }
    }
    return __pytra_truthy(false)
}

func py_all(values *Any) bool {
    __iter_0 := __pytra_as_list(values)
    for __i_1 := int64(0); __i_1 < int64(len(__iter_0)); __i_1 += 1 {
        value := __iter_0[__i_1]
        if (!__pytra_truthy(value)) {
            return __pytra_truthy(false)
        }
    }
    return __pytra_truthy(true)
}
