// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/sequence.py
// generated-by: tools/gen_runtime_from_manifest.py

import scala.collection.mutable
import scala.util.boundary, boundary.break
import java.nio.file.{Files, Paths}


def py_range(start: Long, stop: Long, step: Long): mutable.ArrayBuffer[Long] = {
    var out: mutable.ArrayBuffer[Long] = __pytra_as_list(mutable.ArrayBuffer[Any]()).asInstanceOf[mutable.ArrayBuffer[Long]]
    if (step == 0L) {
        return out
    }
    if (step > 0L) {
        var i: Long = start
        while (i < stop) {
            out.append(i)
            i += step
        }
    } else {
        var i: Long = start
        while (i > stop) {
            out.append(i)
            i += step
        }
    }
    return out
}

def py_repeat(v: String, n: Long): String = {
    if (n <= 0L) {
        return ""
    }
    var out: String = ""
    var i: Long = 0L
    while (i < n) {
        out += v
        i += 1L
    }
    return out
}
