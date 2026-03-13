// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/numeric_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

import scala.collection.mutable
import scala.util.boundary, boundary.break
import java.nio.file.{Files, Paths}


def sum(values: mutable.ArrayBuffer[Any]): T = {
    if (__pytra_len(values) == 0L) {
        return 0L
    }
    var acc: Any = __pytra_get_index(values, 0L) - __pytra_get_index(values, 0L)
    var i: Long = 0L
    var n: Long = __pytra_len(values)
    while (i < n) {
        acc += __pytra_get_index(values, i)
        i += 1L
    }
    return acc
}

def py_min(a: T, b: T): T = {
    if (__pytra_float(a) < __pytra_float(b)) {
        return a
    }
    return b
}

def py_max(a: T, b: T): T = {
    if (__pytra_float(a) > __pytra_float(b)) {
        return a
    }
    return b
}
