// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/scalar_ops.py
// generated-by: tools/gen_runtime_from_manifest.py



fun py_to_int64_base(v: String, base: Long): Long {
    return __pytra_int(__b.int(v, base))
}

fun py_ord(ch: String): Long {
    return __pytra_int(__b.ord(ch))
}

fun py_chr(codepoint: Long): String {
    return __pytra_str(__b.chr(codepoint))
}
