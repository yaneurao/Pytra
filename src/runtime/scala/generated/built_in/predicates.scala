// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/predicates.py
// generated-by: tools/gen_runtime_from_manifest.py

import scala.collection.mutable
import scala.util.boundary, boundary.break
import java.nio.file.{Files, Paths}


def py_any(values: Any): Boolean = {
    var i: Long = 0L
    var n: Long = __pytra_int(__pytra_len(values))
    while (i < n) {
        if (__pytra_truthy(__pytra_get_index(values, i))) {
            return true
        }
        i += 1L
    }
    return false
}

def py_all(values: Any): Boolean = {
    var i: Long = 0L
    var n: Long = __pytra_int(__pytra_len(values))
    while (i < n) {
        if (!__pytra_truthy(__pytra_get_index(values, i))) {
            return false
        }
        i += 1L
    }
    return true
}
