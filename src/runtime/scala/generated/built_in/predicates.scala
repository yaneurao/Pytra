// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/predicates.py
// generated-by: tools/gen_runtime_from_manifest.py

import scala.collection.mutable
import scala.util.boundary, boundary.break
import java.nio.file.{Files, Paths}


def py_any(values: Any): Boolean = {
    val __iter_0 = __pytra_as_list(values)
    var __i_1: Long = 0L
    while (__i_1 < __iter_0.size.toLong) {
        val value = __iter_0(__i_1.toInt)
        if (__pytra_truthy(value)) {
            return true
        }
        __i_1 += 1L
    }
    return false
}

def py_all(values: Any): Boolean = {
    val __iter_0 = __pytra_as_list(values)
    var __i_1: Long = 0L
    while (__i_1 < __iter_0.size.toLong) {
        val value = __iter_0(__i_1.toInt)
        if (!__pytra_truthy(value)) {
            return false
        }
        __i_1 += 1L
    }
    return true
}
