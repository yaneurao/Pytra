// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/zip_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

import scala.collection.mutable
import scala.util.boundary, boundary.break
import java.nio.file.{Files, Paths}


def zip(lhs: mutable.ArrayBuffer[Any], rhs: mutable.ArrayBuffer[Any]): mutable.ArrayBuffer[Any] = {
    var out: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any]())
    var i: Long = 0L
    var n: Long = __pytra_len(lhs)
    if (__pytra_len(rhs) < n) {
        n = __pytra_len(rhs)
    }
    while (i < n) {
        out.append(mutable.ArrayBuffer[Any](__pytra_get_index(lhs, i), __pytra_get_index(rhs, i)))
        i += 1L
    }
    return out
}
