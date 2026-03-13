// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/iter_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

import scala.collection.mutable
import scala.util.boundary, boundary.break
import java.nio.file.{Files, Paths}


def py_reversed_object(values: Any): mutable.ArrayBuffer[Any] = {
    var out: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any]())
    var i: Long = (__pytra_len(values) - 1L)
    while (i >= 0L) {
        out.append(__pytra_get_index(values, i))
        i -= 1L
    }
    return out
}

def py_enumerate_object(values: Any, start: Long): mutable.ArrayBuffer[Any] = {
    var out: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any]())
    var i: Long = 0L
    var n: Long = __pytra_int(__pytra_len(values))
    while (i < n) {
        out.append(mutable.ArrayBuffer[Any](start + i, __pytra_get_index(values, i)))
        i += 1L
    }
    return out
}
