// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/iter_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

import scala.collection.mutable
import scala.util.boundary, boundary.break
import java.nio.file.{Files, Paths}


def py_reversed_object(values: Any): mutable.ArrayBuffer[Any] = {
    var out: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any]())
    val __iter_0 = __pytra_as_list(values)
    var __i_1: Long = 0L
    while (__i_1 < __iter_0.size.toLong) {
        val value = __iter_0(__i_1.toInt)
        out.append(value)
        __i_1 += 1L
    }
    return __pytra_as_list(reversed(out))
}

def py_enumerate_object(values: Any, start: Long): mutable.ArrayBuffer[Any] = {
    var out: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any]())
    var i: Long = start
    val __iter_0 = __pytra_as_list(values)
    var __i_1: Long = 0L
    while (__i_1 < __iter_0.size.toLong) {
        val value = __iter_0(__i_1.toInt)
        out.append(mutable.ArrayBuffer[Any](i, value))
        i += 1L
        __i_1 += 1L
    }
    return out
}
