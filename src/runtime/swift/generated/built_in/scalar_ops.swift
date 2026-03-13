// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/scalar_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

import Foundation


func py_to_int64_base(_ v: String, _ base: Int64) -> Int64 {
    return __pytra_int(v)
}

func py_ord(_ ch: String) -> Int64 {
    return __pytra_int(__b.ord(ch))
}

func py_chr(_ codepoint: Int64) -> String {
    return __pytra_str(__b.chr(codepoint))
}
