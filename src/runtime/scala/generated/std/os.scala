// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/os.py
// generated-by: tools/gen_runtime_from_manifest.py

import scala.collection.mutable
import scala.util.boundary, boundary.break
import java.nio.file.{Files, Paths}


def getcwd(): String = {
    return __pytra_str(__os.getcwd())
}

def mkdir(p: String): Unit = {
    __os.mkdir(p)
}

def makedirs(p: String, exist_ok: Boolean): Unit = {
    __os.makedirs(p, exist_ok)
}
