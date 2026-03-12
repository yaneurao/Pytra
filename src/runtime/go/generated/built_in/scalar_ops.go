// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/scalar_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

package main


func py_to_int64_base(v string, base int64) int64 {
    return __pytra_int(__b.int(v, base))
}

func py_ord(ch string) int64 {
    return __pytra_int(__b.ord(ch))
}

func py_chr(codepoint int64) string {
    return __pytra_str(__b.chr(codepoint))
}
