// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/scalar_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

import scala.collection.mutable
import scala.util.boundary, boundary.break
import java.nio.file.{Files, Paths}


def py_to_int64_base(v: String, base: Long): Long = {
    return __pytra_int(__b.int(v, base))
}

def py_ord(ch: String): Long = {
    return __pytra_int(__b.ord(ch))
}

def py_chr(codepoint: Long): String = {
    return __pytra_str(__b.chr(codepoint))
}
